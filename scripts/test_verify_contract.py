"""Compatibility and drift checks without credentials or a network service."""

import contextlib
import copy
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "verify_contract", Path(__file__).with_name("verify-contract.py")
)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def contract(version=None):
    suffix = f"-v{version}" if version else ""
    return verifier.read_json(
        verifier.ROOT / "contracts" / f"agentix-contract{suffix}.json"
    )


def rest_docs(version=None):
    expected = contract(version)
    methods = {}
    for operation in expected["rest"]["operations"]:
        method, path = operation.split(" ", 1)
        methods.setdefault(path, []).append(method)
    docs = {
        "service": "agentix",
        "status": "production",
        "methods": [{"path": path, "methods": verbs} for path, verbs in methods.items()],
        "restMethodCount": expected["rest"]["methodCount"],
        "types": expected["types"],
    }
    if version != "0.3":
        docs["coordination"] = {}
    if version is None:
        docs["activation"] = {}
    return docs


class CompatibilityTests(unittest.TestCase):
    def verify_rest(self, docs):
        with patch.object(verifier, "request_json", return_value=docs) as request:
            verifier.verify_live_rest(contract(), "https://agentix.example/")
            request.assert_called_once_with("https://agentix.example/api/docs")

    def test_rest_accepts_each_released_contract(self):
        for version in ["0.3", "0.4", None]:
            with self.subTest(version=version):
                self.verify_rest(rest_docs(version))

    def test_missing_activation_marker_does_not_hide_a_changed_contract(self):
        docs = rest_docs()
        del docs["activation"]
        with self.assertRaisesRegex(SystemExit, "live REST operations drift"):
            self.verify_rest(docs)

    def test_every_version_rejects_missing_or_duplicate_operations(self):
        for version in ["0.3", "0.4", None]:
            for mutation in ["missing", "duplicate"]:
                with self.subTest(version=version, mutation=mutation):
                    docs = rest_docs(version)
                    if mutation == "missing":
                        docs["methods"].pop()
                    else:
                        docs["methods"].append(copy.deepcopy(docs["methods"][0]))
                    with self.assertRaises(SystemExit):
                        self.verify_rest(docs)

    def test_mcp_accepts_legacy_and_current_json_and_sse(self):
        for version in ["0.3", "0.4", None]:
            expected = contract(version)
            tools = [
                {
                    "name": name,
                    "annotations": {"readOnlyHint": name in expected["mcp"]["readTools"]},
                }
                for name in expected["mcp"]["tools"]
            ]
            raw = json.dumps({"result": {"tools": tools}})
            for payload in [raw, f"event: message\ndata: {raw}\n\n"]:
                with self.subTest(version=version, transport=payload[:5]):
                    with patch.object(verifier, "urlopen", return_value=io.BytesIO(payload.encode())):
                        with contextlib.redirect_stdout(io.StringIO()):
                            verifier.verify_live_mcp(contract(), "https://agentix.example", "test-token")

    def test_mcp_cannot_fall_back_to_legacy_after_losing_claim_tool(self):
        expected = contract()
        tools = [{"name": name} for name in expected["mcp"]["tools"] if name != "claim_issue"]
        raw = json.dumps({"result": {"tools": tools}}).encode()
        with patch.object(verifier, "urlopen", return_value=io.BytesIO(raw)):
            with self.assertRaisesRegex(SystemExit, "live MCP tool names drift"):
                verifier.verify_live_mcp(contract(), "https://agentix.example", "test-token")


if __name__ == "__main__":
    unittest.main()

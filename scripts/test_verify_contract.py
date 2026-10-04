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
    def schema_docs(self):
        docs = rest_docs()
        docs["schemaContract"] = copy.deepcopy(verifier.schema_snapshot())
        return docs

    def test_schema_contract_accepts_current_baseline(self):
        self.verify_rest(self.schema_docs())

    def test_candidate_requires_schema_marker_but_legacy_probe_still_accepts_old_service(self):
        docs = self.schema_docs()
        self.verify_rest(docs, require_schema_contract=True)
        del docs["schemaContract"]
        with self.assertRaisesRegex(SystemExit, "required schemaContract marker"):
            self.verify_rest(docs, require_schema_contract=True)
        self.verify_rest(docs)

    def test_candidate_requires_mcp_token_without_making_an_unauthenticated_request(self):
        with patch.object(verifier, "urlopen") as request:
            for token in [None, ""]:
                with self.subTest(token=token):
                    with self.assertRaisesRegex(SystemExit, "requires authenticated MCP"):
                        verifier.verify_live_mcp(contract(), "https://agentix.example", token, require_mcp=True)
            verifier.verify_live_mcp(contract(), "https://agentix.example", None)
            request.assert_not_called()

    def test_candidate_requirements_cannot_succeed_as_static_only_checks(self):
        for flag in ["--require-schema-contract", "--require-mcp"]:
            with self.subTest(flag=flag):
                with patch.object(verifier.sys, "argv", ["verify-contract.py", flag]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        verifier.parse_args()
                    self.assertEqual(raised.exception.code, 2)
        with patch.object(verifier.sys, "argv", ["verify-contract.py", "--live", "--require-schema-contract", "--require-mcp"]):
            args = verifier.parse_args()
            self.assertTrue(args.live and args.require_schema_contract and args.require_mcp)

    def test_schema_contract_rejects_capability_changes(self):
        for field, value in [("strictMcpInputs", False), ("strictMcpInputs", 1), ("inboxExplicitSelection", False), ("testCommandMaxLength", 2000), ("documentReadersVersion", 2), ("backlinksReadersVersion", 2), ("issueCommentsReadersVersion", 2)]:
            with self.subTest(field=field):
                docs = self.schema_docs()
                docs["schemaContract"]["capabilities"][field] = value
                with self.assertRaisesRegex(SystemExit, "schema/capability drift"):
                    self.verify_rest(docs)
        docs = self.schema_docs()
        docs["schemaContract"]["version"] = 2
        with self.assertRaisesRegex(SystemExit, "schema/capability drift"):
            self.verify_rest(docs)

    def test_schema_contract_rejects_changed_validation_semantics(self):
        mutations = [
            lambda schema: schema["rest"]["POST /api/onboarding/issue"]["properties"]["testCommand"].update(maxLength=2000),
            lambda schema: schema["mcp"]["complete_issue"]["properties"].pop("claimId"),
            lambda schema: schema["mcp"]["complete_issue"]["required"].remove("specRevision"),
            lambda schema: schema["mcp"]["set_task_spec"].update(additionalProperties=True),
            lambda schema: schema["mcp"]["set_task_spec"]["properties"]["claimId"].update(type="number"),
            lambda schema: schema["mcp"]["mark_read"]["properties"]["notificationIds"].update(minItems=0),
            lambda schema: schema["mcp"]["list_documents"]["properties"]["limit"].update(maximum=500),
            lambda schema: schema["mcp"]["list_documents"]["properties"].pop("offset"),
            lambda schema: schema["mcp"]["get_backlinks"]["properties"]["limit"].update(maximum=500),
            lambda schema: schema["mcp"]["get_backlinks"]["properties"]["limit"].update(default=50),
            lambda schema: schema["mcp"]["get_backlinks"]["properties"].pop("offset"),
            lambda schema: schema["mcp"]["list_comments"]["properties"].pop("cursor"),
            lambda schema: schema["mcp"]["list_comments"]["properties"]["limit"].update(maximum=500),
            lambda schema: schema["rest"]["GET /api/issues/:ref/comments"]["properties"]["limit"].update(default=200),
            lambda schema: schema["rest"]["GET /api/issues/:ref/comments"].update(additionalProperties=True),
            lambda schema: schema["rest"]["GET /api/documents"]["properties"]["limit"].update(default=200),
            lambda schema: schema["rest"]["GET /api/documents/:ref/versions"]["anyOf"][1]["properties"]["limit"].update(maximum=500),
            lambda schema: schema["rest"]["GET /api/documents/:ref/versions"]["anyOf"][0]["properties"]["versionId"].pop("format"),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                docs = self.schema_docs()
                mutate(docs["schemaContract"])
                with self.assertRaisesRegex(SystemExit, "schema/capability drift"):
                    self.verify_rest(docs)

    def test_mcp_checks_real_catalogue_schemas_against_declared_baseline(self):
        expected = contract()
        schemas = verifier.schema_snapshot()
        tools = [{"name": name, "annotations": {"readOnlyHint": name in expected["mcp"]["readTools"]}, "inputSchema": copy.deepcopy(schemas["mcp"].get(name, {}))} for name in expected["mcp"]["tools"]]
        def verify():
            raw = json.dumps({"result": {"tools": tools}}).encode()
            with patch.object(verifier, "urlopen", return_value=io.BytesIO(raw)):
                with contextlib.redirect_stdout(io.StringIO()):
                    verifier.verify_live_mcp(expected, "https://agentix.example", "test-token", schemas)
        verify()
        next(tool for tool in tools if tool["name"] == "set_task_spec")["inputSchema"]["properties"]["expectedRevision"] = {"type": "string"}
        with self.assertRaisesRegex(SystemExit, "live MCP set_task_spec schema/capability drift"):
            verify()

    def verify_rest(self, docs, require_schema_contract=False):
        with patch.object(verifier, "request_json", return_value=docs) as request:
            verifier.verify_live_rest(contract(), "https://agentix.example/", require_schema_contract)
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

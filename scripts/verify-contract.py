#!/usr/bin/env python3
"""Verify that the packaged Agentix instructions match the declared live contract.

The static check is deliberately credential-free.  --live reads the public REST
contract and can additionally inspect the authenticated MCP catalogue only when
AGENTIX_CONTRACT_MCP_TOKEN is supplied through the runner environment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "contracts" / "agentix-contract.json"
SKILL_PATH = ROOT / "skills" / "agentix" / "SKILL.md"
CLAUDE_MANIFEST_PATH = ROOT / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST_PATH = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
DEFAULT_BASE_URL = "https://agentix.moone.dev"


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {path.relative_to(ROOT)}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain an object")
    return value


def string_values(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"{label} must be an array of strings")
    return list(value)


def sorted_unique(values: list[str], label: str) -> list[str]:
    if len(values) != len(set(values)):
        fail(f"{label} contains duplicates")
    return sorted(values)


def snapshot() -> dict[str, Any]:
    payload = read_json(SNAPSHOT_PATH)
    mcp = payload.get("mcp")
    rest = payload.get("rest")
    types = payload.get("types")
    if not isinstance(mcp, dict) or not isinstance(rest, dict) or not isinstance(types, dict):
        fail("contract snapshot must contain mcp, rest, and types objects")
    tools = string_values(mcp.get("tools"), "mcp.tools")
    read_tools = string_values(mcp.get("readTools"), "mcp.readTools")
    operations = string_values(rest.get("operations"), "rest.operations")
    sorted_unique(tools, "mcp.tools")
    sorted_unique(operations, "rest.operations")
    if mcp.get("toolCount") != len(tools):
        fail("mcp.toolCount does not match mcp.tools")
    if not isinstance(mcp.get("readToolCount"), int) or not isinstance(mcp.get("writeToolCount"), int):
        fail("mcp read/write counts must be integers")
    if mcp["readToolCount"] != len(read_tools):
        fail("mcp.readToolCount does not match mcp.readTools")
    if not set(read_tools).issubset(set(tools)):
        fail("mcp.readTools must be a subset of mcp.tools")
    if mcp["readToolCount"] + mcp["writeToolCount"] != len(tools):
        fail("mcp read/write counts do not add up to mcp.toolCount")
    if rest.get("methodCount") != len(operations):
        fail("rest.methodCount does not match rest.operations")
    for name, values in types.items():
        string_values(values, f"types.{name}")
    return payload


def require_equal(actual: list[str], expected: list[str], label: str) -> None:
    actual_sorted = sorted_unique(actual, label)
    expected_sorted = sorted_unique(expected, f"expected {label}")
    if actual_sorted != expected_sorted:
        missing = sorted(set(expected_sorted) - set(actual_sorted))
        extra = sorted(set(actual_sorted) - set(expected_sorted))
        fail(f"{label} drift (missing={missing or 'none'}, extra={extra or 'none'})")


def static_skill_contract(contract: dict[str, Any]) -> None:
    skill = SKILL_PATH.read_text(encoding="utf-8")
    table = re.search(
        r"^\| Area \| Tools \|\n(?P<table>(?:^\|.*\|\n?)+)",
        skill,
        re.MULTILINE,
    )
    if table is None:
        fail("SKILL.md is missing the MCP tool table")
    actual_tools = re.findall(r"`([a-z][a-z0-9_]*)`", table.group("table"))
    require_equal(actual_tools, contract["mcp"]["tools"], "SKILL MCP tool table")

    enum_table = re.search(
        r"^\| Type \| Values \|\n(?P<table>(?:^\|.*\|\n?)+)",
        skill,
        re.MULTILINE,
    )
    if enum_table is None:
        fail("SKILL.md is missing the core enum table")
    enum_rows = {
        label.strip().lower(): re.findall(r"`([^`]+)`", values)
        for label, values in re.findall(
            r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
            enum_table.group("table"),
            re.MULTILINE,
        )
    }
    expected_enums = {
        "issue status": contract["types"]["issueStatus"],
        "issue priority": contract["types"]["issuePriority"],
        "project status": contract["types"]["projectStatus"],
        "epic status": contract["types"]["epicStatus"],
        "milestone status": contract["types"]["milestoneStatus"],
        "relation": contract["types"]["relationType"],
        "document": contract["types"]["documentType"],
    }
    for label, expected in expected_enums.items():
        if label not in enum_rows:
            fail(f"SKILL.md core enum table is missing {label}")
        require_equal(enum_rows[label], expected, f"SKILL {label}")

    status_contract = (
        "no issues → planned",
        "any issue open → in_progress",
        "all closed, at least one done → completed",
        "all closed, all canceled → canceled",
    )
    normalized_skill = skill.replace("≥", "at least ").replace("cancelled", "canceled")
    for phrase in status_contract:
        if phrase not in normalized_skill:
            fail(f"SKILL.md is missing derived epic-status rule: {phrase}")

    codex_mcp = (
        "codex mcp add agentix --url https://HOST/api/mcp "
        "--bearer-token-env-var AGENTIX_MCP_TOKEN"
    )
    if codex_mcp not in skill:
        fail("SKILL.md is missing the safe Codex MCP command")


def static_package_contract() -> None:
    claude = read_json(CLAUDE_MANIFEST_PATH)
    codex = read_json(CODEX_MANIFEST_PATH)
    marketplace = read_json(MARKETPLACE_PATH)
    version = claude.get("version")
    if not isinstance(version, str) or codex.get("version") != version:
        fail("Claude and Codex manifest versions must match")
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version):
        fail("plugin version must use strict x.y.z semver")
    frontmatter = SKILL_PATH.read_text(encoding="utf-8").split("---", 2)
    if len(frontmatter) < 3 or f'version: "{version}"' not in frontmatter[1]:
        fail("SKILL.md metadata.version must match both plugin manifests")
    allowed_manifest_keys = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "keywords",
        "skills",
        "interface",
    }
    unexpected = sorted(set(codex) - allowed_manifest_keys)
    if unexpected:
        fail(f"Codex manifest contains unsupported fields: {unexpected}")
    if codex.get("name") != "agentix" or not isinstance(codex.get("description"), str) or not codex["description"].strip():
        fail("Codex manifest must identify and describe the Agentix plugin")
    if codex.get("skills") != "./skills/":
        fail("Codex manifest must expose ./skills/")
    author = codex.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        fail("Codex manifest author.name must be a non-empty string")
    for url_field in ("homepage", "repository"):
        url = codex.get(url_field)
        if not isinstance(url, str) or not url.startswith("https://"):
            fail(f"Codex manifest {url_field} must be an absolute HTTPS URL")
    keywords = codex.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(item, str) and item for item in keywords):
        fail("Codex manifest keywords must be a non-empty array of strings")
    interface = codex.get("interface")
    if not isinstance(interface, dict):
        fail("Codex manifest interface must be an object")
    required_interface_strings = (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "websiteURL",
        "brandColor",
    )
    if any(not isinstance(interface.get(field), str) or not interface[field].strip() for field in required_interface_strings):
        fail("Codex manifest interface is missing a required non-empty string")
    if not interface["websiteURL"].startswith("https://"):
        fail("Codex manifest interface.websiteURL must be an absolute HTTPS URL")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brandColor"]):
        fail("Codex manifest interface.brandColor must use #RRGGBB")
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not all(isinstance(value, str) and value for value in capabilities):
        fail("Codex manifest interface.capabilities must be an array of strings")
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or not all(
        isinstance(prompt, str) and prompt.strip() and len(prompt) <= 128 for prompt in prompts
    ):
        fail("Codex manifest interface.defaultPrompt must contain 1-3 short strings")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("marketplace must expose exactly one Agentix plugin")
    entry = plugins[0]
    if not isinstance(entry, dict):
        fail("marketplace plugin entry must be an object")
    expected_entry = {
        "name": "agentix",
        "source": {"source": "local", "path": "./"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    if entry != expected_entry:
        fail("marketplace Agentix entry differs from the supported packaging contract")


def request_json(url: str, headers: dict[str, str] | None = None, body: bytes | None = None) -> Any:
    request = Request(url, data=body, headers=headers or {}, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        fail(f"live contract request returned HTTP {exc.code}")
    except URLError as exc:
        fail(f"live contract request failed: {exc.reason}")
    except OSError as exc:
        fail(f"live contract request failed: {exc}")
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        fail(f"live contract response was not JSON: {exc}")


def verify_live_rest(contract: dict[str, Any], base_url: str) -> None:
    docs = request_json(f"{base_url.rstrip('/')}/api/docs")
    if not isinstance(docs, dict):
        fail("live /api/docs response must be an object")
    if docs.get("service") != "agentix" or docs.get("status") != "production":
        fail("live /api/docs does not identify the production Agentix contract")
    methods = docs.get("methods")
    if not isinstance(methods, list):
        fail("live /api/docs.methods must be an array")
    operations: list[str] = []
    for item in methods:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            fail("live /api/docs.methods contains an invalid method entry")
        methods_for_path = string_values(item.get("methods"), "live methods[].methods")
        operations.extend(f"{method} {item['path']}" for method in methods_for_path)
    require_equal(operations, contract["rest"]["operations"], "live REST operations")
    if docs.get("restMethodCount") != contract["rest"]["methodCount"]:
        fail("live restMethodCount differs from the contract snapshot")
    live_types = docs.get("types")
    if not isinstance(live_types, dict):
        fail("live /api/docs.types must be an object")
    for name, expected in contract["types"].items():
        actual = live_types.get(name)
        require_equal(string_values(actual, f"live types.{name}"), expected, f"live types.{name}")


def verify_live_mcp(contract: dict[str, Any], base_url: str, token: str | None) -> None:
    if not token:
        print("ok: live MCP catalogue skipped (AGENTIX_CONTRACT_MCP_TOKEN is not configured)")
        return
    body = json.dumps(
        {"jsonrpc": "2.0", "id": "agentix-contract", "method": "tools/list", "params": {}}
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    request = Request(f"{base_url.rstrip('/')}/api/mcp", data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        fail(f"live MCP catalogue returned HTTP {exc.code}")
    except URLError as exc:
        fail(f"live MCP catalogue request failed: {exc.reason}")
    if raw.startswith("data:"):
        data_lines = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
        if not data_lines:
            fail("live MCP catalogue returned an empty SSE response")
        raw = data_lines[-1]
    try:
        envelope = json.loads(raw)
        tools = envelope["result"]["tools"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        fail(f"live MCP catalogue has an invalid JSON-RPC envelope: {exc}")
    if not isinstance(tools, list):
        fail("live MCP tools/list result must contain an array")
    names = [tool.get("name") for tool in tools if isinstance(tool, dict)]
    if len(names) != len(tools) or not all(isinstance(name, str) for name in names):
        fail("live MCP tools/list contains an invalid tool name")
    require_equal(names, contract["mcp"]["tools"], "live MCP tool names")
    read_tools = [
        tool["name"]
        for tool in tools
        if isinstance(tool, dict)
        and isinstance(tool.get("annotations"), dict)
        and tool["annotations"].get("readOnlyHint") is True
    ]
    require_equal(read_tools, contract["mcp"]["readTools"], "live MCP read-only tools")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also verify the deployed public REST contract")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AGENTIX_CONTRACT_URL", DEFAULT_BASE_URL),
        help="Agentix base URL for --live (defaults to AGENTIX_CONTRACT_URL or hosted production)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contract = snapshot()
    static_skill_contract(contract)
    static_package_contract()
    print("ok: static Agentix package contract")
    if args.live:
        verify_live_rest(contract, args.base_url)
        print("ok: live public REST contract")
        verify_live_mcp(contract, args.base_url, os.environ.get("AGENTIX_CONTRACT_MCP_TOKEN"))


if __name__ == "__main__":
    main()

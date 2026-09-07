# Agentix skill

Agentix plugin for Claude Code and Codex. It teaches an agent to orient with
`get_started`, load one issue with `get_context`, create runnable work, and
keep status, checklist, and comment evidence current. The public live service
contract is available at [Agentix API docs](https://agentix.moone.dev/api/docs).

## Install

### Claude Code

```text
/plugin marketplace add kyzdes/claude-skills
/plugin install agentix@claude-skills
```

### Codex

Install the versioned repository marketplace and plugin:

```text
codex plugin marketplace add kyzdes/agentix-skill --ref agentix--v0.4.0
codex plugin add agentix@agentix
```

The skill is installed without credentials. Use an approved secret manager to
make a least-privilege token available as `AGENTIX_MCP_TOKEN` to the process
that launches Codex, then register only that environment-variable name:

```text
codex mcp add agentix --url https://HOST/api/mcp --bearer-token-env-var AGENTIX_MCP_TOKEN
```

Reload the client or start a new session after configuring MCP. Tokens are
workspace-bound, expire, and may be read-only or read-and-write. Never commit,
paste, or package a token; use a separate least-privilege token for each
integration and workspace.

## Package and contract guard

```text
.claude-plugin/plugin.json           Claude Code metadata
.codex-plugin/plugin.json            Codex metadata
.agents/plugins/marketplace.json     Codex Git marketplace entry
skills/agentix/SKILL.md              shared complete agent instructions
hooks/hooks.json                     host-aware SessionStart update hook
scripts/auto-update.sh               debounced opt-in updater
contracts/agentix-contract.json      checked MCP/REST/type snapshot
scripts/verify-contract.py           static and live compatibility check
```

The repository uses one shared skill for both hosts. The Codex manifest does
not bundle an MCP server because a usable Agentix server needs a workspace-
bound Bearer token, and secrets must remain outside the package.

`scripts/verify-contract.py` always checks that the instructions, manifests,
tool map, and enum table match the committed contract snapshot. With `--live`,
it additionally checks public `GET /api/docs` against production; if
`AGENTIX_CONTRACT_MCP_TOKEN` is supplied by CI, it verifies the authenticated
MCP `tools/list` catalogue too.

## Optional automatic updates

The SessionStart hook is network-safe by default: it exits without changing
anything unless the user opts in:

```bash
export AGENTIX_PLUGIN_AUTO_UPDATE=1
```

When enabled, it updates only the plugin for the host starting the session:
Claude refreshes `agentix@claude-skills`; Codex refreshes and reinstalls
`agentix@agentix`. Updates are debounced for four hours, concurrent sessions
are serialized, and the private log is capped at 64 KiB. Configure the
interval and cap with `AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC` and
`AGENTIX_PLUGIN_AUTO_UPDATE_LOG_BYTES`.

## Validate

```bash
python3 /Users/viacheslavkuznetsov/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
claude plugin validate .
bash -n scripts/auto-update.sh
python3 scripts/verify-contract.py
```

GitHub Actions performs these static checks on every PR and also runs the live
public contract probe on a schedule. Configure the repository secret
`AGENTIX_CONTRACT_MCP_TOKEN` to make that scheduled check include the private
MCP catalogue.

## Release status

Version 0.3 targets the hosted production Agentix release: 43 MCP tools, 60
REST operations, and the derived epic states `planned`, `in_progress`,
`completed`, and `canceled`. This public repository currently has no declared
software license; publishing the source therefore does not grant third parties
permission to reuse it.

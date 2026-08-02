# Agentix skill

Companion Claude Code plugin for working with a remote [Agentix](https://github.com/kyzdes/agentix) instance through MCP. It teaches an agent to orient with `get_started`, load one issue with `get_context`, create runnable tasks, and keep status/checklist/comment evidence current.

## Install

```text
/plugin marketplace add kyzdes/claude-skills
/plugin install agentix@claude-skills
```

The Agentix service URL and Bearer token are configured separately in the MCP client. Tokens are workspace-bound, expire, and may be read-only or read-and-write. They are secrets and must not be committed or pasted into chats; use a separate least-privilege token for each integration and workspace.

## Package

```text
.claude-plugin/plugin.json   plugin metadata
skills/agentix/SKILL.md      complete agent instructions
hooks/hooks.json             SessionStart update hook
scripts/auto-update.sh       debounced marketplace updater
```

The SessionStart hook is network-safe by default: it exits without changing anything unless the user explicitly opts in:

```bash
export AGENTIX_PLUGIN_AUTO_UPDATE=1
```

When enabled, it refreshes marketplace metadata and updates only `agentix@claude-skills`, at most once per four hours. Concurrent sessions are serialized with an atomic lock, and the private log under `~/.cache/agentix-plugin` is capped at 64 KiB. The interval and cap can be changed with `AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC` and `AGENTIX_PLUGIN_AUTO_UPDATE_LOG_BYTES`.

## Validate

```bash
jq empty .claude-plugin/plugin.json hooks/hooks.json
bash -n scripts/auto-update.sh
```

GitHub Actions also checks plugin JSON and skill frontmatter.

## Release status

Version 0.2 targets the hosted Agentix release and its live 43-tool MCP
contract. This public repository currently has no declared software license;
publishing the source therefore does not grant third parties permission to
reuse it. Marketplace metadata is released separately from
`kyzdes/claude-skills`.

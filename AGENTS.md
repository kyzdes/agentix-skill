# Working in agentix-skill

This repository packages the shared Agentix skill for Codex and Claude Code.
The Agentix application is a separate repository at `../agentix`.

## Start a session

1. Read `docs/project-state.md` for the current state, paths and open work.
2. Run `git status --short --branch` and inspect the diff before editing.
3. Read only the files needed for the task. Read `README.md` for installation
   or validation, and `skills/agentix/SKILL.md` for agent workflow changes.

Do not preload the application, complete API catalogue, release logs or old
chats. Follow the links in the state file when a task needs that evidence.
Work in the repository requested by the user; changes to the sibling service
have a separate scope and validation process.

## Preserve the package

- Keep one shared `skills/agentix/SKILL.md` and the existing manifest/hook paths.
- Change versions together in both manifests, skill metadata and README install
  ref when making a release. Published release tags are immutable.
- Keep all three contract snapshots: the verifier and tests use the legacy
  files. They are supported compatibility fixtures, not abandoned drafts.
- Live MCP schemas and `/api/docs` own the service contract. Do not overwrite
  a snapshot merely to make a drift check pass; reconcile the service change.
- Credentials remain outside the package and project memory. Automatic updates
  stay opt-in. Preserve any existing user changes, stashes and untracked work.
- Use the checks in `README.md#validate` for relevant plugin changes. Record
  whether a live probe included authenticated MCP or only public REST.

## Keep context small

`docs/project-state.md` is the single current handoff, kept under 120 lines.
Update its date, verified state and open steps after a meaningful change;
replace obsolete statements instead of appending a conversation log.
Keep setup instructions in README, agent behavior in SKILL.md, and detailed
evidence at its owning source. Link to those sources instead of copying them.
Distinguish today's checks from historical evidence and work still unverified.

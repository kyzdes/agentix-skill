---
name: agentix
description: >-
  Work with a remote Agentix issue tracker over its MCP server or REST fallback. Use when Agentix tools are present, or when the user asks to find, create, update, link, plan, or document work in Agentix. Covers safe connection, context-efficient orientation, issue lifecycle, durable evidence, core types, and the complete tool map. Do not use for GitHub Issues, Jira, or Linear, and do not start a local Agentix source checkout merely to use the tracker.
metadata:
  short-description: Work with Agentix over MCP
  version: "0.2.0"
---

# Agentix

Agentix is a remote issue tracker and Markdown knowledge store for humans and AI agents. Prefer its MCP tools. The live tool schemas and `GET /api/docs` are the contract source of truth; do not guess fields from this skill when they disagree.

## Safety and scope

- Call `get_started` first. Pull only the issue and documents needed for the task; do not read the whole workspace.
- Treat Bearer tokens, invitation URLs, sessions, database URLs, and integration keys as secrets. Never print, commit, or paste them into Agentix content.
- Work only in the workspace permanently bound to the token. A header/query selector may confirm that same workspace but cannot switch it; obtain a separate token for each workspace.
- MCP has no user, invitation, label, workspace, token, or import administration. Token listing, minting, and revocation are browser-session-only; use the web UI when the user authorizes credential administration.
- Deletes are hard. Prefer `canceled`, a `duplicates` relation, or a correcting comment when history has value. Confirm the exact target before any `delete_*` or `unlink_issues` call.
- Never claim completion from a tool call alone. Verify the requested outcome and record the evidence.

## Connect

If `get_started` or `whoami` works, continue to the workflow. Otherwise obtain the base URL and token from the user's approved secret store without displaying the token, then configure the MCP server for a future/reloaded session. Tokens expire after 1–365 days (90 by default) and grant either read-only or read-and-write access; request only the capability and lifetime required by the task.

```text
claude mcp add --scope user --transport http agentix https://HOST/api/mcp \
  --header "Authorization: Bearer TOKEN"
```

For the current session, REST is the fallback. Read unauthenticated `GET https://HOST/api/docs`, then authenticate supported calls with the same Bearer token. `GET /api/health` is public. Do not confuse an Agentix `DATABASE_URL` with an API token.

## Work cycle

1. `get_started(project?)`: read the returned brief, project catalogue, conventions, and index status.
2. Before creating anything, use `search(query)` for existing issues and documents, `list_epics` for epics, and `list_milestones` for milestones. MCP has no label tools; inspect or manage labels only through an authorized REST or web workflow.
3. `get_context(issue)` to load one runnable brief. Use narrower `get_*`/`list_*` calls only for missing exact values.
4. For a code task, ensure intent, relevant paths, a verification command, and checkable acceptance criteria are present. Use `set_task_spec` and `add_checklist_item`.
5. Move the issue to `in_progress` immediately before beginning work. Keep decisions and blockers in `add_comment`; tick criteria as they become true.
6. Move reviewable work to `in_review` when it is actually ready for review. Move to `done` only after every criterion is satisfied and a summary names the verification performed and the resulting change.
7. Keep `index` context-map documents short and current when project structure or durable knowledge changes.

These lifecycle steps are an operating convention, not a database-enforced state machine. If the user's workflow differs, follow the user's explicit instruction and leave a clear comment.

## Creating runnable work

A useful issue has one coherent outcome:

- Imperative, specific title.
- Short Markdown description with intent, constraints, and `[[AGX-12]]` / `[[doc-slug]]` links where useful.
- Correct project and, when applicable, an existing epic or milestone.
- Honest priority and assignee.
- For code: `set_task_spec(issue, relevantPaths, testCommand)`.
- One checklist item per observable acceptance criterion; do not bury the definition of done in prose.

Split a smaller piece with `add_sub_issue`; group a theme under an epic; use a milestone for a dated outcome. Epic status is derived from child issues and is not directly settable.

## References and data types

- Project reference: UUID or key such as `AGX`.
- Issue reference: UUID or display key such as `AGX-12`.
- Document reference: UUID or slug. Milestone lookups may accept a UUID or name; follow the live schema for each tool.
- User reference: UUID, email, or exact case-insensitive name where supported.
- Omitted fields mean unchanged/defaulted; `null` clears only fields whose live schema is nullable.
- Markdown fields are `description`, `content`, and `body` at the agent edge; REST also accepts their `*Md` forms.
- Dates are ISO strings. IDs are UUID strings. List bounds and exact write fields come from the live tool/REST schema.

Core enums:

| Type | Values |
|---|---|
| issue status | `backlog`, `todo`, `in_progress`, `in_review`, `done`, `canceled` |
| issue priority | `none`, `low`, `medium`, `high`, `urgent` |
| project status | `active`, `archived` |
| milestone status | `planned`, `active`, `completed`, `canceled` |
| relation | `blocks`, `relates`, `duplicates` |
| document | `plan`, `memory`, `context_map`, `note` |

## MCP tool map (43)

Use the client-exposed schema for exact arguments and return data. Seventeen tools require `read`; the 26 mutating tools require `write`. A read-only credential can discover the full tool catalogue, but write calls return `forbidden` without changing state.

| Area | Tools |
|---|---|
| Orientation/context | `whoami`, `get_started`, `search`, `get_context`, `get_backlinks` |
| Projects | `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project` |
| Epics | `list_epics`, `create_epic`, `update_epic`, `delete_epic` |
| Issues/relations | `list_issues`, `get_issue`, `create_issue`, `update_issue`, `move_issue`, `assign_issue`, `add_sub_issue`, `link_issues`, `unlink_issues`, `delete_issue` |
| Comments | `list_comments`, `add_comment` |
| Documents | `list_documents`, `get_document`, `create_document`, `update_document`, `export_document_md`, `delete_document` |
| Activity/inbox | `list_activity`, `get_inbox`, `mark_read` |
| Milestones | `list_milestones`, `create_milestone`, `update_milestone`, `delete_milestone` |
| Task spec/checklist | `set_task_spec`, `add_checklist_item`, `check_item`, `delete_checklist_item` |

## REST fallback

REST and MCP share service rules and normalizers but are not identical verb-for-tool surfaces. Discover the current 60 REST method/path operations at public `GET /api/docs`. Common mappings are:

| Intent | REST method |
|---|---|
| Orient / context | `GET /api/started`, `GET /api/context?issue=AGX-12` |
| Create / read / edit issue | `POST /api/issues`, `GET|PATCH /api/issues/:ref` |
| Move / assign | `PATCH /api/issues/:ref` with `status` or `assignee` |
| Spec / checklist | `PATCH /api/issues/:ref/spec`, `POST /api/issues/:ref/checklist`, `PATCH /api/checklist/:id` |
| Comment / relation | `POST /api/issues/:ref/comments`, `POST /api/issues/:ref/relations` |
| Documents / search | `/api/documents`, `/api/documents/:ref`, `GET /api/search?query=...` |

REST safe methods require token scope `read`; mutations require `write`. REST success payloads are JSON except Markdown export. Validation and service failures use `{ "error": { "code", "message", "issues"? } }`; unknown paths are JSON 404s, while wrong methods are framework 405s.

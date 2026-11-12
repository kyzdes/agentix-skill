---
name: agentix
description: >-
  Work with a remote Agentix issue tracker over its MCP server or REST fallback. Use when Agentix tools are present, or when the user asks to find, create, update, link, plan, or document work in Agentix. Covers safe connection, context-efficient orientation, issue lifecycle, durable evidence, core types, and the complete tool map. Do not use for GitHub Issues, Jira, or Linear, and do not start a local Agentix source checkout merely to use the tracker.
metadata:
  short-description: Work with Agentix over MCP
  version: "0.6.0"
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

For Claude Code, make `AGENTIX_MCP_TOKEN` available to the launching process and
merge this entry into `.mcp.json`, preserving existing servers. This is a literal
environment reference; never replace it with the token in a committed file:

```json
{"mcpServers":{"agentix":{"type":"http","url":"https://HOST/api/mcp","headers":{"Authorization":"Bearer ${AGENTIX_MCP_TOKEN}"}}}}
```

For Codex, expose the token only in the environment that launches Codex (for
example through an approved secret manager), then register its variable name —
never the literal token:

```text
codex mcp add agentix --url https://HOST/api/mcp --bearer-token-env-var AGENTIX_MCP_TOKEN
```

For the current session, REST is the fallback. Read unauthenticated `GET https://HOST/api/docs`, then authenticate supported calls with the same Bearer token. `GET /api/health` is public. Do not confuse an Agentix `DATABASE_URL` with an API token.

The guided web setup at `/onboarding` creates a separate agent identity and a
workspace-scoped read/write credential (30-day default, 7/90-day alternatives).
The ordinary settings/API token default remains 90 days. After setup, call
`get_started` with this exact credential: creation, `whoami`, REST reads or a
successful call with another token do not mark the new credential connected.
Revocation or expiry requires a new valid credential and its own handshake.
Never ask the user to paste the token into this conversation.

## Work cycle

1. `get_started(project?)`: read the returned brief, project catalogue, conventions, and index status.
2. Before creating anything, use `search(query)` for existing issues and documents, `list_epics` for epics, and `list_milestones` for milestones. MCP has no label tools; inspect or manage labels only through an authorized REST or web workflow.
3. `get_context(issue)` to load one bounded context. For `formatVersion: 2`, read the structured sections: `brief` is only a heading. `maxChars` bounds the whole serialized response; `truncated` and `omitted` explicitly identify partial sections. Use `readMore`, entity UUIDs and paginated `get_*`/`list_*` readers to fetch only the missing information needed for the task. Never interpret a clipped or omitted field as absent. `get_started` v2 similarly bounds its map and catalogues to 24,000 characters. Older servers without `formatVersion` still return their legacy brief; their budget does not guarantee a bound on the entire response. Both formats are supported during rollout.
4. Discover coordination from `get_started.taskCoordinationVersion` and the live tool catalogue. On a server with `claim_issue`, acquire the issue, then reread `get_issue`: keep its `revision`, `specRevision`, and the returned `claimId`. A lease belongs to the exact token, not just the agent account. Renew with `renew_issue_claim` every 5 minutes (15-minute expiry). After expiry, reacquire with a new logical command key and reread before writing. Release with `release_issue_claim` when yielding the task.
5. For a code task, ensure intent, relevant paths, a verification command and checkable criteria are present. Pass `expectedRevision` and `claimId` to task/spec/checklist mutations. Use the revision returned by each successful mutation for the next one. Document edits also require the revision actually read. A 409 means reread and reconcile; never blindly replace the expected revision and resubmit an old draft.
6. Move to `in_progress` before beginning work. Keep decisions and blockers in `add_comment`; comments need no claim. Tick criteria as they become true. `in_review` is optional.
7. On coordination-capable servers, finish with `complete_issue`: all criteria satisfied, current `expectedRevision` and `specRevision`, active `claimId`, summary, artifact references and verification result. Code verification must report the configured command, exit code 0 and actual observed results. Manual checks need details; `not_applicable` needs an explanation and cannot replace a configured command. Agentix checks completeness and records “agent reported”; it does not execute commands. The agent can close the task independently. Direct status changes to Done are rejected. Existing Done without reports is historical; do not invent evidence for it.
8. Use a fresh `idempotencyKey` for each logical creation or task command, and reuse it for identical retries. REST uses `Idempotency-Key`. Results are retained for 24 hours per workspace, credential and operation. Changed payload with the same key returns 409; reread after an ambiguous result before starting a new logical command. Never use this mechanism for token issuance.
9. Keep `index` context-map documents short and current when project structure or durable knowledge changes.

During staged rollout, older servers have no coordination tools or `taskCoordinationVersion`. Use their existing task/spec/checklist tools, verify every criterion, leave the evidence in a comment and then move to Done. This is a legacy convention, not an immutable completion report. Do not call missing tools. Both legacy and v2 context responses remain supported. On the new service, claims, revisions and completion evidence are mandatory server rules; user workflow preferences can choose the optional review step but cannot bypass those rules.

## Daily views and shared documents

On activation-capable servers, `list_issues` exposes an optional `view` argument:
`mine`, `blocked`, `review`, or `recent`. Check the live schema before passing it;
older coordination releases do not accept this field. Combine it with `assignee`
to inspect one worker. `mine` defaults to the current agent. `blocked` contains
active tasks with unfinished incoming dependencies; `recent` contains Done tasks
with a current requirements report from the last 14 days. It excludes historical
Done without reports. Returned claims name the active owner; a different active
credential may not be overridden. Web filters are persisted in `/work` and
project URLs.

Canonical document links are `/documents/<uuid>`, including workspace-wide
notes. Prefer the current project's wiki slug, then a workspace-wide document;
use an explicit UUID for a cross-project reference. Do not construct a foreign
document URL with the open issue's project. Fetch omitted context sections with
the indicated IDs/readers rather than treating truncation as missing data.

On servers advertising `schemaContract.capabilities.documentReadersVersion:1`,
`list_documents` returns metadata without `contentMd` (default 50, max 200).
Continue with `offset`; use `get_document(id)` for a selected Markdown body.
Version history uses an authorized REST read at `/api/documents/<uuid>/versions`:
`{items,total,nextCursor}` contains metadata (default 20, max 100). Pass the opaque
`nextCursor` unchanged as `cursor` until it is null; request one snapshot with
`?versionId=<uuid>`. Do not combine `versionId` with pagination. A selected version
belongs to that document and workspace. Totals/pages use READ COMMITTED semantics,
so concurrent writes can change the catalogue; they are not a fixed snapshot.
On older servers, follow the discovered live contract and its legacy response.

On servers advertising `schemaContract.capabilities.issueCommentsReadersVersion:1`,
`get_issue` includes only the latest 20 comments and `commentPage:{total,nextCursor}`.
`list_comments(issue, limit?, cursor?)` and REST `/api/issues/<uuid>/comments` return
`{items,total,nextCursor}` (default 20, max 200). Each page lists its comments from
oldest to newest; the cursor fetches the preceding, older page. Prepend that page
when building a chronological thread. Pass `nextCursor` unchanged until null; do
not infer that the first page is the whole conversation. Cursor identity is bound
to the issue; malformed or mismatched cursors fail. This public reader rejects
legacy `offset` rather than changing its meaning. Concurrent inserts appear after
refreshing the first page; totals can change and reads do not form a snapshot.
This capability bounds comments only; other issue collections retain their live
contract. Write results have their own capability below; stored retries may retain
the older full detail shape. Older servers
keep their discovered legacy comment shape and arguments.

On servers advertising `schemaContract.capabilities.issueMutationResultsVersion:1`,
`create_issue`, `update_issue`, `move_issue`, `assign_issue`, `add_sub_issue`,
`set_task_spec`, `link_issues` and `complete_issue` return the issue's card fields
(IDs/key, revision/specRevision, title/status/priority, planning IDs, assignee,
labels and dates), plus `descriptionMd`, `relevantPaths`, `testCommand` and `parentId`.
`link_issues` also returns `relationId`, usable by `unlink_issues` without rereading
the whole issue. A keyed retry returns the original success if that relation was
later removed; it does not recreate the relation, and source access is checked again.
`complete_issue` also returns `claim:null` and singular `completion`: exactly the
new report with its ID, provenance, evidence and requirements revision. It is not
completion history. REST create/PATCH issue, PATCH spec, POST relations and POST
complete use the same result semantics; onboarding creation retains its own shape.

Comments, checklist, children, relations and completion history are omitted, not
empty. Keep the authoritative returned revision for your next command. A status
change with unchanged `specRevision` can be merged into the task already read while
retaining its checklist. Retain other prior collections only when the operation
cannot affect them; changed requirements or links need the existing detail refresh
before using affected data. Do not replace a full task snapshot with a mutation
result. Existing idempotent retries still return the originally stored result
exactly, including a legacy full detail; reusing a key does not upgrade its shape.
New results omit history independently of its length. These fields are sufficient
for chaining ordinary writes without adding a mandatory read after every command.

On servers advertising `schemaContract.capabilities.backlinksReadersVersion:1`,
`get_backlinks(issue, limit?, offset?)` returns `{items,nextOffset}` containing
document link metadata, without Markdown bodies (default 20, max 100). Pass the
returned `nextOffset` until it is null; documents are ordered by ID. Read a selected
body with `get_document(sourceId)`. Both target and sources belong to the active
workspace. Supported offsets are 0..1,000,000; a page requiring continuation above
that bound fails explicitly. Offset pages can change under concurrent writes; older servers retain
their discovered legacy response.

On servers whose live schemas expose the fields below (no capability flag; check
the tool schema or `GET /api/docs` before using them):

- `list_activity` and `get_inbox` are newest first and every item carries an opaque
  `cursor`. Pass the last item's `cursor` to read older items. REST `before` remains
  for compatibility but can skip rows that share a millisecond; prefer `cursor`.
- `get_document`, `update_document`, `export_document_md` and `delete_document`
  accept `project` (key, UUID, or `"global"`) to select one of several documents
  sharing a slug, such as the global and a project `index`. It selects; it does not
  move the document. REST uses `?project=` on `/api/documents/:ref`, its `export`
  and `versions`. An ambiguous slug without it fails rather than picking one.
- `update_project`, `update_epic` and `update_milestone` accept an optional
  `expectedRevision`; a stale value is a 409, omission stays allowed. Pass the
  revision you read when another agent may edit the same plan object.
- `unlink_issues` returns `{id,deleted,revision}`; `revision` is the source
  issue's new revision for your next command.
- An update cannot move an issue, epic or milestone to another project: `project`
  in the update is a 400, not a silent no-op. A milestone name shared by two
  projects is a 409 unless a project is given; an ambiguous user name is a 409.
- Deleting an issue detaches its documents instead of deleting them.
- `get_issue` embeds at most 200 children and 200 relations and reports
  `truncated`; a checklist holds at most 200 items and a text at most 50 mentions.
- `[[...]]` inside code blocks and inline code is literal text. `doc:`, `epic:`
  and `milestone:` link prefixes are not resolved as issues.
- Invitations and member removal are browser-session-only, like token administration.

## Creating runnable work

A useful issue has one coherent outcome:

- Imperative, specific title.
- Short Markdown description with intent, constraints, and `[[AGX-12]]` / `[[doc-slug]]` links where useful.
- Correct project and, when applicable, an existing epic or milestone.
- Honest priority and assignee.
- For code: `set_task_spec(issue, relevantPaths, testCommand)`.
- One checklist item per observable acceptance criterion; do not bury the definition of done in prose.

Split a smaller piece with `add_sub_issue`; group a theme under an epic; use a milestone for a dated outcome. Epic status is derived from child issues and is not directly settable: no issues → planned; any issue open → in_progress; all closed, at least one done → completed; all closed, all canceled → canceled.

## References and data types

- Project reference: UUID or key such as `AGX`.
- Issue reference: UUID or display key such as `AGX-12`.
- Document reference: UUID or slug. Milestone lookups may accept a UUID or name; follow the live schema for each tool.
- User reference: UUID, email, or exact case-insensitive name where supported.
- Omitted fields mean unchanged/defaulted; `null` clears only fields whose live schema is nullable.
- Markdown fields are `description`, `content`, and `body` at the agent edge; REST also accepts their `*Md` forms.
- Dates are ISO strings. IDs are UUID strings. List bounds and exact write fields come from the live tool/REST schema.
- If `GET /api/docs` reports `schemaContract.capabilities.inboxExplicitSelection:true`, `mark_read` requires exactly one selector: nonempty `notificationIds` or `all:true`; an empty request is invalid. On older servers, follow the discovered live schema.

Core enums:

| Type | Values |
|---|---|
| issue status | `backlog`, `todo`, `in_progress`, `in_review`, `done`, `canceled` |
| issue priority | `none`, `low`, `medium`, `high`, `urgent` |
| project status | `active`, `archived` |
| epic status | `planned`, `in_progress`, `completed`, `canceled` |
| milestone status | `planned`, `active`, `completed`, `canceled` |
| relation | `blocks`, `relates`, `duplicates` |
| document | `plan`, `memory`, `context_map`, `note` |

## MCP tool map (47; older servers: 43)

Use the client-exposed schema for exact arguments and return data. Seventeen tools require `read`; the 30 mutating tools require `write`. A read-only credential can discover the full tool catalogue, but write calls return `forbidden` without changing state.

| Area | Tools |
|---|---|
| Orientation/context | `whoami`, `get_started`, `search`, `get_context`, `get_backlinks` |
| Projects | `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project` |
| Epics | `list_epics`, `create_epic`, `update_epic`, `delete_epic` |
| Issues/relations | `list_issues`, `get_issue`, `create_issue`, `update_issue`, `move_issue`, `assign_issue`, `add_sub_issue`, `link_issues`, `unlink_issues`, `delete_issue` |
| Coordination | `claim_issue`, `renew_issue_claim`, `release_issue_claim`, `complete_issue` |
| Comments | `list_comments`, `add_comment` |
| Documents | `list_documents`, `get_document`, `create_document`, `update_document`, `export_document_md`, `delete_document` |
| Activity/inbox | `list_activity`, `get_inbox`, `mark_read` |
| Milestones | `list_milestones`, `create_milestone`, `update_milestone`, `delete_milestone` |
| Task spec/checklist | `set_task_spec`, `add_checklist_item`, `check_item`, `delete_checklist_item` |

## REST fallback

REST and MCP share service rules and normalizers but are not identical verb-for-tool surfaces. Discover the current 70 REST method/path operations (60 on the compatible older service) at public `GET /api/docs`. Common mappings are:

| Intent | REST method |
|---|---|
| Claim / renew / release / complete | `POST /api/issues/:ref/claim`, `POST /api/issues/:ref/renew`, `POST /api/issues/:ref/release`, `POST /api/issues/:ref/complete` |
| Orient / context | `GET /api/started`, `GET /api/context?issue=AGX-12` |
| Create / read / edit issue | `POST /api/issues`, `GET|PATCH /api/issues/:ref` |
| Move / assign | `PATCH /api/issues/:ref` with `status` or `assignee` |
| Spec / checklist | `PATCH /api/issues/:ref/spec`, `POST /api/issues/:ref/checklist`, `PATCH /api/checklist/:id` |
| Comment / relation | `POST /api/issues/:ref/comments`, `POST /api/issues/:ref/relations` |
| Documents / search | `/api/documents`, `/api/documents/:ref`, `GET /api/search?query=...` |

REST safe methods require token scope `read`; mutations require `write`. REST success payloads are JSON except Markdown export. Validation and service failures use `{ "error": { "code", "message", "issues"? } }`; unknown paths are JSON 404s, while wrong methods are framework 405s.

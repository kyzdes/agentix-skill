# Agentix MCP tool reference

All 43 tools on the `agentix` MCP server, with a REST mirror at `/api/*`
(Bearer-token auth). Every tool that takes an issue/project/milestone reference
accepts **either a UUID or a display key** (`AGX`, `AGX-12`, a milestone name) —
and users/assignees resolve by UUID, email, or name. Results come back as JSON.

> **Start with `get_started`, then `get_context`.** Reach for the granular
> `list_*` / `get_*` tools only when you need exact values the brief didn't carry.

Many write tools accept **agent-friendly field aliases** that the server renames
to its internal schema field — both the alias and the internal name work:
`description`→descriptionMd, `content`→contentMd, `body`→bodyMd,
`project`→projectId, `issue`→issueId, `parent`→parentId, `assignee`→assigneeId,
`lead`→leadId, `milestone`→milestoneId.

---

## Meta & onboarding (2)

| Tool | Params | Returns |
|------|--------|---------|
| `get_started` | `project?` (ref) | **START HERE.** Onboarding payload: `you`, `workflow`, `conventions`, `inboxUnread`, `projects[]`, `globalIndex`/`globalIndexTemplate`, `globalWiki[]`, and a ready-to-read `brief` markdown string. With `project`: also a `focus` block (that project's index, epics, milestones, doc catalogue). When an index is missing, returns a `…Template` to bootstrap it. |
| `whoami` | — | The current authenticated actor `{ id, name, kind, … }`. |

## Projects (5)

| Tool | Params | Returns |
|------|--------|---------|
| `list_projects` | `status?: "active"\|"archived"` | Projects with `openIssueCount`/`issueCount`. |
| `get_project` | `project` (ref) | One project (id, key, name, description, lead, color, counts). |
| `create_project` | `key` (uppercased), `name`, `description?` (alias→descriptionMd), `lead?` (alias→leadId; UUID/email/name), `color?` | Created project. `key` is the uppercase prefix used in issue keys (e.g. `AGX` → `AGX-1`). |
| `update_project` | `project` (ref), `name?`, `description?` (alias), `status?: "active"\|"archived"`, `color?` | Updated project. |
| `delete_project` | `project` (ref) | Deletion result. **Hard delete — cascades all project contents.** |

## Epics (4)

| Tool | Params | Returns |
|------|--------|---------|
| `list_epics` | `project?` (ref) | Epics with issue counts and a **read-only, auto-derived** `status`. |
| `create_epic` | `project` (ref→alias projectId), `title`, `description?` (alias) | Created epic. **Status is not settable — it's derived from the epic's issues.** |
| `update_epic` | `epicId` (**UUID only**), `title?`, `description?` (alias) | Updated epic. **Status is not settable (derived).** |
| `delete_epic` | `epicId` (**UUID only**) | Deletion result. **Hard delete; the epic's issues are detached, not deleted.** |

## Issues — the core (11)

| Tool | Params | Returns |
|------|--------|---------|
| `list_issues` | `project?` (ref), `status?` (one or array of backlog/todo/in_progress/in_review/done/canceled), `priority?` (none/low/medium/high/urgent), `assignee?` (UUID/email/name), `epicId?` (UUID), `query?` (title match), `limit?` (1–200, default 100) | Issue cards (key, title, status, priority, assignee, epic, labels). |
| `get_issue` | `issue` (ref) | **Full** issue: description, priority, epic, milestone, assignee, reporter, parent, children, labels, checklist, comments, relations (incoming + outgoing), spec (relevantPaths, testCommand). |
| `create_issue` | `project` (ref→alias), `title`, `description?` (alias), `status?` (enum), `priority?` (enum), `epicId?` (UUID), `milestone?` (alias→milestoneId; UUID or name), `parent?` (ref→alias parentId), `assignee?` (alias→assigneeId), `labelIds?` (UUID[]) | Created issue with generated key (e.g. `AGX-1`). Defaults to `backlog`. |
| `update_issue` | `issue` (ref), `title?`, `description?` (alias), `status?` (enum), `priority?` (enum), `epicId?` (UUID, nullable), `milestone?` (alias, nullable→clear) | Updated issue. (Status changes should go through `move_issue`, which emits the status-change event.) |
| `move_issue` | `issue` (ref), `status` (backlog/todo/in_progress/in_review/done/canceled) | Issue with new status (board move); emits a status-change event. |
| `assign_issue` | `issue` (ref), `assignee` (alias→assigneeId; UUID/email/name, **or `null` to unassign**) | Re-assigns or unassigns the issue. |
| `add_sub_issue` | `parent` (ref), `title`, `description?` (alias), `priority?` (enum), `assignee?` (alias) | Sub-issue under `parent` (inherits the parent's project). |
| `link_issues` | `issue` (ref, source), `target` (ref), `type: "blocks"\|"relates"\|"duplicates"` | Created relation. Incoming side is resolved at read-time (`blocked_by`, etc.). |
| `unlink_issues` | `relationId` (**UUID only**; read it from `get_issue`'s relations) | Removal result. Removes one issue relation by its relation id. |
| `delete_issue` | `issue` (ref) | Deletion result. **Hard delete — not reversible.** |
| `add_comment` | _(see Comments)_ | — |

## Comments (2)

| Tool | Params | Returns |
|------|--------|---------|
| `list_comments` | `issue` (ref) | All comments with author + timestamp (markdown bodies). |
| `add_comment` | `issue` (ref), `body` (alias→bodyMd; markdown) | Posts a markdown comment. Use real newlines, not `\n`. |

## Documents — wiki: plans, memory, context maps, notes (6)

| Tool | Params | Returns |
|------|--------|---------|
| `list_documents` | `project?` (ref), `type?: "plan"\|"memory"\|"context_map"\|"note"`, `query?` | Documents (slug, type, createdBy, timestamps). |
| `get_document` | `document` (UUID or slug) | Full document with markdown body. |
| `create_document` | `title`, `content?` (alias→contentMd), `type?` (enum), `project?` (ref→alias), `issue?` (ref→alias issueId), `slug?` | Created document (auto-slugged, unique per project). |
| `update_document` | `document` (UUID/slug), `title?`, `content?` (alias), `type?` (enum), `slug?` | Updated document; `slug` is re-uniqued and links re-synced on change. A version snapshot is taken when content/title changes. |
| `export_document_md` | `document` (UUID/slug) | `{ filename, content }` — markdown with YAML frontmatter. |
| `delete_document` | `document` (UUID/slug) | Deletion result. **Hard delete — not reversible.** |

Document bodies can contain `[[slug]]`, `[[AGX-12]]`, `[[epic:…]]`, `[[milestone:…]]` wiki-links; these build the link graph traversed by `get_context` / `get_backlinks`.

## Search (1)

| Tool | Params | Returns |
|------|--------|---------|
| `search` | `query`, `limit?` (1–50, default 20) | Ranked hits over issues + documents — Postgres full-text (tsvector + GIN), multi-word, stemmed. Your default before creating anything. |

## Activity & inbox (3)

| Tool | Params | Returns |
|------|--------|---------|
| `list_activity` | `project?` (ref), `issue?` (ref), `limit?` (1–200) | Event log: `{ action ("issue.created"…), actor, issue, createdAt, data }`. |
| `get_inbox` | `unreadOnly?` (bool), `limit?` (1–200) | Your notifications: assignments, @mentions, comments, status changes. |
| `mark_read` | `notificationIds?: UUID[]` (omit = mark all unread read) | Marks given (or all unread) notifications read. |

## Context & wiki graph — agentic layer (2)

| Tool | Params | Returns |
|------|--------|---------|
| `get_context` | `issue` (ref), `maxCharsPerDoc?` (200–20000), `maxDocs?` (1–30), `maxChars?` (1000–120000) | **One-call work brief for an issue:** the issue + epic + linked wiki docs (`[[..]]` backlinks) + project knowledge (plans/memory/context_maps) + recent activity, within a token budget. Returns structured sections **plus** a composited `brief` markdown and a `truncated` flag. |
| `get_backlinks` | `issue` (ref) | Wiki docs that `[[..]]`-link the issue: `{ sourceId, title, slug, projectId }`. |

## Milestones (4)

| Tool | Params | Returns |
|------|--------|---------|
| `list_milestones` | `project?` (ref) | Milestones with `status` (planned / active / completed / canceled), `targetDate`, issue counts. |
| `create_milestone` | `project` (ref→alias), `name`, `description?` (alias), `status?` (planned/active/completed/canceled), `targetDate?` (ISO string) | Created milestone. |
| `update_milestone` | `milestoneId` (**UUID only**), `name?`, `description?` (alias), `status?` (enum), `targetDate?` (nullable→clear) | Updated milestone. |
| `delete_milestone` | `milestone` (**UUID or name**), `project?` (ref, scopes the name lookup) | Deletion result. **Hard delete; the milestone's issues are detached, not deleted.** |

## Task-spec & checklist — make an issue runnable (4)

| Tool | Params | Returns |
|------|--------|---------|
| `set_task_spec` | `issue` (ref), `relevantPaths?: string[]` (nullable), `testCommand?: string` (nullable) | Sets the issue's agent brief: files to touch + how to verify. Pass `null` to clear a field. |
| `add_checklist_item` | `issue` (ref), `content` | Adds one acceptance-criteria item `{ id, content, done: false }`. |
| `check_item` | `itemId` (**UUID only**), `done?` (default `true`) | Ticks/unticks a checklist item. |
| `delete_checklist_item` | `itemId` (**UUID only**) | Deletion result. Removes one checklist item. |

---

## Destructive tools (at a glance)

Seven tools delete or unlink — use them to fix genuinely mis-filed work rather
than leaving litter behind. Deletes are **hard** (no soft-delete / trash):

- `delete_project` (ref) — cascades **all** project contents.
- `delete_epic` (epicId UUID) — issues are **detached**, not deleted.
- `delete_issue` (ref) — not reversible.
- `delete_document` (UUID/slug) — not reversible.
- `delete_milestone` (UUID or name) — issues are **detached**, not deleted.
- `delete_checklist_item` (itemId UUID).
- `unlink_issues` (relationId UUID, from `get_issue`'s relations) — removes one relation.

---

## REST mirror (`/api/*`)

The REST surface is a **true mirror** of the MCP adapter — same input contract,
just HTTP verbs and paths. Authenticate with `Authorization: Bearer <token>`
(the `agentix-mcp` key; `agentix-prod` is a `DATABASE_URL`, never a bearer).
Self-describe the whole endpoint map with the **unauthenticated** `GET /api/docs`.

Now true on REST (since the adapter was extracted into a shared normalizer):

- **Refs work everywhere** — every ref field accepts a UUID **or** a display key
  (`AGX`, `AGX-12`, a milestone name), not just UUIDs.
- **Agent field aliases work** — `description`/`descriptionMd`, `content`/`contentMd`,
  `body`/`bodyMd`, `project`/`projectId`, `issue`/`issueId`, `parent`/`parentId`,
  `assignee`/`assigneeId`, `lead`/`leadId`, `milestone`/`milestoneId` are all accepted.
- **Unknown/typo fields → `400`.** Every create/update/list schema is strict; a
  typo like `titel` or `descriptionMdd` is **rejected** with the standard
  `{ error: { code, message } }` envelope (no more silent field drops).
- **List routes accept `project` or `projectKey`** (a display key) in addition to
  `projectId` — on `/api/issues`, `/api/epics`, `/api/milestones`, `/api/documents`.
- **Unknown paths → JSON `404`** (`{ error: { code: "not_found", message: "No such endpoint: <METHOD> <path>" } }`), not Next's HTML. A wrong method on a real path is still `405`.
- **`GET /api/health`** — **unauthenticated** readiness probe; runs `select 1` and
  returns `{ ok: true }`, or `503` with the envelope (`unavailable`) if Postgres is down.

### Common write ops → METHOD + path + body

| Intent | REST call | Body (alias fields accepted) |
|--------|-----------|------------------------------|
| Onboard | `GET /api/started?project=<ref>` | — |
| Who am I | `GET /api/me` | — |
| Create issue | `POST /api/issues` | `{ project, title, description?, status?, priority?, epicId?, milestone?, parent?, assignee?, labelIds?, dueDate? }` |
| **Move issue** (status) | `PATCH /api/issues/:ref` | `{ "status": "in_progress" }` — there is **no** dedicated move route; PATCH the status |
| Update issue | `PATCH /api/issues/:ref` | `{ title?, description?, priority?, epicId?, milestone? }` |
| Assign / unassign | `PATCH /api/issues/:ref` | `{ "assignee": "<uuid\|email\|name>" }` or `{ "assignee": null }` |
| Set task spec | `PATCH /api/issues/:ref/spec` | `{ relevantPaths?, testCommand? }` |
| Add checklist item | `POST /api/issues/:ref/checklist` | `{ content }` |
| **Tick checklist item** | `PATCH /api/checklist/:itemId` | `{ "done": true }` (also `content?`, `sortOrder?`) |
| Add comment | `POST /api/issues/:ref/comments` | `{ body }` |
| Link issues | `POST /api/issues/:ref/relations` | `{ target, type }` |
| **Unlink** a relation | `DELETE /api/issues/:ref/relations/:id` | — (`:id` = relation id from `get_issue`) |
| Create document | `POST /api/documents` | `{ title, content?, type?, project?, issue?, slug? }` |
| Update document | `PATCH /api/documents/:ref` | `{ title?, content?, type?, slug? }` |
| Export document | `GET /api/documents/:ref/export` | — (raw `text/markdown` attachment) |
| Create milestone | `POST /api/milestones` | `{ project, name, description?, status?, targetDate? }` |
| Search | `GET /api/search?q=<query>&limit=` | — (`q` **or** `query`) |
| Delete | `DELETE /api/projects\|epics\|issues\|documents\|milestones/:ref` | — (hard delete) |
| Delete label | `DELETE /api/labels/:id` | — |
| Discover endpoints | `GET /api/docs` | — (**unauthenticated**; full endpoint map + conventions) |

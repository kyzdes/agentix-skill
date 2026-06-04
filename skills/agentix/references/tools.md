# Agentix MCP tool reference

All 36 tools on the `agentix` MCP server, with a REST mirror at `/api/*`
(Bearer-token auth). Every tool that takes an issue/project reference accepts
**either a UUID or a display key** (`AGX`, `AGX-12`) — and users/assignees
resolve by UUID, email, or name. Results come back as JSON.

> **Start with `get_started`, then `get_context`.** Reach for the granular
> `list_*` / `get_*` tools only when you need exact values the brief didn't carry.

---

## Meta & onboarding

| Tool | Params | Returns |
|------|--------|---------|
| `get_started` | `project?` | **START HERE.** Workspace index, house rules, project list, wiki catalogue, your inbox count, and a ready-to-read `brief`. With `project`: also that project's index, epics, milestones, and doc catalogue. When an index is missing, returns `…IndexMissing: true` + a `…Template` to bootstrap it. |
| `whoami` | — | The current authenticated actor `{ id, name, kind: "human"\|"agent", role, email }`. |

## Projects

| Tool | Params | Returns |
|------|--------|---------|
| `list_projects` | `status?: "active"\|"archived"` | Projects with lead + open/total issue counts. |
| `get_project` | `project` | One project (id, key, name, description, lead, color, counts). |
| `create_project` | `key`, `name`, `description?`, `lead?`, `color?` | Created project. `key` is the uppercase prefix used in issue keys (e.g. `AGX` → `AGX-1`). |
| `update_project` | `project`, `name?`, `description?`, `status?`, `color?` | Updated project. |

## Epics

| Tool | Params | Returns |
|------|--------|---------|
| `list_epics` | `project?` | Epics with issue counts and `status` (planned / in_progress / completed / canceled). |
| `create_epic` | `project`, `title`, `description?`, `status?` | Created epic. |
| `update_epic` | `epicId`, `title?`, `description?`, `status?` | Updated epic. |

## Issues (the core)

| Tool | Params | Returns |
|------|--------|---------|
| `list_issues` | `project?`, `status?` (one or array), `priority?`, `assignee?`, `epicId?`, `query?` (title match), `limit?` (1–200, default 100) | Issue cards (key, title, status, priority, assignee, epic, labels). |
| `get_issue` | `issue` | **Full** issue: description, priority, epic, milestone, assignee, reporter, parent, children, labels, checklist, comments, relations (incoming + outgoing), spec (relevantPaths, testCommand). |
| `create_issue` | `project`, `title`, `description?`, `status?`, `priority?`, `epicId?`, `milestone?`, `parent?`, `assignee?`, `labelIds?` | Created issue with generated key (e.g. `AGX-1`). |
| `update_issue` | `issue`, `title?`, `description?`, `priority?`, `epicId?`, `milestone?` | Updated issue. (Status changes go through `move_issue`.) |
| `move_issue` | `issue`, `status` | Issue with new status (board move). Statuses: backlog / todo / in_progress / in_review / done / canceled. |
| `assign_issue` | `issue`, `assignee: string \| null` | Re-assigns (resolves UUID/email/name) or unassigns when `null`. |
| `add_sub_issue` | `parent`, `title`, `description?`, `priority?`, `assignee?` | Sub-issue under `parent` (inherits the parent's project). |
| `link_issues` | `issue` (source), `target`, `type: "blocks"\|"relates"\|"duplicates"` | Created relation. Incoming side is resolved at read-time (`blocked_by`, etc.). |

## Comments

| Tool | Params | Returns |
|------|--------|---------|
| `list_comments` | `issue` | All comments with author + timestamp (markdown bodies). |
| `add_comment` | `issue`, `body` | Posts a markdown comment. Use real newlines, not `\n`. |

## Documents (wiki: plans, memory, context maps, notes)

| Tool | Params | Returns |
|------|--------|---------|
| `list_documents` | `project?`, `type?: "plan"\|"memory"\|"context_map"\|"note"`, `query?` | Documents (slug, type, createdBy, timestamps). |
| `get_document` | `document` (UUID or slug) | Full document with `contentMd`. |
| `create_document` | `title`, `content`, `type?`, `project?`, `issue?`, `slug?` | Created document (auto-slugged, unique per project). |
| `update_document` | `document`, `title?`, `content?`, `type?` | Updated document; a version snapshot is taken when content/title changes. |
| `export_document_md` | `document` | Markdown string with YAML frontmatter. |

Document bodies can contain `[[slug]]`, `[[AGX-12]]`, `[[epic:…]]`, `[[milestone:…]]` wiki-links; these build the link graph traversed by `get_context` / `get_backlinks`.

## Search

| Tool | Params | Returns |
|------|--------|---------|
| `search` | `query`, `limit?` (1–50, default 20) | `{ issues: [...], documents: [...] }` — ranked Postgres full-text (tsvector + GIN), multi-word, stemmed. Your default before creating anything. |

## Activity & inbox

| Tool | Params | Returns |
|------|--------|---------|
| `list_activity` | `project?`, `issue?`, `limit?` (1–200, default 50) | Event log: `{ action ("issue.created"…), actor, issue, createdAt, data }`. |
| `get_inbox` | `unreadOnly?`, `limit?` (1–200) | Your notifications: assignments, @mentions, comments, status changes. |
| `mark_read` | `notificationIds?: UUID[]` | Marks given (or, if omitted, all) notifications read. |

## Context & wiki graph (agentic layer)

| Tool | Params | Returns |
|------|--------|---------|
| `get_context` | `issue`, `maxCharsPerDoc?` (200–20000, def 4000), `maxDocs?` (1–30, def 8), `maxChars?` (1000–120000, def 24000) | **One-call work brief for an issue:** the issue + epic + linked wiki docs (`[[..]]` backlinks) + project knowledge (plans/memory/context_maps) + recent activity, within a token budget. Returns structured sections **plus** a composited `brief` markdown and a `truncated` flag. |
| `get_backlinks` | `issue` | Documents that link to the issue via `[[..]]`: `{ sourceId, title, slug, projectId }`. |

## Milestones

| Tool | Params | Returns |
|------|--------|---------|
| `list_milestones` | `project?` | Milestones with `status` (planned / active / completed / canceled), `targetDate`, issue counts. |
| `create_milestone` | `project`, `name`, `description?`, `status?`, `targetDate?` (ISO date) | Created milestone. |
| `update_milestone` | `milestoneId`, `name?`, `description?`, `status?`, `targetDate?` (`null` to clear) | Updated milestone. |

## Task-spec & checklist (make an issue runnable)

| Tool | Params | Returns |
|------|--------|---------|
| `set_task_spec` | `issue`, `relevantPaths?: string[]`, `testCommand?: string` | Sets the issue's agent brief: files to touch + how to verify. Pass `null` to clear a field. |
| `add_checklist_item` | `issue`, `content` | Adds one acceptance-criteria item `{ id, content, done: false }`. |
| `check_item` | `itemId`, `done?` (default `true`) | Ticks/unticks a checklist item. |

---
name: agentix
description: Work the Agentix issue tracker — an agent-native, Linear-style tracker exposed over an MCP server named `agentix` (projects, epics, issues, milestones, checklists, and a wiki). Use whenever the agentix MCP tools are present (get_started, get_context, create_issue, search, create_document, set_task_spec…) or the user mentions Agentix, "the tracker", "заведи/создай задачу", "create an issue/task", "log work", planning epics/milestones, or maintaining the wiki/index/"оглавление". Teaches the orientation workflow (get_started → index → get_context), the task-creation template (title + spec + checklist), and the index convention that keeps agents from reading the whole wiki. NOT for GitHub Issues, Jira, or the hosted Linear MCP — those are different tools.
metadata:
  short-description: Work the Agentix agent-native issue tracker over MCP
  version: "0.1"
---

# Agentix

Agentix is an **agent-native issue tracker** — projects → epics → issues → milestones, plus checklists, relations, and a wiki — exposed over an MCP server named `agentix` (REST mirror at `/api/*`). This skill tells you how to work it efficiently: orient cheaply, work one issue at a time, and file issues another agent can pick up without you.

## The one rule that protects your context

**Don't read everything.** Call `get_started` first, then pull only what the task needs (`get_context`, `search`, targeted `list_*`). Reading the whole wiki "to understand the project" is the exact failure mode this skill exists to prevent — it burns your context before you've done any work.

## Connect (once)

The human creates an agent user + API token in Agentix (Settings → Members → Create agent, then Settings → API tokens), then registers the server:

```
claude mcp add --transport http agentix https://YOUR_DOMAIN/api/mcp \
  --header "Authorization: Bearer <TOKEN>"
```

Confirm with `whoami` — it returns your actor `{ name, kind: "agent", role }`.

## The work cycle (follow it every time)

1. **Orient** — `get_started` (add `project` to focus one project). Read its `brief`.
2. **Read the index** — the `get_started` brief embeds the workspace index and, when focused, the project index. That's your map. Don't go wider unless the task needs it.
3. **Pick up an issue** — `get_context(issue)`. ONE call returns the description, spec (relevant paths + test command), acceptance checklist, linked wiki docs, sub-issues, relations, and recent activity. Don't reconstruct this by hand.
4. **Before creating** — `search("…")` for duplicates; reuse an existing epic/milestone instead of inventing one.
5. **Create** — title + description, then **`set_task_spec`** (relevantPaths + testCommand) and **`add_checklist_item`** for each acceptance criterion. See `references/task-template.md`.
6. **Make progress visible** — `move_issue` (status), `check_item` (tick criteria), `add_comment` (decisions/blockers), `assign_issue`.
7. **Keep the map current** — when you add a project, a major doc, or learn where something lives, update the relevant `index` document. See `references/index-convention.md`.

`get_started` and the MCP server's `instructions` already restate this cycle, so it works even before this skill loads — but this skill is the detailed version.

## Orient: `get_started` first

`get_started` returns, in one call:

- `you` — your actor; `inboxUnread` — assignments/@mentions waiting.
- `workflow` + `conventions` — the house rules.
- `projects` — every project with a one-liner and open/total issue counts.
- `globalIndex` — the workspace index document (or `globalIndexMissing: true` + `globalIndexTemplate` to bootstrap it).
- `globalWiki` — a catalogue of global docs (slug/type/title) so you know **what exists** without reading them.
- `focus` (when you pass `project`) — that project's `index`, `epics`, `milestones`, and `wiki` catalogue.
- `brief` — all of the above composited into ready-to-read markdown. Read the brief; drill into structured fields only when you need exact values.

If `globalIndexMissing` (or `focus.indexMissing`) is true, **create the index** before doing other work — it's the first investment that pays back on every future session. The response hands you the exact template.

## The index — your map, read first & keep current

The index ("оглавление") is a normal wiki document with **slug `index`, type `context_map`**: one global (no project) plus one per project. It lists domains / where things live, the key docs (as `[[slug]]` links), and active work. Agents read it first and update it when the structure changes — so nobody has to re-read the whole wiki. Full convention, templates, and update triggers: **`references/index-convention.md`**.

## Creating issues that another agent can run

Agentix issues are richer than a title + prose. A good issue carries its own brief:

- **Title** — plain, specific, imperative ("Add cold-start latency to the bench", not "Benchmarking").
- **Description** — context + intent. Link related issues/docs with `[[AGX-12]]` / `[[doc-slug]]`.
- **Spec** — `set_task_spec(issue, relevantPaths, testCommand)`: the files to touch and how to verify. This is what lets an agent start without spelunking.
- **Acceptance criteria** — one `add_checklist_item` per criterion (checkable), **not** a prose blob.
- **Placement** — right `project`, and an `epic`/`milestone` when it belongs to a larger body of work.
- **Size** — one coherent task per issue. Too big? split into sub-issues (`add_sub_issue`). Much too big? it's an epic or milestone, not an issue.

Full template, field-by-field, with the Linear-derived best practices adapted to Agentix: **`references/task-template.md`**.

## Working an issue

- `get_context(issue)` to load everything. Work from its `brief`.
- `move_issue(issue, "in_progress")` when you start; `in_review` when you open a PR; `done` when criteria pass.
- `check_item(itemId, true)` as you satisfy each acceptance criterion.
- `add_comment` for decisions, blockers, and "what I did" — that's the audit trail other agents and humans read.
- Found a dependency? `link_issues(issue, target, "blocks" | "relates" | "duplicates")`.

## Search & navigate (instead of reading everything)

- `search("query")` — ranked full-text over issues **and** documents. Your default for "is there already…?".
- `get_context(issue)` — everything for one issue.
- `get_backlinks(issue)` — which wiki docs point at this issue.
- `list_issues` / `list_documents` / `list_epics` / `list_milestones` — targeted, filterable lists.
- `[[slug]]` / `[[AGX-12]]` in any document body create the wiki-link graph; `get_context` and backlinks traverse it.

## Tool reference

All 36 MCP tools, grouped, with parameters and what they return: **`references/tools.md`**.

## Common workflows

Step-by-step recipes (take an assigned issue, file a well-specced issue, plan an epic, bootstrap/refresh the index): **`references/workflows.md`**.

See also:
- `references/tools.md` — every MCP tool with signatures and return shapes.
- `references/task-template.md` — the issue-creation template + best practices (search-before-create, spec, checklist, granularity ladder).
- `references/index-convention.md` — the global + per-project index convention, templates, and when to update.
- `references/workflows.md` — end-to-end recipes for the most common agent tasks.

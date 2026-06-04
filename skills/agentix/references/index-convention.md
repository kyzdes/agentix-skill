# The index convention ("оглавление")

The index is the map an agent reads **first** and keeps current — so nobody has
to read the whole wiki to find out where things are. It is the single most
valuable doc in an Agentix workspace.

## What it is

A normal wiki document with a fixed identity:

- **slug:** `index`
- **type:** `context_map`
- **scope:** one **global** index (no project) + one index **per project**
  (project-scoped). Both can use slug `index` because slugs are unique *per
  project*, and the global one lives in the `null` project.

`get_started` surfaces the global index always, and the focused project's index
when you pass `project`. When an index doesn't exist yet, `get_started` returns
`globalIndexMissing` / `focus.indexMissing` **plus the template to create it**.

## Why it exists

Without an index, every fresh agent re-reads documents, issues, and code "to
understand the project" and burns its context before doing any work. The index
front-loads that understanding into one short, maintained document: what the
projects are, where each domain lives, which docs matter, and what's in flight.
Read it, then use `search` / `get_context` to pull only the specifics you need.

## When to READ it

- **First thing**, via `get_started`, every session.
- Before creating an issue or a doc (to place it correctly and avoid duplicates).
- When you're unsure where a domain or file lives — check the index before grepping the wiki.

## When to UPDATE it (you own the map)

Update the relevant index in the same session you change the structure:

- Created/renamed/archived a **project** → update the **global** index's project table.
- Wrote a significant **doc** (plan / memory / context_map) → add it to the right index's "Key docs", linked as `[[slug]]`.
- Started/finished a major **epic or milestone** → reflect it in the project index's "Active work".
- Learned **where something lives** (a domain ↔ paths/docs mapping that wasn't written down) → add a row to "Domains / where things live". This is the highest-leverage update — it's exactly what saves the next agent.

Keep it short. The index is a map, not the territory — link out (`[[slug]]`,
`[[AGX-12]]`) instead of inlining content. If a section grows long, it wants to
be its own doc that the index links to.

## Bootstrapping

If `get_started` reports an index missing, create it from the returned template:

```
# global
create_document(title: "Workspace Index", slug: "index", type: "context_map",
                content: <globalIndexTemplate>)

# per project
create_document(title: "<Name> (AGX) — Index", slug: "index", type: "context_map",
                project: "AGX", content: <focus.indexTemplate>)
```

Then fill in the real values. Update with `update_document` (it snapshots a
version on every change, so edits are safe).

## Template — global index

```markdown
# Workspace Index

> **Read me first.** Map of the whole workspace. Skim before reading anything
> else; keep current when the map changes.

## What this is
One paragraph: what this Agentix workspace is for and who works here.

## Projects
| Key | Name | What it's for | Index |
|-----|------|---------------|-------|
| AGX | … | … | [[index]] |

## Cross-project docs
Global plans / memory / context maps — each linked [[slug]] with one line.

## Conventions
- Start here. Call `get_started` (or open this doc) before doing anything.
- One issue = one task. Search before creating; split with sub-issues; promote oversized work to an epic/milestone.
- Every issue gets a spec: relevantPaths + testCommand, and acceptance criteria as checklist items.
- Keep the map current.

## How to find more (don't read everything)
- `search("…")` — ranked full-text over issues + docs.
- `get_context(issue)` — everything for one issue in one call.
- `list_projects` / `list_documents` / `list_issues` — targeted lists.
```

## Template — project index

```markdown
# <Name> (AGX) — Index

> **Read me first** for project AGX. Map of this project's domains, docs, and
> active work. Keep current.

## Purpose
One paragraph: what AGX is and the outcome it's driving toward.

## Domains / where things live
| Domain | What it covers | Where (paths / docs) |
|--------|----------------|----------------------|
| API | request/response surface | app/api, [[some-doc]] |

## Key docs
- [[slug]] (type) — one line on what it's for

## Active work
- **Epics:** in-progress epics
- **Milestones:** current milestone + target date

## Conventions & gotchas
- Build/test commands, naming rules, things that bite.

## Entry points for an agent
- New here? Read this index, then `get_context(AGX-<n>)`.
- `search("…")` for anything not on the map.
```

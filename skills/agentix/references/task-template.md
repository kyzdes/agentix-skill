# Filing issues in Agentix

How to create issues another agent (or human) can pick up and run without
asking you anything. Adapted from Linear's issue best practices, then upgraded
for Agentix — where an issue carries a real, structured spec, not just prose.

## Principle: write issues, not user stories

Keep creation friction low. The only things truly required are a **title** and
a **status**; everything else is optional and added when known. Write a plain,
concrete task — *"Add cold-start latency to the bench harness"* — **not** a
ceremonial *"As a user, I want…"*. Don't pad an issue with fields that don't
apply. Do give it enough that the next agent doesn't have to reverse-engineer
the intent.

## Orient before you create

1. `get_started` (or have its brief already) — know the projects, epics, and conventions.
2. **`search("…")` for duplicates.** If it exists, comment or `link_issues(..., "duplicates")` instead of creating a second one.
3. Pick the right `project`. Reuse an existing `epic` / `milestone` rather than inventing one.
4. Reuse existing labels; don't spawn near-duplicates.

## The template

```
create_issue(
  project:     "AGX",                      # required — right project
  title:       "<imperative, specific>",   # required — e.g. "Cache get_context briefs per issue"
  description: "<context + intent, with [[links]]>",
  priority:    "none|low|medium|high|urgent",
  epicId:      <epic>,                      # when part of a larger body of work
  milestone:   "<name or id>",             # when time-boxed
  assignee:    "<uuid|email|name>",        # if known
)
# then make it runnable:
set_task_spec(issue, relevantPaths: ["lib/services/context.ts", "app/api/context/route.ts"],
                     testCommand:   "npx tsc --noEmit && npx vitest run context")
add_checklist_item(issue, "get_context caches the assembled brief per (issue, opts)")
add_checklist_item(issue, "Cache invalidates when the issue or a linked doc changes")
add_checklist_item(issue, "Bench shows lower p50 for repeat get_context calls")
```

### Field-by-field

- **title** — plain language, imperative, specific. One scan tells you what "done" means. Avoid topic-nouns ("Search", "Benchmarking").
- **description** — the *why* and the *intent*, plus constraints and pointers. Link related work with `[[AGX-12]]` and docs with `[[doc-slug]]` so the issue joins the graph (and shows up in `get_backlinks` / `get_context`). Use real newlines, not `\n`.
- **priority** — `none / low / medium / high / urgent`. Set it honestly; default `none` is fine.
- **spec (`set_task_spec`)** — the Agentix superpower. `relevantPaths` = the files/dirs to touch; `testCommand` = how to verify. This is what lets an agent start in seconds instead of grepping. Fill it for any code task.
- **acceptance criteria (`add_checklist_item`)** — one checkable item per criterion, phrased as a testable outcome. **Not** a prose paragraph in the description. The next agent ticks them with `check_item` as it goes; that *is* the definition of done.
- **placement** — `epicId` for a theme of work, `milestone` for a dated deliverable, `parent`/`add_sub_issue` for a piece of a bigger issue.

## Granularity ladder

One coherent task per issue. When scope doesn't fit, move up the ladder:

```
sub-issue   <   issue   <   epic   <   milestone
(a slice)       (one task)   (a theme)   (a dated outcome)
```

- Too big for one issue but shares an owner/flow → split into **sub-issues** (`add_sub_issue`).
- A cluster of related issues around one theme → group under an **epic**.
- A time-boxed deliverable spanning epics/issues → a **milestone** with a `targetDate`.
- If a single issue's body keeps growing, that's the signal to promote it — don't let one issue become a project.

## Relations instead of duplicates

- `link_issues(A, B, "blocks")` — A blocks B (B shows `blocked_by A`).
- `link_issues(A, B, "relates")` — related, no ordering.
- `link_issues(A, B, "duplicates")` — A duplicates B; prefer this + a comment over filing the same work twice.

## Don't hand-manage status

Move status as work actually progresses — `move_issue(issue, "in_progress")` when
you start, `"in_review"` when a PR is open, `"done"` when the checklist passes —
and leave a `add_comment` trail of decisions and blockers. Status + checklist +
comments are what make the issue legible to the next agent.

## Quick checklist before you hit create

- [ ] Searched for an existing issue/duplicate.
- [ ] Right project; reused an epic/milestone/labels where they exist.
- [ ] Title is imperative and specific.
- [ ] Description carries intent + `[[links]]`.
- [ ] `set_task_spec` filled (relevantPaths + testCommand) for code work.
- [ ] Acceptance criteria are checklist items, not prose.
- [ ] Scope is one task — else split (sub-issues) or promote (epic/milestone).

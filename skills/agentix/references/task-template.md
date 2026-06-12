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
- **spec (`set_task_spec`)** — the Agentix superpower. `relevantPaths` = the files/dirs to touch; `testCommand` = how to verify. This is what lets an agent start in seconds instead of grepping. **A spec (relevantPaths + testCommand) is mandatory for any code task before it can move to `in_progress`** — no spec, not ready to start.
- **acceptance criteria (`add_checklist_item`)** — one checkable item per criterion, phrased as a testable outcome. **Not** a prose paragraph in the description. The next agent ticks them with `check_item` as it goes; that *is* the definition of done.
- **placement** — `epicId` for a theme of work, `milestone` for a dated deliverable, `parent`/`add_sub_issue` for a piece of a bigger issue.
- **labels** — `labelIds` (UUID array) on `create_issue` to tag the work; reuse existing labels rather than spawning near-duplicates.

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
- `unlink_issues(relationId)` — undo a wrong link. The `relationId` comes from `get_issue`'s `relations` array, not the issue key.

## Cleaning up mistakes

Prefer leaving a trail over erasing it. Two correction paths:

- **Cancel (reversible, keeps history).** `move_issue(issue, "canceled")` is the
  default when an issue was real but won't ship — superseded work, scope cut, or
  a probe/spike that has answered its question. The issue and its comments stay
  searchable.
- **Delete (hard, not reversible).** `delete_issue(issue)` only for genuine
  noise that should never have existed — an empty test issue, an accidental
  double-create, a throwaway "does X work?" probe with nothing worth keeping.
  It's a hard delete: comments, checklist, and relations go with it.

Related hard deletes for mis-filed structure (all irreversible): `delete_epic`
(detaches its issues, doesn't delete them), `delete_milestone` (detaches its
issues), `delete_document`. When unsure, cancel or comment — you can't undo a
delete.

## Status lifecycle

Agentix issues move through six statuses: `backlog`, `todo`, `in_progress`,
`in_review`, `done`, `canceled`. Move them as the work actually progresses —
never leave active work parked in `todo` / `backlog`.

- **`backlog` / `todo`** — filed and specced, nobody working it yet.
- **`in_progress`** — `move_issue(issue, "in_progress")` *before* you write any
  code. Starting work without flipping the status is the #1 way two agents
  collide on the same issue.
- **`in_review`** — `move_issue(issue, "in_review")` when the PR is open / the
  change is up for review. Reference the PR or commit in a comment.
- **`done`** — only when **every** checklist item is checked and you've left a
  summary comment.
- **`canceled`** — `move_issue(issue, "canceled")` for work that was filed but
  won't be done (superseded, out of scope, a probe that answered its question).
  Cancel keeps the audit trail; deletion erases it (see *Cleaning up mistakes*).

**Epic status is auto-derived from its issues — never set it by hand.**

## Checklist discipline

The acceptance criteria are not decoration — they are the **definition of done**.

- One `add_checklist_item` per criterion, phrased as a testable outcome. **Not**
  a prose paragraph buried in the description.
- `check_item(itemId, true)` the moment a criterion passes — tick as you go, not
  in a batch at the end.
- **Never move an issue to `done` with unchecked items.** Unticked criteria mean
  the work isn't finished; close the gap or split the remainder into a follow-up
  issue first.

## Comments as an audit trail

`add_comment` is the legible history other agents and humans read. Comment, don't
just act silently:

- on **every status change** — say what you did and why you're moving it.
- on **blockers and decisions** — the trade-off you took, the dependency you
  found (`link_issues(...)`), the thing that's waiting on someone else.
- a **summary comment before `done`** — what shipped, which `testCommand` you
  ran and that it was green, and the PR/commit reference.

Status + checklist + comments together are what make the issue runnable by the
next agent without asking you anything.

The two gates (ready-to-start, ready-for-done) as concrete checklists:
**`quality-gates.md`**.

## Quick checklist before you hit create

- [ ] Searched for an existing issue/duplicate.
- [ ] Right project; reused an epic/milestone/labels where they exist.
- [ ] Title is imperative and specific.
- [ ] Description carries intent + `[[links]]`.
- [ ] `set_task_spec` filled (relevantPaths + testCommand) for code work.
- [ ] Acceptance criteria are checklist items, not prose.
- [ ] Scope is one task — else split (sub-issues) or promote (epic/milestone).

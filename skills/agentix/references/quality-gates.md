# Agentix quality gates

Two checklists that bracket every issue: one before you flip it to `in_progress`,
one before you flip it to `done`. They keep statuses honest and issues runnable by
the next agent. The full template lives in `task-template.md`; the status
lifecycle is in `SKILL.md` ("Working an issue") and `task-template.md`.

## Gate 1 — Ready to start (move to `in_progress`)

Don't start coding until all of these hold. If one fails, fix the issue first —
an under-specced issue costs the next agent (maybe you) a grep safari.

- [ ] **Title** is imperative and specific — one scan tells you what "done" means
      ("Cache get_context briefs per issue", not "Caching").
- [ ] **Description** carries intent + context: the *why*, constraints, and
      `[[links]]` to related issues/docs.
- [ ] **For a code task: spec is set** — `set_task_spec` with `relevantPaths`
      (files/dirs to touch) **and** `testCommand` (how to verify). Mandatory; no
      spec = not ready to start.
- [ ] **At least 2 checklist criteria** (`add_checklist_item`), each a checkable,
      testable outcome — not a prose blob in the description.
- [ ] Right `project`; reusing an existing `epic` / `milestone` / labels where
      they fit.

When it passes: `move_issue(issue, "in_progress")` **before** writing code, and
`add_comment` that you've picked it up.

## Gate 2 — Ready for done (move to `done`)

Don't close until all of these hold. An issue at `done` is a promise that the
work is finished and verifiable.

- [ ] **Every checklist item is checked** (`check_item(itemId, true)`). Unticked
      criteria = not done — close the gap or split the remainder into a follow-up
      issue.
- [ ] **A summary comment** is posted: what shipped, which `testCommand` you ran
      and that it was green, and any decisions/trade-offs worth recording.
- [ ] **PR / commit referenced** in a comment when the work produced one (so the
      change is traceable from the issue).
- [ ] Status path was honest: it passed through `in_review` when the PR was up —
      don't jump straight from `in_progress` to `done` on reviewable work.

When it passes: `move_issue(issue, "done")`. Don't touch the parent epic's status
— it's auto-derived from its issues.

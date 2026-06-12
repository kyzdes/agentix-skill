# Common Agentix workflows

End-to-end recipes for the tasks agents do most. Recipes 0–6 assume the `agentix`
MCP tools are loaded; recipe 7 is the **REST/curl fallback** for when they are
not (and you can't reload the session mid-task). The golden rule runs through all
of them: **orient with `get_started`, pull specifics with `get_context` /
`search`, don't read the whole wiki.**

---

## 0. First contact with a workspace

```
get_started
```
Read the `brief`. If `globalIndexMissing` is true, bootstrap the index from
`globalIndexTemplate` (see `index-convention.md`) before anything else — one
investment that pays back every session. Then either focus a project or pick up
your inbox.

---

## 1. Pick up an assigned issue and run it

```
get_inbox(unreadOnly: true)        # what's waiting on you
get_context("AGX-12")              # full brief in one call
move_issue("AGX-12", "in_progress")          # BEFORE writing any code
# …do the work, guided by the spec (relevantPaths) and testCommand…
check_item(<itemId>, true)         # tick each acceptance criterion as it passes
add_comment("AGX-12", "Chose approach X over Y because <reason>.")  # decisions as you go
# …open the PR…
add_comment("AGX-12", "Ran <testCommand>, green. PR: <url>. Summary: <what shipped>.")
move_issue("AGX-12", "in_review")  # when the PR is up
# …after merge / all checklist items checked…
move_issue("AGX-12", "done")       # only with every criterion ticked
mark_read()                        # clear the inbox notifications
```
Work from `get_context`'s `brief`; don't reconstruct context by hand. Move the
status as the work moves, `check_item` as each criterion passes, and `add_comment`
on every decision/blocker. If you discover a dependency,
`link_issues("AGX-12", "AGX-9", "blocks")`. Linked the wrong pair? Read the
relation's id from `get_issue("AGX-12")` (its `relations[]`), then
`unlink_issues(<relationId>)`. To drop a checklist criterion that no longer
applies, `delete_checklist_item(<itemId>)`.

---

## 2. File a well-specced issue

```
search("cold start latency")                 # avoid duplicates first
get_started(project: "AGX")                   # right epic/milestone/labels
create_issue(project: "AGX",
             title: "Add cold-start latency to the bench harness",
             description: "Measure first-request latency... relates to [[AGX-7]].",
             priority: "medium", epicId: <perf-epic>)
set_task_spec("AGX-31",
              relevantPaths: ["scripts/bench/", "docs/load-testing.md"],
              testCommand: "node scripts/bench/run.mjs --cold")
add_checklist_item("AGX-31", "Bench records p50/p95 first-request latency")
add_checklist_item("AGX-31", "Runbook documents how to read the cold-start number")
```
Now it's ready to start: spec (relevantPaths + testCommand) is set and there are
>=2 checklist criteria. Whoever picks it up moves it to `in_progress` before
coding. Full field-by-field guidance: `task-template.md`; the two gates:
`quality-gates.md`.

---

## 3. Plan an epic (break a big ask into runnable issues)

```
get_started(project: "AGX")
create_epic(project: "AGX", title: "Realtime updates")     # epic status is auto-derived — don't set it
# one issue per coherent task, each with its own spec + criteria:
create_issue(project: "AGX", title: "Add SSE endpoint for issue events", epicId: <epic>)
set_task_spec(...); add_checklist_item(...)
create_issue(project: "AGX", title: "Client subscribes to issue stream", epicId: <epic>)
add_sub_issue("AGX-40", title: "Reconnect with backoff")   # split a piece off
link_issues("AGX-41", "AGX-40", "blocks")                  # ordering
```
The epic's status derives from its issues — as they move to `in_progress` /
`done`, the epic rolls up automatically. You never `move_issue` an epic by hand.
Optionally write a plan doc and link it:
```
create_document(title: "Realtime updates — plan", type: "plan", project: "AGX",
                content: "## Approach… see [[AGX-40]], [[AGX-41]].")
```
Then **update the project index** "Active work" to mention the new epic.

---

## 4. Capture knowledge as a wiki doc

When you learn something durable (a decision, a gotcha, an architecture note):
```
create_document(title: "Why search uses tsvector not trigram", type: "memory",
                project: "AGX", content: "Decision: … Trade-offs: … See [[AGX-3]].")
```
Then add it to the project index's "Key docs" as `[[why-search-uses-tsvector-not-trigram]]`.
Use `[[..]]` links liberally — they build the graph that `get_context` and
`get_backlinks` traverse, so the knowledge actually surfaces later.

---

## 5. Bootstrap or refresh the index

```
get_started                       # check globalIndexMissing / focus.indexMissing
# if missing — create from the returned template:
create_document(title: "Workspace Index", slug: "index", type: "context_map",
                content: <globalIndexTemplate>)
# if present but stale — edit it:
update_document("index", content: <updated map>)
```
Update triggers (new project, major doc, epic/milestone change, a newly-learned
"where things live" mapping) and both templates are in `index-convention.md`.

---

## 6. Investigate / report on a project

```
get_started(project: "AGX")       # index + active work + doc catalogue
list_issues(project: "AGX", status: ["in_progress", "in_review"])
list_activity(project: "AGX", limit: 30)
search("<topic>")                 # pull specific issues/docs
```
Answer from these targeted calls — resist `get_document` on everything. The
index + `search` tell you which few docs are actually worth opening.

---

## 7. No MCP tools loaded — drive Agentix over REST

If `get_started` / `whoami` aren't callable, the `agentix` MCP didn't load. You
**cannot** reload the session mid-task without killing this agent — so don't try.
Instead drive the same service over its REST mirror with `curl`. Every write runs
through the *same* normalizer as MCP, so refs accept a UUID **or** display key
(`AGX`, `AGX-12`, a milestone name) and bodies accept the agent aliases
(`description`, `content`, `body`, `project`, `assignee`, `milestone`, …). Unknown
or mistyped fields are rejected `400`, not silently dropped.

Get the Bearer token from keys-keeper `agentix-mcp` (NOT `agentix-prod` — that's a
`DATABASE_URL`, never a bearer). The base URL is `https://agentix.moone.dev`.

```bash
BASE=https://agentix.moone.dev
TOKEN=$(keys get agentix-mcp)            # the MCP/REST bearer; never agentix-prod
H="-H Authorization:Bearer\ $TOKEN -H Content-Type:application/json"

curl -s $BASE/api/health                 # unauthenticated readiness probe ({ok:true})
curl -s $H "$BASE/api/docs"              # self-describing endpoint map + conventions
curl -s $H "$BASE/api/started?project=AGX"   # == get_started; read the brief

# orient on one issue (the REST mirror of get_context):
curl -s $H "$BASE/api/context?issue=AGX-12"   # issue + linked wiki + brief
curl -s $H "$BASE/api/issues/AGX-12"          # or the raw issue alone

# work the lifecycle — there's no move/assign verb; PATCH the field:
curl -s $H -X PATCH "$BASE/api/issues/AGX-12" -d '{"status":"in_progress"}'
curl -s $H -X PATCH "$BASE/api/issues/AGX-12/spec" \
     -d '{"relevantPaths":["lib/"],"testCommand":"npm test"}'
curl -s $H -X POST  "$BASE/api/issues/AGX-12/checklist" -d '{"content":"Tests green"}'
curl -s $H -X PATCH "$BASE/api/checklist/<itemId>" -d '{"done":true}'
curl -s $H -X POST  "$BASE/api/issues/AGX-12/comments" -d '{"body":"Decision: …"}'
curl -s $H -X PATCH "$BASE/api/issues/AGX-12" -d '{"status":"in_review"}'

# file a new issue with alias body (project key + description alias):
curl -s $H -X POST "$BASE/api/issues" \
     -d '{"project":"AGX","title":"…","description":"…","priority":"medium"}'
```
Start every REST session at `GET /api/docs` — it hands you the full verb/path map
and the alias/ref conventions, so you don't have to guess. Hitting an unknown path
returns a JSON `404` (`{error:{code:"not_found",…}}`), not Next's HTML.

---

## 8. Clean up mis-filed work (the delete / unlink surface)

Creation is reversible. When something was filed wrong — an empty test issue, a
duplicate, a stale doc, an abandoned epic or milestone — prefer fixing it over
leaving the board dishonest. **Hard deletes are irreversible**, so confirm intent
and reach for a status (`canceled`) or a `duplicates` link first when the record
still carries history worth keeping.

```
delete_issue("AGX-99")              # empty/duplicate issue — hard delete, gone for good
delete_epic(<epicId>)               # epicId is UUID-only; issues are DETACHED, not deleted
delete_milestone("Q3 launch")       # by UUID or name; issues are detached
delete_document(<uuid-or-slug>)     # stale wiki/plan doc — irreversible
delete_project("OLD")               # hard delete — CASCADES all contents; last resort
unlink_issues(<relationId>)         # remove a wrong relation (id from get_issue's relations)
delete_checklist_item(<itemId>)     # drop a criterion that no longer applies
```
Picking the id: `delete_epic` / `update_epic`, `update_milestone`, `check_item`,
`delete_checklist_item`, and `unlink_issues` all take a **UUID** (or, for
milestones, a name) — get it from `get_issue` (relations, checklist items),
`list_epics`, or `list_milestones`. Over REST the same surface is `DELETE
/api/issues/:ref`, `DELETE /api/epics/:id`, `DELETE /api/milestones/:id`, `DELETE
/api/documents/:ref`, `DELETE /api/projects/:ref`, `DELETE
/api/issues/:ref/relations/:id`, and `DELETE /api/checklist/:id`.

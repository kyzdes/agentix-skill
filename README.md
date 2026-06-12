# agentix (Claude Code skill)

Teaches AI agents how to **work the [Agentix](https://github.com/kyzdes/agentix) issue tracker** — an agent-native, Linear-style tracker exposed over MCP (projects, epics, issues, milestones, checklists, and a wiki).

The problem it solves: an agent connecting "from scratch" doesn't know how the platform is shaped, how to file tasks, or where things live — so it reads the whole wiki and burns its context. This skill front-loads the workflow, the task-creation template, and a wiki **index ("оглавление")** convention so agents orient cheaply and pull only what they need.

## Install

```
/plugin marketplace add kyzdes/claude-skills
/plugin install agentix@claude-skills
```

## What it teaches

- **Orientation workflow** — `get_started` → read the index → `get_context(issue)` → act → keep the map current. Don't read everything.
- **The index convention** — a `slug:index`, `type:context_map` document (one global + one per project) that agents read first and maintain.
- **Task-creation template** — title + description, plus Agentix's structured spec: `set_task_spec` (relevant paths + test command) and acceptance criteria as `add_checklist_item` (not prose). Granularity ladder: sub-issue → issue → epic → milestone.
- **Full tool reference** — all 43 MCP tools with signatures and return shapes.
- **Common workflows** — take an assigned issue, file a well-specced issue, plan an epic, capture knowledge, bootstrap the index.

## Pairs with the platform

Agentix itself ships a `get_started` MCP tool and sets the MCP server `instructions`, so any connecting agent is onboarded even without this skill. This plugin is the detailed companion — richer prose, templates, and recipes.

## Structure

```
skills/agentix/
  SKILL.md                       # the workflow + house rules
  references/
    tools.md                     # all 43 MCP tools
    task-template.md             # issue-creation template + best practices
    quality-gates.md             # ready-to-start + ready-for-done checklists
    index-convention.md          # the global + per-project index convention
    workflows.md                 # end-to-end recipes
```

Part of [kyzdes/claude-skills](https://github.com/kyzdes/claude-skills).

---
description: Enable or disable concept-level operator briefing (default off)
argument-hint: "[on|off|global|status]"
---

The user invoked `/spp:high-level`. This is **high-level**.

Read `${CLAUDE_PLUGIN_ROOT}/skills/high-level/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/skills/high-level/references/claude-md-block.md`.
If those paths are missing, use the `high-level` skill in the skills
directory. Do not summarize them. Announce at start: "Using high-level
to brief the operator at concept level."

`$ARGUMENTS` is a single word, case-insensitive:

| Args | Action |
|---|---|
| empty or `on` | Enable for this project |
| `global` | Enable for this user (`~/.claude/CLAUDE.md`) |
| `off` | Remove the project pointer; if none, the global one |
| `status` | Print `on (project)`, `on (global)`, both, or `off` |

A project already carrying a hand-written briefing of the same substance
counts as on. Do not insert a duplicate.

Enable: copy the block from `references/claude-md-block.md` verbatim,
including both markers, into the target file. Prefer the file the
project already uses (`.claude/CLAUDE.md`, then `./CLAUDE.md`, then
`./AGENTS.md`). Insert after `decision-log-directives-end` if that
marker is present, else near the top, outside any generated section.
Create the file only when enabling globally and `~/.claude/CLAUDE.md`
does not exist.

Disable: delete from `spp-high-level-start` through `spp-high-level-end`,
inclusive.

Commit a project-file change by explicit path (`docs: enable spp
high-level` / `docs: disable spp high-level`) when the repo is clean
enough that this is the only change. Do not `git add -A`. A global
enable is not a git commit.

Then follow the skill for the rest of this turn.

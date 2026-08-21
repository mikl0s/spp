---
description: Short name for superpowers-plus — wave scheduling and the silent-wrongness review lens
argument-hint: "[pause|resume]"
---

The user invoked `/spp`.

If `$ARGUMENTS` is `pause` or starts with `pause`: follow
`${CLAUDE_PLUGIN_ROOT}/commands/spp/pause.md`. If that path is missing,
`commands/spp/pause.md` beside this file. Stop after it.

If `$ARGUMENTS` is `resume` or starts with `resume`: follow
`${CLAUDE_PLUGIN_ROOT}/commands/spp/resume.md`. If that path is missing,
`commands/spp/resume.md` beside this file. Stop after it.

Otherwise this is the short name for **superpowers-plus**.

Read and follow `${CLAUDE_PLUGIN_ROOT}/skills/superpowers-plus/SKILL.md`.
If that path is missing, follow the `superpowers-plus` skill in the skills
directory. Do not summarize it. Announce at start: "Using superpowers-plus
for wave scheduling and review lens."
Never offer subagent vs in-session. Always
`superpowers:subagent-driven-development` unless the user already asked
for inline / in session / executing-plans.
TDD is the default. Do not ask whether to skip tests.

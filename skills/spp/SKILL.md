---
name: spp
description: Short name for superpowers-plus. Use when the user types /spp, says spp, or wants the wave-scheduling harness without the long name. Also /spp pause and /spp resume after pause.
user-invocable: true
argument-hint: "[pause|resume]"
---

This is the short name for **superpowers-plus**.

If the user said `pause` (including `/spp pause`): follow section 7 of
the sibling skill `superpowers-plus` (`../superpowers-plus/SKILL.md`) —
Pause at the context threshold. Write the handoff to `HANDOFF.md` at
the repo root unless the project already names one. Then stop. Tell
the operator to run `/clear`, then `/spp resume after pause`. Do not
clear the session yourself. Do not start new work.

If the user said `resume` (including `/spp resume` and
`/spp resume after pause`): this is the `spp-resume` skill. Read and
follow `../spp-resume/SKILL.md`. Do not summarize it.

Otherwise read and follow the sibling skill `superpowers-plus` (same
skills directory, `../superpowers-plus/SKILL.md`). Do not summarize it.
Announce at start: "Using superpowers-plus for wave scheduling and
review lens."
Never offer subagent vs in-session. Always subagent-driven-development
unless the user already asked for inline / in session / executing-plans.
TDD is the default. Do not ask whether to skip tests.

To update the plugin itself, that is `/spp-update`, not this skill.

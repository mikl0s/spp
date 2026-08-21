---
description: Pause the run at the context threshold — write the handoff and stop
---

The user invoked `/spp pause`. This is the pause protocol in
**superpowers-plus**.

Read and follow `${CLAUDE_PLUGIN_ROOT}/skills/superpowers-plus/SKILL.md`
section 7 (Pause at the context threshold). If that path is missing,
follow the `superpowers-plus` skill in the skills directory, same
section. Do not summarize it. Announce at start: "Using superpowers-plus
for wave scheduling and review lens."

Write the handoff to `HANDOFF.md` at the repo root unless the project
already names a handoff file — use that. The handoff **must name the
plan file**, character for character, plus what to run first, so
`/spp resume` does not have to guess. Then stop. Tell the operator
to run, in this order:

```
/clear
/spp resume
```

Do not clear the session yourself. Do not start new work.

---
name: spp-resume
description: >
  Resume after a context pause. Use when the user types /spp resume,
  /spp:resume, /spp-resume, or /spp resume after pause, or asks to
  pick up from a handoff.
user-invocable: true
---

# Resume after pause

Announce at start: "Using superpowers-plus for wave scheduling and
review lens."

This is a **continuation**, not a new run. Do not reconstruct the run
from the conversation. The handoff and the plan are the corpus.

1. **Read the handoff.** `HANDOFF.md` at the repo root, or the path
   the project already names. If it is missing, say so and stop.

2. **Read the plan the handoff names.** If it names none, look for a
   written plan the project already has (common: `docs/superpowers/plans/`,
   `docs/plans/`). If more than one could be it, stop and name them —
   do not pick. If none exists, say so and stop.

3. **Read only what the handoff says you need next** — standing
   directives, unreviewed log entries, open follow-ups. Do not
   re-derive findings the handoff says not to re-derive.

4. **Follow** the sibling skill `superpowers-plus` (same skills
   directory, `../superpowers-plus/SKILL.md`). Do not summarize it.

   Start at what the handoff says to run first. The meter starts from
   current position, not from empty. Pre-flight only if the handoff
   says the plan changed, or the next task is still task 1 of an
   unstarted plan. A mid-plan resume does not re-preflight the whole
   plan.

Never offer subagent vs in-session. Always
`superpowers:subagent-driven-development` unless the user already asked
for inline / in session / executing-plans. TDD is the default.

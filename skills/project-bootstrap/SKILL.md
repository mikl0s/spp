---
name: project-bootstrap
description: Write a project's CLAUDE.md and seed its decision log, so an autonomous run starts with the standing directives, conventions and hard-won facts a fresh context needs. Use in a new or empty repository, when a project has no CLAUDE.md, when one exists but carries no standing directives, or when the user says bootstrap, set up this project, wire this repo, or asks why an agent keeps getting the same thing wrong. Runs before any plan is written.
---

# Project bootstrap

`CLAUDE.md` is the first thing every future context reads and the only thing
that survives a compaction unchanged. A project without one starts every
session cold — re-deriving the same facts, re-making the same wrong
assumptions, and asking the operator questions it was told the answer to last
week.

This writes that file, and seeds the decision log so the log exists before the
first decision needs it.

Announce at start: "Using project-bootstrap to wire this project."

## 1. Look before asking

Even an "empty" repo usually is not. Spend one pass:

```bash
ls -a && git log --oneline -5 2>/dev/null && cat README* 2>/dev/null | head -40
```

Note the language, the build tool, the test command, anything already
committed. **Every fact you can read is a question you do not have to ask.**
Ask only what the repository cannot tell you.

## 2. Ask only what only the operator knows

Four questions, in one batch, and no more unless an answer opens a real fork:

1. **What is this, in one sentence, and who is it for?** The one-line thesis.
2. **What must never happen?** The constraint that outranks everything —
   data that must not leave, a system that must not be written to, a cost
   ceiling. There is usually exactly one, and it belongs near the top.
3. **How autonomous?** Does an agent ask, or decide and log? If it decides,
   the standing directives in §3 apply and the decision log is mandatory.
4. **What does a session need to run?** Build, test, lint, start — the commands
   an agent would otherwise guess wrong.

If the operator does not know yet, write the section with what is true today
and say so in the file. **An honest gap outlives a confident guess.**

## 3. The standing-directives block

If the project is autonomous, the decision-logging directive goes in first,
using the canonical block from the `decision-log` skill's
`references/claude-md-block.md`. Do not paraphrase it — the review flow greps
for its markers.

**Placement is load-bearing.** Hand-maintained sections go at the **top of the
file, above every generated or managed marker section**. Tools that regenerate
`CLAUDE.md` rewrite the region between their own markers; anything above is
left alone. A standing directive below a marker is a directive with an expiry
date nobody wrote down.

## 4. What the file must contain

In order. Skip a section only when the project genuinely has nothing to put in
it — and say so rather than leaving a heading empty.

| # | Section | Why it earns its place |
|:-:|---|---|
| 1 | Standing directives | Decision logging, the pause protocol, anything that must survive regeneration |
| 2 | What this is | One sentence, then the constraint that outranks everything |
| 3 | Commands | Build, test, lint, run. Exact strings, not descriptions |
| 4 | Conventions | Only where this project differs from the obvious default |
| 5 | **Things a fresh context reliably gets wrong** | See §5 — the highest-value section in the file |
| 6 | Findings not to re-derive | Anything settled by research or by a painful afternoon |
| 7 | Layout | Only if the structure is not self-evident |

## 5. Things a fresh context reliably gets wrong

The section that pays for the file. It is empty on day one and grows every time
a context gets something wrong that the last one also got wrong.

Each entry is one line: **the wrong assumption, then the correction.** Not
advice — a correction. "The database is shared; never reset it" beats "be
careful with the database."

Seed it at bootstrap with anything the operator names in question 2, and add to
it whenever a run wastes time on something a note would have prevented. If an
agent asks a question the file could have answered, the answer belongs here
before the session ends.

## 6. The pause protocol

For autonomous projects, state the context threshold and the ordered handoff:
confirm every subagent has returned **and its output is processed**; finish the
decision log; write the handoff; commit; tell the operator to clear and resume.

A returned agent whose findings exist only in the conversation is unprocessed.
That sentence is worth including verbatim — it is the one people skip.

## 7. Seed the decision log

Create `docs/DECISIONS.md` with its title, a one-line explanation, and the
footer, exactly as the `decision-log` skill specifies. An empty log that exists
beats a missing log that has to be created mid-decision, when the agent is
already busy and likely to improvise the format.

Record the bootstrap itself as `D-001`, type `directive`, capturing what the
operator asked for. The log then starts with the reason the project exists.

## 8. Before finishing

- Every command in §3 was **run**, not assumed. A wrong test command is worse
  than none, because it is trusted once and then quietly fails.
- No section is a heading with nothing under it.
- The standing directives sit above every generated marker. Check by reading
  the file top to bottom, not by intending it.
- Commit `CLAUDE.md` and `docs/DECISIONS.md` together, by explicit path.

Then say what you wrote and what you left empty, so the operator can fill the
gaps you could not.

`references/claude-md-template.md` is a fill-in skeleton.

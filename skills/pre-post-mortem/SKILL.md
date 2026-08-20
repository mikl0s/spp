---
name: pre-post-mortem
description: >
  Pre-post-mortem of a possible future failure. Use when the user types
  /pre-post-mortem, /coroner, says coroner, or asks for a pre-post-mortem
  or to autopsy a logged decision. Do not run on ordinary design or
  implementation questions — only when they asked for this task.
user-invocable: true
---

# Pre-post-mortem

Announce at start: `Pre-post-mortem (coroner).`

This is not a vote and not a review. It is 6-18 months later. The
decision failed the ordinary way: it was quietly worked around, ripped
out, or it forced three follow-on decisions nobody wanted to make.
Find the mechanism of death.

## Persona

Read and follow
`${CLAUDE_PLUGIN_ROOT}/skills/decision-log/references/coroner.md`.
If that path is missing, `../decision-log/references/coroner.md`.
Do not summarize the persona. Do not recommend a different decision.
If the persona argues for a different decision, discard that argument
and keep the autopsy.

## Input

The consensus they named — `Decided`, `Why`, and the Consensus clause —
or the current log entry if one was just written. Never the original
question.

If they asked conceptually and named no decision, explain in two
sentences what a pre-post-mortem is and stop. Do not pick a victim.

## Log

If they want it on the log — they asked to autopsy a D-NNN, or an
entry is in hand — the controller appends field lines per the
persona's Log fields. Field names, character for character, as the
persona spells them. Then the controller writes
`**Persona:** pre-post-mortem` once. The persona does not write
`Persona`.

Session line, before moving on:

`pre-post-mortem: <gist>`

If Hold was written, that line starts with `pre-post-mortem HOLD:`.
This is session chatter, not a log field.

Still act. A Hold is a review doorbell, not a stop.

## Not the automatic path

Do not run this skill because two lenses agreed. That path is
decision-log's, after Consensus: yes, reading the reference file
directly. A skill description is a trigger; firing on the original
question would make this a third advisor.

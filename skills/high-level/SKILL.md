---
name: high-level
description: >
  Use when the project's CLAUDE.md, AGENTS.md, or ~/.claude/CLAUDE.md
  contains spp-high-level-start, or the user ran /spp:high-level,
  /spp:stay-high-level, or /superpowers-plus:high-level, or asked to
  brief at concept level. Default off — do not load without the marker
  or the slash.
user-invocable: true
---

# High-level

An opt-in overlay on how SPP talks to the operator. It does not change
what is decided, logged, or scheduled. Where this file and another
skill's default phrasing disagree, this file wins.

Announce at start: "Using high-level to brief the operator at concept
level."

> **Concepts over code. Idea over implementation.**

The operator holds the design, including parts that were never written
down, and is not checking the engineering. Pitch what a thing *is* and
what it *does to the product, the user, the loop*. File paths,
identifiers, versions, and hashes are noise unless they asked.

## Operator-facing shape

Every message the operator will read, including `/spp` status and
`decision-review` questions:

1. **If they just thought out loud**, lead with a one-breath restatement
   of it. That is how they spot holes, not a courtesy.
2. **The concept.** What it is. What it does. Consequence they can rule
   on.
3. **Hygiene, if any, as a bullet list.** Each bullet is ELI5 and at
   most 100 characters. One bullet per item. This is the only form
   engineering hygiene takes in this mode.
4. **The ask**, when there is one, in ordinary chat. Then stop.
   Never a multiple-choice picker (`AskUserQuestion`,
   `ask_user_question`). The box is too narrow. One ruling at a time;
   they type accept / change / discuss.

A long explanation is a failure signal. If it takes three paragraphs,
the concept has not been found yet. Find it, then write one.

**`Discuss` means "this is nonsense to me, say it again in plain
words".** Re-explain, then ask for the ruling. It is never an invitation
to debate the engineering.

**Expect a reframe.** If every option looks wrong, the options were
probably wrong. Check the framing before defending the menu.

## During decision-review

This file replaces `decision-review` §6's question body and the bulk
line `ID — chose X over Y`. The walk, the cursor, and the hard
criteria stay theirs.

**Individual.** Ordinary chat, one ID at a time. Concept, then
consequence. Lenses only as what each would do to the product, the
user, the loop — not as engineering positions. Then they type accept /
change / discuss.

**Bulk.** Concept one-liners for what remains. Hygiene as the
100-character bullets. Then ask `accept all N?` in ordinary chat.
Same three answers as the skill: accept all, review individually,
pick some — typed, not a picker.

## Hygiene (this mode only)

Hygiene is work that does not change what the product is or does for
the user: version stamps, refactors, test placement, internal names,
build plumbing.

- Decide it, log it, act. Do not ask.
- Surface it only as the 100-character ELI5 bullets above.
- In `decision-review`, hygiene rides the bulk list in that form. Do
  not individually walk it, even at `project` blast radius.

  - Old saves still open after we changed how they're stored.
  - Tests now live next to the code they check.

Do not individually walk `directive` entries. Those are calls already
made.

## Enable / disable

Default off. The enable bit is a short pointer in CLAUDE.md (project)
or `~/.claude/CLAUDE.md` (global). The rules stay in this file so
`/spp-update` can change them without touching every project.

`/spp:high-level` writes the pointer. `/spp:high-level off` removes it.
See `references/claude-md-block.md`.

## Red flags

| Thought | Reality |
|---|---|
| "They need the files" | They need the concept. |
| "Discuss = defend it" | Say it in plain words, then ask. |
| "Hygiene needs a walk" | Bulk, as 100-character bullets. |
| "Skip the restatement" | It is for them, so they see holes. |
| "No marker, but use it" | Default off. Do not load. |
| "The picker is faster" | It clips the concept. Ordinary chat. |
| "Keep option — pro — con" | This file replaces §6. |
| "Bulk is chose X over Y" | Concept one-liners, then accept all N? |

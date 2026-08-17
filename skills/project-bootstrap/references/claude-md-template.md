# CLAUDE.md skeleton

Fill in and delete what does not apply. Angle brackets are placeholders.
Order matters: everything hand-maintained sits above any generated marker.

---

```markdown
<!-- decision-log-directives-start — HAND-MAINTAINED, do not remove; verified by the decision-log skill -->

## Decision Logging (standing directive)

- Every decision made without the operator is logged via the `decision-log`
  skill into `docs/DECISIONS.md` BEFORE acting on it: uniform entries (ID,
  type decision/directive/pause, Decided, Options, Why, mandatory
  **Consensus: yes/no** naming any dissenting lens, **Blast radius**, Impact).
- Orchestrator decisions carry two lenses — `superpowers-plus` and `ponytail`
  — with agreement, dissent, or synthesis recorded honestly. Ties break on
  blast radius: `task` to `ponytail`, wider to `superpowers-plus`.
- Operator directives received mid-run are logged as type `directive`;
  context-window pauses as type `pause`.
- The operator reviews unreviewed entries with the `decision-review` skill
  before context clears — it surfaces non-consensus entries, so the
  Consensus line must be honest.
- The log is append-only: never edit or renumber past entries; never touch
  the `<!-- reviewed-through -->` marker outside the review skill.

<!-- decision-log-directives-end -->

# Operating rules — read before doing anything

> Hand-maintained, and above every generated marker deliberately. A tool that
> regenerates this file rewrites only the region between its own markers.
> Do not move this section below one.

## What this is

<One sentence: what it is and who it is for.>

> **⛔ <The thing that must never happen.>**
>
> <Why, and what it costs if ignored. One constraint, near the top, where it
> cannot be missed. If there are two, say which outranks the other.>

## Pause at ~<N>% context — not optional

When context use passes ~<N>%, stop taking on new work and hand off. Not at 70%
because the current task feels nearly done. The failure this prevents is
running out mid-task with unprocessed subagent output and no written record,
which loses the reasoning, not merely the position.

1. **Confirm every subagent has returned and its output is processed** —
   written to a file, folded into a decision, or explicitly marked stale.
   A returned agent whose findings exist only in the conversation is
   unprocessed.
2. **Finish the decision log.** Nothing deferred to next time.
3. **Write the handoff**: where things stand, what to run first on resume,
   what a fresh context reliably gets wrong, findings not to re-derive, and
   what is open and waiting on the operator.
4. **Commit**, working tree clean.
5. **Tell the operator to clear and resume**, stating what is unresolved.

## Commands

```bash
<build>
<test>
<lint>
<run>
```

<Each one run at least once. A wrong command here is trusted, then fails
quietly.>

## Conventions

- <Only where this project differs from the obvious default.>
- <Commit style, branch policy, what may be committed directly.>
- <Anything an agent would otherwise reasonably get wrong.>

## Things a fresh context reliably gets wrong

<One line each: the wrong assumption, then the correction. Empty on day one;
add an entry every time a session loses time to something a note would have
prevented. If an agent asks a question this file could have answered, the
answer belongs here before the session ends.>

1. **<The wrong assumption.>** <The correction.>
2. **<The wrong assumption.>** <The correction.>

## Findings not to re-derive

<Anything settled by research or by a painful afternoon, with enough detail
that nobody re-opens it. Cite where the reasoning lives.>

## Layout

```
<dir>/     <what lives here>
```

<Only if the structure is not self-evident.>
```

---

## Seed `docs/DECISIONS.md`

```markdown
# Decision log — <project>

Every decision made without the operator. Uniform entries via the
`decision-log` skill; reviewed via `decision-review`.

---

## D-001 — bootstrap this project (directive, <YYYY-MM-DD>)

**Decided:** wired the project with standing directives, conventions and a
decision log.
**Options:** none — direct operator instruction.
**Why:** <what the operator asked for, in their terms>
**Consensus:** yes — uncontested.
**Blast radius:** project

---
*Log maintained by the decision-log skill. Entries are append-only.*
```

## The two questions people skip

**"What must never happen?"** — there is almost always exactly one, the
operator knows it immediately, and it never makes it into the file unless
asked directly. It belongs above the conventions, not among them.

**Do not ask "how autonomous?"** SPP's default is decide-and-log. The
standing-directives block always belongs. A project that wants the agent
to ask on every ambiguity is not using SPP; remove the block after
bootstrap rather than skipping it here.

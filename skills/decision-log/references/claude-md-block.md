# The canonical `CLAUDE.md` block

A project is *wired* for decision logging when its `CLAUDE.md` carries a
standing directive telling every agent to log decisions instead of asking. This
file holds the canonical form of that directive.

## Where it goes

Insert it at the **top** of `.claude/CLAUDE.md`, or `./CLAUDE.md` if the
project keeps its instructions there. Prefer whichever file the project already
uses; never create a second one.

Insert it **outside any generated or managed marker section**. Blocks inside a
managed section are rewritten whenever the generator runs, and a standing
directive that disappears on the next regeneration is worse than no directive
at all — the run believes it is wired and is not.

## When a project is already wired

A project carrying its own hand-written directive of the same substance counts
as wired. **Substance over markers.** Do not insert a duplicate block beside an
existing directive that already says decisions are logged before acting, in a
uniform format, with a mandatory consensus line, append-only, and reviewed
before context clears. Two directives saying the same thing in different words
is how they drift apart.

If the existing directive covers only part of the substance, extend it in
place; do not bolt the canonical block on next to it.

## The block

Copy verbatim, including both markers. The start marker is what the
`decision-review` skill greps for.

```markdown
<!-- decision-log-directives-start — HAND-MAINTAINED, do not remove; verified by the decision-log skill -->

## Decision Logging (standing directive)

- Every decision made without the operator is logged via the `decision-log`
  skill into `docs/DECISIONS.md` BEFORE acting on it: uniform entries (ID,
  type decision/directive/pause, Decided, Options, Why, mandatory
  **Consensus: yes/no** naming any dissenting lens, **Blast radius**, Impact).
- Orchestrator decisions carry two lenses — `superpowers-plus` and `ponytail`
  — with agreement, dissent, or synthesis recorded honestly.
- Operator directives received mid-run are logged as type `directive`;
  context-window pauses as type `pause`.
- The operator reviews unreviewed entries with the `decision-review` skill
  before context clears — it surfaces non-consensus entries, so the
  Consensus line must be honest.
- The log is append-only: never edit or renumber past entries; never touch
  the `<!-- reviewed-through -->` marker outside the review skill.

<!-- decision-log-directives-end -->
```

## Related conventions

A short **"things a fresh context reliably gets wrong"** list in the same
`CLAUDE.md` is the same anti-decay mechanism: write down what is otherwise
re-learned every window. It is a convention, not part of this block.

# The canonical high-level enable bit

A project is *in high-level mode* when its instructions file carries this
pointer. The rules live in the plugin skill `high-level`. Do not copy
those rules into the project — `/spp-update` would then leave a stale
copy here.

## Where it goes

**Project:** `.claude/CLAUDE.md`, or `./CLAUDE.md`, or `./AGENTS.md` —
whichever the project already uses. Prefer the existing file; never
create a second one.

**Global:** `~/.claude/CLAUDE.md`. That covers every project for this
user.

Insert it **outside any generated or managed marker section**, near the
top. After `decision-log-directives-end` if that block is present.

A project already carrying a hand-written briefing of the same
substance (concepts over code, hygiene not walked individually) counts
as enabled. Substance over markers. Do not insert a duplicate.

## The block

Copy verbatim, including both markers. The start marker is what the
skill greps for.

```markdown
<!-- spp-high-level-start — enable bit only; rules live in the plugin skill -->

This project briefs the operator at concept level. Follow the
`high-level` skill for every operator-facing message, including `/spp`
and `decision-review`. That skill wins over those skills' default
phrasing.

<!-- spp-high-level-end -->
```

## Removing it

Delete from the start marker through the end marker, inclusive.
`/spp:high-level off` does that.

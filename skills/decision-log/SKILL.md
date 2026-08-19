---
name: decision-log
description: Append a uniformly-formatted entry to the project decision log (docs/DECISIONS.md) and commit it. Use EVERY time a decision is made without the operator during autonomous or semi-autonomous work — technology choices, scope cuts, interpretation of ambiguous requirements, deviations from plan — and also to record operator directives received mid-run, and context-window pauses. Trigger on "log this decision", "decision log", "/decision-log", or whenever standing project directives require decisions to be logged rather than asked. If in doubt whether something is log-worthy: it is.
---

# Decision Log

The log is the audit trail that replaces interactive approval. An agent working
without the operator records what it decided, what it would have asked, and why
it chose as it did. The operator rules on those decisions later, in batch.
Autonomy is granted in exchange for the record.

Every entry is written to one format, because a review tool has to parse logs
from every project on the machine. Deviate from the format and the entry is
silently skipped at review — a decision the operator never sees.

## 1. Verify the project is wired (self-heal)

One grep, cheap enough to run on every invocation. Look for
`decision-log-directives-start`, or failing that `decision-log`, in
`.claude/CLAUDE.md`, then `./CLAUDE.md`.

- **Hit** — proceed.
- **Miss** — insert the block from `references/claude-md-block.md` at the top
  of the file, outside any generated or managed marker section, commit it
  together with the entry, and mention the self-heal in the reply.

A project with its own hand-written directive of the same substance counts as
wired. Substance over markers, no duplicate block.

## 2. Locate the log

`docs/DECISIONS.md` in the repo under work. If it does not exist, create it with
a title, a one-line explanation of what it is, and a footer stating the log is
append-only. Nothing else — the file is entries.

## 3. Determine the next ID

Parse every `## D-NNN` heading. The next ID is the highest seen plus one,
zero-padded to three digits. An empty or freshly created log starts at `D-001`.
IDs strictly increase and are never reused, never renumbered. Gaps are fine; the
first entry in a log need not be `D-001`.

If `validate.py` reports that a heading line does not parse — wrong heading
level, wrong separator, a malformed ID, invisible or misplaced characters —
stop and repair that heading before writing. A heading the scan cannot read is
an ID the scan cannot see, so the highest-ID count comes back low and the next
entry reuses an ID — the one thing this skill says must never happen.
`validate.py` beside this file is the authority: exit 0 valid, exit 1 problems
found, anything else a broken check.

Two reports carry a heading's line number without being that. `ID D-NNN does
not increase (previous …) — duplicate or out of order` covers both the
duplicate and the out-of-order case; neither heading failed to parse, its ID is
already visible, and the only repair for either is changing an ID, which this
section forbids. An impossible date is the same shape of trap: it is reported
only after the heading has matched, so nothing is hidden, the string is already
well-formed, and the true date is not recoverable from the file — a repair
would invent one. Report all three to the operator and write nothing.

**This repair is the sole exception to append-only (§7).** It is permitted for
one reason only — an unreadable heading hides an ID and the next entry reuses
it — and it restores only the characters the parser needs to see that heading,
never a recorded value. Where a problem hides no ID the licence does not apply,
however small the fix looks: "the log cannot reach exit 0 otherwise" is not a
reason to edit an entry, or every missing field in the log becomes editable by
the same argument. Nothing else edits an entry, ever.

## 4. Write the entry

Verbatim template. Field names, order, and punctuation are load-bearing.

```markdown
## D-NNN — <short title> (<type>, <YYYY-MM-DD>)

**Decided:** <what was decided, one or two sentences>
**Options:** <the choices that would have been put to the operator, one line each>
**Why:** <the reasoning that picked the winner>
**Consensus:** <yes | no> — <shared reasoning, or who dissented and why overruled>
**Blast radius:** <task | plan | project | cross-project>
**Impact:** <optional — artifacts affected, follow-ups, blockers created>
```

- `<type>` is `decision` (the agent chose), `directive` (an operator
  instruction received mid-run), or `pause` (a context pause: what was in
  flight, why here, what resumes).
- `Decided`, `Options`, `Why`, `Consensus`, `Blast radius` are required.
  `Impact` is optional.
- A `directive` has no alternatives to weigh: its `Options` line reads
  `none — direct operator instruction`.
- **Both separators are U+2014 EM DASH** (`—`): the one after the ID, and the
  one after `yes`/`no` on the Consensus line. A hyphen or an en dash makes the
  heading unreadable to the parser, and an entry whose heading does not parse
  loses every field with it.
- **Values may wrap** to stay inside 80 columns. A continuation line must never
  begin with `**`, or it reads as the next field. The parser is line-oriented
  and keeps the first line, so the discriminating part of a value goes there:
  for Consensus, the `yes`/`no` and the clause naming the dissent.
- **Never annotate the heading.** The heading line is the parse anchor: it is
  written once, at creation, and nothing is ever appended to it — not
  supersession, not review annotations, not anything a later skill invents. An
  unmatched heading discards every field of its entry, so the decision vanishes
  from review. Annotations are appended as further `**Field:**` lines instead.
- **What the parser accepts is one regex.** A field line is recognised by
  `^\*\*([A-Z][A-Za-z ]*):\*\*` in `validate.py` beside this file, applied to
  the raw line. That pattern is the authority and is deliberately not restated
  here in words: to learn whether a name is recognised, match it against the
  pattern, never against an English paraphrase of it. A line the pattern does
  not match is neither a field nor an error — it is dropped unreported, so an
  annotation whose name misses it vanishes from review with its value.

- **What you may write is a strict subset of that.** Start with a capital
  `A`–`Z`; use only the ASCII letters `A-Z` and `a-z` and the space; put
  exactly one space between words; never a space before the colon. Put a date,
  an ID, or a name in the value — `**Operator override:** 2026-08-05 — …`,
  never `**Operator override (2026-08-05):**`. The two sets are not the same,
  and the difference is the reason this rule exists: `**Operator  override:**`
  and `**Reviewed :**` *do* match the parser. They key fields named
  `Operator  override` and `Reviewed ` — names other than the ones they appear
  to be — and no error is raised, so the annotation is filed under a name
  nothing looks for. The house rule is narrower than the parser exactly where
  the parser is silent. This binds every annotation any skill adds, now or
  later.

*The Consensus line is mandatory.* It is what review uses to surface contested
calls. An advisor, reviewer agent, or research finding that disagreed and was
overruled is `Consensus: no`. Nothing contested is `Consensus: yes —
uncontested`.

*Log the alternatives, not just the choice — the operator is reconstructing a
conversation that never happened.* A decision recorded without its rejected
options cannot be ruled on, only accepted.

*Log before acting, in the same turn — not batched at the end of a window,*
where an exhausted context loses them.

## 5. Two lenses on every orchestrator decision

The orchestrator decides too. Small fixes judged not worth interrupting the
operator for are still decisions, and they are the ones most likely to escape a
record. Those entries carry two viewpoints, always:

| Lens | Asks |
|---|---|
| `superpowers-plus` | what does the plan, the graph, and the review lens require? |
| `ponytail` | what is the least that actually works here? |

- **They agree** → one entry, the shared reasoning, `Consensus: yes`.
  Agreement is necessary for bulk, not sufficient — a later persona field
  (`Hold`) still pulls the entry out of the batch.
- **They disagree** → both positions logged, each with its own reasoning, plus
  what was chosen and why the loser lost. `Consensus: no`.
- **Ties break on blast radius.** At `task` scope the tie goes to `ponytail`;
  at `plan`, `project`, or `cross-project` scope it goes to `superpowers-plus`.
  The lazy option wins where being wrong is cheap and locally reversible; the
  structural option wins where it is not. A flat tiebreak in either direction is
  a systematic bias applied hundreds of times.
- **Synthesis is encouraged.** Where the lenses reconcile into a third option
  better than either, log that as the decision and label it a synthesis. A
  staged debate for the file is not the goal; an honest record of disagreement
  is.

### Personas

After the two lenses have produced a Consensus line on a **new** entry, walk
the table. Do not scan `references/`. A later persona is another `.md` in
`references/` plus another row here.

| Persona | Gate | File | Appends |
|---|---|---|---|
| coroner | type is `decision` AND Consensus starts with `yes` | `references/coroner.md` | see below |

- Skip when Consensus is `no` — disagreement already did this work.
- Skip `directive` and `pause` on the write path. Do not run the persona.
- Input is the entry's `Decided`, `Why`, and Consensus clause. Never the
  original question. Never edit `Decided` / `Options` / `Why` / `Consensus`.
  Append field lines only.
- Still act. Personas do not halt the run. `Hold` is a review doorbell, not a
  stop.
- Read `references/coroner.md` and apply it. Map the return onto these names,
  character for character (§4 field-name rules bind them):

  - `**Assumptions:**` always, on a gated yes. Falsifiable claims, or `none`
    plus one sentence.
  - `**Falsification:**` only when Assumptions is not `none`.
  - `**Point of no return:**` only when Assumptions is not `none`. The event,
    not a date. Spaces in the name — a hyphen vanishes unreported.
  - `**Hold:**` only the combo: no cheap falsification AND an early point of
    no return. Omit the field otherwise. Never write `Hold: no`.
    Discriminating content on the first line of the value.

- Personas have no vote. If the persona argues for a different decision,
  discard that argument and keep only assumptions / falsification / point of
  no return.

## 6. Blast radius

An enum, never prose: `task` · `plan` · `project` · `cross-project`.

**Classify by who can observe the difference.** If nothing outside this task's
own files can tell which option was taken, it is `task`; if another task can, it
is at least `plan`; if the running system or its operators can, `project`; if
another repository can, `cross-project`. Under-stating the radius silently hands
every tie to `ponytail`, which is the systematic bias the tiebreak exists to
avoid — when genuinely torn, take the wider one.

It drives three things: triage ordering, whether an entry escapes the bulk
batch at review, and whether the decision qualifies for a deadline-ask. Prose
impact notes stay in `Impact`; the sortable field is what makes a long log
triageable.

## 7. Supersession and outcome

Both annotations below are field lines, and so is any a later skill invents:
the two field-name rules in §4 bind them. Write the name exactly — one space
between words, none before the colon. A drifted name still parses; it just
files the annotation under a different field, unreported.

**Supersession.** When a later decision overturns an earlier one, append a
`**Superseded by:**` line to the old entry, keep its reasoning intact, and point
at the successor. The heading is not touched. When reversing yourself, say
plainly what was wrong.

```markdown
**Superseded by:** D-004 — the unknown marker was replaced by a typed column.
```

**Outcome.** Where a decision's consequence becomes observable later — commits
made, fix rounds triggered, a real-data figure that contradicted it, tests added
or broken — append an `**Outcome:**` line to the original entry. Outcomes are
appended, never edited into the original reasoning, so review sees the decision
and what it caused side by side.

The log is append-only. Never edit, never renumber, never delete — supersede.
Never touch the `<!-- reviewed-through: D-NNN YYYY-MM-DD -->` cursor; the
`decision-review` skill owns it.

## 8. Commit

`docs: log D-NNN <short title>`, or fold the entry into the commit of the work
that produced it. Respect the project's own commit tooling and hooks. When
other agents share the git index, add the log by explicit path — never
`git add -A`.

## 9. Worked example

An implementer running task `T3` finds the plan does not say what happens when
an input record is missing a field the plan assumes is always present. It does
not stop to ask. It decides, logs, and continues:

```markdown
## D-042 — missing field treated as unknown, not zero (decision, 2026-08-04)

**Decided:** records lacking the field are carried through with an explicit
unknown marker and counted, rather than defaulting to zero.
**Options:** (a) default to zero, (b) drop the record, (c) carry an explicit
unknown and count it.
**Why:** zero is a legitimate value in this field, so defaulting makes a parse
failure indistinguishable from a real reading. Dropping loses the row silently.
**Consensus:** no — `ponytail` wanted the zero default as the smallest change;
overruled because the blast radius is `plan` and a silent wrong value
propagates into every downstream total.
**Blast radius:** plan
**Impact:** the downstream summary needs an unknown column; noted for T7.
```

A later task decides something both lenses already agree on. Coroner runs
because Consensus starts with `yes`. Nothing is load-bearing, so the field
is still written — `none` plus one sentence — and `Hold` is omitted:

```markdown
## D-043 — keep the denominator table as-is (decision, 2026-08-05)

**Decided:** the denominator table is left unchanged; no extra rollup
column is added in this task.
**Options:** (a) leave the table as-is, (b) add a rollup column now.
**Why:** nothing in this task reads a rollup, and adding one would pull
work that belongs in a later plan.
**Consensus:** yes — uncontested.
**Blast radius:** task
**Assumptions:** none — no downstream total in this plan reads a rollup
from this table.
```

## Red flags

| Thought | Reality |
|---|---|
| "I should ask the operator about this" | Only if you are hard-blocked. Otherwise decide, log it, continue. |
| "It's a small thing, no need to log it" | If in doubt whether it is log-worthy: it is. |
| "Both lenses obviously agree" | Then say so in one line. Skipping Consensus is what breaks triage. |
| "I'll write up the decisions at the end" | A dying context loses them. Log before acting, same turn. |
| "I'll fix the wording of D-017 while I'm here" | Append-only. Supersede it or add an Outcome. |
| "I'll put coroner in skills/ so it can be invoked" | A skill description is a trigger. It would fire on the original question and become a third advisor. Personas are controller-read files. |
| "Hold means stop" | Still act. Hold only forces individual review. |
| "Nothing load-bearing, skip the field" | Write `Assumptions: none` plus one sentence. Review fail-closed needs observed absence of Hold, not absence of the whole block. |

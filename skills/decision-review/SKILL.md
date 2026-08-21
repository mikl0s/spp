---
name: decision-review
description: Walk the operator through every decision logged in the project decision log (docs/DECISIONS.md) since the last review marker, one structured question per decision — accept it, change it, or discuss it — then update the marker and commit. Use whenever the user says "decision review", "/decision-review", "review the decision log", "walk me through the decisions", "go through what you decided", or before a context clear or autonomous resume when unreviewed entries exist. Also use when the user asks "what did you decide while I was away".
---

# Decision Review

The operator's catch-up pass. An autonomous run logged its decisions instead of
asking; this replays them as questions the operator can accept, change, or
discuss. Run it before a context clear or an autonomous resume.

Triage is what makes a 200-entry log reviewable in the context that remains.
The failure it exists to catch is a **prefix treated as the set**: as the
window fills, the unread tail vanishes, so supersession, chain-approval, and
the second lens never make it into a question. The log file is the corpus.
The conversation is not.

## 1. Mode: triage (default) vs `--all`

**Read every unreviewed entry from the log file before the first
question.** Cursor to end, one pass. Do not walk the first four and
discover the rest as you go. The tail is where `Superseded by` and
chain-approval live. Entries you have not read are not eligible for
bulk, auto-accept, skip, or a close-out count.

**Auto-accept — do not ask.** Append `**Reviewed:** ✅ operator-reviewed
<date> — auto: <reason>` and drop from the question list. These are
settled, not skipped:

1. Type `directive`. A decision the operator made, then logged, is
   already approved. Do not re-ask it.
2. Already carries `Reviewed`, `Reconfirmed`, `Operator override`, or
   `Discussed`.
3. Carries `Superseded by`, or a later unreviewed entry settles the
   same question (the same choice, or a directive covering it). Keep
   the latest; auto-accept the earlier as chain.
4. No choice. Options is `none`, missing, or a single option. A
   review with one option is not a review.

Deduplicate on the question asked, not the title. Two entries that
decide the same thing are one review.

**Individually questioned — hard criteria. No judgement, no exceptions.** An
entry matching any of these is questioned individually whatever else you
think of it:

1. Every entry whose Consensus is not `yes`. Never triaged away, never folded
   into a bulk batch, regardless of type or blast radius. **Read this
   fail-closed:** an entry whose Consensus line is missing, malformed, or
   anything you cannot read as `yes` counts as `no`. Only a legible `yes` earns
   the bulk batch. Absence of dissent is not consensus.
2. Every entry with blast radius `project` or `cross-project`. A blast radius
   you cannot read is treated as `project`. "It looks unremarkable" is not a
   reason to bulk one — the radius is the operator's own declared threshold,
   not your estimate of interest.
3. Every entry whose parsed fields contain `Hold`. **Read this fail-closed:**
   only an entry you have *observed* to lack a `Hold` field may enter the bulk
   batch. If you did not parse the fields, you have not observed absence.
   Blast radius never demotes a Hold. Type never exempts a present Hold on
   a remaining entry — a `pause` that somehow carries one is still
   individual. A `directive` was auto-accepted above: the operator already
   decided. Absence of the field is not Hold: pre-coroner logs stay in
   the bulk batch.

**Individually questioned — judgement.** On top of the hard criteria, include
anything you judge attention-worthy: rulings made on the operator's behalf at
an external interface, deviations from operator-pinned decisions, relaxed
security checks.

When unsure, include it. *Triage saves clicks, not accountability.*

**Everything else** becomes one bulk-accept question. Each line is
`ID — chose X over Y — <consensus clause or ⚠ dissent>`, so a stray is
still spottable and a choice is visible. Options: `Accept all N` /
`Review individually` / `Pick some to discuss`. `pause` entries default
to the bulk batch after the auto-accept filter — but the hard criteria
bind them too. Type never exempts a remaining entry from any of them.

`Pick some to discuss` splits the batch: the picked entries move to the
individual walk of §6, and **the unpicked remainder is not accepted by
default** — it is re-offered as a fresh bulk-accept question once the picks are
resolved. Nothing is accepted that the operator did not accept.
Auto-accept in this section is that prior acceptance, already on the log.

`--all` disables bulk of what remains after auto-accept. It does not
put settled entries back on the question list.

## 2. Locate the log

`docs/DECISIONS.md` by default; an argument overrides the path. If it is
absent, say so and stop. **Never scaffold a log the project does not have** —
an empty log manufactured here reads as "nothing was decided", which is the
opposite of the truth.

## 3. Validate before reading — three outcomes, not two

Run the validator that ships beside the log skill:

```bash
python3 <plugin>/skills/decision-log/validate.py <log-path> ; echo "exit=$?"
```

Read the exit code. It has **three** meanings and they are not
interchangeable:

| Exit | Meaning | What you do |
|---|---|---|
| `0` | Valid | Proceed. |
| `1` | Problems found, one per line on stdout | Report every line verbatim, then ask whether to continue. |
| anything else | **A broken check** | Stop. Say the check itself failed. |

- **Exit 1 is not fatal, but it is not silent either.** An entry the validator
  cannot parse is an entry the review walk will skip — a decision the operator
  never sees. Show the problems and let the operator choose; do not decide for
  them, and never continue without saying what will be missed.
- **Any exit other than 0 or 1 means the check did not run**, not that the log
  is clean. A missing file, an unreadable path, a traceback, a validator that
  is not where you expected — all of these are broken checks. Report the exit
  code and the output, and stop. Do not fall back to reading the log
  unvalidated.

*Collapsing "the check broke" into "the check passed" is the exact
failure this plugin exists to catch. Two branches is a bug. Write three.*

**Keep this run's output as the baseline.** Save the exit code and the exact
problem lines. §8 step 1 compares against them to tell a problem the review
introduced from one that was already there. Without a baseline, one
pre-existing malformed entry blocks every future review of that log.

## 4. Setup check — one grep, piggybacked

While you are here, confirm the project's `.claude/CLAUDE.md` or `./CLAUDE.md`
carries a standing directive to log decisions. Grep for
`decision-log-directives-start`, or failing that `decision-log`.

**A grep miss is not proof of a miss.** A project may carry its own
hand-written directive of the same substance under different wording, and that
counts as wired. Before flagging, read the file and judge the substance: does
it tell an autonomous run to record decisions rather than ask? If it does, say
nothing. Offering a duplicate block to a correctly-wired project is the failure
here.

A genuine miss means the next autonomous run will not log at all. Do not
interrupt the walk for it — flag it in the close-out and offer to insert the
canonical block from the log skill's references.

## 5. Find the cursor

The cursor is a single line: `<!-- reviewed-through: D-NNN YYYY-MM-DD -->`.

- **Present** → unreviewed is every entry with an ID after that one.
- **Absent** → every entry is unreviewed.
- **Nothing unreviewed** → report "fully reviewed through D-NNN" and stop.

## 6. Walk the decisions

The filter in §1 has already run. Walk only what remains, in ID order,
batched up to 4 per `AskUserQuestion` call.

**Question body, in this order — a recipe, not a compression:**

1. **ELI5.** One sentence a colleague who was not in the run would
   understand. No log jargon, no entry title recycled as the question.
2. **The choices.** Each option on its own line: option — pro — con.
   Pros and cons come from `Options`, `Why`, and the lens positions.
   If a side was not argued, write `not argued`. Do not invent a con
   to make a thin entry look like a debate, and do not drop a choice
   that was on the table.
3. **Viewpoints.** Both lenses at equal weight, or the Consensus
   clause if they agreed. The overruled lens is not a footnote; it is
   the reason the entry is here.

An entry that cannot fill (2) had no choice and should have been
auto-accepted in §1. Do not ask it.

Do not re-argue. The operator is ruling on what was decided, not on
your summary of why it was right. Surfacing the table they were not
in the room for is not re-arguing.

- **Header** is the ID.
- **Non-consensus entries are prefixed `⚠ NON-CONSENSUS —` and name the
  dissent in one clause.** They must never read like routine accepts.
- **Hold entries are prefixed `⚠ HOLD —` and name who wrote it, from
  the parsed `Persona` field, then the combo in one clause** (no cheap
  falsification, early point of no return). Shape:
  `⚠ HOLD — coroner — <combo in one clause>`. If `Persona` lists
  several names, use that value (`coroner, <name>`). If Hold is
  present and `Persona` is missing (pre-byline entries), keep
  `⚠ HOLD —` with no name rather than inventing one. They must never
  read like routine accepts. `Persona` is a byline, not a hard criterion.
  Hold remains row 3 of the hard criteria.
- **If an entry is both non-consensus and Hold, the non-consensus prefix
  wins** (dissent already did the work); still individual.
- **A re-offered entry is presented with the ruling it already carries.** An
  entry can come round twice — the cursor parked behind a skip (§8 step 2)
  re-offers everything after it. If §1 already auto-accepted it, it is not
  in this walk. If it still is, and it already has a `**Reviewed:**`,
  `**Operator override:**` or `**Discussed:**` line, say so in the question:
  *"previously overruled: fail fast instead — re-confirm?"* Asking about a
  decision the operator already overruled, with no sign they ever ruled,
  invites an Accept that lands after the override and reads as reversing it.
- **A second acceptance appends `**Reconfirmed:**`, never a second
  `**Reviewed:**`.** Nothing is edited: an entry already carrying a ruling
  gets a distinct new field, so the sequence stays readable and append-only
  holds without exception. Two identical field names would in any case be
  wrong twice over: the parser keeps only the last value, so the earlier
  ruling is invisible, *and* the validator emits `line N: D-NNN repeats field
  '<name>'` — which §8 step 1 then reads as a problem the review introduced,
  and blocks the commit on.
- **Options are exactly three:** `Accept`, `Change`, `Discuss`.

## 7. Handle the answers

**Never annotate a heading.** The heading is the parse anchor: an ID, a title,
a type, and a date, written once when the entry is created. Anything appended
to it — a tick, a date, a reviewed marker — makes the heading unmatchable, and
an unmatched heading discards *every field of that entry*. Accepting a decision
would delete it from the audit trail, and accepting the newest one would leave
a cursor pointing at an ID no longer in the log. Every annotation this skill
writes is an appended `**Field:**` line.

**A field name must match what the parser accepts, character for character:
`**`, one character from `A-Z`, then any number of `A-Za-z` and spaces, then
`:**`.** No digits, no punctuation, no accented or otherwise non-ASCII
letters, and nothing between those pieces. A hyphen, a parenthesis, a digit or
a colon inside the name makes the line match nothing: it registers as neither a
field nor an error, and the annotation sits in the log invisible to every
check. `Follow-up` and `Operator override (<date>)` are both unparseable for
the same reason — this is a charset rule, not a ban on one punctuation mark.

**Spaces are the trap the wording exists for, and there are two of them.** A
trailing space — `**Reviewed :**` — parses, but its name is `Reviewed `, a
*different* field from `Reviewed`. A doubled space inside the name does exactly
the same: `**Operator  override:**` parses as `Operator  override`, which is
not `Operator override`. Two of the five names in the table below carry a
space, so this second case is live here, not theoretical. Either way two
identical-looking annotations split into two distinct fields and neither the
repeat check nor anything else says a word.

**Where the parser and the house rule disagree, the parser wins the question
"did this line register", and the house rule wins the question "may I write
it".** The parser is the laxer of the two — it accepts any run of spaces
between words — so writing to the parser's limit produces annotations that are
technically parsed and practically invisible. House rule: exactly one space
between words, the colon straight after the last letter, and the name spelled
character for character as the table below spells it. Dates and detail go in
the **value**, never in the name. Same reasoning as the heading ban: *if the
parser cannot see it, it cannot be wrong out loud.*

| Answer | Line appended |
|---|---|
| Accept | `**Reviewed:** ✅ operator-reviewed <date>` |
| Accept, second time round | `**Reconfirmed:** <date> — …` |
| Change | `**Operator override:** <date> — …` |
| Discuss | `**Discussed:** <date> — …` |
| deferred change | `**Follow up:** <date> — …` |

**Change.** Ask in plain text — **not** `AskUserQuestion` — what should
change. Append the override, keeping the original text intact. Apply the
change if it fits the remaining context; otherwise append `**Follow up:**`.
Never silently dropped.

**Discuss.** Stop batching. Converse, then append the `**Discussed:**` line and
resume.

If any answer in a batch is Change or Discuss, resolve those fully in ID order
before presenting the next batch. A queued override that gets overtaken by the
next batch is an operator ruling that never landed.

## 8. Close out

**Both checks below diff against the §3 baseline and take their verdict from
this one table.** What blocks the commit is a problem the review *introduced*,
not the count — the split is by novelty, not by exit code as in §3. Three rows,
never two:

| Result | Verdict |
|---|---|
| Exit 0, or exit 1 whose problems are all in the baseline | **Proceed.** A pre-existing problem the operator already elected to continue past is reported in the close-out, never a blocker: blocking would let one malformed entry veto every future review of that log, and neither remedy fits a fault the review did not write. |
| Exit 1 with a problem absent from the baseline | **The review introduced it.** Fix it, or revert. Both remedies are defined immediately below, and bound there. |
| Any other exit | **The check did not run.** Nothing to compare and nothing to fix. Say the check broke and stop; **do not commit.** Silence from a broken check is not a clean diff. |

**A fix re-runs; two bounds on it.** Fixing means re-running that whole step
from the top and reading the table again — an artifact validated in neither the
state before the fix nor the state after is precisely what these checks exist to
stop. **One retry only:** if that re-run still shows a problem absent from the
baseline, stop fixing and revert. And **a fix may rename or repair an
annotation; it may never remove a ruling.** Deleting one of the two lines is the
obvious repair for `repeats field` and it is the wrong one — renaming the second
to `**Reconfirmed:**` (§6) is the repair. A fix that drops a ruling reaches, by
the other door, the outcome this whole section exists to prevent: the log
validates, the commit is clean, and step 5 never names the loss, because its
discard item fires only on a revert. Where the only repair that clears the
problem would drop a ruling, revert instead — the rule below then names it.

**Any revert in this section ends the review.** Reverting is
`git checkout -- <log-path>` — annotations and cursor out together, exact
because the review only ever appends to a file that was committed clean;
hand-deleting appended lines across a dozen entries is how half-reverted logs
arise. Once you revert, **no cursor is written**, **nothing is committed**, and
step 4 is skipped: go straight to step 5, which names entry by entry what was
discarded. A revert throws away a completed operator review to punish a fault it
did not cause, so it is the second choice, never the reflex — and never silent.

*A revert leaves the loop; it does not re-enter it.* The re-run above is the
fix's, not the revert's. A revert that re-ran the check, saw the log back at its
baseline and read that as permission to carry on would write a cursor over a log
with no rulings left in it — entries marked reviewed that nobody saw, and never
re-offered. That is the loss the cursor-last rule of step 2 exists to prevent,
reached from the other side.

1. **Re-run the validator on the annotated log, before writing the cursor.**
   At fault here are your own annotations; a review that damages the log it was
   auditing is the worst outcome available.

   **Compare on the problem text with any `line N:` prefix stripped — never on
   the raw line, and never on the ID.** Several messages are line-number
   prefixed, and your own annotations shift every line below them. Appending a
   ruling above a pre-existing fault renumbers it, and a raw diff then reports
   that untouched fault as newly introduced — reverting a legitimate review for
   a defect it did not cause. This normalisation is deliberate, not sloppiness.

   Comparing on the ID instead looks equivalent and is not. An entry already in
   the baseline for one fault would absorb any second, *different* fault the
   review adds to it — the entry's ID is already present, so the diff is empty
   and the corruption ships. Several of the validator's messages carry no ID at
   all, so they could not be compared that way in any case.

   **Count occurrences; compare as a multiset, not a set.** Several of the
   messages repeat character-for-character once the `line N:` prefix is
   stripped. A second occurrence then normalises onto the first and vanishes
   from a set difference, so one pre-existing instance would license any number
   of new ones. Work from the lines the validator actually printed — this skill
   deliberately does not roster them, because a prose copy of a program's
   output goes stale the next time the program changes.

   **No baseline means no comparison.** If §3 did not run to completion, do not
   guess which problems are yours: treat any problem as blocking, say the
   baseline is missing, and stop.

2. **Only once step 1 has reached the proceed row** — a revert has already ended
   the review, so it never arrives here — write the cursor: advance it to the
   highest ID **resolved** (asked, or auto-accepted in §1), and **never past a
   skipped entry**. If an entry was skipped — unparseable, or unread for any
   reason — the cursor stops at the last ID before it, even when later entries
   were resolved. Those later rulings stand as their own field lines; they are
   simply re-offered next time (§6). Advancing past a skip marks a decision
   reviewed that nobody ever saw, which is worse than reviewing one twice.
   Auto-accepted entries are resolved: leaving the cursor behind them
   re-offers a settled chain.

   **The cursor is written last for a reason.** It is the one annotation that
   causes entries to be *skipped* in future runs, so it must never survive a
   review that was reverted or abandoned. Reverts are covered above; **an
   abandoned review** — context exhausted, the operator stops it, a broken check
   at any step — is the same: write no cursor, and if one is already written
   take it back out with the annotations by that same `git checkout`. An
   abandoned review leaves either a clean log or annotated entries with no
   cursor. Never a cursor.

3. **Re-run the validator once more, now that the cursor is written.** Step 1
   saw a log without the cursor, so **the cursor is the one annotation no check
   has ever seen** — an appended-rather-than-replaced cursor, or one carrying
   an impossible date, passes step 1 and commits unreported. Validate the
   artifact you are actually committing.

   Normalise, compare and branch by the same table; at fault here is the cursor
   alone, step 1 having already cleared the annotations. Two rows would be worse
   here than anywhere — this is the last gate, and a validator that exits 2
   prints nothing on stdout, which reads as an empty problem list, which reads
   as no regression, which commits. **A broken check here leaves a cursor on
   disk**, which step 1's run never saw: that is an abandoned review, so take
   the cursor back out under step 2's abandoned clause before you stop.

4. Commit: `docs: operator decision review through D-NNN`. Add by explicit
   path — other agents may share the index.
5. Summarise. These are mandatory line items, not discretionary:
   - counts of accepted / changed / discussed;
   - **auto-accepted, by reason** (operator / superseded / chain /
     no-choice) — say "0 auto-accepted" when none were;
   - **every entry skipped and why** — say "0 skipped" when none were, so the
     absence is stated rather than inferred;
   - **the validator exit status the walk ran under**, the exit status of the
     final re-run in step 3 — the one that saw the committed log — and any
     pre-existing problems carried past;
   - **every non-consensus entry and how the operator ruled on it**;
   - **every Hold entry and how the operator ruled on it** — name the
     persona when the field is present;
   - **if anything was reverted, every ruling that reverting destroyed**, named
     against its entry — a revert reported only as "reverted" is silent loss;
   - every follow-up recorded for the next session;
   - the wiring flag from §4 if it fired.

   A close-out reporting "12 accepted" after seeing 12 of 15 is a false
   report. The denominator is part of the result. Auto-accepted entries
   are in that denominator; they are not silent.

6. **If context use is at or above 45%**, tell the operator to run these
   in this order, and stop. Do not run them yourself.

   ```
   /spp pause
   /clear
   /spp resume
   ```

   45% is earlier than the skill's 50% pause threshold because this walk
   already spent the room. If you cannot read a meter, treat a review of
   more than a handful of entries as at the threshold. Below 45%, say
   nothing about pause.

## Notes

- Reviews only append. Never renumber, never rewrite history, never edit the
  original reasoning of an entry — an override sits beside it, not over it.
- Headings are immutable. Everything a review records is a new field line.
- A follow-up recorded in the log beats a half-applied change in a dying
  context window.
- The cursor belongs to this skill alone. Nothing else writes it.

## Red flags

| Thought | Reality |
|---|---|
| "The validator errored, so there is nothing to report" | An error is a broken check, not a clean log. Stop. |
| "One non-consensus entry, low blast radius, bulk it" | Blast radius never demotes a `Consensus: no`. It is always individual. |
| "Task-scope Hold, bulk it" | Hold is a hard criterion. Radius never demotes it. |
| "No Hold field, so I didn't look" | Observed absence only. Unparsed fields cannot enter the bulk batch. |
| "Hold, but don't say who" | The prefix names `Persona`. Anonymous HOLD is the same defect as unattributed Assumptions. |
| "I'll note the override and apply it later" | Later is after the context clear. Apply it or write the follow-up now. |
| "A tick on the heading shows it was reviewed" | It also makes the entry unparseable and drops every field. Append a field line. |
| "Three entries would not parse, but the other twelve were fine" | Then say so in the close-out, and do not move the cursor past them. |
| "No cursor, so start from the end" | No cursor means everything is unreviewed. |
| "Consensus line is missing, so nothing was contested" | Unreadable is `no`. Only a legible `yes` earns the bulk batch. |
| "The re-run still exits 1, so revert the review" | Compare to the baseline. You only own the problems you introduced. |
| "I reverted, and now the log is clean again — carry on" | A revert ends the review. Clean is the baseline, not permission: carrying on writes a cursor over a log with no rulings in it. Go to the close-out and name what was discarded. |
| "Dating or hyphenating the field name reads better" | `[A-Z]` then `[A-Za-z ]`, colon straight after the last letter. A hyphen, digit or parenthesis matches nothing and is never reported; a space before the colon *does* match, and silently keys a second field. Date goes in the value. |
| "§8 step 1 was clean, so the commit is clean" | Step 1 never saw the cursor. Re-validate after writing it (§8 step 3), or ship a cursor no check has read. |
| "Then one check, after the cursor, is enough" | No — before it *and* after it. The first clears your annotations, the second clears the cursor; one check alone cannot say which of the two broke the log. Cursor still last: one that outlives a reverted review skips entries whose rulings were deleted. |
| "The cursor is wrong, so revert the review" | Fix the cursor and re-validate first. Reverting deletes every ruling over a one-line fault; if you do revert, list what you destroyed. |
| "There is no log, I'll create one" | An empty log claims nothing was decided. Say it is missing and stop. |
| "I'll start asking; I can read the rest as we go" | The tail holds supersession and chain-approval. Read the set first. |
| "Directive, but Hold, so ask" | The operator already decided. Auto-accept. |
| "One option, still ask for completeness" | No choice, nothing to review. |
| "One sentence is enough, they have the log" | The question is the review. ELI5, each choice with pro/con, both viewpoints. |
| "Context is 47%, squeeze the next wave" | After review at ≥45%, the three-line pause sequence. Do not run it yourself. |

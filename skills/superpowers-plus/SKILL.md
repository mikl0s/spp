---
name: superpowers-plus
description: Use alongside superpowers subagent-driven-development or executing-plans whenever running a written plan with subagents. Adds wave-based parallel scheduling from a dependency graph, a progress meter, dispatch-prompt rules, plan pre-flight, and the silent-wrongness review lens. Invoke at the start of any plan execution, and whenever asking "can any of these tasks run in parallel?" Also /spp.
user-invocable: true
---

# Superpowers Plus

Refinements layered on top of `superpowers:subagent-driven-development`. That
skill governs the loop — implementer, review, fix rounds, ledger, breaker. This
one governs **scheduling, reporting, and what reviewers are told to look for**.

Follow the base skill for everything it covers. Where this file adds a rule,
apply it too. Where they conflict, this file wins.

Announce at start: "Using superpowers-plus for wave scheduling and review lens."

## 1. Schedule waves from a dependency graph, never a queue

The base skill's loop reads as strictly sequential. It is not. Tasks in a plan
are vertical slices with real dependencies, and most plans contain several
slices that share nothing.

**Before dispatching anything**, build the graph. For each task record:

- **Creates** — files it will add
- **Modifies** — existing files it will edit
- **Consumes** — interfaces, schemas, or functions from earlier tasks

Two tasks may run concurrently when their `Creates ∪ Modifies` sets are
disjoint AND every `Consumes` is already committed. Group into waves; dispatch
each wave in one message with multiple tool calls.

Present the graph to the user before starting. It is the cheapest check on your
own scheduling — they know the domain and will spot a wrong edge.

```
DONE   │  T1 ──── T2
WAVE A │  T3   T4   T5   T7   T10   T11      (disjoint files, deps committed)
WAVE B │  T6 ◄── T3 (same file) + T5 (interface)
       │  T8 ◄── T11 (schema)
WAVE C │  T9 ◄── most of the above      T13 ◄── T8
WAVE D │  T12 ◄── T9 (same file), T10, T11
```

**Derive waves, never declare them.** A hand-written wave number silently
claims parallelism the graph forbids. A task's wave is `1 + max(wave of its
dependencies)`, and every task needs an explicit dependency entry — an omitted
one reads as dependency-free and lands in the first wave.

`wavemap.py` in this skill's directory renders the graph as a terminal map with
per-task status, computing waves and the critical path from the dependency dict.
Edit its `TASKS`/`DEPS` literals for the plan at hand and run it. Knowing the
critical path matters: it is the floor on wall-clock no amount of extra agents
beats.

**Reorder tasks to remove conflicts.** If task A creates a file and task B
later edits it, flipping them so B's dependency lands first often lets A write
the file complete in one pass — removing both a conflict and a wasted edit
step. Reordering the plan is allowed and expected; record it (§8).

**Reviews are read-only** and never conflict. A review of task N can run
concurrently with the implementer of task N+1.

**Per-wave dispatch rules**, because parallel agents share one git index:

- **Name the files each agent owns, then relay this verbatim:** "Commit ONLY
  your own files, by explicit path. Never `git add -A` or `git add .` — that
  sweeps up other agents' in-flight work. If `git add` or `git commit` fails on
  `index.lock`, wait 3s and retry, up to 5 attempts. If you believe a file you
  do not own needs changing, do not edit it: STOP and return with
  `NEEDS-INPUT:` as the first line, naming the file. That is not a stall — you
  lack ownership, and missing authority over a resource is a missing input,
  exactly like a missing credential. A step you are merely told not to take is
  different: skip it and report it, do not return `NEEDS-INPUT:`."
  The ownership case is hard-blocked in §3's sense: no permitted option exists.
- **This binds the controller too.** Committing ledger notes, plan
  corrections, or docs while a wave is running will capture every agent's
  half-finished edits into your commit. Observed in a real run: a one-line
  doc fix swallowed three agents' working trees. Nothing broke, but the
  history stopped attributing changes to the task that made them, and one
  agent found its work already committed and had nothing to commit. Always
  name your paths — `git add docs/plan.md`, never `git add -A`.
- Prefer committing controller-side docs *between* waves rather than during
  one. The ledger lives in a git-ignored directory precisely so routine
  bookkeeping needs no commit at all.
- At most one agent per wave may touch any given shared file.

## 2. Progress meter on every update

Lead every status update with a one-line meter. One cell per task, each cell
showing that task's own stage:

🌑 not started · 🌒 implementing · 🌕 in review or fix round · 🏆 complete

```
🏆🏆🌕🌒🌑🌑🌑🌑🌑🌑🌑🌑🌑  13 tasks · T1-2 done · T3 review · T4 implementing
```

Fallback where emoji render badly — distinguished by SIZE, not shade:
`·` `▪` `■` `█`. Pure ASCII: `.` `o` `O` `@`. Never a shade gradient
(`░▒▓█`); those steps are too similar to tell apart at a glance.

The meter never replaces the explanation. Keep the reasoning — what was found,
why it matters, what it changes — and put the meter above it. Include the meter
in **every** update, including short ones.

## 3. Dispatch prompts: context, not history

Anything that constrains the agent belongs **inside** the quoted brief. Prose
outside the quotes is addressed to you, the controller — the agent never sees
it, so an unstated prohibition leaves its own skills and the project's standing
directives in force.

The base skill says don't paste session history. Additionally, every dispatch
should carry:

- **One sentence on why this task exists** in the wider system. An implementer
  who knows what its output feeds makes better judgement calls than one told
  only to write a function.
- **The interfaces it consumes**, with exact signatures — an agent cannot see
  its neighbours' code.
- **Expected real-world results with stop thresholds**, whenever a step runs
  against real data or a live system: "expect roughly N; if materially
  different, stop your own work and return immediately with the figure — do
  not proceed on it, and do not wait for an answer." A wrong number caught
  early costs minutes; caught late it has contaminated everything downstream.
  Returning with a finding is not stalling. This bullet, decide-and-record and
  hard-blocked are one policy: **always return control, never sit waiting on
  it.** Decide where an option exists, return `NEEDS-INPUT:` where none does,
  return the figure where it breaches a threshold — and in every case hand back
  to the controller rather than idling (§6).
- **What NOT to do**: steps to skip, files not to touch, external services not
  to contact, scope not to expand into. Say that skipping is expected and must
  be reported.
- **Decide and record, do not stall.** "If the brief is ambiguous or the plan
  does not cover your case, take the most defensible option and continue. Do
  not wait for me. Return the decision with your result: what you decided, the
  alternatives you would have offered, why you picked one, whether it was
  contested, and its blast radius. Do not open or write the decision log
  yourself, and do not invoke the decision-log skill; I write it."
  A blocked run is worse than a logged decision the operator can override at
  the next review. You write the log (§8).
- **Hard-blocked is not the same as unsure**, and needs its own line in the
  brief, or the bullet above is the agent's only policy when no option exists:
  "If you are hard-blocked — an unreachable service, a missing credential, a
  required input that does not exist — do not invent a way forward and do not
  decide. Stop and return with `NEEDS-INPUT:` as the first line of your reply,
  naming what is missing. Ambiguity never qualifies: wherever an option exists,
  take the most defensible one and continue."

## 4. Pre-flight the plan against itself — mandatory

Before dispatching task 1, read the plan hunting for **self-contradiction**: a
test asserting one thing while the code it tests does another, a function
defined in one task and called with a different signature in another, a value
that changed meaning between sections, a hand-computed expected value that the
specified algorithm does not produce.

This is not optional and is not a formality. Since agents no longer stop to ask
(§3), nothing halts a wave when the plan itself is wrong, and a defect can
propagate through every task that inherits it. Pre-flight is the last cheap
check before that happens.

Plans written in one pass reliably contain these. Finding several defects
before any code is written is normal and is the point of the pass.

## 5. The review lens: silent wrongness beats loud failure

Beyond the base skill's rubric, direct reviewers at the failure mode testing
does not catch — **code that produces a plausible wrong answer instead of
failing**. Have reviewers hunt specifically for:

- **Missing values becoming defaults.** A parse or lookup failure yielding `0`,
  `""`, or `[]` where "unknown" was meant. The default is often a legitimate
  value, so it silently becomes a result. This is the highest-value check in
  any data path.
- **Silent skips.** A loop that `continue`s past malformed input with no
  counter, no log, no warning. The output looks complete and is not.
- **Counts that overstate.** Returning "items processed" when items were
  deduplicated, replaced, or dropped. The number reassures while the data
  shrinks.
- **Over-strict validation added by a fix.** When a fix tightens a check, ask
  whether it now rejects legitimate input — trading a wrong-value bug for a
  missing-record bug, which is strictly worse.
- **Partial coverage that looks total.** A pattern, mapping, or branch that
  handles the common shape of the input and silently mishandles a variant. Ask
  what fraction of real input each branch actually covers.
- **Guards that assert nothing.** No assertion may treat "the command failed"
  and "the command found nothing" as the same outcome. Anything reading
  `| wc -l`, `test -z "$(…)"`, `|| true`, or a bare `!` on a pipeline is
  presumed guilty until it has been observed failing. Four instances of this
  one shape appeared in a single phase of one real project, each found only by
  *executing* the check rather than reasoning about it.
- **An assertion never observed failing is not an assertion.** Every guard
  needs a paired negative case proving it fires. The decisive test is removing
  what it detects: a vanished finding must diff as loudly as a new one.

Also require re-reviewers to **verify each new test fails against the pre-fix
code**. A test that passes either way locks in nothing.

## 6. Real-data results are findings, not just verification

When a task runs against real data or a live system, have the agent report the
actual figures, and read them as domain results rather than as test output.

**Investigate any number that surprises you, in the controller session, before
letting it flow downstream.** Plausible-looking figures are often wrong, and
the anomaly usually shows up as a small oddity in one task's output long before
it becomes a wrong conclusion. Chasing it costs minutes; inheriting it costs
the whole run.

Compare against any figure the plan predicted. A mismatch means the plan's
assumption was wrong, the implementation is wrong, or the earlier estimate was
— all three are worth knowing which.

## 7. Pause at the context threshold

At ~50% context use, stop taking on new work and hand off. Not at 70% because
the current task feels nearly done. The failure this prevents is running out
mid-task with unprocessed subagent output and no written record — which loses
the reasoning, not merely the position.

In order:

1. **Confirm every subagent has returned and its output is processed** —
   written to a file, folded into a decision, or explicitly marked stale. A
   returned agent whose findings exist only in the conversation is unprocessed.
2. **Write the decision log, including every decision still parked in the
   ledger (§8).** Nothing deferred to next time.
3. **Write the handoff:** where things stand, what to run first on resume, what
   a fresh context reliably gets wrong, findings that must not be re-derived,
   and what is open and waiting on the operator.
4. **Commit**, working tree clean.
5. **Tell the operator to clear and resume**, stating plainly what is
   unresolved.

Mid-window course corrections are normal. The operator may change direction
while subagents are running — redirect them rather than discarding their work,
and when output lands against a superseded premise, banner it section by
section rather than deleting it or silently trusting it.

## 8. Ledger additions

On top of the base skill's entries, record:

- The wave plan, and any reordering
- Real-data figures reported by each task
- Cross-task notes discovered mid-run, addressed to the task that needs them
- Plan defects found, and the commit that fixed them

The decision log is a separate artifact, kept via the `decision-log` skill.
**The controller writes it, between waves.** Agents return their decision
fields with their results and never open the log themselves: IDs come from a
shared sequence, so allocation has to be serial. Between waves because the log
is a committed shared doc, and §1 prefers those between waves.

**Park a returned agent's decision fields in the ledger the moment it
returns**, verbatim, and promote them into the decision log at the wave
boundary. The ledger is git-ignored, so parking costs no commit, allocates no
ID, and cannot collide with a running agent. Fields left only in the
conversation are lost to a compaction, and unlike code there is no file to
recover them from.

Route by one test: does the record outlive this run and change the project's
shape, or does it only describe how this run proceeded? Wave plans, defects
noticed and figures reported only describe the run, so they stay in the ledger.
The judgement calls made without the operator — which option a deviation took,
how a defect was resolved — outlive it and go to the decision log. Two kinds of
record are both. A figure that contradicts a prediction: the ledger carries the
number, the decision log what was decided about it. A reordering: the ledger
carries that it happened, the decision log why this ordering over the one the
plan gave.

The test governs the categories it names. Everywhere else the in-doubt rule
wins — if you are unsure whether something is log-worthy, it is.

## Red flags

| Thought | Reality |
|---|---|
| "Tasks run one at a time" | Only if they share files. Build the graph first. |
| "The plan says N then N+1" | Reorder to remove file conflicts; record it. |
| "The number looks about right" | Check it. Plausible is not correct. |
| "Tests pass, so it's correct" | Tests do not catch silent wrongness. That is the review's job. |
| "I'll just fix this small thing myself" | Controller fixes skip review. Send it to the implementer. |
| "I should ask the operator about this" | Only if you are hard-blocked. Otherwise decide, log it, continue. |
| "It's a small thing, no need to log it" | If in doubt whether it is log-worthy: it is. |
| "Pre-flight is a formality" | It is the only thing between a wrong plan and nine tasks inheriting it. |
| "No need for the meter on a short update" | Every update. That is the point of it. |

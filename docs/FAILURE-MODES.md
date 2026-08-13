# Failure modes

The catalogue behind the review lens in `SKILL.md` §5.

The unifying property: **none of these raise an error.** They all produce a
confident, plausible, wrong answer. Tests pass, the run reports success, and
the number is used to make a decision. Ordinary code review does not look for
them because ordinary code review asks "is this correct?" rather than "how
would this be wrong without telling me?"

Each entry: what it looks like, why testing misses it, and what to ask.

---

## 1. Missing values becoming defaults

A parse, lookup, or fetch fails and the code yields `0`, `""`, `[]`, or `False`
instead of "unknown".

**Why it survives testing.** The default is a legitimate value. `0` cores is
indistinguishable from an unparsed core count; an empty list of roles is
indistinguishable from a node that has none. Fixtures use well-formed input, so
the failure branch never runs.

**Why it is the worst one.** The default usually means something *specific*
downstream. Zero capacity means "nothing to reclaim". Zero units means "nothing
running". The wrong value does not sit inertly — it actively drives the
conclusion, often to the exact opposite of the truth.

**Ask:** for every field, what is written when the source is absent or
unparseable? Is that value distinguishable from a real measurement of the same
shape? If not, it must be null.

**Corollary — the reverse also matters.** Sometimes `0` is correct and null
means something else ("present but empty" versus "not present at all"). Those
are different findings. Check the direction is right, not just that a null
exists.

---

## 2. Partial coverage that looks total

A pattern, mapping, or branch handles the common shape of the input and
silently mishandles a variant.

**Why it survives testing.** Fixtures are written from the common shape,
usually copied from the first real example the author looked at.

**Observed:** a regex written against one vendor's format left 24% of records
unparsed. Every test passed; the gap was invisible until a real-data figure
looked odd.

**Ask:** what fraction of real input does each branch actually match? Run the
matcher over the whole real corpus and count the misses. This takes one command
and is the highest-yield check available.

---

## 3. Silent skips

A loop `continue`s past malformed input with no counter, no log, no warning.

**Why it survives testing.** The happy path is tested; the skip path produces
no observable effect to assert on.

**Ask:** if this skipped every record, would anything in the output differ from
a successful run? If no, the skip must be counted and surfaced. "How many did
you skip?" should be answerable by the code, not by the operator diffing counts
by hand afterwards.

---

## 4. Counts that overstate

A function returns "items processed" when items were deduplicated, replaced by
an upsert, or dropped.

**Why it survives testing.** Single-item fixtures never collide, so the
returned count and the stored count agree.

**Why it matters.** The count is what gets reported and believed. It reassures
precisely while the data shrinks.

**Ask:** is the returned number counted from the input or measured from the
destination? Only the latter is trustworthy. Also: what happens on a
primary-key collision — is it detected, or does one record silently win?

---

## 5. Over-strict validation introduced by a fix

A fix tightens a check and now rejects legitimate input.

**Why it is easy to miss.** It appears as an improvement, and the finding it
addresses is genuinely real.

**Why it is worse than the bug.** It trades a wrong-value bug for a
missing-record bug. A wrong value is at least visible; a dropped record is not.

**Ask:** after any fix that adds a check, what is the new rejection rate
against real data? It should be exactly the intended cases and nothing else.

---

## 6. Scope that widens silently over time

A cache or accumulator is deliberately unscoped for reuse, and a consumer reads
it without restricting to the slice it meant.

**Observed:** a cache intentionally not keyed by run — so re-runs stay cheap —
was aggregated with no filter, taking the maximum across every window ever
fetched. A one-off spike would mark a record as active permanently.

**Why it survives testing.** Each test uses a fresh store containing exactly
one slice, so the missing filter has nothing to over-select.

**Ask:** for every read of a shared or long-lived store, what restricts it to
the current run? Two individually sensible decisions — "cache across runs" and
"aggregate the cache" — collide.

---

## 7. Tests that pass against the bug

A regression test whose expected value coincides with what the broken code
already produced.

**Observed:** a guard against double-multiplication used a fixture where the
correct answer and the buggy answer were arithmetically identical.

**Why it is dangerous.** It advertises protection that does not exist, and the
next person will trust it.

**Ask:** run the test against the pre-fix code and confirm it fails. Require
this in every re-review. Choose fixture values where the correct answer differs
from *every* plausible wrong answer, not just from a null result.

---

## 8. Depending on another system's incidental code path

Reusing a tool by invoking an entry point that does not do what its name
implies.

**Observed:** a CLI ingest command populated most tables but not one the plan
depended on — that table was written only by a web handler. The column would
have been uniformly zero, making two opposite conditions identical.

**Why it survives testing.** Fixtures hand-build the dependency's output, so
the real code path is never exercised.

**Ask:** for any reused external tool, read the source of the entry point being
called and confirm it writes everything assumed. Do not infer behaviour from a
command's name.

---

## 9. Plan-level self-contradiction

The plan itself specifies two incompatible things — a test asserting the
opposite of its function, a constant that breaks a downstream join, a join
through a column that is null for exactly the rows of interest.

**Why it matters more than a code bug.** Every implementer faithfully executes
the contradiction, and the reviews check the code against the same wrong
requirement. Nothing catches it.

**Ask:** before dispatching, read the plan hunting only for internal
disagreement. Plans written in one pass reliably contain several.

---

## 10. Guards that report green while asserting nothing

A check that cannot distinguish "the command failed" from "the command found
nothing", and reports the second when the first happened. It is the only entry
here that fails in the *verification* layer rather than the data layer, which
is why it is the most expensive: it disarms every other check that runs
through it.

**Observed** — four instances of one shape within a single phase of one
project:

| What looked like an assertion | What it actually did |
|---|---|
| `! cmd \| grep -q "x"` | Command errors → grep finds nothing → `!` inverts → prints PASSED, exit 0, even under `set -euo pipefail` |
| A capability read from a process status file | Read identically inside and outside the sandbox, because an enclosing layer had already set it. A neighbouring field distinguished them |
| A `#` comment in a pattern file passed to a grep that has no comment syntax | The comment is a live expression that matches the pattern file itself |
| `grep -f bad.re -- path \| wc -l` | An unbalanced paren makes the file an invalid expression → exit 128 → `wc -l` prints `0` → a "prints nothing" criterion passes while a real credential sits in the scanned path |

**Why it survives testing.** The guard is asserted *about*, not executed.
Reviews read it, agree it looks right, and move on; the reasoning is about what
the pipeline means, not what it returns. Every one of the four above was found
by running the check, never by reading it — and reading them is exactly what
had already happened.

**Ask:** does this distinguish failure from absence? Has it been observed
failing — not argued to fail, observed? What is the exit code when the tool
itself breaks rather than when the input is clean? Anything reading `| wc -l`,
`test -z "$(…)"`, `|| true`, or a bare `!` on a pipeline is presumed guilty
until it has been watched firing.

**The structural fix.** Asking the question at each call site scales badly —
it is a review discipline, and review is what already missed these. Route the
scans through one chokepoint that owns exit-status discipline: 0 and 1 are
legitimate found/not-found, anything else is a hard failure that stops the run.
Then the *next* call site is safe by construction rather than by review, which
is the only version of this fix that survives the reviewer being tired.

---

## 11. The harness that never ran the thing it measured

Entry 10's failure, one level out. There the guard ran and could not tell
failure from absence; here the guard never ran at all, and its silence was
read as a pass. A check that reports success without having executed is
indistinguishable, from the outside, from one that executed and passed.

**Observed** — six instances in a single day, in the tooling built to catch
exactly this:

| The instrument | Why it measured nothing |
|---|---|
| `python3 <(git show REV:file) log.md` run from outside the repo | `git show` fails, process substitution hands Python an **empty program**, exit 0. Two separate agents reported a passing check that never ran |
| A mutation harness whose needle was a literal ` ` | The source holds the six-character *text*, not the character, so `replace` matched nothing and the file ran **unmutated**. Three "survivors" were phantoms |
| A byte-order-mark fixture placed before the log's title line | The mark sat where it was harmless, so the mutant survived and the assertion passed for the wrong reason |
| A 285-case grid mutating positions *around* an intact identifier | The one arrangement that reproduces the defect was outside its axes; a 312-case grid on different axes found it immediately |
| An A/B demonstration on a *required* field | Both arms failed loudly, so the pair could not show the silent case it was cited as proving. The conclusion was right and the evidence was not |
| A comment asserting a test pinned a behaviour | It did not. The claim told the next maintainer to stop looking |

**Why it survives testing.** It *is* the testing. There is no outer check to
catch it, and every instance produces the output a real pass produces. Worse,
each one was built by someone already thinking carefully about verification —
the harness is written in the same breath as the fix, by the same person, with
the same blind spot.

**Ask:** has this check been observed *failing*, on this exact input path? Does
the instrument itself have a control — a known-bad case it must reject and a
known-good case it must accept? When a mutant survives, was the mutation
applied at all: did the bytes change? Does a "verified" result name the
revision, the file, and the command, so someone can re-run it?

**The structural fix.** Every new check ships with a demonstration that it can
fail. Not an argument that it would — an observed red. For mutation work,
prove application before believing survival: diff the bytes, and show an input
the unmutated check catches and the mutant misses. A survivor from a mutation
that never applied is the same observation as a real survivor, with the
opposite meaning.

---

## 12. A number in prose is an assertion with nothing behind it

A count, a size, or a threshold stated in a comment, a docstring, or an
operator-facing message. It reads as authoritative *because* it is specific,
and nothing tests it. Unlike stale prose generally, it can be wrong on the day
it is written and stay wrong forever.

**Observed:**

| The claim | The count |
|---|---|
| "Six of them end a line for `splitlines()`" | Ten of sixty-seven |
| "Five Unicode categories" — then six were named | Eight |
| "Five of the validator's message formats carry no ID" | Eight, and it was stale **one commit** after it was written |
| A prose paraphrase of a character class | Drifted five consecutive times: parentheses, then a lowercase initial, then a hyphen, then non-ASCII letters, then "single spaces" against `[A-Za-z ]*` |

The third is the sharpest: it was *true when written*, and a sibling agent
improved the parser an hour later. Nobody was careless.

**Why it survives testing.** Reviews check that code does what the comment
says, not that the comment counts what it claims. A parenthetical figure in a
docstring is not something anyone re-derives — and a wrong one is invisible to
every test in the repository.

**Ask:** did someone count this, and can they say how? Does this number describe
a set that changes? Is the same claim made at more than one site — and do they
agree? For prose restating a program: why is it restated rather than quoted?

**The structural fix.** Prefer "several" to "six" unless you counted at the
moment of writing and said what you counted. Where a document must state a
program's rule, **quote it and name the program as the authority for
disagreements** rather than paraphrasing — a copy can only go stale when the
original changes, but a paraphrase can be wrong immediately. Where a roster
exists purely to be helpful, delete it: the argument almost always survives
without the list.

---

## 13. A replacement that inherits nothing

A mechanism is swapped for a better one, and the better one silently drops a
responsibility the old one carried. The diff shows an improvement; what is
absent from the diff is the guarantee that left with the old code.

**Observed:**

| The improvement | What left with it |
|---|---|
| A character *blacklist* replaced by a *whitelist* — correctly diagnosed, since no list of bad characters ever closes | It was wired as the **condition on** the existing format check rather than beside it, so malformed identifiers stopped being reported at all. Inputs that previously exited 1 now exited 0, silently. A strict regression inside a real improvement |
| A definition tightened so an exception argued from *authority* rather than from *consequence* | The tightening made a neighbouring rule read as a hard block, so an agent needing to record something was instructed to stop and wait instead |
| A second validation step added beside an existing one | Added a round apart, never sharing a rule. They drifted, and the older one lost a termination guarantee the newer one had |

**Why it survives testing.** Every test written for the change tests the change.
The lost behaviour had its own tests, and those still pass — because the old
mechanism is gone, so nothing exercises the path. Review reads the diff and
sees a better predicate.

**Ask:** what did the replaced code do that the replacement does not? Was the
new mechanism wired *beside* the old check or *in front of* it? Run the previous
revision against the same inputs and diff the outputs — a regression is a
difference, and differences are only visible from both sides.

**The structural fix.** After a fix, ask what it now forbids that used to be
allowed, and what it now permits that used to be caught. Both directions.
Where two mechanisms encode one rule, hoist the rule so there is one copy;
two copies added a round apart will drift, and the drift lands in whichever
copy is not being edited.

---

## 14. Instructions the actor never sees

A constraint written where the person or process it governs will not read it.
It is not neutral: an unstated prohibition leaves whatever *else* is instructing
the actor in force, so silence resolves to the wrong default rather than to no
default.

**Observed** — three consecutive rounds on one document, each closing the
instance and leaving the class:

| Where it was written | Where it needed to be |
|---|---|
| A destination named in a section addressed to the coordinator | Inside the quoted brief the agent actually receives |
| A prohibition placed one line **outside** the closing quotation mark, in the second person, reading as a continuation of the brief | Inside the quotes |
| A protocol token defined only in narration, while another section depended on that definition by reference | Inside the brief of whoever emits it |

In the second case the consequence was exact: the agent's only remaining
instruction for an impossible situation was "take the most defensible option
and continue" — which manufactures a decision where none was possible.

**Why it survives testing.** The document reads correctly to anyone holding all
of it, which is everyone reviewing it and nobody executing it. The reviewer has
the surrounding prose in view; the actor has one string.

**Ask:** extract only what the actor receives — the quoted brief, the prompt,
the config block — and read it with nothing else in scope. Is every constraint
it needs present? What *else* is instructing this actor, and does silence here
hand the decision to that?

**The structural fix.** State the rule that anything constraining the actor
belongs inside what the actor receives, and that prose outside it is addressed
to the coordinator. Once written down, the remaining violations become
enumerable instead of a matter of taste — which is what turned an open-ended
hunt into a finite checklist.

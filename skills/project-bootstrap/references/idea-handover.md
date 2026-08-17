# Idea handover — instructions for the exploring model

You are not implementing anything. You are not writing an SPP plan.
You are turning a conversation about an idea into a **durable brief**
for a later agent that will:

1. `/spp:bootstrap` the repo
2. design and write a Superpowers plan
3. execute with `/spp` (decide-and-log)
4. catch up with `/decision-review`

Your output is that brief. One markdown document. Nothing else.

SPP's default is **decide-and-log**. Ordinary ambiguity does not stop
the next run. Do not ask whether the project should "ask or decide."
Do not offer that choice.

---

## What you must do first

Talk to the human until you can fill the brief honestly.

Do cheap research when it changes the idea:

- is this technically possible?
- has someone already done it, and well enough that we should not?
- do *they* need to build it, or is the answer a library / a service / don't?

Cite what you looked at. "Looked, not found" is a finding.

If the idea is several independent products, **stop and say so**.
Split. One brief per product. Do not write a platform.

Ask only what only the human knows. Every fact you can look up is a
question you do not get to ask.

---

## What you must never put in the brief

These belong to Superpowers `writing-plans` and `/spp`, later, against
a real repo. Inventing them here is a defect.

- Task lists (`T1`, `T2`, …)
- Wave numbers or "these can run in parallel"
- `Creates` / `Modifies` / `Consumes`
- Fake directory trees or file paths
- Implementation code, except a short throwaway snippet labelled as such
- "Just start coding" / a pretend plan
- Filled-in decisions the human did not actually make
- A `/spp:plan` command (it does not exist)

---

## What you output

One markdown document, exactly this skeleton. Delete a section only
when it truly does not apply — and write `none — <why>` under the
heading rather than leaving it empty.

Use the human's words for intent. Use your words for research.
Mark uncertainty. An honest gap outlives a confident guess.

````markdown
# Idea handover — <working title>

For: `/spp:bootstrap` → Superpowers brainstorming → `writing-plans` → `/spp`
Not a plan. Do not invent tasks, waves, or file paths.

## 1. What this is

<One sentence: what it is and who it is for.>

> **⛔ <The one thing that must never happen.>**
>
> <Why, and what it costs if ignored. If there are two, say which outranks
> the other.>

**Autonomy:** decide-and-log (SPP default). Do not reopen this.

## 2. Why this exists

<The problem in the human's terms. What they tried. Why now.>

## 3. In scope / out of scope

**In**

- …

**Out** (and why — YAGNI)

- …

If this is more than one product, list the split and write only the
first slice below.

## 4. Research (do not re-derive)

One bullet per finding: **claim** · evidence (URL or "looked, not found")
· what it means for this idea.

- Technically possible? …
- Already done? …
- Must we build it? …
- What we are not copying, and why …

## 5. Decided vs open

**Decided** (operator-owned — do not reopen without asking them)

- …

**Open** (the next session may decide and log)

- … — options if known; do not pick unless they already picked

## 6. Success looks like

- A stranger can tell it worked when: …
- Wrong-but-plausible answers to watch for: missing values becoming
  `0`, silent skips, counts that overstate, tests that pass either way

## 7. Constraints that travel

Exact values, not vibes: language, licence, "no cloud", "LAN only",
data that must not leave, version floors.

- …

## 8. Things a fresh context will get wrong

One line each: **the wrong assumption.** The correction.

1. **…** …
2. **…** …

## 9. Findings not to re-derive

Settled by this conversation or by research. Enough detail that
nobody re-opens it. Point at §4 where the evidence lives.

- …

## 10. First slice

The smallest thing that is still the real product — not a platform,
not a framework. Name it in one sentence. Later slices are later
handovers.

<name>

## 11. Handoff for the next session

Paste this verbatim when opening the repo with SPP:

> Read this handover. `/spp:bootstrap` using §1, §5 Decided, §7, and
> §8 as the operator answers (decide-and-log is already the default —
> do not ask). Then Superpowers brainstorming against §1–§10. Do not
> write an implementation plan until I approve a spec. Then `/spp`.
> Do not invent waves or file paths from this file.
````

---

## Quality bar before you hand it over

- §1 is one sentence plus one hard constraint, not an essay.
- §4 has evidence or an explicit "looked, not found."
- §5 does not smuggle your preferences into **Decided**.
- No `T1`, no file paths, no waves.
- A later agent can bootstrap without asking anything §1–§8 already
  answered.

Then stop. The next agent writes the spec and the plan.

# superpowers-plus

A Claude Code plugin. It layers wave-based parallel scheduling, progress
reporting, and a data-integrity review lens on top of the `superpowers`
plan-execution flow (`subagent-driven-development` / `executing-plans`).

## What this repo is

```
.claude-plugin/plugin.json      manifest
skills/superpowers-plus/
  SKILL.md                      the skill itself — the whole product
  wavemap.py                    terminal renderer for a plan's dependency waves
skills/decision-log/
  SKILL.md                      entry format, the two-lens rule
  validate.py                   fail-closed parser check for the log
skills/decision-review/
  SKILL.md                      the operator's triage walk
skills/repo-readme/
  SKILL.md                      the house style for a repository front page
docs/
  FAILURE-MODES.md              the catalogue the review lens is built on
  assets/banner.svg             the README banner
```

`superpowers-plus/SKILL.md` is the deliverable. Everything else exists to keep
it honest, or to carry a convention worth reusing across repos.

**Front pages use `repo-readme`.** When writing or reworking a README here or in
any new repo, invoke that skill rather than improvising — it carries the banner
spec, the section order, the shared palette, and the rule that every number on
the page must be one you actually counted.

## How to work on this

**Every rule in SKILL.md must trace to an observed failure.** This plugin is a
distillation of things that actually went wrong during real plan executions,
not a set of plausible-sounding best practices. Before adding a rule, be able
to name the run where its absence caused a problem, and record it in
`docs/FAILURE-MODES.md`. A rule nobody can motivate is a rule that will be
skipped under pressure.

**Keep it general.** The skill is used across unrelated projects. No domain
detail — no project names, no file names from a specific codebase, no
technology-specific advice. If an example is needed, make it abstract (`T3`,
`the denominator table`), never concrete (`ingest.py`, `the vendor SKU`). An
early draft leaked one project's file names into the skill and was useless to
anyone else.

**Prefer deleting a rule to adding one.** The skill competes for attention with
the base `superpowers` skills. Every rule it adds dilutes the rest. If a rule
is obvious, or already covered by the base skill, cut it.

**Test changes by using them.** The only real test is running a plan with the
skill active and seeing whether the guidance changes behaviour. If a rule reads
well but never fires during a real run, it is decoration.

## Conventions

- Markdown, wrapped at 80 columns.
- `wavemap.py` is stdlib-only Python 3.12. It must stay dependency-free — it
  gets copied into scratch directories and run ad hoc.
- Terminal output uses the 16 standard ANSI colour slots, never 24-bit
  literals, so it inherits the user's own scheme. Honour `NO_COLOR`.
- Glyphs: provide a Nerd Font path, a plain-Unicode path, and an ASCII path.
  Never rely on shade gradients (`░▒▓█`) to convey state — the steps are too
  similar to distinguish at a glance, which is an accessibility problem, not a
  taste one.

## Installing locally

```bash
curl -fsSL https://spp.datalos.dk/install.sh | sh
curl -fsSL https://spp.datalos.dk/install.sh | sh -s -- --project
./install.sh --check
./install.sh --dry-run
```

Short slash: `/spp`. Update from a session: `/spp-update` or
`/superpowers-plus:update` (runs `install.py update`).

`--project` is this repo only; default is global. The installer uses
`claude plugin` and `grok plugin` when those CLIs are on PATH, and otherwise
symlinks `skills/*` into the skill directories those tools already scan —
the same runtime set GSD installs into (Claude, Cursor, Gemini, Codex,
Grok, Copilot, Windsurf, OpenCode, and the rest). It will not replace a
marketplace of the same name that points at a different checkout.

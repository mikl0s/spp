---
name: repo-readme
description: Write a repository front page in the house style — SVG banner, status chips, a one-line thesis, one diagram that carries the actual idea, a read-in-this-order table, and depth folded into details blocks. Use when opening a new repo, when a README is a wall of prose nobody reads, or when the user asks for a README, a front page, a project overview, or says an existing one looks generic. For internal repos: no licence section, no contributing section, no badges.
---

# Repository front page

A README is read once, by someone deciding whether to keep reading. The house
style optimises for that single pass: what this is, why it exists, what to open
next, and where the depth is hidden if they want it.

Announce at start: "Using repo-readme for the front page."

## 1. The shape

In order, separated by `---` rules. Skip any section the repo has nothing real
to put in — an empty section is worse than an absent one.

| # | Section | Job |
|:-:|---|---|
| 1 | Banner image | Identity, in the subject's own vocabulary. See §4 |
| 2 | Chip line | Five or fewer backticked tokens: status, kind, stack, scale |
| 3 | Thesis | **One bold sentence.** The whole bet |
| 4 | Context | Two short paragraphs. What exists, what it lacks, why this |
| 5 | The idea in one diagram | Mermaid. The mechanism, not the file tree |
| 6 | Read in this order | Numbered table: document, line count, why |
| 7 | Body sections | One idea each, each opening or closing on a pull quote |
| 8 | Constraints | `⛔` blockquotes for what is non-negotiable |
| 9 | Layout | A tree, annotated per line |
| 10 | Status | Inside `<details>`. Symbols, not prose |
| 11 | Footer | Italic. One human note |

## 2. The rules that make it work

**Every number is real.** `243 lines`, `16 checks`, `four instances in one
phase`. Go and count them. A README with approximate figures reads as a README
nobody checked, and it is the first thing a careful reader tests.

**Bold exactly the load-bearing sentence.** One per section at most. If three
things are bold, nothing is.

**Blockquotes are verdicts, not decoration.** Use one where a section reaches a
conclusion worth remembering out of context. If it could be an ordinary
sentence, make it one.

**`<details>` is for depth, not for clutter.** Fold the evidence, the long
table, the specifics — anything a second reader wants and a first reader does
not. Never fold something the reader needs to understand the section above it.

**Personality lives in asides, never in technical claims.** A joke about a name
is fine. A joke inside a benchmark figure is not.

**Tables over lists** wherever there are two dimensions. Lists over tables where
there is one.

**End human.** The last line is the one people remember. Something true about
how the thing was built, or who it is for.

## 3. Internal repositories

No licence section, no contributing section, no badge row, no code of conduct.
Those exist to answer questions outsiders ask. If the audience is the operator
and their agents, answer *their* questions instead: what is unfinished, what is
deliberately not being done, what breaks if you touch it.

## 4. The banner

An SVG at `docs/assets/banner.svg`, `viewBox="0 0 900 300"`, illustration left,
wordmark right.

- **Draw the subject's own vocabulary.** If the product has a visual language
  already — a state glyph, a diagram, a unit of work — draw that. A generic
  abstract shape is the visual equivalent of a stock photo.
- **System fonts only**: a serif stack for the wordmark, a mono stack for the
  tagline and gloss. No web fonts; the host will not load them.
- **Dark-mode aware.** Put the palette in a `<style>` block inside `<defs>` and
  override every fill under `@media (prefers-color-scheme: dark)`. A banner that
  vanishes on a dark background is the most common failure.
- **Two text tiers under the wordmark**: a letter-spaced uppercase tagline
  (three or four words), then one or two lines of gloss at ~12px that say the
  thesis in plain language.
- Reuse `<g id="…">` plus `<use>` for repeated marks so the file stays short
  enough to read.
- Give it `role="img"` and an `aria-label` carrying the wordmark and tagline.

Verify it parses (`python3 -c "import xml.etree.ElementTree as ET;
ET.parse('docs/assets/banner.svg')"`) and check the geometry by arithmetic —
text width ≈ characters × font-size × 0.55 for serif, × 0.6 plus letter-spacing
for mono. There is usually no rasteriser to hand.

## 5. The diagram

One diagram, and it must carry the **mechanism** — how the thing works, what
flows where, where the decision is made. Not the directory tree, not a layer
cake, not boxes labelled with the section headings.

Style the two or three nodes that matter, and leave the rest unstyled:

```
style NODE fill:#3E705922,stroke:#3E7059,stroke-width:2px
```

A `22` alpha suffix on the fill against a solid stroke reads correctly in both
themes. Colour the beginning, the decision, and the end — not every box.

## 6. Before finishing

- Every link resolves. Check them, do not assume.
- Every line count matches `wc -l`.
- No project specifics leaked in from a sibling repo's README.
- The first screen answers "what is this and why" with no scrolling.
- Read only the bold sentences top to bottom: they should form a summary.

`references/template.md` in this skill's directory is a fill-in skeleton with
the structure and no content.

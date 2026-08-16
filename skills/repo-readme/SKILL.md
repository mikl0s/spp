---
name: repo-readme
description: Use when opening a new repo, writing or improving a README, updating a front page for new features, or when an existing README is a wall of prose or looks generic. Also when the user mentions readme seeds, branding examples, asciinema, vhs, or a GIF/video demo on GitHub.
---

# Repository front page

A README is read once, by someone deciding whether to keep reading. The house
style optimises for that single pass: what this is, why it exists, what to open
next, and where the depth is hidden if they want it.

Announce at start: "Using repo-readme for the front page."

## 0. Job, audience, seeds

**Job** — pick one, from what they asked, not from habit:

| Job | What you do |
|---|---|
| **New** | No README, or they asked to generate one. Write the front page from the repo. |
| **Improve** | A README exists and they want it better. Keep facts; change the scan. |
| **Update** | New features, a release, a renamed command. Edit in place. Do not restyle the whole page unless they asked. |

**Audience** — public or private. Ask once if the repo does not make it obvious (`PRIVATE` in an existing chip line, no remote, or they said internal).

| | Public | Private |
|---|---|---|
| Licence, contributing, CoC, badge row | Yes, if the files exist. Never invent a licence. | No. Those answer outsiders. |
| Seed repos | Craft only. Do not copy logos, SVG, or prose. | Same — ideas, not their art. No licence requirement on *this* README. |
| What to answer | What it is, why, how to try it. | What is unfinished, what is deliberately not done, what breaks if you touch it. |

**Seeds** — twenty public READMEs ship in `references/seeds.txt`. Each line is a link and what to steal (a GIF-first screen, a tape-to-GIF demo, a typeset hierarchy — not "this one is pretty").

Load the first file that exists:

1. `<repo>/.superpowers/readme-seeds.txt`
2. `~/.config/superpowers-plus/readme-seeds.txt`
3. the shipped `references/seeds.txt`

An override **replaces** the shipped list. First line `include-defaults` keeps the twenty and appends theirs. Three of their own branded repos is a complete set. They can delete every default.

Do not fetch all twenty. Pick two to four whose `take:` matches this job (CLI → vhs/asciinema/fzf; visual product → excalidraw/starship; dense reference → ripgrep/yt-dlp). Read those READMEs. Steal the *move*, not the look. House style (§1) is the spine unless they said "just use these."

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

## 5. Motion — asciinema, tape, GIF

If the product is a CLI or TUI, a still banner is not the demo. Prefer, in
order:

1. **An existing recording in the repo** (`.cast`, `vhs` tape, `docs/*.gif`).
   Use it. Do not re-record what they already have.
2. **asciinema** — `asciinema rec docs/demo.cast`. Embed the player, or
   render an SVG (`agg` / `svg-term`) and commit that. The `.cast` is the
   source; the SVG is what GitHub shows without JavaScript.
3. **vhs** (`charmbracelet/vhs`) — a tape file checked in next to the GIF
   so the demo can be remade. Prefer this when they already use the charm
   stack or want a GIF.
4. **A short GIF or muted MP4** they hand you. Do not invent ffmpeg
   pipelines or download stock terminal footage.

Cap the file. A 4 MB GIF that autoplays is a worse front page than no
demo. One loop, one command, no desktop chrome.

Skip motion for a library, a spec, or a private repo whose audience
already runs the tool.

## 6. The diagram

One diagram, and it must carry the **mechanism** — how the thing works, what
flows where, where the decision is made. Not the directory tree, not a layer
cake, not boxes labelled with the section headings.

Style the two or three nodes that matter, and leave the rest unstyled:

```
style NODE fill:#3E705922,stroke:#3E7059,stroke-width:2px
```

A `22` alpha suffix on the fill against a solid stroke reads correctly in both
themes. Colour the beginning, the decision, and the end — not every box.

## 7. Before finishing

- Every link resolves. Check them, do not assume.
- Every line count matches `wc -l`.
- No project specifics leaked in from a sibling repo's README.
- The first screen answers "what is this and why" with no scrolling.
- Read only the bold sentences top to bottom: they should form a summary.

`references/template.md` in this skill's directory is a fill-in skeleton with
the structure and no content.

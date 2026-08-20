#!/usr/bin/env python3
r"""Validate a decision log against the format decision-review parses.

Exit 0: valid.  Exit 1: problems found.  Any other exit: broken check.

The distinction matters more than the checks themselves. `decision-review`
silently skips entries it cannot parse, so an entry this file fails to notice
is a decision the operator never sees. Anything ambiguous is therefore a
problem, and anything that goes wrong inside the checker is exit 2 — never
exit 1, which would read as "your log is invalid".

Fifteen checks, in five groups:

  headings  1 format mismatch   2 wrong level
            3 heading hidden by invisible or misplaced characters
            4 title carrying a control character
  entries   5 none found        6 ID does not increase (covers duplicates)
            7 missing required field            8 repeated field
            9 Consensus value  10 blast radius value
  cursors  11 unusable (unparseable, or an impossible date)
           12 more than one    13 points at a missing entry
  file     14 byte-order mark hiding an entry, stray or consumed
  shared   15 calendar-date validation, applied at two call sites (heading,
              cursor) — one rule, not two checks

The four heading checks say the same thing but imply different repairs — add
the em dash, fix the level, delete the invisible character, delete the control
character — and a human hand-edits this file, so merging them into "your
heading is wrong somehow" would be worse. The cursor checks are likewise not
inferable from each other: 12 answers "which one wins", 13 answers "it points
at nothing".

Why a whitelist, and why only on the skeleton. Three rounds of this checker
classified stray characters by Unicode category — Cf plus non-plain whitespace
— and each round the grid found more categories that hide an entry just as
well: combining marks and variation selectors (Mn), the Hangul filler (Lo), the
blank Braille pattern (So). There is no category set that closes; "invisible"
is a rendering property, not a Unicode property. So the structural skeleton —
hashes, ID, em dash, parenthesised type and date — is required to be exactly
canonical, which HEADING already enforces character by character, and anything
else in that region is defective by construction with nothing left to
enumerate.

The skeleton, not the whole line. `<short title>` is free text in the format
this checker serves, so a heading is not defective for being written in the
language its author writes in: `Björn owns it`, curly quotes, an en dash, `µs`,
`漢字`, an emoji. A round of this checker applied the whitelist to the whole
line and rejected all of those. That was worse than a false negative: the
skill that writes this log may repair a heading only when a problem hides an
ID, so a log full of ordinary titles was pinned at exit 1 with no sanctioned
repair, reported forever as noise. The one thing a title may not contain is a
control character: the format has no use for one, and ten of the sixty-seven
are turned into a line break by str.splitlines() and by several markdown
readers, which severs the type and date from the ID.

Why a `#` line that matches nothing is still reported. An earlier round gated
the format check on the whitelist, so any heading carrying one non-canonical
character skipped the format branch and had to be rescued by COMPACT_HEADING —
which cannot fire when the stray character sits inside `D-\d{3}` itself. A
lookalike `D`, a hyphen that is not U+002D, or a soft hyphen between the digits
then read as clean. Every `## ` line that reaches the end of the heading rules
is reported, so no heading can fall through in silence.

Known ceiling: a path naming a FIFO or a never-ending character device
(/dev/zero, a named pipe with no writer) blocks in the read_bytes call in
main() and this process hangs rather than exiting. A read timeout is more
machinery than this earns; the log is an ordinary file in a repo.
"""

import re
import sys
from datetime import date
from pathlib import Path

# IDs are pinned to exactly three digits, so they sort correctly as strings.
# This caps a log at D-999; D-1000 is rejected as a malformed heading. That is
# a loud failure, not a silent one, so it is left as is.
HEADING = re.compile(
    r"^## (D-\d{3}) — (.+) \((decision|directive|pause), (\d{4}-\d{2}-\d{2})\)\s*$"
)
# The character set a heading's SKELETON may contain: printable ASCII, plus the
# em dash the format requires. HEADING enforces it there by spelling every
# skeleton character literally; here it drives _compact. Titles are exempt —
# see "Why a whitelist, and why only on the skeleton" above.
CANONICAL = frozenset(chr(c) for c in range(0x20, 0x7F)) | {"—"}
# The one class of character a free title may not contain: C0 and C1 controls
# and the two Unicode line separators — 67 code points. Ten of them end a line
# for str.splitlines() and for several markdown readers (U+000A, U+000B,
# U+000C, U+000D, U+001C, U+001D, U+001E, U+0085, U+2028, U+2029), which severs
# the type and date from the ID. The other 57, TAB among them, end no line
# anywhere and are banned for the duller reason that the format has no use for
# them and they render unpredictably. The message names the character, says the
# format has no use for it, and says that several of the class end a line — the
# second reason being true of the class, not of every member.
TITLE_BAN = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
# Matched against a line reduced to CANONICAL characters with spaces removed,
# so it recognises an intended heading whatever NON-CANONICAL junk was inserted
# and wherever — before the hashes, between them, after them, or before the ID.
# .match() anchors it at the start of the line; an unanchored .search() made
# body text such as "**Why:** supersedes ## D-001." a false positive that
# discarded the surrounding entry.
#
# The anchor is also the ceiling, and the trade is deliberate: a PRINTABLE
# prefix (`> `, `- `, `1. `, a backtick, a letter, an HTML comment) survives
# _compact, so the line no longer starts with a hash, is not recognised as a
# heading, and its entry is invisible to a downstream `^## ` scan and to this
# file alike. Almost every printable prefix behaves that way. The exceptions
# are of two kinds and no others: a run of whitespace, which _compact strips,
# and a prefix that is itself hashes, which the line reports as the wrong
# heading level. Every ancestor has had this gap. Closing it means unanchoring
# the search, which re-opens the body-text false positive above — the worse of
# the two, because that one discards the fields of an entry that is valid.
# The hash run is unbounded, not `{1,6}`: seven hashes is not a markdown
# heading, but it is unmistakably an intended entry, and bounding the run let it
# match nothing and pass in silence.
COMPACT_HEADING = re.compile(r"(#+)(D-\d{3})")
# Field names are `[A-Z][A-Za-z ]*`: no digits, hyphens or underscores. The
# decision-log skill states the same rule for its annotation names. Widening
# one without the other silently drops annotations, so change both together.
FIELD = re.compile(r"^\*\*([A-Z][A-Za-z ]*):\*\*")
CURSOR = re.compile(
    r"<!--\s*reviewed-through:\s*(D-\d{3})\s+(\d{4}-\d{2}-\d{2})\s*-->"
)
# Anything shaped like a cursor, so a malformed one is reported rather than
# ignored. decision-review reads a missing cursor as "nothing reviewed yet"
# and would re-offer every decision the operator already ruled on.
LOOSE_CURSOR = re.compile(r"<!--[^>]*?reviewed-through.*?-->")

REQUIRED = ("Decided", "Options", "Why", "Consensus", "Blast radius")
RADII = ("task", "plan", "project", "cross-project")


def _real_date(text):
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _compact(line):
    """The line reduced to the characters a heading's skeleton may contain.

    Spaces go too, so that junk anywhere in the prefix still leaves an ID to
    recognise. What survives this is what a heading is allowed to be built
    from, so a line that still does not look like a heading afterwards never
    was one.
    """
    return "".join(c for c in line if c in CANONICAL and c != " ")


def problems(text, bom_consumed=False):
    """Return a list of human-readable problems. Empty list means valid.

    `bom_consumed` says the decoder swallowed a leading byte-order mark. It is
    still in the bytes a consumer greps, so if the first line is an entry
    heading the mark sits in front of `## ` and that entry is invisible — a
    clean-looking text here, and nothing found downstream. Real logs open with
    a title, which is why this went unnoticed; the review skill reads logs it
    did not write.
    """
    found = []
    entries = []          # list of {"id": str, "line": int, "fields": dict}
    current = None

    if bom_consumed and COMPACT_HEADING.match(_compact(text.split("\n", 1)[0])):
        found.append(
            "line 1: the byte-order mark the decoder consumed sits before the "
            "first heading — a consumer reading the file's bytes cannot see "
            "that entry"
        )

    # No BOM stripping here on purpose. The decode("utf-8-sig") in main()
    # consumes exactly one leading mark, which is the encoding marker; every
    # further mark is a stray character. Stripping here too consumed two, so a
    # doubled BOM read clean through the CLI. It is reported against the whole
    # text rather than left to the heading rules because a real log opens with
    # a title, so the residual mark lands on a line no heading rule inspects.
    stray = text.find("\ufeff")
    if stray != -1:
        line_no = text.count("\n", 0, stray) + 1
        found.append(
            f"line {line_no}: stray byte-order mark — only the one the decoder "
            "consumes at offset 0 is legitimate"
        )

    # split("\n"), not splitlines(): besides "\n", splitlines() breaks on every
    # other character in TITLE_BAN's line-ending group above — U+000B, U+000C,
    # U+000D, U+001C, U+001D, U+001E, U+0085, U+2028 and U+2029 — and on none
    # of those do grep, re.M or any other consumer. Junk pasted into a heading
    # would otherwise BECOME a line break here and leave a pristine-looking
    # heading behind, while the consumer loses the entry.
    for n, raw in enumerate(text.split("\n"), 1):
        # A CRLF log is not defective, and this strip is not what makes that
        # true: HEADING ends in `\s*$`, field values are .strip()ped, and
        # _compact drops a CR as non-canonical, so every site `line` reaches is
        # already CR-blind. Exhaustive CR injection finds no input whose answer
        # changes with the strip removed — it is defensive and currently
        # unreachable, kept because a future exact comparison would need it.
        # A lone \r inside a line is still a defect and is left in place: in
        # the skeleton the heading rules below catch it, in a title TITLE_BAN
        # does.
        line = raw.removesuffix("\r")

        # HEADING is anchored on '## ', so a match here is also the whitelist
        # test on the skeleton: every character outside the title group is
        # spelled literally in the pattern.
        m = HEADING.match(line)
        if m:
            if not _real_date(m.group(4)):
                found.append(f"line {n}: {m.group(4)} is not a real date")
            ban = TITLE_BAN.search(m.group(2))
            if ban:
                found.append(
                    f"line {n}: entry {m.group(1)} title contains "
                    f"U+{ord(ban.group()):04X} at column "
                    f"{m.start(2) + ban.start() + 1} — a control character, "
                    "which the format has no use for in a title, and several "
                    "of which end the line for a reader, taking the type and "
                    "date with them"
                )
            current = {"id": m.group(1), "line": n, "fields": {}}
            entries.append(current)
            continue

        like = COMPACT_HEADING.match(_compact(line))
        if like:
            eid = like.group(2)
            if len(like.group(1)) != 2:
                found.append(
                    f"line {n}: entry {eid} is at heading level "
                    f"{len(like.group(1))}, must be '## '"
                )
                current = None
                continue
            if not line.startswith(f"## {eid} "):
                # This is the grep-visibility case: the prefix a consumer keys
                # on is not intact, so the entry is invisible, not just ugly.
                found.append(
                    f"line {n}: entry {eid} heading contains invisible or "
                    "misplaced characters and would be skipped entirely"
                )
                current = None
                continue

        # Everything else that opened with '## '. Reached when the ID itself
        # carries the damage — a lookalike letter, a hyphen that is not U+002D
        # — so COMPACT_HEADING could not recognise the line as an entry at all.
        # Falling through in silence here is what made a corrupted first entry
        # read as a clean log.
        if line.startswith("## "):
            found.append(f"line {n}: heading does not match the entry format")
            current = None
            continue

        m = FIELD.match(line)
        if m and current is not None:
            name = m.group(1)
            if name in current["fields"]:
                found.append(f"line {n}: {current['id']} repeats field '{name}'")
            current["fields"][name] = line.split(":**", 1)[1].strip()

    if not entries:
        found.append("no entries found — is this a decision log?")

    seen = {e["id"] for e in entries}
    previous = None
    for e in entries:
        # `<=` makes this cover duplicates too: a repeated ID never increases.
        if previous is not None and e["id"] <= previous:
            found.append(
                f"line {e['line']}: ID {e['id']} does not increase (previous "
                f"{previous}) — duplicate or out of order"
            )
        previous = e["id"]

        for field in REQUIRED:
            if field not in e["fields"]:
                found.append(f"{e['id']}: missing required field '{field}'")

        # Guarded, so a missing field is reported once by the check above
        # rather than twice.
        consensus = e["fields"].get("Consensus")
        if consensus is not None and not re.match(r"^(yes|no)\b", consensus):
            found.append(f"{e['id']}: Consensus must start with 'yes' or 'no'")

        radius = e["fields"].get("Blast radius", "").strip()
        if radius and radius not in RADII:
            found.append(
                f"{e['id']}: blast radius '{radius}' is not one of {', '.join(RADII)}"
            )

    cursors = list(LOOSE_CURSOR.finditer(text))
    if len(cursors) > 1:
        found.append(
            f"found more than one review cursor ({len(cursors)}); there must be one"
        )
    for lm in cursors:
        line_no = text.count("\n", 0, lm.start()) + 1
        m = CURSOR.fullmatch(lm.group(0))
        # Format and date are one conclusion reached a step apart: either way
        # the cursor cannot be acted on.
        if m is None:
            reason = "it does not match '<!-- reviewed-through: D-NNN YYYY-MM-DD -->'"
        elif not _real_date(m.group(2)):
            reason = f"{m.group(2)} is not a real date"
        else:
            reason = None
        if reason:
            found.append(f"line {line_no}: cursor is unusable — {reason}")
            continue
        if m.group(1) not in seen:
            found.append(f"cursor points at {m.group(1)}, which is not in the log")

    return found


# --- fixtures and self-test, below the logic they exercise -----------------

# Fixture headings are built rather than written literally, so that no line of
# this source file starts with "## D-NNN". Otherwise validate.py would itself
# parse as a valid log, and pointing the checker at the wrong file by mistake
# would report "valid".
H = "#" * 2 + " "

# What a downstream consumer sees. Every assertion about a clean log is checked
# against this too: if this file says a log is valid, grep must find every
# entry in it.
GREP = re.compile(r"(?m)^## D-\d{3} ")

GOOD = f"""# Log

{H}D-001 — first thing (decision, 2026-08-04)

**Decided:** did a thing.
**Options:** (a) this, (b) that.
**Why:** this was cheaper.
**Consensus:** yes — uncontested.
**Blast radius:** task

<!-- reviewed-through: D-001 2026-08-04 -->
"""

# Characters that have hidden an entry in practice. They span eight Unicode
# categories (Cc, Cf, Lo, Mn, So, Zl, Zp, Zs) — counted, because an earlier
# version of this comment said five and then listed six — and two
# line-breaking behaviours (five of the nineteen break str.splitlines()), which
# is the evidence for the whitelist: this list is test data, not a rule. Adding
# to it must never require touching the checker.
HAZARDS = (
    ("\u200b", "ZWSP"), ("\u200d", "ZWJ"), ("\u200f", "RLM"),
    ("\ufeff", "BOM"), ("\u00a0", "NBSP"), ("\t", "TAB"),
    ("\u00ad", "SHY"), ("\u2060", "WJ"), ("\u3000", "IDSP"),
    ("\u2028", "LS"), ("\u2029", "PS"), ("\x0b", "VT"),
    ("\x0c", "FF"), ("\x85", "NEL"),
    ("\u0301", "COMBINING ACUTE"), ("\u034f", "CGJ"), ("\ufe0f", "VS16"),
    ("\u3164", "HANGUL FILLER"), ("\u2800", "BRAILLE BLANK"),
)


def _entry(n):
    """A complete, valid entry — for fixtures needing several headings."""
    return (
        f"\n{H}D-{n:03d} — thing {n} (decision, 2026-08-04)\n\n"
        f"**Decided:** did thing {n}.\n"
        "**Options:** (a) this, (b) that.\n"
        "**Why:** it was cheaper.\n"
        "**Consensus:** yes — uncontested.\n"
        "**Blast radius:** task\n"
    )


MULTI = "# Log\n" + _entry(1) + _entry(2) + _entry(3)

# A complete second entry, used where a fixture needs a real body so that an
# assertion cannot pass on incidental text from a missing-field message. Its
# dissenting Consensus is the only 'no' in any fixture — but only the equality
# assertion below pins the `no` half of the alternation. Every other use of
# this fixture sits inside an any(...), where one EXTRA complaint is invisible,
# so an earlier version of this comment claimed a coverage it did not have.
SECOND = _entry(2).replace(
    "**Consensus:** yes — uncontested.",
    "**Consensus:** no — the other lens wanted the interface.",
)

# The vocabularies, exercised whole. Nothing used `directive`, `pause` or
# `cross-project`, so either word could be dropped from its alternation without
# a single assertion noticing — and a type this checker does not know is a
# heading it reports as malformed, which is the loud kind of wrong on a log
# that is in fact correct.
VOCABULARY = (
    "# Log\n"
    + _entry(1).replace("(decision,", "(directive,")
    + _entry(2).replace("(decision,", "(pause,").replace(
        "**Blast radius:** task", "**Blast radius:** cross-project"
    )
    + _entry(3).replace("**Blast radius:** task", "**Blast radius:** project")
)

# Titles a person would actually write. None is a defect: the ID prefix a
# consumer greps for is untouched, the em dash and the parenthesised tail parse,
# and the skill that writes this log offers no sanctioned repair for any of
# them — so reporting one would pin a log at exit 1 forever.
LEGITIMATE_TITLES = (
    "Björn owns the migration",
    "An\u00e4\u2019s review",
    "the vendor\u2019s SLA wins",
    "adopt \u201cfail fast\u201d",
    "retry 3–5 times",
    "defer the rest…",
    "cap latency at 500µs",
    "rename to 漢字 mode",
    "ship it 🚀",
    "tilt 45° default",
)


def self_test():
    assert problems(GOOD) == []
    assert problems(MULTI) == [], "multi-entry fixture must be valid"
    assert len(GREP.findall(MULTI)) == 3, "fixture entries must be grep-visible"

    # Equality, not any(...): a dissenting Consensus and the three vocabulary
    # words the other fixtures never use must produce NO complaint, and an
    # extra complaint is what a narrowed alternation emits.
    assert problems("# Log\n" + SECOND) == [], "a dissenting Consensus is valid"
    assert problems(VOCABULARY) == [], "directive, pause, cross-project rejected"

    # CRLF is a line ending, not a defect.
    assert problems(GOOD.replace("\n", "\r\n")) == [], "CRLF log reported invalid"

    # Coroner annotations must remain valid optional fields. If a later
    # change whitelists required names, a log carrying Assumptions,
    # Falsification, Point of no return, Hold, or a Persona byline would
    # fail — and an old log without them must still exit 0, which GOOD
    # already pins. The five together is a parser fixture, not a
    # write-path autopsy: a real empty coroner omits Falsification and
    # Point of no return when Assumptions is none.
    CORONER = GOOD.replace(
        "**Blast radius:** task\n",
        "**Blast radius:** task\n"
        "**Persona:** pre-post-mortem\n"
        "**Assumptions:** none — nothing load-bearing.\n"
        "**Falsification:** grep the existing callers today.\n"
        "**Point of no return:** first external consumer of the interface.\n"
        "**Hold:** no cheap falsification, early public interface\n",
    )
    assert problems(CORONER) == [], (
        "coroner fields must be valid optional annotations"
    )
    # Spaced name is what we write; a hyphenated lookalike is not a field
    # and vanishes unreported — the skill's own warning for this name.
    assert FIELD.match("**Point of no return:**").group(1) == "Point of no return"
    assert FIELD.match("**Point-of-no-return:**") is None
    assert FIELD.match("**Persona:**").group(1) == "Persona"

    missing = GOOD.replace("**Why:** this was cheaper.\n", "")
    assert any("Why" in p for p in problems(missing)), "missing field undetected"

    # A missing field must report once, not once per check that touches it.
    gone = GOOD.replace("**Consensus:** yes — uncontested.\n", "")
    assert len([p for p in problems(gone) if "Consensus" in p]) == 1, (
        "missing Consensus reported more than once"
    )

    bad_radius = GOOD.replace("**Blast radius:** task", "**Blast radius:** huge")
    assert any("blast radius" in p.lower() for p in problems(bad_radius))

    # The blast-radius check is guarded on the field being present, exactly as
    # the Consensus one is; without the guard an absent field is reported twice,
    # once as missing and once as the empty string not being a valid radius.
    no_radius = problems(GOOD.replace("**Blast radius:** task\n", ""))
    assert any("missing required field 'Blast radius'" in p for p in no_radius), (
        "missing blast radius undetected"
    )
    assert not any("is not one of" in p for p in no_radius), (
        "missing blast radius reported twice"
    )

    # Duplicate IDs are caught by the non-increase comparison, which is `<=`.
    # There is no input where a separate duplicate check would fire alone. The
    # assertion names both IDs, because "previous == current" is what makes it
    # a duplicate rather than merely out of order; the word "duplicate" is a
    # static part of the message and would discriminate nothing.
    dupe = GOOD + SECOND.replace("D-002", "D-001")
    assert any(
        "ID D-001 does not increase (previous D-001)" in p for p in problems(dupe)
    ), "duplicate ID undetected"

    backwards = GOOD + SECOND.replace("D-002", "D-000")
    assert any("does not increase" in p for p in problems(backwards)), (
        "decreasing ID undetected"
    )

    gap = GOOD.replace("D-001", "D-007")
    assert problems(gap) == [], "first ID need not be 001"

    bad_consensus = GOOD.replace("**Consensus:** yes", "**Consensus:** maybe")
    assert any("consensus" in p.lower() for p in problems(bad_consensus))

    dangling = GOOD.replace("reviewed-through: D-001", "reviewed-through: D-099")
    assert any("D-099" in p for p in problems(dangling)), "dangling cursor undetected"

    malformed = GOOD.replace(
        "## D-001 — first thing (decision, 2026-08-04)",
        "## D-001 first thing (decision, 2026-08-04)",
    )
    # Named exactly, not just "some heading complaint": this heading is fully
    # visible to grep and its only defect is the missing separator, so calling
    # it hidden would send the operator hunting for a character that is not
    # there. The two messages carry different repairs.
    assert any(
        "does not match the entry format" in p for p in problems(malformed)
    ), "malformed heading undetected, or reported as a hidden one"

    wrong_level = GOOD + SECOND.replace("## D-002", "### D-002")
    assert any("level" in p for p in problems(wrong_level)), (
        "mis-levelled heading undetected"
    )

    # Every hazard at every position it can occupy, on the first, a middle and
    # the last entry. Earlier versions placed the character only where the bug
    # had been found — first at offset 0, then only before the hashes — so each
    # fix was verified on the one axis it was written for. The grid is the
    # point, and the parity assertion is the invariant behind it: this file may
    # not call a log clean unless grep can see every entry in it.
    for ch, label in HAZARDS:
        for pos, build in (
            ("before hashes", lambda c: c + "## D-"),
            ("between hashes", lambda c: "#" + c + "# D-"),
            ("after hashes", lambda c: "##" + c + " D-"),
            ("before ID", lambda c: "## " + c + "D-"),
        ):
            for n in (1, 2, 3):
                broken = MULTI.replace(f"{H}D-{n:03d}", build(ch) + f"{n:03d}")
                reported = problems(broken)
                assert reported or len(GREP.findall(broken)) == 3, (
                    f"{label} {pos} on entry {n}: clean, but grep loses an entry"
                )
                hits = [
                    p for p in reported
                    if f"D-{n:03d}" in p and "skipped entirely" in p
                ]
                assert hits, f"{label} {pos} on entry {n} undetected"

    # A fifth position, which the four above cannot reach: the space after the
    # ID is part of what a consumer greps for, so junk sitting immediately
    # after the digits hides the entry exactly as a prefix does, and must be
    # named as hidden rather than merely non-canonical.
    for ch, label in HAZARDS:
        broken = MULTI.replace(f"{H}D-002 ", f"{H}D-002{ch} ")
        hits = [
            p for p in problems(broken)
            if "D-002" in p and "skipped entirely" in p
        ]
        assert hits, f"{label} immediately after the ID undetected"

    # Damage inside the ID itself, which COMPACT_HEADING cannot recognise as an
    # entry at all — the case a previous round let through in silence. Placed on
    # the FIRST entry: corrupting a middle one leaves its orphaned fields to
    # collide with the entry above and produce a report about the wrong entry,
    # which masked exactly this bug.
    for label, bad_id in (
        ("non-breaking hyphen U+2011", "D\u2011001"),
        ("hyphen U+2010", "D\u2010001"),
        ("minus sign U+2212", "D\u2212001"),
        ("fullwidth hyphen U+FF0D", "D\uFF0D001"),
        ("soft hyphen among the digits", "D-0\u00AD01"),
        ("zero width space among the digits", "D-0\u200B01"),
        ("fullwidth D", "\uFF24-001"),
        ("Cyrillic dze", "\u0405-001"),
    ):
        broken = MULTI.replace(f"{H}D-001 ", f"{H}{bad_id} ")
        reported = problems(broken)
        assert reported, f"{label} in the ID read as a clean log"
        # And the fixture is the real thing: grep has genuinely lost the entry.
        assert len(GREP.findall(broken)) == 2, f"{label}: fixture hides nothing"

    # Seven hashes is not a heading in any markdown reader, so the entry is
    # invisible; bounding the hash run at six let this match nothing at all.
    deep = MULTI.replace(f"{H}D-001 ", "####### D-001 ")
    assert any("heading level 7" in p for p in problems(deep)), (
        "over-deep heading undetected"
    )

    # The level is named, not merely complained about: a heading that is too
    # SHALLOW is as invisible as one that is too deep, and a check that only
    # looked for 'deeper than 2' would let level 1 fall through to the message
    # about invisible characters, sending the operator hunting for one.
    shallow = MULTI.replace(f"{H}D-002 ", "# D-002 ")
    assert any("is at heading level 1" in p for p in problems(shallow)), (
        "level-1 heading undetected or misreported"
    )

    # Three digits, not 'some digits'. A four-digit ID parses as an entry the
    # moment the count is relaxed, and is then invisible to a consumer keyed on
    # `^## D-[0-9][0-9][0-9] `. On the LAST entry, so that no ID-ordering
    # complaint can stand in for the one being tested.
    four = MULTI.replace(f"{H}D-003 ", f"{H}D-1000 ")
    assert len(GREP.findall(four)) == 2, "four-digit fixture hides nothing"
    assert problems(four), "four-digit ID accepted as an entry"

    # A title is free text: the format's own template says `<short title>`, and
    # the skill that writes this log licenses no repair for one, so reporting a
    # title would pin a log at exit 1 with nothing the operator could do.
    for title in LEGITIMATE_TITLES:
        text = MULTI.replace("thing 2 (decision", f"{title} (decision")
        assert problems(text) == [], f"legitimate title rejected: {title}"

    # The one exception, reported with the character and its column, because a
    # control character is not something an operator can see to delete. One
    # from each of the three ranges TITLE_BAN spells, so no range can be
    # dropped from it and still pass.
    for code in ("\x0b", "\x85", "\u2028"):
        ctrl = MULTI.replace("thing 2 (decision", f"thing{code}2 (decision")
        heading = next(ln for ln in ctrl.split("\n") if "D-002" in ln)
        want = f"U+{ord(code):04X} at column {heading.index(code) + 1}"
        assert [p for p in problems(ctrl) if want in p], (
            f"control character {want} in a title undetected"
        )

    # Body text mentioning a heading is not a heading. The unanchored search
    # this replaced flagged these and discarded the surrounding entry.
    for prose in (
        GOOD.replace("**Why:** this was cheaper.", "**Why:** supersedes ## D-002."),
        GOOD + "\nsee ## D-002 for the follow-up\n",
    ):
        assert problems(prose) == [], "body text mentioning a heading flagged"

    for empty in ("", "just some prose\n\nwith no entries at all\n"):
        assert any("no entries" in p for p in problems(empty)), (
            "input with no entries reported as valid"
        )

    # problems() itself strips nothing: a BOM reaching it is a stray character
    # wherever it sits. The decoder handles the one legitimate offset-0 mark,
    # so "a single-BOM file is clean" is an external check, not one of these.
    bom_first = "\ufeff" + GOOD.split("# Log\n\n", 1)[1]
    assert any("skipped entirely" in p for p in problems(bom_first)), (
        "stray BOM before a heading undetected"
    )
    # The doubled-BOM guard. A previous commit deleted this assertion while
    # claiming to fix the bug it guards; it is the only in-file check that the
    # decoder's one legitimate strip is not applied twice.
    assert any("skipped entirely" in p for p in problems("\ufeff" + bom_first)), (
        "doubled BOM undetected"
    )
    # And the case that actually reaches an operator: a log opening with a
    # title, where a residual mark lands on a line no heading rule inspects.
    assert any("byte-order mark" in p for p in problems("\ufeff" + GOOD)), (
        "residual BOM on a title line undetected"
    )
    # The mark the decoder legitimately consumes is a finding after all, when
    # the first line is an entry: the bytes still start with it, so grep sees
    # nothing. A log opening with a title is unaffected \u2014 that is the whole
    # reason this went unnoticed for as long as it did.
    entry_first = GOOD.split("# Log\n\n", 1)[1]
    assert any(
        "cannot see" in p for p in problems(entry_first, bom_consumed=True)
    ), "consumed BOM in front of the first entry undetected"
    assert problems(GOOD, bom_consumed=True) == [], (
        "consumed BOM in front of a title reported"
    )
    # And through main(), because the decoding and the flag that reports it
    # live there and nothing else reaches them: a mark in front of the first
    # heading must exit 1, the same mark in front of a title must exit 0.
    # Imported here rather than at the top: the checker itself needs neither.
    import contextlib
    import io
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "log.md"
        for label, data, want in (
            ("BOM hiding the first heading", "﻿" + entry_first, 1),
            ("BOM in front of a title", "﻿" + GOOD, 0),
        ):
            path.write_bytes(data.encode("utf-8"))
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([str(path)])
            assert code == want, f"{label}: exit {code}, expected {want}"

    for broken in ("<!-- reviewed-through: D-001 04/08/2026 -->",
                   "<!-- reviewed-through: D-001 -->",
                   "<!-- reviewed-through: D-99 2026-08-04 -->",
                   "<!-- reviewed-through: D-001 2026-02-30 -->"):
        text = GOOD.replace("<!-- reviewed-through: D-001 2026-08-04 -->", broken)
        assert any("unusable" in p for p in problems(text)), (
            f"unusable cursor undetected: {broken}"
        )

    two = GOOD + "\n<!-- reviewed-through: D-001 2026-08-04 -->\n"
    assert any("more than one" in p for p in problems(two)), (
        "duplicate cursor undetected"
    )

    repeated = GOOD.replace(
        "**Blast radius:** task", "**Blast radius:** task\n**Blast radius:** plan"
    )
    assert any("repeats" in p for p in problems(repeated)), "repeated field undetected"

    for bad_day in ("2026-13-45", "2026-02-30"):
        text = GOOD.replace("2026-08-04)", f"{bad_day})")
        assert any("not a real date" in p for p in problems(text)), (
            f"impossible date undetected: {bad_day}"
        )

    print("self-test: pass")


def main(argv):
    if "--self-test" in argv:
        # This guard cannot be exercised from inside self_test() — it runs
        # before it — so it is covered by external observation only, never by
        # the mutation table.
        if len(argv) != 1:
            print("--self-test takes no other arguments", file=sys.stderr)
            return 2
        # A failing self-test is a broken check, not an invalid log. Without
        # this the AssertionError propagates and Python exits 1.
        try:
            self_test()
        except Exception as exc:  # noqa: BLE001 - any failure here means broken
            print(f"self-test FAILED: {exc!r}", file=sys.stderr)
            return 2
        return 0
    if len(argv) != 1:
        print("usage: validate.py <log-path> | --self-test", file=sys.stderr)
        return 2
    try:
        # Read bytes and decode here rather than read_text, because whether the
        # decoder swallowed a mark is itself a finding: the mark is still in the
        # bytes every downstream consumer greps.
        data = Path(argv[0]).read_bytes()
        text = data.decode("utf-8-sig")
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see below
        # Not just OSError: UnicodeDecodeError is a ValueError, so a UTF-16 or
        # Latin-1 log would otherwise crash out with exit 1 and read as
        # "invalid log". Anything that stops us reading is a broken check.
        print(f"cannot read {argv[0]}: {exc}", file=sys.stderr)
        return 2
    try:
        found = problems(text, bom_consumed=data.startswith(b"\xef\xbb\xbf"))
    except Exception as exc:  # noqa: BLE001 - a parser bug must not read as 1
        print(f"checker failed on {argv[0]}: {exc!r}", file=sys.stderr)
        return 2
    for p in found:
        print(p)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

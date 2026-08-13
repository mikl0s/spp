#!/usr/bin/env python3
"""Render a plan's dependency waves as a terminal map.

Feed it a plan graph; it prints the waves, what runs in parallel, status per
task, and the critical path. Waves are derived from the dependency graph, never
declared, so the map cannot claim parallelism the graph forbids.

Nerd Font glyphs by default, `--plain` for ASCII, `NO_COLOR=1` for no colour.
Colour uses the 16 standard ANSI slots so it inherits the terminal's scheme.

ponytail: the graph is a literal dict, not a parser. Plans differ too much to
parse reliably, and typing 13 lines is faster than debugging a parser.
"""
import argparse
import shutil

# Standard 16-colour ANSI slots, never 24-bit literals: these resolve through
# the terminal's own palette, so the map inherits whatever scheme the user runs
# instead of imposing one. NO_COLOR is honoured.
C = {
    "text": "\033[39m", "dim": "\033[90m", "accent": "\033[35m",
    "green": "\033[32m", "yellow": "\033[33m", "blue": "\033[34m",
    "red": "\033[31m", "peach": "\033[36m", "teal": "\033[36m",
    "off": "\033[0m", "b": "\033[1m",
}
if __import__("os").environ.get("NO_COLOR"):
    C = dict.fromkeys(C, "")

# state -> (nerd glyph, ascii glyph, moon, colour)
STATE = {
    "done":    ("\U000F0134", "[x]", "🏆", "green"),
    "review":  ("\U000F0450", "[?]", "🌕", "yellow"),
    "impl":    ("\U000F0450", "[>]", "🌒", "blue"),
    "blocked": ("\U000F0026", "[!]", "🔴", "red"),
    "todo":    ("\U000F0130", "[ ]", "🌑", "dim"),
}

TASKS = {
    #  id: (name,                       state,     files,                 note)
    # Abstract fixture — same shape as a real 13-task run that collapsed
    # to 6 waves. Names are generic on purpose; edit these for your plan.
    1:  ("schema + config", "done",   "schema.py config.py", "10 tables"),
    2:  ("source A extract", "done",   "source_a.py",        "2078 rows"),
    3:  ("cross-check",      "done",   "cross.py",           "114 misses"),
    4:  ("source B extract", "done",   "source_b.py",        "9441 rows"),
    5:  ("source C import",  "done",   "source_c.py",        ""),
    7:  ("metrics pull",     "done",   "metrics.py",         "45 queries"),
    10: ("probe",            "done",   "probe.py",           ""),
    11: ("classify",         "done",   "classify.py schema.py", "28 leftover"),
    6:  ("mentions join",    "todo",   "cross.py",           ""),
    8:  ("summary views",    "todo",   "views.sql",          ""),
    9:  ("cli report",       "todo",   "cli.py",             ""),
    13: ("dashboard",        "todo",   "dashboard/",         ""),
    12: ("investigate",      "todo",   "investigate.py",     ""),
}

# EVERY task needs an entry, including the ones with no dependencies. An
# omitted task silently reads as dependency-free and gets scheduled into the
# first wave — claiming parallelism that does not exist.
DEPS = {1: [], 2: [1], 3: [1, 2], 4: [1], 5: [1], 7: [1], 10: [], 11: [1],
        6: [3, 5], 8: [11], 9: [2, 3, 4, 5, 6, 7, 8], 13: [8], 12: [9, 10, 11]}

WAVE_NAME = {0: "foundation", 1: "extract", 2: "join",
             3: "derive", 4: "surface", 5: "drill-down"}


def render(plain=False):
    g = 1 if plain else 0
    width = min(shutil.get_terminal_size((100, 40)).columns, 92)
    P = (lambda s="": print(s))

    done = sum(1 for t in TASKS.values() if t[1] == "done")
    meter = "".join(STATE[TASKS[i][1]][2] for i in sorted(TASKS))
    waves = sorted({wave_of(i) for i in TASKS})

    P()
    P(f"{C['accent']}{C['b']}╭─ example-plan {'─' * (width - 17)}╮{C['off']}")
    P(f"{C['accent']}│{C['off']}  {meter}")
    P(f"{C['accent']}│{C['off']}  {C['dim']}{done}/{len(TASKS)} tasks · "
      f"{len(waves)} waves · longest chain {critical_path()} deep{C['off']}")
    P(f"{C['accent']}╰{'─' * (width - 1)}╯{C['off']}")

    for w in waves:
        ids = [i for i in sorted(TASKS) if wave_of(i) == w]
        par = len(ids)
        bar = "━" * max(0, width - 34 - len(WAVE_NAME.get(w, "")))
        tag = (f"{par} in parallel" if par > 1 else "sequential")
        col = C["teal"] if par > 1 else C["dim"]
        P()
        P(f" {col}{C['b']}WAVE {w}{C['off']} {C['dim']}{WAVE_NAME.get(w,'')}{C['off']} "
          f"{col}{bar} {tag}{C['off']}")

        for n, i in enumerate(ids):
            name, state, files, note = TASKS[i]
            glyph, ascii_g, _, colour = STATE[state]
            mark = ascii_g if plain else glyph
            elbow = "└" if n == len(ids) - 1 else "├"
            dep = DEPS.get(i) or []
            deptxt = f"◄ {','.join('T%d' % d for d in dep)}" if dep else ""
            P(f"   {C['dim']}{elbow}─{C['off']} {C[colour]}{mark}{C['off']} "
              f"{C['b']}T{i:<3}{C['off']}{C[colour]}{name:<24}{C['off']}"
              f"{C['dim']}{files:<22}{C['off']}"
              f"{C['peach']}{note:<18}{C['off']}{C['dim']}{deptxt}{C['off']}")

    P()
    legend = "  ".join(
        f"{C[c]}{(a if plain else gl)}{C['off']} {C['dim']}{k}{C['off']}"
        for k, (gl, a, _, c) in STATE.items())
    P(f" {C['dim']}legend{C['off']}  {legend}")
    P()


def wave_of(i: int) -> int:
    """Earliest wave a task can run in: one past its deepest dependency.
    Derived, never declared — a hand-written wave number silently claims
    parallelism the graph does not permit."""
    d = [x for x in DEPS.get(i, []) if x in TASKS]
    return 1 + max((wave_of(x) for x in d), default=-1)


def critical_path() -> int:
    """Longest dependency chain — the floor on wall-clock, however wide you fan out."""
    memo = {}

    def depth(i):
        if i not in memo:
            memo[i] = 1 + max((depth(d) for d in DEPS.get(i, []) if d in TASKS),
                              default=0)
        return memo[i]

    return max(depth(i) for i in TASKS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", action="store_true", help="ASCII, no Nerd Font")
    render(**vars(ap.parse_args()))

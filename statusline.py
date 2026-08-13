#!/usr/bin/env python3
"""Claude Code statusline for superpowers-plus.

Reads the hook JSON on stdin, prints one line. Never hangs, never crashes
the bar: a bad payload prints nothing.

Shows model, current todo if any, directory, and a context meter. The
meter turns at 50% — that is the skill's pause threshold, not a decoration.
Filled vs empty cells differ by SIZE (■ ·), not by a shade gradient.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
OFF = "\033[0m"
BOLD = "\033[1m"


def ctx_meter(remaining: float | None) -> str:
    if remaining is None:
        return ""
    used = max(0, min(100, int(round(100 - remaining))))
    filled = min(10, used // 10)
    bar = "■" * filled + "·" * (10 - filled)
    if used < 50:
        color = GREEN
    elif used < 80:
        color = YELLOW
    else:
        color = RED
    return f" {color}{bar} {used}%{OFF}"


def current_todo(session: str) -> str:
    if not session or "/" in session or "\\" in session or ".." in session:
        return ""
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    todos = claude / "todos"
    if not todos.is_dir():
        return ""
    try:
        files = sorted(
            (p for p in todos.iterdir()
             if p.name.startswith(session) and p.suffix == ".json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return ""
    if not files:
        return ""
    try:
        items = json.loads(files[0].read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(items, list):
        return ""
    for item in items:
        if isinstance(item, dict) and item.get("status") == "in_progress":
            return str(item.get("activeForm") or item.get("content") or "")
    return ""


def render(data: dict) -> str:
    model = (data.get("model") or {}).get("display_name") or "Claude"
    workspace = data.get("workspace") or {}
    directory = workspace.get("current_dir") or os.getcwd()
    dirname = Path(directory).name or directory
    remaining = (data.get("context_window") or {}).get("remaining_percentage")
    if remaining is not None:
        try:
            remaining = float(remaining)
        except (TypeError, ValueError):
            remaining = None
    task = current_todo(str(data.get("session_id") or ""))
    parts = [f"{DIM}{model}{OFF}"]
    if task:
        parts.append(f"{BOLD}{task}{OFF}")
    parts.append(f"{DIM}{dirname}{OFF}")
    line = " │ ".join(parts)
    meter = ctx_meter(remaining)
    return line + (" │" + meter if meter else "")


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
        if not isinstance(data, dict):
            return 0
        sys.stdout.write(render(data))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

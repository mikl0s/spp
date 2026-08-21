#!/usr/bin/env python3
"""Claude Code statusline for superpowers-plus.

Reads the hook JSON on stdin, prints one line. Never hangs, never crashes
the bar: a bad payload prints nothing.

Shows model, SPP wave if a run is live, directory, a context meter, then
running work: [model time] for subagents, {model time} for shells. The
meter turns at 50% — that is the skill's pause threshold, not a decoration.
Filled vs empty cells differ by SIZE (■ ·), not by a shade gradient.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
OFF = "\033[0m"
BOLD = "\033[1m"
if os.environ.get("NO_COLOR"):
    DIM = GREEN = YELLOW = RED = OFF = BOLD = ""

WAVE_TODO = re.compile(r"(?i)^\s*wave\s+(\d+)\s*[,:]\s*(.+?)\s*$")
AGENT_ID = re.compile(r"agentId:\s*([A-Za-z0-9_-]+)")
BG_ID = re.compile(r"background with ID:\s*([A-Za-z0-9_-]+)")
NOTIF_ID = re.compile(r"<task-id>\s*([^<]+?)\s*</task-id>", re.I)
NOTIF_TOOL = re.compile(r"<tool-use-id>\s*([^<]+?)\s*</tool-use-id>", re.I)
NOTIF_STATUS = re.compile(r"<status>\s*([^<]+?)\s*</status>", re.I)
TRANSCRIPT_TAIL = 8 * 1024 * 1024
AGENT_TOOLS = {"Agent", "Task"}
SHELL_TOOLS = {"Bash", "Shell"}
DONE_STATUS = {"completed", "failed", "killed", "cancelled", "error"}
ACTIVE_ORDER = (
    ("review", "reviewing"),
    ("impl", "implementing"),
    ("blocked", "blocked"),
)
ACTIVE_STATES = dict(ACTIVE_ORDER)


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


def format_elapsed(seconds: float) -> str:
    secs = max(0, int(seconds))
    if secs < 60:
        return f"{secs}s"
    minutes, secs = divmod(secs, 60)
    if minutes < 60:
        return f"{minutes}:{secs:02d}"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}"


def short_model(name: str | None, session: str) -> str:
    raw = (name or session or "Claude").strip()
    low = raw.lower()
    if "haiku" in low:
        return "Haiku"
    if "sonnet" in low:
        return "Sonnet"
    if "opus" in low:
        return "Opus"
    if raw and " " not in raw and "-" not in raw:
        return raw[:1].upper() + raw[1:]
    return session or raw


def _safe_session(session: str) -> str:
    if not session or "/" in session or "\\" in session or ".." in session:
        return ""
    return session


def _load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _in_progress_texts(session: str, config_dir: Path) -> list[str]:
    session = _safe_session(session)
    if not session:
        return []
    texts: list[str] = []

    def take(item: object) -> None:
        if not isinstance(item, dict) or item.get("status") != "in_progress":
            return
        text = str(item.get("activeForm") or item.get("content") or "")
        if text:
            texts.append(text)

    todos = config_dir / "todos"
    if todos.is_dir():
        try:
            files = sorted(
                (p for p in todos.iterdir()
                 if p.name.startswith(session) and p.suffix == ".json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            files = []
        for path in files:
            data = _load_json(path)
            if isinstance(data, list):
                for item in data:
                    take(item)
            elif isinstance(data, dict):
                for item in data.get("todos") or data.get("items") or []:
                    take(item)

    task_dir = config_dir / "tasks" / session
    if task_dir.is_dir():
        try:
            files = sorted(task_dir.glob("*.json"))
        except OSError:
            files = []
        for path in files:
            take(_load_json(path))
    return texts


def wave_from_todo(session: str, config_dir: Path) -> str:
    for text in _in_progress_texts(session, config_dir):
        match = WAVE_TODO.match(text)
        if match:
            return f"wave {int(match.group(1))}, {match.group(2).strip()}"
    return ""


def _load_graph(path: Path) -> tuple[dict | None, dict | None]:
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return None, None
    tasks = deps = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
        if "TASKS" in names and isinstance(value, dict):
            tasks = value
        if "DEPS" in names and isinstance(value, dict):
            deps = value
    return tasks, deps


def _wave_of(i: object, deps: dict, tasks: dict, memo: dict) -> int:
    if i in memo:
        return memo[i]
    edges = [x for x in (deps.get(i) or []) if x in tasks]
    memo[i] = 1 + max((_wave_of(x, deps, tasks, memo) for x in edges),
                      default=-1)
    return memo[i]


def wave_from_wavemap(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    tasks, deps = _load_graph(path)
    if not tasks:
        return ""
    deps = deps or {}
    memo: dict = {}
    active: dict[int, list[tuple]] = {}
    for i, spec in tasks.items():
        if not isinstance(spec, (tuple, list)) or len(spec) < 2:
            continue
        state = spec[1]
        if state not in ACTIVE_STATES:
            continue
        wave = _wave_of(i, deps, tasks, memo)
        active.setdefault(wave, []).append((i, state))
    if not active:
        return ""
    wave = min(active)
    items = sorted(active[wave], key=lambda x: str(x[0]))
    parts = []
    for state, verb in ACTIVE_ORDER:
        ids = [i for i, st in items if st == state]
        if ids:
            parts.append(verb + " " + ", ".join(f"T{i}" for i in ids))
    if not parts:
        return ""
    return f"wave {wave}, {', '.join(parts)}"


def _blob(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        bits = []
        for item in value:
            if isinstance(item, dict):
                bits.append(str(item.get("text") or item.get("content") or ""))
            else:
                bits.append(str(item))
        return "\n".join(bits)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("content") or "")
    return str(value or "")


def _parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    text = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _read_transcript(path: Path) -> str:
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > TRANSCRIPT_TAIL:
                fh.seek(size - TRANSCRIPT_TAIL)
                fh.readline()
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def _apply_notification(blob: str, status_of: dict[str, str]) -> None:
    if "<task-notification>" not in blob:
        return
    status = (NOTIF_STATUS.search(blob) or [None, ""])[1].strip().lower()
    if not status:
        return
    for rx in (NOTIF_ID, NOTIF_TOOL):
        match = rx.search(blob)
        if match:
            status_of[match.group(1).strip()] = status


def _sidecar_model(transcript: Path, agent_id: str) -> str | None:
    path = (transcript.with_suffix("") / "subagents"
            / f"agent-{agent_id}.jsonl")
    if not path.is_file():
        return None
    model = None
    try:
        with path.open() as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = row.get("message") or {}
                if isinstance(msg, dict) and msg.get("model"):
                    model = str(msg["model"])
    except OSError:
        return None
    return model


def running_chips(transcript_path: str, session_model: str,
                  now: datetime) -> list[str]:
    path = Path(transcript_path)
    if not path.is_file():
        return []
    raw = _read_transcript(path)
    if not raw.strip():
        return []

    items: dict[str, dict] = {}
    status_of: dict[str, str] = {}

    for line in raw.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        _apply_notification(_blob(row.get("content")), status_of)
        att = row.get("attachment")
        if isinstance(att, dict):
            _apply_notification(_blob(att.get("prompt")), status_of)
        ts = _parse_ts(row.get("timestamp"))
        msg = row.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype == "tool_use":
                name = part.get("name")
                oid = part.get("id")
                if not oid or name not in AGENT_TOOLS | SHELL_TOOLS:
                    continue
                inp = part.get("input") or {}
                kind = "agent" if name in AGENT_TOOLS else "shell"
                items[str(oid)] = {
                    "kind": kind,
                    "start": ts,
                    "model": inp.get("model") if kind == "agent" else None,
                    "bg": bool(inp.get("run_in_background")),
                    "task_id": None,
                    "result": False,
                    "async": False,
                }
            elif ptype == "tool_result":
                oid = str(part.get("tool_use_id") or "")
                item = items.get(oid)
                if not item:
                    continue
                item["result"] = True
                text = _blob(part.get("content"))
                if item["kind"] == "agent":
                    match = AGENT_ID.search(text)
                    if match:
                        item["task_id"] = match.group(1)
                        item["async"] = True
                    elif "async agent launched" in text.lower():
                        item["async"] = True
                    else:
                        item["async"] = False
                else:
                    match = BG_ID.search(text)
                    if match:
                        item["task_id"] = match.group(1)
                        item["bg"] = True
                    elif "running in background" in text.lower():
                        item["bg"] = True

    chips = []
    for oid, item in items.items():
        ids = [oid]
        if item.get("task_id"):
            ids.append(item["task_id"])
        last = next((status_of[i] for i in ids if i in status_of), "")
        if last in DONE_STATUS:
            continue
        if item["kind"] == "shell" and item["result"] and not item["bg"]:
            continue
        if item["kind"] == "agent" and item["result"] and not item["async"]:
            continue
        model = item.get("model")
        if item["kind"] == "agent" and item.get("task_id"):
            model = model or _sidecar_model(path, item["task_id"])
        label = short_model(str(model) if model else None, session_model)
        start = item.get("start")
        elapsed = (now - start).total_seconds() if start else 0
        body = f"{label} {format_elapsed(elapsed)}"
        chip = f"[{body}]" if item["kind"] == "agent" else f"{{{body}}}"
        chips.append((item["kind"], start or now, oid, chip))
    chips.sort(key=lambda row: (0 if row[0] == "agent" else 1, row[1], row[2]))
    return [row[3] for row in chips]


def render(data: dict, now: datetime | None = None,
           wavemap_path: Path | None = None,
           config_dir: Path | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)
    if config_dir is None:
        config_dir = Path(os.environ.get(
            "CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    if wavemap_path is None:
        wavemap_path = (Path(__file__).resolve().parent
                        / "skills" / "superpowers-plus" / "wavemap.py")

    session_model = (data.get("model") or {}).get("display_name") or "Claude"
    workspace = data.get("workspace") or {}
    directory = workspace.get("current_dir") or os.getcwd()
    dirname = Path(directory).name or directory
    remaining = (data.get("context_window") or {}).get("remaining_percentage")
    if remaining is not None:
        try:
            remaining = float(remaining)
        except (TypeError, ValueError):
            remaining = None

    wave = wave_from_todo(str(data.get("session_id") or ""), config_dir)
    if not wave:
        wave = wave_from_wavemap(wavemap_path)

    parts = [f"{DIM}{session_model}{OFF}"]
    if wave:
        parts.append(f"{BOLD}{wave}{OFF}")
    parts.append(f"{DIM}{dirname}{OFF}")
    line = " │ ".join(parts)
    meter = ctx_meter(remaining)
    if meter:
        line += " │" + meter
    chips = running_chips(
        str(data.get("transcript_path") or ""),
        session_model, now)
    if chips:
        line += " │ " + " ".join(chips)
    return line


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

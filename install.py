#!/usr/bin/env python3
"""Install superpowers-plus into whatever agent CLIs are already here.

Prefers each tool's own plugin command. Falls back to skill-directory
symlinks those tools already scan.

  curl -fsSL https://spp.datalos.dk/install.sh | sh
  curl -fsSL https://spp.datalos.dk/install.sh | sh -s -- --project
  # payload is fetched from GitHub unless SPP_ORIGIN is set

  ./install.py                global (default)
  ./install.py --project      this project only
  ./install.py update         pull latest and re-link
  ./install.py --dry-run
  ./install.py --check
  ./install.py --uninstall
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

PLUGIN = "superpowers-plus"
DEFAULT_ORIGIN = "https://raw.githubusercontent.com/mikl0s/spp/main"
# Features that are Python. Skills install without it.
PYTHON_FEATURES = (
    ("statusline.py", "the bar (model, wave, meter, live chips)"),
    ("wavemap.py", "the wave map"),
    ("validate.py", "the decision-log checker"),
)
HOME = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share"))


def this_file() -> Path | None:
    raw = globals().get("__file__")
    if not raw or raw == "<stdin>":
        return None
    p = Path(raw)
    return p.resolve() if p.exists() else None


def which(name: str) -> str | None:
    return shutil.which(name)


def python_recipe() -> str | None:
    """The one command we will run on this machine, if we know it."""
    recipes = (
        ("apt-get", "sudo apt-get install -y python3"),
        ("dnf", "sudo dnf install -y python3"),
        ("yum", "sudo yum install -y python3"),
        ("pacman", "sudo pacman -S --noconfirm python"),
        ("zypper", "sudo zypper install -y python3"),
        ("apk", "sudo apk add python3"),
        ("brew", "brew install python3"),
        ("port", "sudo port install python313"),
        ("winget", "winget install Python.Python.3.12"),
        ("choco", "choco install python3 -y"),
    )
    for cli, cmd in recipes:
        if which(cli):
            return cmd
    return None


def note_python_features() -> None:
    py = which("python3")
    print("python3          " + (py or "not found"))
    print("needs python3    " + ", ".join(name for name, _ in PYTHON_FEATURES))
    if py:
        return
    print("  without it those three do not run. skills / /spp still do.")
    rec = python_recipe()
    if rec:
        print(f"  this machine    {rec}")
        print("  or              re-run with --install-python")
    else:
        print("  install Python 3 yourself, then re-run — we only auto-run")
        print("  the ten common package managers.")


def run(cmd: list[str], dry: bool) -> tuple[int, str]:
    printable = " ".join(cmd)
    if dry:
        print(f"  would run  {printable}")
        return 0, ""
    try:
        proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    except OSError as exc:
        print(f"  fail       {printable}\n             {exc}", file=sys.stderr)
        return 2, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        print(f"  ran        {printable}")
    else:
        print(f"  fail       {printable}  (exit {proc.returncode})", file=sys.stderr)
        for line in out.strip().splitlines()[:8]:
            print(f"             {line}", file=sys.stderr)
    return proc.returncode, out


def env_dir(var: str, *parts: str) -> Path:
    raw = os.environ.get(var)
    if raw:
        return Path(raw).expanduser()
    return HOME.joinpath(*parts)


def xdg_dir(var: str, name: str) -> Path:
    raw = os.environ.get(var)
    if raw:
        return Path(raw).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / name
    return HOME / ".config" / name


# Same set GSD installs into. Skills go in <config>/skills globally, and in
# .<name>/skills in a project (windsurf's global home is the odd one out).
# Cline is rules-based and has no skills directory — omitted on purpose.
RUNTIMES: tuple[tuple[str, tuple[str, ...], Path, str], ...] = (
    ("claude",      ("claude",),
     env_dir("CLAUDE_CONFIG_DIR", ".claude"), ".claude/skills"),
    ("cursor",      ("cursor", "cursor-agent", "cursor-cli"),
     env_dir("CURSOR_CONFIG_DIR", ".cursor"), ".cursor/skills"),
    ("gemini",      ("gemini", "gemini-cli"),
     env_dir("GEMINI_CONFIG_DIR", ".gemini"), ".gemini/skills"),
    ("codex",       ("codex", "codex-cli"),
     env_dir("CODEX_HOME", ".codex"), ".codex/skills"),
    ("grok",        ("grok", "agent"),
     env_dir("GROK_HOME", ".grok"), ".grok/skills"),
    ("agents",      ("grok", "agent", "codex"),
     env_dir("GROK_AGENTS_HOME", ".agents"), ".agents/skills"),
    ("copilot",     ("copilot", "copilot-cli"),
     env_dir("COPILOT_CONFIG_DIR", ".copilot"), ".copilot/skills"),
    ("antigravity", ("antigravity", "antigravity-cli"),
     env_dir("ANTIGRAVITY_CONFIG_DIR", ".gemini", "antigravity"),
     ".gemini/antigravity/skills"),
    ("windsurf",    ("windsurf", "windsurf-cli"),
     env_dir("WINDSURF_CONFIG_DIR", ".codeium", "windsurf"),
     ".windsurf/skills"),
    ("augment",     ("augment", "augment-cli"),
     env_dir("AUGMENT_CONFIG_DIR", ".augment"), ".augment/skills"),
    ("trae",        ("trae", "trae-cli"),
     env_dir("TRAE_CONFIG_DIR", ".trae"), ".trae/skills"),
    ("qwen",        ("qwen", "qwen-code", "qwen-cli"),
     env_dir("QWEN_CONFIG_DIR", ".qwen"), ".qwen/skills"),
    ("hermes",      ("hermes", "hermes-cli"),
     env_dir("HERMES_HOME", ".hermes"), ".hermes/skills"),
    ("codebuddy",   ("codebuddy", "codebuddy-cli"),
     env_dir("CODEBUDDY_CONFIG_DIR", ".codebuddy"), ".codebuddy/skills"),
    ("opencode",    ("opencode",),
     xdg_dir("OPENCODE_CONFIG_DIR", "opencode"), ".opencode/skills"),
    ("kilo",        ("kilo", "kilo-cli"),
     xdg_dir("KILO_CONFIG_DIR", "kilo"), ".kilo/skills"),
)


def first_cli(aliases: tuple[str, ...]) -> str | None:
    for name in aliases:
        hit = which(name)
        if hit:
            return hit
    return None


def detect() -> dict[str, str | None]:
    seen: dict[str, str | None] = {}
    for name, aliases, _cfg, _proj in RUNTIMES:
        if name == "agents":
            continue
        seen[name] = first_cli(aliases)
    return seen


def git_root(start: Path) -> Path | None:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return None


def looks_like_checkout(path: Path) -> bool:
    return (path / "skills" / PLUGIN / "SKILL.md").is_file()


def list_skills(root: Path) -> list[Path]:
    skills = root / "skills"
    if not skills.is_dir():
        return []
    return sorted(p for p in skills.iterdir() if (p / "SKILL.md").is_file())


def skill_homes(scope: str, project: Path) -> tuple[tuple[str, Path, tuple[str, ...]], ...]:
    homes = []
    for name, aliases, config, rel in RUNTIMES:
        dest = (project / rel) if scope == "project" else (config / "skills")
        homes.append((name, dest, aliases))
    return tuple(homes)


def fetch_to(origin: str, rel: str, dest: Path, dry: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = origin.rstrip("/") + "/" + rel.lstrip("/")
    if dry:
        print(f"  would get  {url}  →  {dest}")
        return
    if url.startswith("file://"):
        src = Path(url[7:]) 
        shutil.copy2(src, dest)
    else:
        with urllib.request.urlopen(url) as r, dest.open("wb") as f:
            f.write(r.read())
    print(f"  fetched    {rel}")


def bootstrap(origin: str, dest: Path, dry: bool) -> Path:
    if looks_like_checkout(dest):
        print(f"  checkout   {dest}")
        return dest
    print(f"  fetching   {origin}  →  {dest}")
    listing = dest / "files.txt"
    fetch_to(origin, "files.txt", listing, dry)
    if dry:
        print("  would fetch the plugin payload listed in files.txt")
        return dest
    names = [ln.strip() for ln in listing.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    if not names:
        raise SystemExit("files.txt from origin was empty")
    for rel in names:
        fetch_to(origin, rel, dest / rel, dry)
    if not looks_like_checkout(dest):
        raise SystemExit(f"fetch did not produce a plugin at {dest}")
    return dest


def resolve_root(scope: str, origin: str, dest_arg: Path | None, dry: bool) -> tuple[Path, Path]:
    """Return (plugin_root, project_root)."""
    cwd = Path.cwd()
    project = git_root(cwd) or cwd
    here = this_file()
    local = None
    if here and looks_like_checkout(here.parent):
        local = here.parent
    elif looks_like_checkout(cwd):
        local = cwd

    if dest_arg:
        dest = dest_arg
    elif local is not None:
        dest = local
    elif scope == "project":
        dest = project / ".superpowers-plus"
    else:
        dest = DATA_HOME / PLUGIN

    if not looks_like_checkout(dest):
        dest.mkdir(parents=True, exist_ok=True)
        dest = bootstrap(origin, dest, dry)
    return dest, project


def claude_marketplace_path(name: str, scope: str, project: Path) -> Path | None:
    if scope == "project":
        catalog = project / ".claude" / "settings.json"
    else:
        catalog = HOME / ".claude" / "plugins" / "known_marketplaces.json"
    try:
        data = json.loads(catalog.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if scope == "project":
        entry = (data.get("extraKnownMarketplaces") or {}).get(name) or {}
    else:
        entry = data.get(name) or {}
    src = entry.get("source") or {}
    path = src.get("path") or entry.get("installLocation")
    return Path(path).resolve() if path else None


def link_skill(target_dir: Path, skill: Path, dry: bool, undo: bool) -> str:
    dest = target_dir / skill.name
    if undo:
        if dest.is_symlink() and dest.resolve() == skill.resolve():
            if dry:
                print(f"  would rm   {dest}")
            else:
                dest.unlink()
                print(f"  removed    {dest}")
            return "removed"
        if dest.exists():
            print(f"  skip       {dest}  (not our symlink)")
            return "skipped"
        return "absent"
    if dest.is_symlink() and dest.resolve() == skill.resolve():
        print(f"  ok         {dest}")
        return "present"
    if dest.exists() or dest.is_symlink():
        print(f"  skip       {dest}  (already exists, not our link)")
        return "skipped"
    if dry:
        print(f"  would ln   {dest}  →  {skill}")
        return "linked"
    dest.symlink_to(skill, target_is_directory=True)
    print(f"  linked     {dest}  →  {skill}")
    return "linked"


def install_skill_homes(
    found: dict[str, str | None],
    homes: tuple[tuple[str, Path, tuple[str, ...]], ...],
    skills: list[Path],
    dry: bool,
    undo: bool,
) -> int:
    changed = 0
    for label, path, aliases in homes:
        exists = path.is_dir()
        cli_present = first_cli(aliases) is not None
        config_present = path.parent.is_dir()
        # A --project install always seeds .claude/skills: that is where
        # the next session in this repo will look, even if `claude` is not
        # on PATH in this particular shell.
        always = path.parent.name == ".claude" and path.name == "skills"
        if not exists and not cli_present and not config_present and not always:
            continue
        if not exists:
            if undo:
                continue
            if dry:
                print(f"  would mkdir {path}   ({label})")
            else:
                path.mkdir(parents=True, exist_ok=True)
                print(f"  mkdir      {path}   ({label})")
        else:
            print(f"  {label}: {path}")
        for skill in skills:
            if link_skill(path, skill, dry, undo) in {"linked", "removed"}:
                changed += 1
    return changed


def install_claude(root: Path, scope: str, project: Path, dry: bool, undo: bool) -> int:
    if not which("claude"):
        print("  Claude Code not on PATH — skip")
        return 0
    current = claude_marketplace_path(PLUGIN, scope, project)
    ours = root.resolve()
    flag = ["--scope", "project"] if scope == "project" else ["--scope", "user"]
    yes = ["-y"] if (not sys.stdin.isatty() or not sys.stdout.isatty()) else []
    if current is not None and current != ours:
        print(f"  marketplace {PLUGIN} already points at {current}")
        print("  leaving it alone — skill-directory links below use this copy")
        return 0
    if undo:
        if current == ours:
            run(["claude", "plugin", "uninstall", f"{PLUGIN}@{PLUGIN}"], dry)
            return 1
        print("  nothing of ours to uninstall")
        return 0
    if current is None:
        code, _ = run(["claude", "plugin", "marketplace", "add", *flag, str(root)], dry)
        if code != 0:
            return 0
    else:
        print(f"  marketplace {PLUGIN} already points here")
    code, _ = run(
        ["claude", "plugin", "install", f"{PLUGIN}@{PLUGIN}", "-s", scope, *yes],
        dry,
    )
    return 1 if code == 0 else 0


def grok_already_installed(out: str) -> bool:
    return "already installed" in (out or "").lower()


def grok_plugin_is_ours(root: Path) -> bool:
    proc = subprocess.run(
        ["grok", "plugin", "list"],
        check=False, text=True, capture_output=True,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    return PLUGIN in blob and str(root.resolve()) in blob


def install_grok(
    root: Path, scope: str, dry: bool, undo: bool, refresh: bool = False,
) -> int:
    if not which("grok"):
        print("  Grok not on PATH — skip")
        return 0
    if scope == "project":
        print("  Grok has no project plugin scope — skill dir only")
        return 0
    if undo:
        if grok_plugin_is_ours(root):
            run(["grok", "plugin", "uninstall", PLUGIN, "--confirm"], dry)
            return 1
        print("  nothing of ours to uninstall")
        return 0
    if grok_plugin_is_ours(root):
        print("  already ours")
        if refresh:
            run(["grok", "plugin", "update", PLUGIN], dry)
        return 0
    code, out = run(["grok", "plugin", "install", str(root), "--trust"], dry)
    if code != 0 and grok_already_installed(out):
        print("  already installed — leaving it")
        if refresh:
            run(["grok", "plugin", "update", PLUGIN], dry)
        return 0
    return 1 if code == 0 else 0


# Companions we offer. frontend-design is its own official plugin, not
# a superpowers extra. ponytail is the other lens in the decision log.
COMPANIONS = (
    {
        "name": "superpowers",
        "why": "required — spp layers on it",
        "required": True,
        "claude_id": "superpowers@claude-plugins-official",
        "marketplace": "anthropics/claude-plugins-official",
        "marketplace_name": "claude-plugins-official",
        "grok_src": "anthropics/claude-plugins-official#plugins/superpowers",
    },
    {
        "name": "ponytail",
        "why": "required — the second viewpoint on orchestrator decisions",
        "required": True,
        "claude_id": "ponytail@ponytail",
        "marketplace": "DietrichGebert/ponytail",
        "marketplace_name": "ponytail",
        "grok_src": "DietrichGebert/ponytail",
    },
    {
        "name": "frontend-design",
        "why": "optional — distinctive UI, not needed for SPP to run",
        "required": False,
        "claude_id": "frontend-design@claude-plugins-official",
        "marketplace": "anthropics/claude-plugins-official",
        "marketplace_name": "claude-plugins-official",
        "grok_src": "anthropics/claude-plugins-official#plugins/frontend-design",
    },
)


def installed_claude_plugins() -> set[str]:
    catalog = HOME / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(catalog.read_text())
    except (OSError, json.JSONDecodeError):
        return set()
    names = set()
    for key in (data.get("plugins") or {}):
        names.add(key.split("@", 1)[0])
    return names


def companion_present(name: str) -> bool:
    if name in installed_claude_plugins():
        return True
    if (HOME / ".claude" / "skills" / name).exists():
        return True
    return False


def missing_companions(*, required_only: bool = False) -> list[dict]:
    out = []
    for c in COMPANIONS:
        if required_only and not c.get("required"):
            continue
        if not companion_present(c["name"]):
            out.append(c)
    return out


def offer_companions() -> None:
    print("companions")
    for c in COMPANIONS:
        state = "installed" if companion_present(c["name"]) else "missing"
        print(f"  {c['name']:<18} {state}  — {c['why']}")
    need = missing_companions(required_only=True)
    if need:
        names = ", ".join(c["name"] for c in need)
        print(f"  required missing: {names}")
        print("  default install pulls those; --no-deps skips the pull")


def refuse_missing_required(*, no_deps: bool) -> int:
    missing = missing_companions(required_only=True)
    if not missing:
        return 0
    for c in missing:
        print(
            f"SPP cannot complete installation because required dependency",
            file=sys.stderr,
        )
        print(f"'{c['name']}' was not found.", file=sys.stderr)
    if no_deps:
        print(
            "Install the required dependencies, or rerun without --no-deps.",
            file=sys.stderr,
        )
    else:
        print(
            "Install the required dependencies and re-run.",
            file=sys.stderr,
        )
    return 2


def ensure_marketplace(source: str, name: str, dry: bool) -> bool:
    if not which("claude"):
        return False
    proc = subprocess.run(
        ["claude", "plugin", "marketplace", "list"],
        check=False, text=True, capture_output=True,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    if name in blob:
        return True
    code, _ = run(["claude", "plugin", "marketplace", "add", source], dry)
    return code == 0


def install_companions(scope: str, dry: bool) -> int:
    missing = missing_companions(required_only=True)
    if not missing:
        print("  required companions already present")
        return 0
    n = 0
    yes = ["-y"] if (not sys.stdin.isatty() or not sys.stdout.isatty()) else []
    flag = ["-s", "project"] if scope == "project" else ["-s", "user"]
    for c in missing:
        print(f"  {c['name']}")
        if which("claude"):
            if not ensure_marketplace(c["marketplace"], c["marketplace_name"], dry):
                print("    skip — could not add marketplace")
                continue
            code, _ = run(
                ["claude", "plugin", "install", c["claude_id"], *flag, *yes],
                dry,
            )
            if code == 0:
                n += 1
        elif which("grok"):
            code, _ = run(
                ["grok", "plugin", "install", c["grok_src"], "--trust"],
                dry,
            )
            if code == 0:
                n += 1
        else:
            print("    no claude/grok CLI — install this one yourself:")
            print(f"      claude plugin install {c['claude_id']}")
    return n


def plugin_version(root: Path) -> str:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
        return str(data.get("version") or "?")
    except (OSError, json.JSONDecodeError):
        return "?"


def refresh(origin: str, dest: Path, dry: bool) -> None:
    if (dest / ".git").exists():
        print(f"  git pull   {dest}")
        code, _ = run(["git", "-C", str(dest), "pull", "--ff-only"], dry)
        if code != 0:
            raise SystemExit(f"git pull failed in {dest}")
        return
    print(f"  refresh    {origin}  →  {dest}")
    listing = dest / "files.txt"
    fetch_to(origin, "files.txt", listing, dry)
    if dry:
        print("  would refresh the plugin payload listed in files.txt")
        return
    names = [ln.strip() for ln in listing.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    if not names:
        raise SystemExit("files.txt from origin was empty")
    for rel in names:
        fetch_to(origin, rel, dest / rel, dry)


def statusline_command(root: Path) -> str:
    py = which("python3") or sys.executable
    script = root / "statusline.py"
    return f'"{py}" "{script}"'


def statusline_spec(root: Path) -> dict:
    return {
        "type": "command",
        "command": statusline_command(root),
        "refreshInterval": 1,
    }


def is_our_statusline(cmd: str) -> bool:
    return "statusline.py" in cmd and ("superpowers" in cmd or "/spp" in cmd)


def is_gsd_statusline(cmd: str) -> bool:
    return "gsd-statusline" in cmd


def install_statusline(root: Path, dry: bool, undo: bool, force: bool) -> int:
    settings_path = HOME / ".claude" / "settings.json"
    if not settings_path.exists() and not (HOME / ".claude").is_dir():
        print("  no ~/.claude — skip statusline")
        return 0
    prev_path = HOME / ".claude" / "spp-statusline.prev.json"
    want = statusline_spec(root)
    try:
        settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  skip       settings.json unreadable ({exc})")
        return 0
    if not isinstance(settings, dict):
        print("  skip       settings.json is not an object")
        return 0
    current_obj = settings.get("statusLine")
    if not isinstance(current_obj, dict):
        current_obj = {}
    current = current_obj.get("command") or ""
    if undo:
        if not is_our_statusline(current):
            print("  statusline is not ours — leave it")
            return 0
        if prev_path.exists():
            try:
                prev = json.loads(prev_path.read_text())
            except (OSError, json.JSONDecodeError):
                prev = None
            if dry:
                print(f"  would restore statusline from {prev_path}")
            else:
                if prev is None:
                    settings.pop("statusLine", None)
                else:
                    settings["statusLine"] = prev
                settings_path.write_text(json.dumps(settings, indent=2) + "\n")
                prev_path.unlink(missing_ok=True)
                print("  restored  previous statusline")
            return 1
        if dry:
            print("  would remove spp statusline (no previous to restore)")
        else:
            settings.pop("statusLine", None)
            settings_path.write_text(json.dumps(settings, indent=2) + "\n")
            print("  removed   spp statusline")
        return 1
    if current and not is_our_statusline(current) and not is_gsd_statusline(current) and not force:
        print("  statusline already custom — pass --statusline to replace it")
        return 0
    if current_obj == want:
        print("  statusline already ours")
        return 0
    if dry:
        print(f"  would set  statusLine → {want}")
        return 1
    if current and not is_our_statusline(current):
        prev_path.write_text(json.dumps(settings.get("statusLine"), indent=2) + "\n")
        print(f"  backed up  {prev_path}")
    settings["statusLine"] = want
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    who = "GSD" if is_gsd_statusline(current) else "previous"
    print(f"  wired      Claude statusline ({who + ' replaced' if current else 'new'})")
    return 1


def check(found: dict[str, str | None], root: Path, homes: tuple) -> int:
    print("detected")
    for name, path in found.items():
        print(f"  {name:<12} {path or 'not found'}")
    print("skill homes")
    skills = list_skills(root)
    any_home = False
    for label, path, _ in homes:
        if path.is_dir():
            any_home = True
            ours = sum(1 for s in skills if (path / s.name).exists())
            print(f"  {label:<20} {path}  ({ours}/{len(skills)} skills)")
    if not any_home:
        print("  none yet")
    print(f"plugin root    {root}")
    print(f"skills         {', '.join(s.name for s in skills) or '(none)'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--global", dest="scope", action="store_const", const="user",
                       help="install for this user (default)")
    scope.add_argument("--user", dest="scope", action="store_const", const="user",
                       help="same as --global")
    scope.add_argument("--project", dest="scope", action="store_const", const="project",
                       help="install into the current project only")
    ap.set_defaults(scope="user")
    ap.add_argument("--origin", default=os.environ.get("SPP_ORIGIN", DEFAULT_ORIGIN),
                    help=f"where to fetch the plugin from (default {DEFAULT_ORIGIN})")
    ap.add_argument("command", nargs="?", default="install",
                    choices=["install", "update", "uninstall", "check"],
                    help="install (default), update, uninstall, or check")
    ap.add_argument("--dest", type=Path, default=None,
                    help="plugin checkout to use or fetch into")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--statusline", action="store_true",
                    help="replace an existing non-GSD custom statusline")
    ap.add_argument("--no-statusline", action="store_true",
                    help="do not touch Claude Code's statusLine setting")
    ap.add_argument("--install-python", action="store_true",
                    help="try to install python3 via the local package manager")
    ap.add_argument("--no-deps", action="store_true",
                    help="do not install required companions; fail if they are missing")
    ap.add_argument("--with-deps", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.with_deps and args.no_deps:
        print("cannot combine --with-deps and --no-deps", file=sys.stderr)
        return 2
    if args.with_deps:
        print("note: required companions are installed by default; --with-deps is ignored")
    if args.uninstall:
        args.command = "uninstall"
    if args.update:
        args.command = "update"
    if args.check:
        args.command = "check"

    if args.install_python:
        rec = python_recipe()
        if which("python3"):
            print("python3 already on PATH — nothing to install")
        elif not rec:
            print("no known package manager — install Python 3 yourself", file=sys.stderr)
            return 2
        else:
            print(f"running  {rec}")
            code, _ = run(rec.split(), dry=args.dry_run)
            if code != 0:
                return code

    found = detect()
    if args.no_deps and args.command != "uninstall":
        code = refuse_missing_required(no_deps=True)
        if code:
            return code
    try:
        root, project = resolve_root(args.scope, args.origin, args.dest, args.dry_run)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"could not locate the plugin: {exc}", file=sys.stderr)
        return 2

    skills = list_skills(root)
    homes = skill_homes(args.scope, project)

    if args.command == "check":
        print(f"scope          {args.scope}")
        print(f"project        {project}")
        print(f"version        {plugin_version(root)}")
        note_python_features()
        offer_companions()
        return check(found, root, homes)

    before = plugin_version(root)
    if args.command == "update":
        print(f"superpowers-plus  update  {before}")
        try:
            refresh(args.origin, root, args.dry_run)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"update failed: {exc}", file=sys.stderr)
            return 2
        skills = list_skills(root)
        after = plugin_version(root)
        print(f"version           {before} → {after}")

    if not skills and not args.dry_run:
        print("no skills/ with SKILL.md in the plugin root", file=sys.stderr)
        return 2

    verb = args.command
    if verb == "update":
        verb = "re-link"
    print(f"superpowers-plus  {verb}  ({'project' if args.scope == 'project' else 'global'})")
    print(f"plugin            {root}")
    print(f"project           {project}")
    for name, path in found.items():
        print(f"{name:<16}{path or 'not found'}")
    print()

    undo = args.command == "uninstall"
    n = 0
    print("Claude Code")
    n += install_claude(root, args.scope, project, args.dry_run, undo)
    print()
    print("Grok")
    n += install_grok(
        root, args.scope, args.dry_run, undo,
        refresh=args.command == "update",
    )
    print()
    print("Skill directories")
    n += install_skill_homes(found, homes, skills, args.dry_run, undo)
    print()
    print("Statusline")
    if args.no_statusline and args.command != "uninstall":
        print("  skipped    --no-statusline")
    elif not which("python3") and args.command != "uninstall":
        print("  skipped    no python3 — statusline will not run")
        print("  install Python 3 and re-run, or pass --install-python")
    else:
        n += install_statusline(
            root, args.dry_run, args.command == "uninstall", args.statusline,
        )
    print()
    print("Companions")
    if args.command == "uninstall":
        print("  leaving superpowers / ponytail / frontend-design in place")
    elif args.no_deps:
        print("  skipped    --no-deps (required companions already present)")
    else:
        n += install_companions(args.scope, args.dry_run)
        if not args.dry_run and refuse_missing_required(no_deps=False):
            return 2

    print()
    if args.dry_run:
        print("dry-run only — nothing written.")
    elif args.command == "uninstall":
        print("done. Restart a session for the change to take.")
    elif args.command == "update":
        print("done. Restart the session so it picks up the new skills.")
        print("Short names: /spp  ·  /spp-update")
    else:
        where = "this project" if args.scope == "project" else "this user"
        print(f"done. Restart a session, then invoke /spp or superpowers-plus ({where}).")
        print("Tools we do not detect: symlink skills/ into that tool yourself.")
    return 0 if n or args.dry_run else 1


if __name__ == "__main__":
    sys.exit(main())

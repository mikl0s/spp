#!/bin/sh
# One-liner (any of curl, wget, fetch):
#   curl -fsSL https://spp.datalos.dk/install.sh | sh
#   wget -qO-  https://spp.datalos.dk/install.sh | sh
#   fetch -o - https://spp.datalos.dk/install.sh | sh
#   … | sh -s -- --project
#   … | sh -s -- --install-python
#   … | sh -s -- --with-deps
#
# The one-liner may be served from the site. The payload is always GitHub
# (override with SPP_ORIGIN).
#
# python3 is optional. Skills install without it. The statusline, wavemap,
# and decision-log checker need it — we offer the common ways to get one.
set -eu

ORIGIN="${SPP_ORIGIN:-https://raw.githubusercontent.com/mikl0s/spp/main}"
PLUGIN=superpowers-plus
WANT_PYTHON=0
for arg in "$@"; do
  case "$arg" in
    --install-python) WANT_PYTHON=1 ;;
  esac
done

has_python() { command -v python3 >/dev/null 2>&1; }

# The ten we will actually run. Anything else is "install Python yourself".
python_recipe() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "sudo apt-get install -y python3"
  elif command -v dnf >/dev/null 2>&1; then
    echo "sudo dnf install -y python3"
  elif command -v yum >/dev/null 2>&1; then
    echo "sudo yum install -y python3"
  elif command -v pacman >/dev/null 2>&1; then
    echo "sudo pacman -S --noconfirm python"
  elif command -v zypper >/dev/null 2>&1; then
    echo "sudo zypper install -y python3"
  elif command -v apk >/dev/null 2>&1; then
    echo "sudo apk add python3"
  elif command -v brew >/dev/null 2>&1; then
    echo "brew install python3"
  elif command -v port >/dev/null 2>&1; then
    echo "sudo port install python313"
  elif command -v winget >/dev/null 2>&1; then
    echo "winget install Python.Python.3.12"
  elif command -v choco >/dev/null 2>&1; then
    echo "choco install python3 -y"
  else
    echo ""
  fi
}

explain_python() {
  echo "python3 is not on PATH."
  echo "Without it these will not run:"
  echo "  statusline     the bar (model, git, context meter)"
  echo "  wavemap.py     the wave map"
  echo "  validate.py    the decision-log checker"
  echo "Skills, /spp, and /spp-update still install."
  echo
  rec=$(python_recipe)
  echo "Common ways to get Python:"
  echo "  apt      sudo apt-get install -y python3"
  echo "  dnf      sudo dnf install -y python3"
  echo "  yum      sudo yum install -y python3"
  echo "  pacman   sudo pacman -S --noconfirm python"
  echo "  zypper   sudo zypper install -y python3"
  echo "  apk      sudo apk add python3"
  echo "  brew     brew install python3"
  echo "  macports sudo port install python313"
  echo "  winget   winget install Python.Python.3.12"
  echo "  choco    choco install python3 -y"
  echo "Anything else: install Python 3 yourself, then re-run."
  if [ -n "$rec" ]; then
    echo
    echo "This machine looks like: $rec"
    echo "Or re-run with --install-python to have the installer run that."
  fi
}

install_python() {
  rec=$(python_recipe)
  if [ -z "$rec" ]; then
    echo "no known package manager — install Python 3 yourself" >&2
    return 1
  fi
  echo "running  $rec"
  # shellcheck disable=SC2086
  sh -c "$rec"
}

if ! has_python && [ "$WANT_PYTHON" -eq 1 ]; then
  install_python || true
fi

if ! has_python; then
  explain_python
  echo
fi

find_installer() {
  here=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)
  if [ -n "${here:-}" ] && [ -f "$here/install.py" ] && [ -f "$here/skills/$PLUGIN/SKILL.md" ]; then
    echo "$here/install.py"
    return 0
  fi
  if [ -f ./install.py ] && [ -f ./skills/$PLUGIN/SKILL.md ]; then
    echo "./install.py"
    return 0
  fi
  return 1
}

if has_python; then
  if inst=$(find_installer); then
    exec python3 "$inst" --origin "$ORIGIN" "$@"
  fi
  if command -v curl >/dev/null 2>&1; then
    download() { curl -fsSL "$1"; }
  elif command -v wget >/dev/null 2>&1; then
    download() { wget -qO- "$1"; }
  elif command -v fetch >/dev/null 2>&1; then
    download() { fetch -o - "$1"; }
  else
    echo "curl, wget, or fetch is required" >&2
    exit 1
  fi
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  download "$ORIGIN/install.py" > "$tmp"
  exec python3 "$tmp" --origin "$ORIGIN" "$@"
fi

# No python: skills still go in. Statusline / wavemap / validate wait.
echo "installing skills only (no python3)"
ROOT=""
if inst=$(find_installer); then
  ROOT=$(CDPATH= cd -- "$(dirname -- "$inst")" && pwd)
else
  echo "no checkout and no python3 to fetch one — cannot install skills" >&2
  echo "install Python (see above) or clone the repo and re-run ./install.sh" >&2
  exit 1
fi

link_dir() {
  dest=$1
  mkdir -p "$dest"
  for skill in "$ROOT"/skills/*/SKILL.md; do
    [ -f "$skill" ] || continue
    name=$(basename "$(dirname "$skill")")
    src="$ROOT/skills/$name"
    if [ -L "$dest/$name" ] || [ -e "$dest/$name" ]; then
      echo "  ok         $dest/$name"
    else
      ln -s "$src" "$dest/$name"
      echo "  linked     $dest/$name"
    fi
  done
}

# The common runtimes. Anything else: symlink skills/ into that tool yourself.
for spec in \
  "claude:.claude/skills" \
  "cursor:.cursor/skills" \
  "gemini:.gemini/skills" \
  "codex:.codex/skills" \
  "grok:.grok/skills" \
  "agent:.agents/skills" \
  "copilot:.copilot/skills" \
  "windsurf:.windsurf/skills" \
  "opencode:.opencode/skills" \
  "qwen:.qwen/skills"
do
  cli=${spec%%:*}
  rel=${spec#*:}
  if command -v "$cli" >/dev/null 2>&1 || [ -d "$HOME/${rel%/*}" ]; then
    link_dir "$HOME/$rel"
  fi
done
# Always seed ~/.claude/skills — that is where the next session looks.
link_dir "$HOME/.claude/skills"

echo
echo "done. Skills are in. Statusline, wavemap, and validate wait on python3."
echo "Companions (superpowers, ponytail, frontend-design): install python3"
echo "and re-run with --with-deps, or:"
echo "  claude plugin install superpowers@claude-plugins-official"
echo "  claude plugin marketplace add DietrichGebert/ponytail"
echo "  claude plugin install ponytail@ponytail"
echo "  claude plugin install frontend-design@claude-plugins-official"
echo "Short names: /spp  ·  /spp-update"

#!/bin/sh
# /spp-update. The slash command runs this; the LLM does not.
set -eu
PLUGIN=superpowers-plus

find_installer() {
  if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/install.py" ]; then
    echo "$CLAUDE_PLUGIN_ROOT/install.py"
    return 0
  fi
  here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  if [ -f "$here/install.py" ]; then
    echo "$here/install.py"
    return 0
  fi
  data="${XDG_DATA_HOME:-$HOME/.local/share}/$PLUGIN"
  if [ -f "$data/install.py" ]; then
    echo "$data/install.py"
    return 0
  fi
  return 1
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for /spp-update" >&2
  exit 2
fi

if inst=$(find_installer); then
  exec python3 "$inst" update "$@"
fi

if command -v curl >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/mikl0s/spp/main/install.sh | sh -s -- update "$@"
  exit $?
fi
echo "no install.py and no curl" >&2
exit 2

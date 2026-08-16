#!/bin/sh
# Run inside the e2e image. Expects the checkout at /opt/origin (read-only).
set -eu

ORIGIN_DIR=/opt/origin
ORIGIN=http://127.0.0.1:8765
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/superpowers-plus"
SKILLS="decision-log decision-review project-bootstrap repo-readme spp spp-bootstrap spp-update superpowers-plus"
n_ok=0
n_fail=0

fail() { n_fail=$((n_fail + 1)); echo "FAIL  $*"; }
pass() { n_ok=$((n_ok + 1)); echo "ok    $*"; }

need() {
  if [ ! -e "$1" ]; then
    fail "$2 (missing $1)"
    return 1
  fi
  pass "$2"
}

need_link() {
  dest=$1
  label=$2
  if [ ! -L "$dest" ]; then
    fail "$label (not a symlink: $dest)"
    return 1
  fi
  if [ ! -f "$dest/SKILL.md" ]; then
    fail "$label (broken link $dest)"
    return 1
  fi
  pass "$label"
}

if [ ! -f "$ORIGIN_DIR/install.sh" ] || [ ! -f "$ORIGIN_DIR/files.txt" ]; then
  echo "mount the checkout at /opt/origin" >&2
  exit 2
fi

# Tools have been used: config dirs exist, CLIs are not on PATH.
# The installer still seeds ~/.claude/skills and any config it can see.
mkdir -p "$HOME/.claude" "$HOME/.grok"

echo "== origin"
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$ORIGIN_DIR" >/tmp/origin.log 2>&1 &
origin_pid=$!
trap 'kill "$origin_pid" 2>/dev/null || true' EXIT
i=0
while [ "$i" -lt 25 ]; do
  if curl -fsS "$ORIGIN/install.sh" >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 0.1
done
curl -fsS "$ORIGIN/install.sh" >/dev/null || {
  echo "origin did not serve install.sh" >&2
  cat /tmp/origin.log >&2 || true
  exit 2
}
pass "origin serves install.sh"

echo
echo "== one-liner (global)"
cd "$HOME"
# Not a checkout, so dest becomes ~/.local/share/superpowers-plus.
# SPP_ORIGIN must be in `sh`'s environment — a prefix on curl does not
# survive the pipe.
export SPP_ORIGIN="$ORIGIN"
set +e
curl -fsSL "$ORIGIN/install.sh" | sh
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  pass "curl | sh  exit $rc"
else
  fail "curl | sh  exit $rc"
fi

need "$DEST/skills/superpowers-plus/SKILL.md" "fetched plugin root"
need "$DEST/install.py" "fetched install.py"
need "$DEST/statusline.py" "fetched statusline.py"
need "$DEST/.claude-plugin/plugin.json" "fetched plugin manifest"

for name in $SKILLS; do
  need_link "$HOME/.claude/skills/$name" "claude skill  $name"
done
for name in $SKILLS; do
  need_link "$HOME/.grok/skills/$name" "grok skill    $name"
done

if grep -q statusline.py "$HOME/.claude/settings.json" 2>/dev/null; then
  pass "statusline wired in ~/.claude/settings.json"
else
  fail "statusline not wired"
fi

echo
echo "== --check"
set +e
out=$(python3 "$DEST/install.py" --check)
rc=$?
set -e
printf '%s\n' "$out"
if [ "$rc" -eq 0 ]; then
  pass "install.py --check  exit 0"
else
  fail "install.py --check  exit $rc"
fi
echo "$out" | grep -q "claude.*/.claude/skills  (8/8 skills)" \
  && pass "check reports 8/8 claude skills" \
  || fail "check did not report 8/8 claude skills"

echo
echo "== python features"
set +e
python3 "$DEST/skills/decision-log/validate.py" --self-test
rc=$?
set -e
[ "$rc" -eq 0 ] && pass "validate.py --self-test" || fail "validate.py --self-test exit $rc"

set +e
python3 "$DEST/skills/superpowers-plus/wavemap.py" --plain >/tmp/wavemap.out
rc=$?
set -e
[ "$rc" -eq 0 ] && pass "wavemap.py --plain" || fail "wavemap.py --plain exit $rc"
grep -q WAVE /tmp/wavemap.out && pass "wavemap prints WAVE rows" || fail "wavemap output has no WAVE"

echo
echo "== one-liner (--project)"
proj=/tmp/spp-proj
mkdir -p "$proj"
cd "$proj"
set +e
curl -fsSL "$ORIGIN/install.sh" | sh -s -- --project
rc=$?
set -e
[ "$rc" -eq 0 ] && pass "curl | sh --project  exit $rc" || fail "curl | sh --project  exit $rc"
need "$proj/.superpowers-plus/skills/superpowers-plus/SKILL.md" "project plugin root"
for name in $SKILLS; do
  need_link "$proj/.claude/skills/$name" "project claude skill  $name"
done

echo
echo "== uninstall (global)"
cd "$HOME"
set +e
python3 "$DEST/install.py" uninstall
rc=$?
set -e
[ "$rc" -eq 0 ] && pass "uninstall exit 0" || fail "uninstall exit $rc"
if [ -L "$HOME/.claude/skills/superpowers-plus" ]; then
  fail "claude skill still linked after uninstall"
else
  pass "claude skills unlinked"
fi
if [ -L "$HOME/.grok/skills/superpowers-plus" ]; then
  fail "grok skill still linked after uninstall"
else
  pass "grok skills unlinked"
fi

echo
echo "== $((n_ok + n_fail)) checks · $n_ok passed · $n_fail failed"
[ "$n_fail" -eq 0 ]

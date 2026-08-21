#!/bin/sh
# Skills-only path: checkout present, no python3.
set -eu

ORIGIN_DIR=/opt/origin
SKILLS=""
for _skill in "$ORIGIN_DIR"/skills/*/SKILL.md; do
  SKILLS="$SKILLS $(basename "$(dirname "$_skill")")"
done
SKILLS=${SKILLS# }
n_ok=0
n_fail=0

fail() { n_fail=$((n_fail + 1)); echo "FAIL  $*"; }
pass() { n_ok=$((n_ok + 1)); echo "ok    $*"; }

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

if ! command -v python3 >/dev/null 2>&1; then
  pass "python3 absent"
else
  fail "python3 should be absent in this image"
fi

mkdir -p "$HOME/.claude"
echo "== ./install.sh (skills only)"
cd "$HOME"
set +e
sh "$ORIGIN_DIR/install.sh"
rc=$?
set -e
[ "$rc" -eq 0 ] && pass "./install.sh exit $rc" || fail "./install.sh exit $rc"

for name in $SKILLS; do
  need_link "$HOME/.claude/skills/$name" "claude skill  $name"
done

echo
echo "== $((n_ok + n_fail)) checks · $n_ok passed · $n_fail failed"
[ "$n_fail" -eq 0 ]

#!/bin/sh
# Reproduce a clean-machine install of superpowers-plus.
# Same entry point locally and on GitHub Actions.
#
#   ./e2e/run.sh           one-liner + project + check + uninstall
#   ./e2e/run.sh nopython  checkout, no python3, skills only
#   ./e2e/run.sh all
#
# Needs docker or podman. The checkout is bind-mounted read-only so the
# image stays a base OS — nothing from this repo is baked in.
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$here/.." && pwd)
cmd=${1:-default}

if command -v docker >/dev/null 2>&1; then
  engine=docker
elif command -v podman >/dev/null 2>&1; then
  engine=podman
else
  echo "docker or podman is required" >&2
  exit 2
fi

run_case() {
  file=$1
  tag=$2
  echo
  echo "########  $tag  ($engine)"
  set -- build -f "$here/$file" -t "$tag" "$here"
  # CI logs are unreadable with BuildKit's default progress.
  if [ -n "${CI:-}${GITHUB_ACTIONS:-}" ]; then
    set -- build --progress=plain -f "$here/$file" -t "$tag" "$here"
  fi
  "$engine" "$@"
  "$engine" run --rm \
    -v "$root:/opt/origin:ro" \
    "$tag"
}

case "$cmd" in
  default|"")
    run_case Dockerfile spp-e2e
    ;;
  nopython)
    run_case Dockerfile.nopython spp-e2e-nopython
    ;;
  all)
    run_case Dockerfile spp-e2e
    run_case Dockerfile.nopython spp-e2e-nopython
    ;;
  *)
    echo "usage: $0 [default|nopython|all]" >&2
    exit 2
    ;;
esac

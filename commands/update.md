---
description: Update superpowers-plus and re-link skill directories
argument-hint: "[--project] [--dry-run]"
---

Update this plugin in place.

Run: !`python3 ${CLAUDE_PLUGIN_ROOT}/install.py update $ARGUMENTS`

If `CLAUDE_PLUGIN_ROOT` is empty, find `install.py` two levels above
`skills/spp-update/SKILL.md`, or run `curl -fsSL https://raw.githubusercontent.com/mikl0s/spp/main/install.sh | sh`.

Show the installer output, including the version before and after. Tell the
operator to start a new session so `/spp` picks up the new files.

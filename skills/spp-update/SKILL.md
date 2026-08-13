---
name: spp-update
description: Update superpowers-plus in place. Use when the user runs /spp-update, /spp:update, /superpowers-plus:update, or asks to update the plugin.
user-invocable: true
argument-hint: "[--project] [--dry-run]"
---

Update this plugin to whatever spp.datalos.dk (or the checkout's origin) is
serving, then re-link every runtime skill directory already installed.

## Find the installer

Try, in order:

1. `${CLAUDE_PLUGIN_ROOT}/install.py` if that env var is set
2. Two directories above this file: `skills/spp-update/SKILL.md` → repo root
3. `~/.local/share/superpowers-plus/install.py`
4. Fall back: `curl -fsSL https://spp.datalos.dk/install.sh | sh`

## Run it

```bash
python3 "$INSTALLER" update $ARGUMENTS
```

If the user asked for a project-only update and did not pass `--project`, add
`--project`.

## Report

Print the installer's output. Name the version before and after. Tell the
operator to start a new session so `/spp` and `/spp-update` pick up the new
files. Do not restart anything yourself.

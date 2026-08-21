---
name: spp-update
description: >
  Use when the user runs /spp-update, /spp:update,
  /superpowers-plus:update, or asks to update the plugin.
user-invocable: true
argument-hint: "[--project] [--dry-run]"
---

The slash command is a script. Do not find files. Do not write a report.
The script prints the report.

```bash
sh "${CLAUDE_PLUGIN_ROOT:-$HOME/.local/share/superpowers-plus}/update.sh" $ARGUMENTS
```

If that path is missing, `update.sh` next to `install.py` in this plugin.
Print the script's stdout and stderr unchanged. Then stop.

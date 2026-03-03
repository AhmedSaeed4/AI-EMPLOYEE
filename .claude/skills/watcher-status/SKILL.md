---
description: Check the status of the File System Watcher and show recent activity
---

# Watcher Status

Check if the File System Watcher is running and display recent activity from the Drop Zone.

## What This Does

1. Checks if the `filesystem_watcher.py` process is running
2. Lists files currently in the Drop_Zone folder
3. Shows recently processed files from Needs_Action
4. Displays watcher health status

## Usage

```
/watcher-status
```

## What It Checks

| Check | Description |
|--------|-------------|
| **Process Status** | Is `filesystem_watcher.py` running? |
| **Drop Zone** | What files are waiting? |
| **Recently Processed** | What tasks were created? |
| **Inbox** | What files were copied? |

## Troubleshooting

If the watcher is not running:

```bash
# Start the watcher
cd "/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts"
uv run python watchers/filesystem_watcher.py
```

To stop the watcher, press `Ctrl+C` in the terminal where it's running.

## Restarting the Watcher

If the watcher stops responding:
```bash
# Kill all watcher processes
pkill -9 -f filesystem_watcher

# Start fresh
cd "/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts"
uv run python watchers/filesystem_watcher.py
```

---
description: Check status of all watcher scripts (File System, Gmail, LinkedIn) and show their running status.
---

# Check Watchers Skill

This skill checks the status of all running watcher processes.

## How It Works

1. Checks for running watcher processes
2. Shows which watchers are active
3. Shows which watchers are stopped
4. Displays recent activity if available

## Usage

```
/check-watchers
```

## Watcher Status

| Watcher | Process Name | Status | Purpose |
|----------|--------------|---------|---------|
| File System | filesystem_watcher.py | Monitors Drop_Zone folder |
| Gmail | gmail_watcher.py | Monitors Gmail for important emails |
| LinkedIn | linkedin_watcher.py | Monitors LinkedIn messages and engagement |
| Orchestrator | orchestrator.py | Monitors Approved folder and executes actions |

## Instructions to Claude

When this skill is invoked:

1. **Check for running processes** using `ps aux | grep [watcher_name]`
2. **List all watchers** and their status
3. **Check log files** in `AI_Employee_Vault/Logs/` for recent activity
4. **Display a summary** showing:
   - Which watchers are running
   - Which watchers are stopped
   - Recent items processed (if any)
   - Any errors in logs

## Example Output

```
Watcher Status Summary:

✅ File System Watcher    - Running (PID: 12345)
❌ Gmail Watcher           - Stopped
✅ LinkedIn Watcher         - Running (PID: 12346)
✅ Orchestrator            - Running (PID: 12347)

Recent Activity:
- FILE_test.txt processed at 2026-02-12 05:30
- EMAIL_client_request.md created at 2026-02-12 05:25

Errors in last hour:
- None
```

## Troubleshooting

If a watcher is stopped:

| Watcher | Start Command |
|----------|--------------|
| File System | `cd ai_employee_scripts && uv run python watchers/filesystem_watcher.py` |
| Gmail | `cd ai_employee_scripts && uv run python watchers/gmail_watcher.py` |
| LinkedIn | `cd ai_employee_scripts && uv run python watchers/linkedin_watcher.py` |
| Orchestrator | `cd ai_employee_scripts && uv run python orchestrator.py` |

Use /start-watcher skill to start watchers automatically.

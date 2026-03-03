
---
description: Start one or more watcher scripts as background processes. File System, Gmail, LinkedIn, or Orchestrator.
---

# Start Watcher

Start watcher scripts as background processes.

## Usage

```
/start-watcher [watcher_name]
```

Options:
- `filesystem` - Start File System Watcher (monitors Drop_Zone)
- `gmail` - Start Gmail Watcher (monitors Gmail API)
- `linkedin` - Start LinkedIn Watcher (monitors LinkedIn messages)
- `orchestrator` - Start Approval Orchestrator (monitors Approved folder)
- `all` - Start all watchers
- (no argument) - Same as `filesystem`

Or start multiple:
```
/start-watcher gmail linkedin
```

## What This Does

1. Checks if watcher process is already running
2. Starts the specified script in the background with logging
3. Records the PID for process management
4. Verifies the watcher started successfully

## Watchers Available

| Watcher | Script | Check Interval | Purpose |
|----------|---------|---------------|---------|
| File System | `watchers/filesystem_watcher.py` | 60s | Monitor Drop_Zone for file drops |
| Gmail | `watchers/gmail_watcher.py` | 120s | Monitor Gmail for important emails |
| LinkedIn | `watchers/linkedin_watcher.py` | 300s | Monitor LinkedIn for messages/engagement |
| Orchestrator | `orchestrator.py` | 30s | Execute approved actions |

## Example Output

Single watcher:
```
Starting Gmail Watcher...
✅ Started (PID: 12345)
📝 Log: /tmp/gmail_watcher.log
⏱️ Check interval: 120 seconds
```

All watchers:
```
Starting all watchers...
✅ File System Watcher - Started (PID: 12343)
✅ Gmail Watcher - Started (PID: 12344)
✅ LinkedIn Watcher - Started (PID: 12345)
✅ Orchestrator - Started (PID: 12346)

All watchers running. Use /check-watchers to verify.
```

## Log Files

Each watcher logs to:
- File System: `/tmp/filesystem_watcher.log`
- Gmail: `/tmp/gmail_watcher.log`
- LinkedIn: `/tmp/linkedin_watcher.log`
- Orchestrator: `/tmp/orchestrator.log`

View logs with:
```bash
tail -f /tmp/gmail_watcher.log
```

## Managing Watchers

| Action | Command |
|---------|----------|
| Check status | /check-watchers |
| Stop watcher | /stop-watcher [name] |
| Stop all | /stop-watcher all |

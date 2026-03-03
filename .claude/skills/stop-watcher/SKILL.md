---
description: Stop one or more watcher scripts. Specify watcher name or 'all' to stop everything.
---

# Stop Watcher

Stop running watcher processes gracefully.

## Usage

```
/stop-watcher [watcher_name]
```

Options:
- `filesystem` - Stop File System Watcher
- `gmail` - Stop Gmail Watcher
- `linkedin` - Stop LinkedIn Watcher
- `orchestrator` - Stop Approval Orchestrator
- `all` - Stop all watchers (default if no argument)

Or stop multiple:
```
/stop-watcher gmail linkedin
```

## What This Does

1. Checks for running watcher processes
2. Gracefully terminates specified watchers
3. Confirms processes are stopped
4. Reports status

## Example Output

Single watcher:
```
Stopping Gmail Watcher...
✅ Stopped (terminated PID: 12345)
```

All watchers:
```
Stopping all watchers...
✅ File System Watcher - Stopped
✅ Gmail Watcher - Stopped
✅ LinkedIn Watcher - Stopped
✅ Orchestrator - Stopped

All watchers stopped. Use /start-watcher to restart.
```

## Safety

- Only stops watcher-related processes (filesystem_watcher, gmail_watcher, linkedin_watcher, orchestrator)
- Does not affect other running scripts or services
- Attempts graceful termination first (SIGTERM), then force (SIGKILL)

## Restarting

To start watchers again, use `/start-watcher`:

```
/start-watcher all
```

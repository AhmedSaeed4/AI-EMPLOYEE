---
description: Generate a daily summary of all activities and update the Dashboard
---

# Daily Summary

Generates a comprehensive daily summary of all AI Employee activities and updates the Dashboard.md file.

## What This Does

1. Reviews all activity logs for today
2. Checks completed tasks (files moved to /Done/)
3. Counts pending tasks (files in /Needs_Action/)
4. Updates Dashboard.md with today's summary
5. Creates a dated log entry in the Logs/ folder

## Usage

```
/daily-summary
```

## Summary Includes

| Section | Content |
|----------|----------|
| **Tasks Completed** | List of items moved to /Done/ today |
| **Tasks Pending** | Count of items in /Needs_Action/ |
| **Files Processed** | Files handled from /Inbox/ |
| **Watcher Activity** | Events from File System Watcher |
| **Recommendations** | Suggestions for improvements |

## Output

Updates the `AI_Employee_Vault/Dashboard.md` with:
- Updated Quick Stats table
- New entry in Recent Activity section
- Creates daily log: `Logs/YYYY-MM-DD_daily_summary.md`

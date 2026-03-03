---
description: Check all pending tasks in Needs_Action folder and display a summary
---

# Check Tasks

Checks the `AI_Employee_Vault/Needs_Action/` folder for any pending tasks and displays a summary of what needs to be done.

## What This Does

1. Reads all `.md` files from the vault's Needs_Action folder
2. Displays a summary of each pending task
3. Shows total count and priorities

## Usage

```
/check-tasks
```

## Notes

- Tasks are created by watchers when new items arrive in the Drop_Zone
- Each task has a priority level (high, normal, low)
- Tasks should be moved to `/Done/` folder after completion

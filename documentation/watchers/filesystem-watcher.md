# File System Watcher Documentation

## Overview

The File System Watcher monitors a local folder (Drop_Zone) for new files. When a file is dropped into the watched folder, it creates a task in `Needs_Action/` and copies the file to `Inbox/` for safekeeping.

**Location:** `ai_employee_scripts/watchers/filesystem_watcher.py`

**Inheritance:** Does NOT inherit from `BaseWatcher` (standalone implementation)

---

## Features

### What It Does

| Action | Description |
|--------|-------------|
| Monitors | Polls Drop_Zone folder every N seconds (default: 2) |
| Copies | New files are copied to `Inbox/` |
| Creates | Task file in `Needs_Action/` with file details |
| Tracks | Remembers processed files to avoid duplicates |

### WSL Compatibility

Uses **polling** instead of `inotify` for WSL compatibility:
- `inotify` doesn't work reliably on WSL with Windows-mounted drives
- Polling works consistently across all platforms
- 2-second default check interval provides near-real-time response

---

## Architecture

### Polling Flow

```
┌─────────────────────────────────────┐
│  1. Scan Drop_Zone                 │
│  - Get list of all files           │
│  - Compare with processed_files set │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Detect New Files                │
│  - Files not in processed_files     │
│  - Skip hidden files (starting .)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Process Each New File           │
│  - Call process_new_file()          │
│  - Copy to Inbox/                   │
│  - Create task in Needs_Action/     │
│  - Add to processed_files           │
└─────────────────────────────────────┘
```

### Methods

| Method | Description |
|--------|-------------|
| `check_for_updates()` | Returns list of new file paths |
| `process_new_file(source: Path)` | Copies file to Inbox and creates task |
| `run()` | Main polling loop |
| `stop()` | Stops the watcher |

**Note:** Uses `process_new_file()` instead of `create_action_file()` (different from BaseWatcher pattern).

---

## Setup Guide

### Prerequisites

1. **Python 3.13+** installed
2. **AI_Employee_Vault** folder exists
3. **Drop_Zone** folder exists (or will be created)

### Step 1: Verify Folders

Ensure these folders exist (watcher auto-creates if missing):

```bash
/path/to/ai-employee/
├── AI_Employee_Vault/
│   ├── Needs_Action/
│   ├── Inbox/
│   └── Logs/
└── Drop_Zone/
```

### Step 2: Run the Watcher

```bash
cd ai_employee_scripts
python watchers/filesystem_watcher.py
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════╗
║           FILE SYSTEM WATCHER - NOW ACTIVE                  ║
║           (Polling Mode - WSL Compatible)                   ║
╠════════════════════════════════════════════════════════════╣
║  Drop Zone: /path/to/Drop_Zone
║  Vault:      /path/to/AI_Employee_Vault
║  Check Interval: 2 seconds
╚════════════════════════════════════════════════════════════╝

Waiting for files... Drop any file into the Drop_Zone folder!

Press Ctrl+C to stop.

📂 Scanned existing files: 0 files
```

---

## Configuration

### Paths

Edit `filesystem_watcher.py` `__main__` section to customize paths:

```python
if __name__ == "__main__":
    vault_path = "/path/to/ai-employee/AI_Employee_Vault"
    drop_zone_path = "/path/to/ai-employee/Drop_Zone"

    watcher = FileSystemWatcher(vault_path, drop_zone_path, check_interval=2)
    watcher.run()
```

### Check Interval

Adjust polling frequency (in seconds):

| Setting | Use Case |
|---------|----------|
| `1` | Near-instant response (higher CPU) |
| `2` | Default - balanced |
| `5` | Lower CPU usage |
| `10+` | Minimal impact, slower response |

---

## File Processing

### When a File is Dropped

**1. Copy to Inbox:**
```
Drop_Zone/report.pdf → Inbox/report.pdf
```

**2. Create Task File:**
```
Needs_Action/FILE_report_20260228_123456.md
```

### Task File Format

```markdown
---
type: file_drop
original_name: report.pdf
source_path: /path/to/Drop_Zone/report.pdf
copied_to: /path/to/Inbox/report.pdf
size: 1234567
created: 2026-02-28T12:34:56
priority: normal
status: pending
---

# New File Dropped for Processing

## File Details
- **Name:** report.pdf
- **Size:** 1.2 MB
- **Type:** .pdf
- **Dropped at:** 2026-02-28T12:34:56

## Suggested Actions
- [ ] Review the file content
- [ ] Determine what action is needed
- [ ] Execute the action
- [ ] Move to /Done when complete

## Notes
*File has been copied to Inbox for safekeeping.*
```

---

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from watchers.filesystem_watcher import FileSystemWatcher

vault_path = "/path/to/AI_Employee_Vault"
drop_zone = "/path/to/Drop_Zone"

watcher = FileSystemWatcher(
    vault_path=vault_path,
    drop_zone_path=drop_zone,
    check_interval=2
)

watcher.run()  # Runs until Ctrl+C
```

### Custom Check Interval

```python
# Check every 5 seconds instead of 2
watcher = FileSystemWatcher(
    vault_path=vault_path,
    drop_zone_path=drop_zone,
    check_interval=5
)
```

### Stopping the Watcher

```python
# In another script or terminal
watcher.stop()
```

Or press `Ctrl+C` in the terminal running the watcher.

---

## File Tracking

### Processed Files Set

The watcher maintains a set of processed file paths:

```python
self.processed_files = set()
```

**Behavior:**
- Files are added when processed
- Scanned on startup to avoid reprocessing
- Stored in memory only (reset on restart)

**Note:** If watcher restarts, existing files in Drop_Zone are scanned and marked as processed to avoid duplicate tasks.

---

## Files and Paths

| File/Folder | Location | Purpose |
|-------------|----------|---------|
| Watcher Script | `ai_employee_scripts/watchers/filesystem_watcher.py` | Main watcher code |
| Drop Zone | `Drop_Zone/` (project root) | Monitored folder |
| Inbox | `AI_Employee_Vault/Inbox/` | Copied files storage |
| Tasks | `AI_Employee_Vault/Needs_Action/` | Task files created |
| Logs | `AI_Employee_Vault/Logs/` | **NOT USED** (uses print instead) |

---

## Troubleshooting

### Issue: Files Not Detected

**Symptoms:** File dropped but no task created

**Solutions:**
1. Check watcher is running: `ps aux | grep filesystem_watcher`
2. Verify Drop_Zone path in script
3. Check file isn't hidden (starts with `.`)
4. Check Logs folder for errors

---

### Issue: Duplicate Tasks

**Symptoms:** Same file creates multiple tasks

**Cause:** Watcher was restarted

**Solution:** This is expected behavior on restart - existing files are scanned and marked processed.

---

### Issue: Permission Denied

**Error Message:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
1. Check folder permissions
2. Ensure watcher has read access to Drop_Zone
3. Ensure watcher has write access to Inbox/Needs_Action

---

### Issue: "File in Use" on Windows

**Symptoms:** Can't copy file, or copy fails

**Cause:** File is open in another program

**Solution:** Close the file in its application before dropping in Drop_Zone.

---

## Running as Background Service

### Using nohup (Linux/WSL)

```bash
cd ai_employee_scripts
nohup python watchers/filesystem_watcher.py > /dev/null 2>&1 &
```

### Using screen

```bash
screen -S filesystem_watcher
cd ai_employee_scripts
python watchers/filesystem_watcher.py
# Ctrl+A, D to detach
```

### Checking Status

```bash
ps aux | grep filesystem_watcher | grep -v grep
```

### Stopping Background Watcher

```bash
pkill -f filesystem_watcher
```

---

## Skills Using File System Watcher

| Skill | Usage | Description |
|-------|-------|-------------|
| `watcher-status` | Check if running | Shows recent activity |
| `process-file` | Process dropped files | Handles files from Drop_Zone |
| `stop-watcher` | Stop watcher | Stops file system watcher |

---

## Dependencies

```
python-standard-library
```

No external dependencies - uses only Python standard library:
- `pathlib`
- `shutil`
- `time`
- `datetime`

---

## Comparison: BaseWatcher vs FileSystemWatcher

| Feature | BaseWatcher | FileSystemWatcher |
|---------|-------------|-------------------|
| **Inheritance** | Abstract base class | Standalone (doesn't inherit) |
| **Pattern** | Abstract methods | Direct implementation |
| **Logging** | Built-in logging class | Print statements |
| **Error Handling** | Failed_Queue files | Try/except with print |
| **Use Case** | API-based watchers | Simple file polling |

---

## Related Documentation

- [Base Watcher](base-watcher.md) - Abstract base class
- [Gmail Watcher](gmail-watcher.md) - Email monitoring
- [LinkedIn Watcher](linkedin-watcher.md) - LinkedIn messaging

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*

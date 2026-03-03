# Base Watcher Documentation

## Overview

The `BaseWatcher` is an abstract base class that provides the foundation for all watcher scripts in the AI Employee project. It implements the polling loop pattern, error handling, logging, and action file creation workflow that all concrete watchers inherit from.

**Location:** `ai_employee_scripts/watchers/base_watcher.py`

---

## Architecture

### Polling Pattern

The BaseWatcher uses **polling** instead of event-driven architecture (like `inotify`) for better WSL compatibility:

```
┌─────────────────────────────────────┐
│  1. Start Watcher                   │
│  - Initialize logging               │
│  - Create folders                   │
│  - Load previous state              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Polling Loop                    │
│  - Check for new items              │
│  - Process each item                │
│  - Wait check_interval seconds      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Create Action Files             │
│  - Call create_action_file()        │
│  - Save to Needs_Action/            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Error Handling                  │
│  - Track consecutive errors         │
│  - Create Failed_Queue files        │
│  - Wait 60s after 10 consecutive    │
└─────────────────────────────────────┘
```

---

## Class Structure

### Constructor

```python
BaseWatcher(vault_path: str, check_interval: int = 60)
```

**Parameters:**
- `vault_path`: Path to `AI_Employee_Vault/`
- `check_interval`: Seconds between polling checks (default: 60)

**Initialized Folders:**
- `Needs_Action/` - Tasks awaiting processing
- `Failed_Queue/` - Failed items for retry
- `Logs/` - Activity logs

---

## Abstract Methods

Concrete watchers **must** implement these methods:

### `check_for_updates() -> list`

Return a list of new items to process.

**Returns:** List of items (format depends on watcher type)

**Example implementations:**
- `FileSystemWatcher`: Returns list of new `Path` objects
- `GmailWatcher`: Returns list of Gmail message objects
- `LinkedInWatcher`: Returns list of message dictionaries

### `create_action_file(item) -> Path`

Create a `.md` task file in `Needs_Action/` folder.

**Parameters:**
- `item`: Single item to process

**Returns:** Path to created action file

---

## Built-in Methods

### `run()`

Main polling loop. Runs continuously until stopped:

1. Calls `check_for_updates()`
2. For each new item, calls `create_action_file()`
3. Handles errors with retry logic
4. Sleeps for `check_interval` seconds
5. Repeats until `Ctrl+C` or `stop()` called

### `stop()`

Stops the watcher by setting `self.running = False`.

### `_create_failed_queue_file(item, error, retry_count=0)`

Creates a failed queue file when an action cannot be processed.

**Failed Queue File Format:**
```markdown
# Failed Action - [WatcherClassName]

retry_count: 0
timestamp: 2026-02-28T12:34:56
watcher: WatcherClassName

## Error
ExceptionType: Error message

## Item Details
```
Item representation
```

## Traceback
```
Stack trace
```

## Notes
This action will be retried automatically. After 3 failed attempts,
it will be moved to the archived folder and a human review alert
will be created.
```

---

## Error Handling

### Consecutive Error Tracking

The watcher tracks consecutive errors and implements exponential backoff:

| Consecutive Errors | Behavior |
|--------------------|----------|
| 1-9 | Log error, continue immediately |
| 10+ | Wait 60 seconds before next retry |

### Error Recovery

After each successful item processed:
- `consecutive_errors` reset to 0
- Normal polling resumes

---

## Logging

### Log Files

Each watcher creates its own log file:

```
AI_Employee_Vault/Logs/
├── FileSystemWatcher.log
├── GmailWatcher.log
├── LinkedInWatcher.log
└── BaseWatcher.log
```

### Log Format

```
YYYY-MM-DD HH:MM:SS - WatcherName - LEVEL - Message
```

### Log Levels

- `INFO` - Normal operations (new items, files created)
- `WARNING` - Recoverable issues
- `ERROR` - Failed operations (API errors, file errors)

---

## Folder Structure

### Vault Folders (Auto-created)

```
AI_Employee_Vault/
├── Needs_Action/      # Task files created by watchers
├── Failed_Queue/      # Failed items for retry
├── Logs/              # Watcher log files
└── Inbox/             # Full content storage (some watchers)
```

---

## Creating a New Watcher

To create a new watcher, inherit from `BaseWatcher`:

```python
from base_watcher import BaseWatcher
from pathlib import Path
from datetime import datetime

class MyWatcher(BaseWatcher):
    """Watcher for [your service]."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        super().__init__(vault_path, check_interval)
        # Add your initialization here

    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        # Your polling logic here
        return []

    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'MY_ITEM_{timestamp}.md'

        content = f"""---
type: my_watcher
created: {datetime.now().isoformat()}
---

# My Item

## Details
{item}
"""

        filepath = self.needs_action / filename
        filepath.write_text(content)
        return filepath
```

---

## Usage Example

```python
from pathlib import Path
from watchers.my_watcher import MyWatcher

vault_path = Path(__file__).parent / 'AI_Employee_Vault'

watcher = MyWatcher(
    vault_path=str(vault_path),
    check_interval=120  # Check every 2 minutes
)

# Run continuously
watcher.run()
```

---

## Concrete Watchers

| Watcher | Purpose | Location |
|---------|---------|----------|
| `FileSystemWatcher` | Monitors Drop_Zone for new files | `filesystem_watcher.py` |
| `GmailWatcher` | Monitors Gmail for new emails | `gmail_watcher.py` |
| `LinkedInWatcher` | Monitors LinkedIn for messages | `linkedin_watcher.py` |

---

## Dependencies

```
python-standard-library
```

No external dependencies - uses only Python standard library.

---

## Related Documentation

- [File System Watcher](filesystem-watcher.md)
- [Gmail Watcher](gmail-watcher.md)
- [LinkedIn Watcher](linkedin-watcher.md)
- [LinkedIn Session Saver](linkedin-session-saver.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*

"""
File System Watcher - Monitors a folder for new files using POLLING
When a file is dropped in the watched folder, it creates a task in Needs_Action.

NOTE: Uses polling instead of inotify for better compatibility with WSL and all platforms.
"""
import shutil
import time
from pathlib import Path
from datetime import datetime


class FileSystemWatcher:
    """Polling-based file system watcher - works everywhere including WSL."""

    def __init__(self, vault_path: str, drop_zone_path: str, check_interval: int = 2):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.drop_zone = Path(drop_zone_path)
        self.check_interval = check_interval
        self.processed_files = set()
        self.running = False

        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.drop_zone.mkdir(parents=True, exist_ok=True)

        # Scan existing files on startup so we don't reprocess them
        self._scan_existing_files()

    def _scan_existing_files(self):
        """Scan drop zone for existing files to avoid reprocessing."""
        for item in self.drop_zone.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                self.processed_files.add(str(item))

    def check_for_updates(self) -> list:
        """Check for new files in drop zone."""
        new_files = []

        for item in self.drop_zone.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                if str(item) not in self.processed_files:
                    new_files.append(item)
                    self.processed_files.add(str(item))

        return new_files

    def process_new_file(self, source: Path):
        """Process a new file that was dropped."""
        timestamp = datetime.now().isoformat()

        # Copy to Inbox
        inbox_dest = self.inbox / source.name
        shutil.copy2(source, inbox_dest)

        # Create task file in Needs_Action
        task_filename = f"FILE_{source.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        task_path = self.needs_action / task_filename

        # Determine file type for better description
        file_size = source.stat().st_size
        size_kb = file_size / 1024
        size_display = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"

        task_content = f"""---
type: file_drop
original_name: {source.name}
source_path: {source}
copied_to: {inbox_dest}
size: {file_size}
created: {timestamp}
priority: normal
status: pending
---

# New File Dropped for Processing

## File Details
- **Name:** {source.name}
- **Size:** {size_display}
- **Type:** {source.suffix or 'unknown'}
- **Dropped at:** {timestamp}

## Suggested Actions
- [ ] Review the file content
- [ ] Determine what action is needed
- [ ] Execute the action
- [ ] Move to /Done when complete

## Notes
*File has been copied to Inbox for safekeeping.*
"""

        task_path.write_text(task_content)
        print(f"\n✅ New file detected: {source.name}")
        print(f"   → Copied to: {inbox_dest}")
        print(f"   → Task created: {task_filename}\n")

    def run(self):
        """Main polling loop."""
        self.running = True

        print(f"""
╔════════════════════════════════════════════════════════════╗
║           FILE SYSTEM WATCHER - NOW ACTIVE                  ║
║           (Polling Mode - WSL Compatible)                   ║
╠════════════════════════════════════════════════════════════╣
║  Drop Zone: {self.drop_zone}
║  Vault:      {self.vault_path}
║  Check Interval: {self.check_interval} seconds
╚════════════════════════════════════════════════════════════╝

Waiting for files... Drop any file into the Drop_Zone folder!

Press Ctrl+C to stop.
""")

        # Initial scan to register existing files
        print(f"📂 Scanned existing files: {len(self.processed_files)} files")

        try:
            while self.running:
                try:
                    new_files = self.check_for_updates()
                    for new_file in new_files:
                        self.process_new_file(new_file)
                except Exception as e:
                    print(f"Error in polling loop: {e}")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n✅ File System Watcher stopped.")

    def stop(self):
        """Stop the watcher."""
        self.running = False


if __name__ == "__main__":
    # Paths - adjust these if your folders are in different locations
    vault_path = "/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/AI_Employee_Vault"
    drop_zone_path = "/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/Drop_Zone"

    watcher = FileSystemWatcher(vault_path, drop_zone_path, check_interval=2)
    watcher.run()

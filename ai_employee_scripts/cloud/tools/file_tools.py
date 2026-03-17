"""
File Tools for Cloud Agents

Function tools that allow agents to read and write files in the vault.
These tools enable agents to:
- Read task files from Needs_Action/
- Write draft files to Pending_Approval/ (for human review)
- Move files for locking mechanism
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..config.settings import get_settings


def get_settings_safe():
    """Get settings safely, returning None if not configured."""
    try:
        return get_settings()
    except Exception:
        return None


# ============================================================================
# Task File Operations
# ============================================================================

def read_task(filename: str) -> dict:
    """
    Read a task file from the Needs_Action folder.

    Args:
        filename: Name of the task file to read

    Returns:
        Dictionary with file content and metadata
    """
    settings = get_settings_safe()
    if settings is None:
        return {"error": "Settings not configured", "content": ""}

    task_path = settings.needs_action_path / filename

    if not task_path.exists():
        return {"error": f"Task file not found: {filename}", "content": ""}

    try:
        with open(task_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "filename": filename,
            "content": content,
            "path": str(task_path),
            "size": len(content),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "content": ""}


def list_tasks() -> list[dict]:
    """
    List all task files in the Needs_Action folder.

    Returns:
        List of task file metadata
    """
    settings = get_settings_safe()
    if settings is None:
        return []

    if not settings.needs_action_path.exists():
        return []

    tasks = []
    for file_path in settings.needs_action_path.glob("*.md"):
        stat = file_path.stat()
        tasks.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return sorted(tasks, key=lambda x: x["modified"])


def move_to_progress(filename: str, agent_type: str = "cloud") -> dict:
    """
    Move a task file to In_Progress for locking.

    Args:
        filename: Name of the task file to move
        agent_type: Type of agent claiming the task (cloud/local)

    Returns:
        Result dictionary with status
    """
    settings = get_settings_safe()
    if settings is None:
        return {"success": False, "error": "Settings not configured"}

    source_path = settings.needs_action_path / filename

    if not source_path.exists():
        return {"success": False, "error": f"Task file not found: {filename}"}

    # Create progress folder if needed
    progress_folder = settings.in_progress_path / agent_type
    progress_folder.mkdir(parents=True, exist_ok=True)

    destination_path = progress_folder / filename

    try:
        shutil.move(str(source_path), str(destination_path))
        return {
            "success": True,
            "from": str(source_path),
            "to": str(destination_path),
            "agent_type": agent_type
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Draft File Operations
# ============================================================================

def write_draft(
    content: str,
    original_task: str,
    draft_type: str = "response",
    prefix: str = "DRAFT",
    original_content: str = None
) -> dict:
    """
    Write a draft response to the Pending_Approval folder.

    Cloud agents write drafts here for human review before execution.

    Args:
        content: The draft content to write
        original_task: Original task filename this draft is for
        draft_type: Type of draft (email, social, finance, general)
        prefix: Prefix for the draft filename
        original_content: Original task content (optional, to show in draft)

    Returns:
        Result dictionary with status and file path
    """
    settings = get_settings_safe()
    if settings is None:
        return {"success": False, "error": "Settings not configured"}

    # Create Pending_Approval folder if needed
    settings.pending_approval_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_original = original_task.replace(".md", "")
    filename = f"{prefix}_{draft_type}_{safe_original}_{timestamp}.md"
    filepath = settings.pending_approval_path / filename

    # Prepare draft content with metadata and human section
    original_section = ""
    if original_content:
        original_section = f"""
---

## Original Task Content

**Source:** {original_task}

```markdown
{original_content}
```

---
"""

    draft_content = f"""---
type: {draft_type}
status: pending_approval
created_by: cloud_agent
created_at: {datetime.now().isoformat()}
original_task: {original_task}
---

# Draft: {draft_type.title()} for {original_task}

{content}{original_section}

## Human Section
**Status:** [ ] Approve  [ ] Request changes  [ ] Reject

**Your Instructions:**
<!-- Write your feedback, edits, or instructions here -->

**Action if Approved:** Move this file to Approved/ folder
**Action if Changes:** Edit content above, then move to Approved/
**Action if Reject:** Move to Rejected/ folder
"""

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(draft_content)

        return {
            "success": True,
            "filename": filename,
            "path": str(filepath),
            "draft_type": draft_type,
            "size": len(draft_content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_pending_drafts() -> list[dict]:
    """
    List all draft files in the Pending_Approval folder.

    Returns:
        List of draft file metadata
    """
    settings = get_settings_safe()
    if settings is None:
        return []

    if not settings.pending_approval_path.exists():
        return []

    drafts = []
    for file_path in settings.pending_approval_path.glob("*.md"):
        stat = file_path.stat()
        drafts.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return sorted(drafts, key=lambda x: x["modified"], reverse=True)


# Kept for backward compatibility - now redirects to pending_approval
def list_updates() -> list[dict]:
    """
    List all draft files in the Pending_Approval folder (backward compatible).

    Returns:
        List of draft file metadata
    """
    return list_pending_drafts()


# ============================================================================
# Vault Reading Tools
# ============================================================================

def read_vault_file(relative_path: str) -> dict:
    """
    Read a file from the vault by relative path.

    Args:
        relative_path: Relative path from vault root

    Returns:
        Dictionary with file content or error
    """
    settings = get_settings_safe()
    if settings is None:
        return {"error": "Settings not configured", "content": ""}

    filepath = settings.vault_path / relative_path

    if not filepath.exists():
        return {"error": f"File not found: {relative_path}", "content": ""}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "path": relative_path,
            "content": content,
            "size": len(content),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "content": ""}


def list_vault_files(folder: str = "", pattern: str = "*.md") -> list[str]:
    """
    List files in a vault folder.

    Args:
        folder: Folder path relative to vault root
        pattern: Glob pattern for files

    Returns:
        List of file paths
    """
    settings = get_settings_safe()
    if settings is None:
        return []

    search_path = settings.vault_path / folder if folder else settings.vault_path

    if not search_path.exists():
        return []

    return [str(f.relative_to(settings.vault_path)) for f in search_path.glob(pattern)]

"""
Cloud Tools Module

Function tools for cloud agents to interact with:
- Vault file system
- Git operations
- Task management

Cloud agents write drafts to Pending_Approval/ for human review.
"""

from .file_tools import write_draft, read_task, move_to_progress
from .vault_tools import read_email_style, read_handbook, read_context

__all__ = [
    "write_draft",
    "read_task",
    "move_to_progress",
    "read_email_style",
    "read_handbook",
    "read_context",
]

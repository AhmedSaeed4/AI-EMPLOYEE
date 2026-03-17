"""
Git Tools for Cloud Agents

Function tools for git operations to sync with remote repository.
These tools enable agents to:
- Commit and push changes
- Pull updates from remote
- Check git status
"""

import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime


def run_git_command(cwd: str, *args) -> dict:
    """
    Run a git command and return the result.

    Args:
        cwd: Working directory for the command
        *args: Git command arguments

    Returns:
        Dictionary with success status, stdout, stderr
    """
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def git_status(repo_path: Optional[str] = None) -> dict:
    """
    Get git status of the repository.

    Args:
        repo_path: Path to the git repository

    Returns:
        Dictionary with status information
    """
    if repo_path is None:
        # Use vault path as default
        from ..config.settings import get_settings
        settings = get_settings()
        repo_path = str(settings.vault_path)

    return run_git_command(repo_path, "status", "--porcelain")


def git_add(repo_path: str, files: str = ".") -> dict:
    """
    Add files to git staging area.

    Args:
        repo_path: Path to the git repository
        files: Files to add (default: all changes)

    Returns:
        Dictionary with operation result
    """
    return run_git_command(repo_path, "add", files)


def git_commit(repo_path: str, message: str) -> dict:
    """
    Commit staged changes.

    Args:
        repo_path: Path to the git repository
        message: Commit message

    Returns:
        Dictionary with operation result
    """
    # Add co-author signature
    full_message = f"""{message}

Co-Authored-By: AI Employee Cloud Agent <cloud@ai-employee>
"""
    return run_git_command(repo_path, "commit", "-m", full_message)


def git_push(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """
    Push commits to remote repository.

    Args:
        repo_path: Path to the git repository
        remote: Remote name
        branch: Branch name

    Returns:
        Dictionary with operation result
    """
    return run_git_command(repo_path, "push", remote, branch)


def git_pull(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """
    Pull updates from remote repository.

    Args:
        repo_path: Path to the git repository
        remote: Remote name
        branch: Branch name

    Returns:
        Dictionary with operation result
    """
    return run_git_command(repo_path, "pull", remote, branch)


def git_commit_push(
    repo_path: str,
    message: str,
    remote: str = "origin",
    branch: str = "main"
) -> dict:
    """
    Commit and push changes in one operation.

    Args:
        repo_path: Path to the git repository
        message: Commit message
        remote: Remote name
        branch: Branch name

    Returns:
        Dictionary with operation result
    """
    # Check if there are changes to commit
    status = git_status(repo_path)
    if not status["success"]:
        return status

    if not status["stdout"]:
        return {
            "success": True,
            "message": "No changes to commit",
            "stdout": "",
            "stderr": ""
        }

    # Add, commit, and push
    add_result = git_add(repo_path, ".")
    if not add_result["success"]:
        return add_result

    commit_result = git_commit(repo_path, message)
    if not commit_result["success"]:
        return commit_result

    return git_push(repo_path, remote, branch)


def create_commit_message(action: str, details: str = "") -> str:
    """
    Create a formatted commit message.

    Args:
        action: Action performed (e.g., "Drafted email reply")
        details: Additional details

    Returns:
        Formatted commit message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[Cloud] {action}"

    if details:
        message += f"\n\n{details}"

    message += f"\n\nGenerated at {timestamp}"

    return message

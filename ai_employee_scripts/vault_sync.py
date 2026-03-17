#!/usr/bin/env python3
"""
Vault Sync Script - Platinum Tier

Automatically sync AI_Employee_Vault between local and cloud via Git.

Usage:
    python vault_sync.py
    python vault_sync.py --dry-run    # Test without pushing
    python vault_sync.py --daemon     # Run continuously

Cron (every 5 minutes):
    */5 * * * * cd /path/to/ai_employee_scripts && uv run python vault_sync.py
"""

import subprocess
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"

# Sync settings
SYNC_INTERVAL = 300  # 5 minutes
COMMIT_MESSAGE = "Auto-sync: Update vault {timestamp}"

# Dry run mode (set via --dry-run flag)
DRY_RUN = False


# =============================================================================
# GIT FUNCTIONS
# =============================================================================

def git_cmd(cmd, cwd=None):
    """Run git command at PROJECT_ROOT level."""
    if DRY_RUN:
        # In dry run mode, just print what would happen
        cmd_str = " ".join(cmd)
        print(f"[DRY RUN] Would execute: {cmd_str}")
        return 0, "", ""

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,  # Run from project root (where .git is)
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"


def has_changes():
    """Check if there are uncommitted changes."""
    returncode, stdout, stderr = git_cmd(["git", "status", "--porcelain"])
    return stdout.strip() != ""


def pull_changes():
    """Pull changes from remote with rebase."""
    print(f"[{timestamp()}] Pulling changes...")

    # Fetch first
    returncode, stdout, stderr = git_cmd(["git", "fetch"])
    if returncode != 0:
        print(f"[{timestamp()}] Fetch failed: {stderr}")
        return False

    # Rebase local changes on top of remote
    returncode, stdout, stderr = git_cmd(["git", "rebase", "origin/main"])
    if returncode != 0:
        print(f"[{timestamp()}] Rebase failed, aborting...")
        git_cmd(["git", "rebase", "--abort"])
        return False

    print(f"[{timestamp()}] Pull successful")
    return True


def push_changes():
    """Push local changes to remote."""
    print(f"[{timestamp()}] Pushing changes...")

    # Add all changes
    git_cmd(["git", "add", "-A"])

    # Commit
    commit_msg = COMMIT_MESSAGE.format(timestamp=datetime.now().isoformat())
    returncode, stdout, stderr = git_cmd(["git", "commit", "-m", commit_msg])

    # Push
    returncode, stdout, stderr = git_cmd(["git", "push"])
    if returncode != 0:
        print(f"[{timestamp()}] Push failed: {stderr}")
        return False

    print(f"[{timestamp()}] Push successful")
    return True


def sync():
    """Perform one sync cycle (pull, check local changes, push if any)."""
    try:
        # Pull first
        pull_changes()

        # Check if we have local changes to push
        if has_changes():
            push_changes()
        else:
            print(f"[{timestamp()}] No local changes to push")

        return True

    except Exception as e:
        print(f"[{timestamp()}] Sync error: {e}")
        return False


def run_daemon():
    """Run sync continuously in daemon mode."""
    print(f"[{timestamp()}] Vault sync daemon starting...")
    print(f"[{timestamp()}] Sync interval: {SYNC_INTERVAL}s")
    print(f"[{timestamp()}] Vault path: {VAULT_PATH}")
    print(f"[{timestamp()}] Press Ctrl+C to stop\n")

    while True:
        try:
            sync()
            print(f"[{timestamp()}] Waiting {SYNC_INTERVAL}s until next sync...\n")
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n[{timestamp()}] Daemon stopped by user")
            break


def timestamp():
    """Get current timestamp for logging."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# MAIN
# =============================================================================

def main():
    global DRY_RUN

    parser = argparse.ArgumentParser(description="Sync vault via git")
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run continuously as daemon"
    )
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="Run once and exit"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Test mode: show what would happen without making changes"
    )
    args = parser.parse_args()

    # Set dry run mode
    if args.dry_run:
        DRY_RUN = True
        print("=" * 60)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 60)

    # Check if vault exists
    if not VAULT_PATH.exists():
        print(f"ERROR: Vault not found at {VAULT_PATH}")
        sys.exit(1)

    # Check if git repo
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        print(f"ERROR: Not a git repository: {PROJECT_ROOT}")
        print("Initialize git first:")
        print(f"  cd {PROJECT_ROOT}")
        print("  git init")
        print("  git remote add origin <your-repo-url>")
        sys.exit(1)

    if args.daemon:
        run_daemon()
    else:
        # Run once (default for cron)
        sync()


if __name__ == "__main__":
    main()

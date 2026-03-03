"""
Shared utilities for AI Employee MCP servers.

This module provides common functionality reused across all MCP servers:
- Logging setup
- Vault path access
- Action logging to vault
"""

import json
import logging
from datetime import datetime
from pathlib import Path


def get_vault_path() -> Path:
    """
    Get the AI Employee vault path.

    The vault is located at the project root.
    """
    return Path(__file__).parent.parent.parent / "AI_Employee_Vault"


def setup_logger(name: str) -> logging.Logger:
    """
    Set up logging for an MCP server.

    Args:
        name: Logger name (usually server name)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_action(
    server_name: str,
    action_name: str,
    parameters: dict,
    result: str,
    error: str = None
) -> None:
    """
    Log an action to the vault's Logs folder.

    Creates or updates a daily JSON log file with:
    - Timestamp
    - Server name
    - Action performed
    - Parameters (sanitized)
    - Result
    - Error (if any)

    Args:
        server_name: Name of the MCP server
        action_name: Action that was performed
        parameters: Action parameters (will be sanitized)
        result: Result message
        error: Error message if failed
    """
    vault_path = get_vault_path()
    logs_dir = vault_path / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_date = datetime.now().strftime('%Y-%m-%d')
    log_file = logs_dir / f"{log_date}.json"

    # Read existing logs
    existing_logs = []
    if log_file.exists():
        try:
            existing_logs = json.loads(log_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            pass  # Start fresh if file is corrupted

    # Sanitize parameters (remove sensitive data)
    sanitized_params = sanitize_params(parameters)

    # Add new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "server": server_name,
        "action": action_name,
        "parameters": sanitized_params,
        "result": result,
        "error": error
    }
    existing_logs.append(entry)

    # Write back
    log_file.write_text(
        json.dumps(existing_logs, indent=2),
        encoding='utf-8'
    )


def sanitize_params(params: dict) -> dict:
    """
    Remove sensitive data from parameters before logging.

    Args:
        params: Original parameters dict

    Returns:
        Sanitized parameters dict
    """
    sensitive_keys = {
        'authorization', 'token', 'password', 'secret',
        'api_key', 'apikey', 'credential', 'session'
    }

    sanitized = {}
    for key, value in params.items():
        # Check for sensitive keys
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            sanitized[key] = f"{value[:50]}..."
        else:
            sanitized[key] = value

    return sanitized


def create_approval_request(
    action_type: str,
    details: dict,
    reason: str = None
) -> str:
    """
    Create an approval request file in the vault.

    For sensitive actions that require human approval.

    Args:
        action_type: Type of action (e.g., "payment", "email_send")
        details: Action details dict
        reason: Optional reason for approval

    Returns:
        Path to created approval file
    """
    vault_path = get_vault_path()
    approval_folder = vault_path / "Pending_Approval"
    approval_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_action = action_type.replace('/', '-').replace(' ', '_')

    filename = f"APPROVAL_{safe_action}_{timestamp}.md"
    filepath = approval_folder / filename

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"type: approval_request",
        f"action: {action_type}",
        f"status: pending",
        f"created: {datetime.now().isoformat()}",
        f"expires: {datetime.now().isoformat()}",  # TODO: Add 24h expiry
        "---",
        ""
    ]

    # Build body
    body_lines = [
        f"# Approval Required: {action_type}",
        "",
        "## Action Details",
    ]

    for key, value in details.items():
        body_lines.append(f"- **{key}**: {value}")

    if reason:
        body_lines.extend([
            "",
            "## Reason",
            reason
        ])

    body_lines.extend([
        "",
        "## To Approve",
        "Move this file to ../Approved/",
        "",
        "## To Reject",
        "Move this file to ../Rejected/"
    ])

    content = "\n".join(frontmatter_lines + body_lines)

    filepath.write_text(content, encoding='utf-8')

    return str(filepath)

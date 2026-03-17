"""
Vault Tools for Cloud Agents

Function tools for reading context and reference materials from the vault.
These tools enable agents to:
- Read brand voice/style guides
- Read Company Handbook rules
- Read previous context and history
"""

from typing import Optional

from .file_tools import read_vault_file, list_vault_files


def read_email_style() -> dict:
    """
    Read the EmailStyle.md or brand voice guide from the vault.

    Returns:
        Dictionary with style guide content or error
    """
    # Try common locations for email style guide
    possible_paths = [
        "EmailStyle.md",
        "Brand_Voice.md",
        "Company_Handbook.md",
        "Style/EmailStyle.md",
        "Guidelines/EmailStyle.md"
    ]

    for path in possible_paths:
        result = read_vault_file(path)
        if result.get("error") is None:
            return {
                "found": True,
                "path": path,
                "content": result["content"],
                "size": result.get("size", 0)
            }

    return {
        "found": False,
        "content": "# Default Email Style\n\nUse a professional, friendly tone. Be clear and concise.",
        "note": "No email style guide found in vault. Using default style."
    }


def read_handbook() -> dict:
    """
    Read the Company Handbook from the vault.

    Returns:
        Dictionary with handbook content or error
    """
    result = read_vault_file("Company_Handbook.md")

    if result.get("error"):
        return {
            "found": False,
            "content": "# Company Handbook\n\nNo handbook found.",
            "note": "No Company_Handbook.md found in vault."
        }

    return {
        "found": True,
        "content": result["content"],
        "size": result.get("size", 0)
    }


def read_context(context_type: str = "recent") -> dict:
    """
    Read context information from the vault.

    Args:
        context_type: Type of context to read (recent, email, social, etc.)

    Returns:
        Dictionary with context information
    """
    if context_type == "recent":
        # List recent done tasks for context
        return {
            "type": "recent",
            "files": list_vault_files("Done", "*.md")[:20],
            "note": "Recent completed tasks from Done folder"
        }

    elif context_type == "dashboard":
        result = read_vault_file("Dashboard.md")
        if result.get("error") is None:
            return {
                "type": "dashboard",
                "content": result["content"],
                "found": True
            }
        return {"type": "dashboard", "found": False, "content": ""}

    elif context_type == "handbook":
        return read_handbook()

    elif context_type == "email_style":
        return read_email_style()

    else:
        return {
            "type": context_type,
            "error": f"Unknown context type: {context_type}",
            "content": ""
        }


def get_vault_structure() -> dict:
    """
    Get the vault folder structure.

    Returns:
        Dictionary with vault folder listing
    """
    folders = {
        "Needs_Action": list_vault_files("Needs_Action"),
        "Updates": list_vault_files("Updates"),
        "In_Progress/cloud": list_vault_files("In_Progress/cloud"),
        "In_Progress/local": list_vault_files("In_Progress/local"),
        "Pending_Approval": list_vault_files("Pending_Approval"),
        "Approved": list_vault_files("Approved"),
        "Done": list_vault_files("Done"),
    }

    return {
        "folders": folders,
        "total_files": sum(len(files) for files in folders.values())
    }

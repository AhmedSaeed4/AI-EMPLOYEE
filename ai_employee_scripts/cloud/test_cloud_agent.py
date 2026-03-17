#!/usr/bin/env python3
"""
Test Script for Cloud Agent

Tests the cloud agent setup without requiring a full deployment.
Run this to verify your configuration is correct.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to set up environment
from dotenv import load_dotenv

# Load from .env.cloud if it exists, otherwise .env
env_file = Path(__file__).parent.parent / ".env.cloud"
if not env_file.exists():
    env_file = Path(__file__).parent.parent / ".env"

if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from: {env_file}")
else:
    print("Warning: No .env file found")

# Set VAULT_PATH to point to the actual vault location
# The vault is at the parent of ai_employee_scripts
import os
if "VAULT_PATH" not in os.environ:
    os.environ["VAULT_PATH"] = str(Path(__file__).parent.parent.parent / "AI_Employee_Vault")
    print(f"Set VAULT_PATH to: {os.environ['VAULT_PATH']}")

# Import cloud components
from cloud.config.settings import get_settings
from cloud.tools.file_tools import list_tasks, write_draft, read_task
from cloud.agent_definitions.models import TriageDecision, TaskType
from cloud.agent_definitions.triage_agent import triage_and_process, simple_route, OPENAI_AGENTS_AVAILABLE

# Debug: Check the value immediately after import
print(f"[DEBUG] OPENAI_AGENTS_AVAILABLE after import: {OPENAI_AGENTS_AVAILABLE}")


def test_settings():
    """Test configuration loading."""
    print("\n" + "="*60)
    print("TEST 1: Configuration")
    print("="*60)

    try:
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  - Vault Path: {settings.vault_path}")
        print(f"  - Model: {settings.model_name}")
        print(f"  - Polling Interval: {settings.polling_interval}s")
        print(f"  - Needs_Action: {settings.needs_action_path}")
        print(f"  - Updates: {settings.updates_path}")
        print(f"  - In_Progress: {settings.in_progress_path}")

        # Check if paths exist
        if settings.vault_path.exists():
            print(f"✓ Vault path exists")
        else:
            print(f"✗ Vault path does not exist: {settings.vault_path}")

        return True
    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        return False


def test_openai_agents():
    """Test OpenAI Agents SDK availability."""
    print("\n" + "="*60)
    print("TEST 2: OpenAI Agents SDK")
    print("="*60)

    if OPENAI_AGENTS_AVAILABLE:
        print("✓ OpenAI Agents SDK is installed and available")

        # Check for API key
        api_key = os.getenv("GLM") or os.getenv("XIAOMI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"✓ API key found (starts with: {api_key[:8]}...)")
            return True
        else:
            print("✗ No API key found (GLM, XIAOMI_API_KEY, or OPENAI_API_KEY)")
            print("  Set your API key in .env or .env.cloud")
            return False
    else:
        print("✗ OpenAI Agents SDK not installed")
        print("  Run: uv add openai-agents")
        return False


def test_vault_folders():
    """Test vault folder structure."""
    print("\n" + "="*60)
    print("TEST 3: Vault Folders")
    print("="*60)

    try:
        settings = get_settings()

        folders = {
            "Needs_Action": settings.needs_action_path,
            "Updates": settings.updates_path,
            "In_Progress": settings.in_progress_path,
            "In_Progress/cloud": settings.cloud_progress_path,
        }

        all_exist = True
        for name, path in folders.items():
            if path.exists():
                print(f"✓ {name}: {path}")
            else:
                print(f"✗ {name}: {path} (missing)")
                all_exist = False

        return all_exist
    except Exception as e:
        print(f"✗ Folder test failed: {e}")
        return False


def test_file_operations():
    """Test file read/write operations."""
    print("\n" + "="*60)
    print("TEST 4: File Operations")
    print("="*60)

    try:
        # Test listing tasks
        tasks = list_tasks()
        print(f"✓ Listed {len(tasks)} task(s) in Needs_Action/")

        # Test writing a draft
        draft_result = write_draft(
            content="This is a test draft.",
            original_task="test_task.md",
            draft_type="test",
            prefix="TEST"
        )

        if draft_result.get("success"):
            print(f"✓ Wrote test draft: {draft_result['filename']}")

            # Clean up test file
            draft_path = Path(draft_result['path'])
            if draft_path.exists():
                draft_path.unlink()
                print(f"✓ Cleaned up test file")
        else:
            print(f"✗ Failed to write draft: {draft_result.get('error')}")

        return True
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False


async def test_triage_routing():
    """Test triage routing (simple, no API call)."""
    print("\n" + "="*60)
    print("TEST 5: Triage Routing (Keyword-based)")
    print("="*60)

    try:
        # Test email routing
        email_task = "Please reply to this email from john@example.com about the project proposal."
        email_route = simple_route(email_task)
        print(f"✓ Email task routed to: {email_route.target_agent}")
        print(f"  Confidence: {email_route.confidence}")

        # Test social routing
        social_task = "Draft a LinkedIn post about our new product launch."
        social_route = simple_route(social_task)
        print(f"✓ Social task routed to: {social_route.target_agent}")
        print(f"  Confidence: {social_route.confidence}")

        # Test finance routing
        finance_task = "Create an invoice for client ABC for $5000."
        finance_route = simple_route(finance_task)
        print(f"✓ Finance task routed to: {finance_route.target_agent}")
        print(f"  Confidence: {finance_route.confidence}")

        return True
    except Exception as e:
        print(f"✗ Triage routing test failed: {e}")
        return False


async def test_ai_routing():
    """Test AI-based triage routing (requires API key)."""
    print("\n" + "="*60)
    print("TEST 6: AI Triage Routing (requires API key)")
    print("="*60)

    if not OPENAI_AGENTS_AVAILABLE:
        print("⊘ Skipped (OpenAI Agents SDK not available)")
        return True

    api_key = os.getenv("XIAOMI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⊘ Skipped (No API key found)")
        return True

    try:
        task = "Please draft a reply to Sarah's email about the invoice payment."
        result = await triage_and_process(task)

        print(f"✓ AI routing complete")
        print(f"  Response Type: {type(result).__name__}")

        # Check if it's a specialist response or routing decision
        if hasattr(result, 'target_agent'):
            # It's a TriageDecision (fallback)
            print(f"  Task Type: {result.task_type}")
            print(f"  Target Agent: {result.target_agent}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Reasoning: {result.reasoning}")
        else:
            # It's a specialist response (handoff worked!)
            print(f"  Specialist response received (handoff successful)")
            if hasattr(result, 'subject'):
                print(f"  Subject: {result.subject}")
            if hasattr(result, 'content'):
                print(f"  Content preview: {result.content[:100]}...")

        return True
    except Exception as e:
        print(f"✗ AI routing test failed: {e}")
        print("  This may be due to API issues - check your API key")
        return False


def create_sample_task():
    """Create a sample task file for testing."""
    print("\n" + "="*60)
    print("BONUS: Creating Sample Task File")
    print("="*60)

    try:
        settings = get_settings()
        sample_path = settings.needs_action_path / "SAMPLE_EMAIL_task.md"

        content = """# Task: Reply to Email

**From:** john.smith@example.com
**Subject:** Project Proposal Inquiry

**Body:**
Hi,

I'm interested in your services for a new project. We need a website redesign for our e-commerce store.

Could you provide a quote and timeline?

Thanks,
John

---
**Context:** This is a new lead from the website contact form.
**Action Required:** Draft a professional response asking for more details.
"""

        with open(sample_path, 'w') as f:
            f.write(content)

        print(f"✓ Created sample task: {sample_path}")
        print("  Run the orchestrator to process this task!")
        return True

    except Exception as e:
        print(f"✗ Failed to create sample task: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CLOUD AGENT TEST SUITE")
    print("="*60)

    results = []

    # Run tests
    results.append(("Configuration", test_settings()))
    results.append(("OpenAI Agents SDK", test_openai_agents()))
    results.append(("Vault Folders", test_vault_folders()))
    results.append(("File Operations", test_file_operations()))
    results.append(("Triage Routing", await test_triage_routing()))
    results.append(("AI Routing", await test_ai_routing()))

    # Bonus: Create sample task
    create_sample_task()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Your cloud agent is ready.")
        print("\nNext steps:")
        print("  1. Set your XIAOMI_API_KEY in .env or .env.cloud")
        print("  2. Run: uv run python cloud/cloud_orchestrator.py --test-run")
        print("  3. Check the Updates/ folder for generated drafts")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

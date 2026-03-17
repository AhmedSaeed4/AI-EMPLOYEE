"""
Triage Agent Implementation

Routes incoming tasks to the appropriate specialist agent.
This is the first agent that processes all incoming tasks.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env FIRST, before any imports
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

# Ensure OPENAI_API_KEY is set for tracing
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from typing import Optional, Any

# Try to import OpenAI Agents SDK
try:
    from agents import Agent, Runner
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    Agent = None
    Runner = None
    OPENAI_AGENTS_AVAILABLE = False

# Skip MCPServerStdio import at module level due to namespace collision
# Will import lazily in triage_and_process() function
MCPServerStdio = None
MCP_SERVER_AVAILABLE = False


# Import models and config (no circular dependency)
from .models import TriageDecision, TaskType, AgentType
from ..config.settings import get_settings, get_run_config
from ..guardrails import get_input_guardrails, get_output_guardrails


# Global agent instances
_triage_agent: Optional['Agent'] = None


def _create_specialist_agents():
    """
    Lazy import and creation of specialist agents.

    This is called inside create_triage_agent to avoid circular imports.
    """
    from .base_agent import INSTRUCTIONS

    specialists = {
        "email": None,
        "social": None,
        "finance": None
    }

    if OPENAI_AGENTS_AVAILABLE:
        try:
            from .email_agent import create_email_agent
            from .social_agent import create_social_agent
            from .finance_agent import create_finance_agent

            specialists["email"] = create_email_agent()
            specialists["social"] = create_social_agent()
            specialists["finance"] = create_finance_agent()
        except Exception as e:
            import sys
            print(f"[DEBUG] Error creating specialists: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    return specialists


def create_triage_agent(handoffs: Optional[list] = None) -> Optional['Agent']:
    """
    Create the Triage Agent with handoffs to specialists.

    Args:
        handoffs: Optional list of agents to hand off to

    Returns:
        Configured Triage Agent or None if SDK not available
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return None

    # Lazy import base_agent to avoid circular dependency
    from .base_agent import create_base_agent, INSTRUCTIONS

    # Create specialist agents
    specialists = _create_specialist_agents()

    # Use handoffs for automatic routing
    specialist_handoffs = []
    for name, agent in specialists.items():
        if agent is not None:
            specialist_handoffs.append(agent)
            import sys
            print(f"[DEBUG] Adding {name} agent to handoffs: {agent.name}", file=sys.stderr)
        else:
            import sys
            print(f"[DEBUG] WARNING: {name} agent is None!", file=sys.stderr)

    # Get guardrails
    input_guards = get_input_guardrails()
    # NOTE: Triage only uses INPUT guardrails - specialists will use OUTPUT guardrails
    # This prevents duplicate input checking (input checked once at triage level)
    output_guards = []  # Triage doesn't need output guardrails

    # Note: output_type removed because GLM doesn't support strict JSON schema
    # We use keyword-based routing fallback via simple_route() anyway
    agent = create_base_agent(
        name="Triage",
        instructions=INSTRUCTIONS.get("triage", INSTRUCTIONS["general"]),
        handoffs=specialist_handoffs,
        # output_type=TriageDecision,  # DISABLED - causes GLM schema errors
        input_guardrails=input_guards if input_guards else None,
        output_guardrails=None  # No output guardrails on triage
    )

    return agent


def get_triage_agent() -> Optional['Agent']:
    """Get or create the global Triage Agent instance."""
    global _triage_agent
    if _triage_agent is None:
        _triage_agent = create_triage_agent()
    return _triage_agent


async def triage_and_process(task_content: str, task_metadata: dict = None):
    """
    Triage task and process with appropriate specialist via handoff.

    Args:
        task_content: The task content to analyze and process
        task_metadata: Optional metadata about the task

    Returns:
        Specialist's response (EmailDraft, SocialPost, FinanceAction) or TriageDecision if fallback
    """
    if not OPENAI_AGENTS_AVAILABLE:
        # Fallback: simple keyword-based routing
        return simple_route(task_content)

    agent = get_triage_agent()
    if agent is None:
        return simple_route(task_content)

    odoo_server = None
    finance_agent = None

    import sys
    print(f"[DEBUG] Setting up MCP server for Finance Agent...", file=sys.stderr)

    try:
        settings = get_settings()
        config = get_run_config(settings)

        # Always attach Odoo MCP server to Finance Agent (per-request lifecycle)
        try:
            # Import MCPServerStdio here to avoid namespace collision at module level
            import agents.mcp.server as mcp_server_mod
            MCPServerStdio_Class = mcp_server_mod.MCPServerStdio
            print(f"[DEBUG] MCPServerStdio imported successfully", file=sys.stderr)

            # Get the Finance Agent from the Triage Agent's handoffs (not global cache)
            print(f"[DEBUG] Triage agent has {len(agent.handoffs)} handoffs", file=sys.stderr)
            for handoff_agent in agent.handoffs:
                if hasattr(handoff_agent, 'name') and handoff_agent.name == 'FinanceAgent':
                    finance_agent = handoff_agent
                    print(f"[DEBUG] Found Finance Agent in handoffs", file=sys.stderr)
                    break

            if finance_agent is None:
                print(f"[DEBUG] Finance Agent not found in handoffs, skipping MCP", file=sys.stderr)
            else:
                print(f"[DEBUG] Creating MCPServerStdio instance...", file=sys.stderr)
                # Create Odoo MCP server (per-request)
                odoo_server = MCPServerStdio_Class(
                    params={
                        "command": "uv",
                        "args": ["run", "cloud/mcp_servers/odoo_server.py"]
                    },
                    client_session_timeout_seconds=60
                )
                print(f"[DEBUG] Attaching server to agent...", file=sys.stderr)
                # Attach to Finance Agent
                finance_agent.mcp_servers = [odoo_server]
                print(f"[DEBUG] Connecting server...", file=sys.stderr)
                # Connect the server
                await odoo_server.connect()
                print(f"[DEBUG] MCP server connected!", file=sys.stderr)
        except Exception as e:
            # MCP setup failed, continue without it
            import sys
            print(f"[DEBUG] MCP setup failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            odoo_server = None

        # Prepare input with context
        input_text = f"""Task to process:

{task_content}
"""

        if task_metadata:
            input_text += f"\nMetadata: {task_metadata}"

        result = await Runner.run(
            agent,
            input=input_text,
            run_config=config
        )

        # Just return whatever the agent produces - text or model
        return result.final_output

    except Exception as e:
        # Fallback to simple routing on error
        return simple_route(task_content, error=str(e))

    finally:
        # Cleanup MCP server
        if odoo_server is not None:
            try:
                await odoo_server.cleanup()
            except Exception:
                pass  # Ignore cleanup errors
            # Clear agent's MCP servers
            if finance_agent is not None:
                finance_agent.mcp_servers = []


def simple_route(task_content: str, error: str = None) -> TriageDecision:
    """
    Simple keyword-based routing as fallback.

    Args:
        task_content: Task content to analyze
        error: Optional error message from AI routing

    Returns:
        TriageDecision with routing information
    """
    task_lower = task_content.lower()

    # Simple keyword matching
    if any(word in task_lower for word in ["email", "reply", "message", "inbox"]):
        return TriageDecision(
            task_type=TaskType.EMAIL,
            target_agent=AgentType.EMAIL,
            confidence="medium",
            reasoning=f"Keyword-based routing matched EMAIL. {error or ''}",
            requires_human_input=False
        )

    elif any(word in task_lower for word in ["social", "twitter", "linkedin", "facebook", "instagram", "post"]):
        return TriageDecision(
            task_type=TaskType.SOCIAL,
            target_agent=AgentType.SOCIAL,
            confidence="medium",
            reasoning=f"Keyword-based routing matched SOCIAL. {error or ''}",
            requires_human_input=False
        )

    elif any(word in task_lower for word in ["invoice", "payment", "finance", "accounting", "revenue", "expense"]):
        return TriageDecision(
            task_type=TaskType.FINANCE,
            target_agent=AgentType.FINANCE,
            confidence="medium",
            reasoning=f"Keyword-based routing matched FINANCE. {error or ''}",
            requires_human_input=False
        )

    else:
        return TriageDecision(
            task_type=TaskType.GENERAL,
            target_agent=AgentType.TRIAGE,
            confidence="low",
            reasoning=f"Could not determine task type. {error or ''}",
            requires_human_input=True,
            questions_for_human=["What type of task is this?"]
        )

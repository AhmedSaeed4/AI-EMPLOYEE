"""
Finance Agent Implementation

Handles financial tasks including invoice analysis,
payment summaries, and financial insights.

INTEGRATED WITH ODOO MCP SERVER for read-only access to:
- Customer information
- Invoice history
- Pricing data
- Draft invoice creation
"""

from typing import Optional
import asyncio

# Try to import OpenAI Agents SDK
try:
    from agents import Agent, Runner
    # NOTE: MCPServerStdio imported lazily in get_odoo_mcp_server() to avoid import issues
    OPENAI_AGENTS_AVAILABLE = True
except ImportError as e:
    import sys
    print(f"[DEBUG] finance_agent SDK import failed: {e}", file=sys.stderr)
    Agent = None
    Runner = None
    MCPServerStdio = None
    OPENAI_AGENTS_AVAILABLE = False

# Import models separately - they're always needed (not just when SDK is available)
try:
    from .base_agent import create_base_agent, INSTRUCTIONS
    from .models import FinanceAction, FinanceActionType, RiskLevel, ConfidenceLevel
    from ..config.settings import get_settings, get_run_config
    from ..guardrails import get_output_guardrails
except ImportError as e:
    import sys
    print(f"[DEBUG] finance_agent models import failed: {e}", file=sys.stderr)
    # Models should always be available - if not, fail explicitly
    raise ImportError(f"Required models could not be imported: {e}")

# Global agent instance
_finance_agent: Optional['Agent'] = None
_odoo_server: Optional['MCPServerStdio'] = None


# ============================================================================
# ODOO MCP SERVER INTEGRATION
# ============================================================================

def get_odoo_mcp_server() -> Optional['MCPServerStdio']:
    """
    Create and return the Odoo MCP server for Finance Agent.

    Returns:
        MCPServerStdio instance or None if not available
    """
    # Lazy import MCPServerStdio to avoid import order issues
    try:
        from agents.mcp import MCPServerStdio
    except ImportError:
        return None

    if not OPENAI_AGENTS_AVAILABLE:
        return None

    # Check if Odoo credentials are configured
    import os
    if not os.getenv("ODOO_URL") or not os.getenv("ODOO_PASSWORD"):
        return None

    global _odoo_server
    if _odoo_server is not None:
        return _odoo_server

    # Create MCP server connection
    _odoo_server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "cloud/mcp_servers/odoo_server.py"]
        },
        client_session_timeout_seconds=60
    )

    return _odoo_server


async def with_odoo_server(agent, func, *args, **kwargs):
    """
    Run a function with the Odoo MCP server connected.

    This handles connect/cleanup automatically.

    Args:
        agent: The Finance Agent
        func: Async function to run with server
        *args, **kwargs: Arguments for the function

    Returns:
        Result from the function
    """
    server = get_odoo_mcp_server()

    if server is None:
        # No Odoo server available, run without it
        return await func(*args, **kwargs)

    # Attach server to agent
    agent.mcp_servers = [server]

    try:
        # Connect server
        await server.connect()

        # Run the function
        result = await func(*args, **kwargs)

        return result

    finally:
        # Always cleanup
        try:
            await server.cleanup()
        except Exception:
            pass  # Ignore cleanup errors

        # Clear agent servers
        agent.mcp_servers = []


# ============================================================================
# FINANCE AGENT CREATION
# ============================================================================

def create_finance_agent() -> Optional['Agent']:
    """
    Create the Finance Agent for financial tasks.

    Returns:
        Configured Finance Agent or None if SDK not available
    """
    import sys
    print(f"[DEBUG] create_finance_agent() called, OPENAI_AGENTS_AVAILABLE={OPENAI_AGENTS_AVAILABLE}", file=sys.stderr)

    if not OPENAI_AGENTS_AVAILABLE:
        print("[DEBUG] Returning None because SDK not available", file=sys.stderr)
        return None

    # Get guardrails
    # NOTE: Finance agent only uses OUTPUT guardrails
    # INPUT guardrails already ran at Triage level - prevents duplicate checking
    try:
        output_guards = get_output_guardrails()
        print(f"[DEBUG] Got output_guards: {output_guards is not None}", file=sys.stderr)
    except Exception as e:
        print(f"[DEBUG] Error getting output_guards: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        output_guards = None

    try:
        agent = create_base_agent(
            name="FinanceAgent",
            instructions="""You are a Finance Agent for an AI Employee system. Your job is to handle financial tasks and analysis.

You have access to Odoo (accounting system) through MCP tools that can:
- get_customer(partner_name): Get customer info, balance, payment history
- search_partners(search_term): Find customers/vendors
- get_invoice_history(partner_name): Get customer's past invoices
- get_pricing(service_type): Get pricing for services
- create_draft_invoice(partner_name, amount, description): Create draft invoice (NOT posted)

Guidelines:
- Use Odoo tools to gather real data when available
- Be precise and accurate with numbers
- Flag unusual transactions or patterns
- Provide clear reasoning for recommendations
- Assess risk levels appropriately
- Always warn about potential issues

IMPORTANT: Draft invoices created via MCP are NOT posted/finalized.
They require human approval and posting by the local agent.

Financial actions always require human approval. Never execute without explicit human authorization.""",
            input_guardrails=None,  # No input guardrails (triage already checked)
            output_guardrails=output_guards if output_guards else None
        )
        print(f"[DEBUG] Finance agent created: {agent is not None}", file=sys.stderr)
        return agent
    except Exception as e:
        print(f"[DEBUG] Error creating finance agent: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def get_finance_agent() -> Optional['Agent']:
    """Get or create the global Finance Agent instance."""
    global _finance_agent
    if _finance_agent is None:
        _finance_agent = create_finance_agent()
    return _finance_agent


# ============================================================================
# TEXT PARSING
# ============================================================================

def parse_text_to_finance_action(text: str) -> FinanceAction:
    """
    Parse a text response from GLM into a FinanceAction.
    Extracts finance components from markdown/text format.

    Args:
        text: Raw text response from GLM

    Returns:
        FinanceAction with extracted or default values
    """
    import re
    import json

    # Default values
    action = FinanceAction(
        action_type=FinanceActionType.FLAG_UNUSUAL,
        description=text[:500],  # Truncate if too long
        risk_level=RiskLevel.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        reasoning="Extracted from text response",
        warnings=[],
        suggested_data={}
    )

    # Try to extract action type
    if 'invoice' in text.lower():
        action.action_type = FinanceActionType.CREATE_INVOICE
    elif 'payment' in text.lower():
        action.action_type = FinanceActionType.PAYMENT_SUMMARY
    elif 'revenue' in text.lower() or 'income' in text.lower():
        action.action_type = FinanceActionType.REVENUE_INSIGHT
    elif 'analyze' in text.lower() or 'transaction' in text.lower():
        action.action_type = FinanceActionType.ANALYZE_TRANSACTION

    # Try to extract amount
    amount_match = re.search(r'[\$€£]?\s*([\d,]+\.?\d*)\s*(?:usd|eur|gbp)?', text, re.IGNORECASE)
    if amount_match:
        try:
            action.amount = float(amount_match.group(1).replace(',', ''))
        except ValueError:
            pass

    # Try to extract risk level
    if 'high' in text.lower() and 'risk' in text.lower():
        action.risk_level = RiskLevel.HIGH
    elif 'low' in text.lower() and 'risk' in text.lower():
        action.risk_level = RiskLevel.LOW
    elif 'critical' in text.lower():
        action.risk_level = RiskLevel.CRITICAL

    # Extract description (first substantial paragraph)
    lines = text.split('\n')
    desc_lines = []
    for line in lines:
        # Skip metadata headers
        if any(x in line.lower() for x in ['action:', 'risk level:', 'confidence:', 'reasoning:']):
            continue
        if line.strip():
            desc_lines.append(line)
        if len(desc_lines) > 0 and len('\n'.join(desc_lines)) > 200:
            break

    if desc_lines:
        action.description = '\n'.join(desc_lines).strip()

    return action


# ============================================================================
# FINANCE TASK ANALYSIS (with Odoo MCP)
# ============================================================================

async def analyze_finance_task(
    task_content: str,
    task_type: str = "general"
) -> FinanceAction:
    """
    Analyze a financial task and recommend action.

    NOW WITH ODOO MCP ACCESS for real business data!

    Args:
        task_content: The financial task details
        task_type: Type of financial task

    Returns:
        FinanceAction with recommendation
    """
    if not OPENAI_AGENTS_AVAILABLE:
        # Fallback: simple analysis
        return FinanceAction(
            action_type=FinanceActionType.FLAG_UNUSUAL,
            description="Financial task requires human review (AI unavailable)",
            risk_level=RiskLevel.MEDIUM,
            confidence=ConfidenceLevel.LOW,
            reasoning="Finance agent not available, requires manual review"
        )

    agent = get_finance_agent()
    if agent is None:
        return FinanceAction(
            action_type=FinanceActionType.FLAG_UNUSUAL,
            description="Finance agent not available",
            risk_level=RiskLevel.MEDIUM,
            confidence=ConfidenceLevel.LOW
        )

    # Run with Odoo MCP server
    async def _run_analysis():
        settings = get_settings()
        config = get_run_config(settings)

        input_text = f"""Analyze this financial task:

Task Type: {task_type}

Details:
{task_content}

You have access to Odoo through MCP tools:
- get_customer(partner_name): Get customer info
- search_partners(search_term): Find customers
- get_invoice_history(partner_name): Get past invoices
- get_pricing(service_type): Get pricing

Use these tools to gather real data before making your recommendation.
Assess the risk level and provide clear reasoning.
"""

        result = await Runner.run(
            agent,
            input=input_text,
            run_config=config
        )

        raw_output = result.final_output

        # Handle text response directly (GLM returns text, not JSON)
        if isinstance(raw_output, str):
            return parse_text_to_finance_action(raw_output)
        else:
            # It's already a Pydantic model
            return raw_output

    # Run with Odoo MCP server
    return await with_odoo_server(agent, _run_analysis)


# ============================================================================
# INVOICE DRAFTING (with Odoo MCP)
# ============================================================================

async def draft_invoice_with_context(
    client_name: str,
    description: str,
    hours: Optional[float] = None,
    rate: Optional[float] = None,
    amount: Optional[float] = None
) -> dict:
    """
    Draft an invoice using real data from Odoo.

    NOW WITH ODOO MCP ACCESS for customer lookup and pricing!

    Args:
        client_name: Client to invoice
        description: Invoice description
        hours: Hours worked (optional)
        rate: Hourly rate (optional)
        amount: Total amount (if hours/rate not provided)

    Returns:
        dict with invoice draft data
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return {
            "success": False,
            "error": "AI unavailable - cannot draft invoice"
        }

    agent = get_finance_agent()
    if agent is None:
        return {
            "success": False,
            "error": "Finance agent not available"
        }

    # Run with Odoo MCP server
    async def _run_draft():
        settings = get_settings()
        config = get_run_config(settings)

        # Calculate amount if not provided
        calculated_amount = amount
        if hours is not None and rate is not None:
            calculated_amount = hours * rate

        # Build prompt with Odoo tool instructions
        input_text = f"""Draft an invoice for a client using the Odoo MCP tools.

Client Name: {client_name}
Description: {description}
Hours: {hours or 'N/A'}
Rate: {rate or 'N/A'}
Amount: {calculated_amount or 'N/A'}

INSTRUCTIONS:
1. Use get_customer() to get customer details for {client_name}
2. Use get_pricing() to get standard rates if rate not provided
3. Use create_draft_invoice() to create the draft invoice in Odoo
4. Return the draft invoice details

The draft invoice should be created in Odoo but NOT posted.
It will require human approval before being sent to the client.
"""

        result = await Runner.run(
            agent,
            input=input_text,
            run_config=config
        )

        raw_output = result.final_output

        # Try to extract invoice_id if Odoo tool was used
        import re
        invoice_id_match = re.search(r'"invoice_id":\s*(\d+)', raw_output)
        invoice_id = int(invoice_id_match.group(1)) if invoice_id_match else None

        return {
            "success": True,
            "client": client_name,
            "description": description,
            "amount": calculated_amount,
            "hours": hours,
            "rate": rate,
            "raw_output": raw_output,
            "invoice_id": invoice_id,
            "note": "Draft created in Odoo. Requires human approval before posting."
        }

    # Run with Odoo MCP server
    return await with_odoo_server(agent, _run_draft)


# Legacy function for backward compatibility
async def draft_invoice_summary(
    client_name: str,
    amount: float,
    description: str,
    line_items: list = None
) -> FinanceAction:
    """
    Draft an invoice summary for review.

    Args:
        client_name: Client to invoice
        amount: Total amount
        description: Invoice description
        line_items: Optional list of line items

    Returns:
        FinanceAction with invoice data
    """
    result = await draft_invoice_with_context(
        client_name=client_name,
        description=description,
        amount=amount
    )

    return FinanceAction(
        action_type=FinanceActionType.CREATE_INVOICE,
        description=f"Invoice for {client_name}: ${amount}",
        amount=amount,
        risk_level=RiskLevel.LOW,
        confidence=ConfidenceLevel.MEDIUM,
        suggested_data={
            "client": client_name,
            "amount": amount,
            "description": description,
            "line_items": line_items or []
        }
    )

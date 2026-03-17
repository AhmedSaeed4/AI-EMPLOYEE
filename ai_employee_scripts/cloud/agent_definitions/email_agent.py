"""
Email Agent Implementation

Drafts email replies based on incoming email context.
Maintains brand voice and professional tone.
"""

from typing import Optional

# Try to import OpenAI Agents SDK
try:
    from agents import Agent, Runner, function_tool
    from .base_agent import create_base_agent, INSTRUCTIONS
    from .models import EmailDraft, ConfidenceLevel
    from ..tools.vault_tools import read_email_style, read_handbook
    from ..config.settings import get_settings, get_run_config
    from ..guardrails import get_input_guardrails, get_output_guardrails
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    Agent = None
    Runner = None
    function_tool = None
    OPENAI_AGENTS_AVAILABLE = False


# Global agent instance
_email_agent: Optional['Agent'] = None


@function_tool
def get_brand_style() -> str:
    """Get the brand email style guide from the vault."""
    result = read_email_style()
    if result.get("found"):
        return result["content"]
    return "Use a professional, friendly tone. Be clear and concise."


@function_tool
def get_company_rules() -> str:
    """Get company handbook rules relevant to email communication."""
    result = read_handbook()
    if result.get("found"):
        # Extract relevant sections about communication
        content = result["content"]
        # Simple extraction of email-related rules
        lines = content.split('\n')
        email_sections = []
        in_email_section = False
        for line in lines:
            if 'email' in line.lower() or 'communication' in line.lower():
                in_email_section = True
            if in_email_section:
                email_sections.append(line)
                if line.strip() and not line.startswith('#') and not line.startswith('-'):
                    in_email_section = False
        return '\n'.join(email_sections[:20]) if email_sections else content[:500]
    return "Be professional and helpful in all communications."


def create_email_agent() -> Optional['Agent']:
    """
    Create the Email Agent with writing tools.

    Returns:
        Configured Email Agent or None if SDK not available
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return None

    tools = [get_brand_style, get_company_rules]

    # Get guardrails
    # NOTE: Email agent only uses OUTPUT guardrails
    # INPUT guardrails already ran at Triage level - prevents duplicate checking
    input_guards = []  # No input guardrails (already checked by triage)
    output_guards = get_output_guardrails()

    # Note: output_type removed because GLM doesn't support strict JSON schema
    # We parse text responses manually in parse_text_to_email_draft()
    agent = create_base_agent(
        name="EmailAgent",
        instructions=INSTRUCTIONS.get("email", INSTRUCTIONS["general"]),
        tools=tools,
        # output_type=EmailDraft,  # DISABLED - causes GLM schema errors
        input_guardrails=None,  # No input guardrails (triage already checked)
        output_guardrails=output_guards if output_guards else None
    )

    return agent


def get_email_agent() -> Optional['Agent']:
    """Get or create the global Email Agent instance."""
    global _email_agent
    if _email_agent is None:
        _email_agent = create_email_agent()
    return _email_agent


def parse_text_to_email_draft(text: str, sender: str, subject: str) -> EmailDraft:
    """
    Parse a text response from GLM into an EmailDraft.
    Extracts email components from markdown/text format.

    Args:
        text: Raw text response from GLM
        sender: Default sender email
        subject: Default subject

    Returns:
        EmailDraft with extracted or default values
    """
    import re

    # Default values
    draft = EmailDraft(
        to=sender,
        subject=f"Re: {subject}",
        body=text,
        confidence=ConfidenceLevel.MEDIUM,
        needs_approval=True,
        tone="professional",
        suggested_changes=[],
        missing_info=[]
    )

    # Try to extract subject
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if subject_match:
        draft.subject = subject_match.group(1).strip()

    # Try to extract recipient (To:)
    to_match = re.search(r'To:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if to_match:
        draft.to = to_match.group(1).strip()

    # Try to extract body (content after salutation or before signature)
    lines = text.split('\n')

    # Find body content (skip headers and metadata)
    body_start = 0
    body_end = len(lines)

    for i, line in enumerate(lines):
        # Look for email body start (after "Dear", "Hi", etc.)
        if re.match(r'^(Dear|Hi|Hello|Hey)', line, re.IGNORECASE):
            body_start = i
        # Look for signature end markers
        if re.match(r'^(Best regards|Thanks|Sincerely|Cheers)', line, re.IGNORECASE):
            body_end = i
            break

    # Extract body content
    if body_start < body_end:
        body_lines = lines[body_start:body_end]
        # Remove common headers/metadata from body
        cleaned_lines = []
        for line in body_lines:
            # Skip empty lines at start
            if not cleaned_lines and not line.strip():
                continue
            # Skip metadata lines
            if any(x in line.lower() for x in ['action required', 'status:', 'decision needed:', 'next steps:']):
                break
            cleaned_lines.append(line)

        draft.body = '\n'.join(cleaned_lines).strip()

    return draft


async def draft_email_reply(
    email_content: str,
    sender: str,
    subject: str,
    context: str = ""
) -> EmailDraft:
    """
    Draft an email reply based on incoming email.

    Args:
        email_content: The incoming email body
        sender: The sender's email address or name
        subject: The email subject
        context: Additional context (thread history, etc.)

    Returns:
        EmailDraft with the reply
    """
    if not OPENAI_AGENTS_AVAILABLE:
        # Fallback: simple template
        return EmailDraft(
            to=sender,
            subject=f"Re: {subject}",
            body="Thank you for your email. I have received your message and will respond shortly.",
            confidence=ConfidenceLevel.LOW,
            needs_approval=True,
            suggested_changes=["Please review and edit this draft"]
        )

    agent = get_email_agent()
    if agent is None:
        return EmailDraft(
            to=sender,
            subject=f"Re: {subject}",
            body="Error: Email agent not available.",
            confidence=ConfidenceLevel.LOW,
            needs_approval=True
        )

    try:
        settings = get_settings()
        config = get_run_config(settings)

        input_text = f"""Draft a reply to the following email:

From: {sender}
Subject: {subject}

Email Body:
{email_content}
"""

        if context:
            input_text += f"""
Additional Context:
{context}
"""

        result = await Runner.run(
            agent,
            input=input_text,
            run_config=config
        )

        raw_output = result.final_output

        # Handle text response directly (GLM returns text, not JSON)
        if isinstance(raw_output, str):
            return parse_text_to_email_draft(raw_output, sender, subject)
        else:
            # It's already a Pydantic model
            return raw_output

    except Exception as e:
        # On error, try to extract what we can from any partial response
        error_body = f"Error generating draft: {str(e)}"
        return EmailDraft(
            to=sender,
            subject=f"Re: {subject}",
            body=error_body,
            confidence=ConfidenceLevel.LOW,
            needs_approval=True,
            suggested_changes=[f"Agent error: {str(e)}"]
        )

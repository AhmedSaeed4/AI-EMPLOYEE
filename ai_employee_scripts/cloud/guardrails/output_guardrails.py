"""
Output Guardrails for Cloud Agents

Validates agent outputs before writing to vault.
Ensures outputs are appropriate, formatted correctly, and safe.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any

# Try to import OpenAI Agents SDK
try:
    from agents import Agent, output_guardrail, GuardrailFunctionOutput, Runner
    from ..config.settings import get_settings, get_run_config
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    Agent = None
    output_guardrail = None
    GuardrailFunctionOutput = None
    Runner = None
    OPENAI_AGENTS_AVAILABLE = False


class OutputGuardrailCheck(BaseModel):
    """Result of output guardrail check."""

    is_appropriate: bool = Field(
        description="Whether the output is appropriate"
    )
    reasoning: str = Field(
        description="Explanation of the check result"
    )


# Lazy-loaded output guardrail agent and config
_output_guardrail_agent = None
_output_guardrail_config = None


def _get_output_guardrail_agent_and_config():
    """Get or create the output guardrail agent with proper model configuration."""
    global _output_guardrail_agent, _output_guardrail_config

    if not OPENAI_AGENTS_AVAILABLE:
        return None, None

    if _output_guardrail_agent is not None:
        return _output_guardrail_agent, _output_guardrail_config

    settings = get_settings()
    config = get_run_config(settings)

    # Create output guardrail agent with proper instructions
    _output_guardrail_agent = Agent(
        name="OutputGuardrail",
        instructions="""You are an Output Guardrail Agent. Your job is to check if agent output is appropriate before it is shown to users or written to the vault.

Check for:
1. Inappropriate content (offensive, harmful, misleading, illegal)
2. Accidentally included sensitive data (passwords, API keys, secrets)
3. System prompt leaks (instructions, internal system details)
4. Policy violations (against company rules, handbook)
5. Extremely low-quality or nonsensical responses

Be reasonable - allow normal professional content. Only flag genuine issues.

RESPONSE FORMAT: Start your response with either APPROPRIATE: or BLOCK: followed by your reasoning.
Example: APPROPRIATE: This is a well-written professional email draft.
Example: BLOCK: Contains sensitive API key that should not be included."""
    )

    _output_guardrail_config = config
    return _output_guardrail_agent, _output_guardrail_config


# Output guardrail function
if OPENAI_AGENTS_AVAILABLE and output_guardrail is not None:
    @output_guardrail
    async def check_output_guardrail(context, agent, output_text: str) -> GuardrailFunctionOutput:
        """
        Run output guardrail check using the guardrail agent.

        This function is decorated as an output guardrail and will be called
        automatically after agent processing.
        """
        guardrail_agent, config = _get_output_guardrail_agent_and_config()

        if guardrail_agent is None or config is None:
            return GuardrailFunctionOutput(
                output_info=OutputGuardrailCheck(
                    is_appropriate=True,
                    reasoning="Output guardrail not available, allowing output"
                ),
                tripwire_triggered=False
            )

        try:
            result = await Runner.run(
                guardrail_agent,
                input=output_text,
                run_config=config
            )

            raw_output = result.final_output

            # Handle structured output (Pydantic model) - if model supports it
            if hasattr(raw_output, 'is_appropriate'):
                check_result = raw_output
            # Handle text response - parse APPROACHATE:/BLOCK: prefix
            elif isinstance(raw_output, str):
                output_stripped = raw_output.strip()

                # Check for BLOCK: or APPROPRIATE: prefix
                if output_stripped.upper().startswith("BLOCK:"):
                    is_appropriate = False
                    reasoning = output_stripped[6:].strip()  # Remove "BLOCK:" prefix
                elif output_stripped.upper().startswith("APPROPRIATE:"):
                    is_appropriate = True
                    reasoning = output_stripped[12:].strip()  # Remove "APPROPRIATE:" prefix
                else:
                    # Fallback: keyword search in full response
                    output_lower = output_stripped.lower()
                    # Block indicators (check FIRST)
                    block_keywords = ["block", "inappropriate", "offensive", "harmful", "reject", "unsafe", "sensitive data", "api key", "password"]
                    is_appropriate = not any(kw in output_lower for kw in block_keywords)
                    # Allow/confirm indicators (can override)
                    allow_keywords = ["appropriate", "allow", "safe", "good", "approve", "acceptable", "no issues"]
                    if any(kw in output_lower for kw in allow_keywords):
                        is_appropriate = True
                    reasoning = output_stripped[:500] if len(output_stripped) > 500 else output_stripped

                check_result = OutputGuardrailCheck(
                    is_appropriate=is_appropriate,
                    reasoning=reasoning
                )
            else:
                check_result = OutputGuardrailCheck(
                    is_appropriate=True,
                    reasoning=f"Unexpected output format: {type(raw_output).__name__}"
                )

            return GuardrailFunctionOutput(
                output_info=check_result,
                tripwire_triggered=not check_result.is_appropriate
            )
        except Exception as e:
            # On error, fail open but log
            return GuardrailFunctionOutput(
                output_info=OutputGuardrailCheck(
                    is_appropriate=True,
                    reasoning=f"Output guardrail check failed, allowing: {str(e)}"
                ),
                tripwire_triggered=False
            )


# Simple synchronous check for non-decorator use
def simple_output_check(output_text: str, output_object: Any = None) -> OutputGuardrailCheck:
    """
    Simple synchronous output check without AI agent.

    Args:
        output_text: Text output to check
        output_object: Optional structured output to validate

    Returns:
        OutputGuardrailCheck with results
    """
    # Check for sensitive data patterns
    sensitive_patterns = [
        ("api_key", "API key"),
        ("api-key", "API key"),
        ("apikey", "API key"),
        ("secret_key", "Secret key"),
        ("password", "Password"),
        ("token", "Auth token"),
        ("sk-", "OpenAI API key"),
        ("Bearer", "Bearer token"),
    ]

    output_lower = output_text.lower()
    for pattern, name in sensitive_patterns:
        if pattern in output_lower:
            # Could be false positive, just flag it
            return OutputGuardrailCheck(
                is_appropriate=True,  # Don't block, just note
                reasoning=f"Output may contain {name} - please review"
            )

    return OutputGuardrailCheck(
        is_appropriate=True,
        reasoning="Output passed basic checks"
    )

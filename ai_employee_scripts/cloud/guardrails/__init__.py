"""
Cloud Guardrails Module

Safety and validation checks for:
- Input validation (before agent processing)
- Output validation (before writing to vault)

Guardrails use a prefix-based response format for reliable parsing:
- Input guardrail: "BLOCK:" or "ALLOW:" prefix
- Output guardrail: "BLOCK:" or "APPROPRIATE:" prefix

This works with any model (GLM, OpenAI, etc.) without requiring structured outputs.
"""

from .input_guardrails import (
    check_input_guardrail,
    simple_input_check,
    InputGuardrailCheck,
    OPENAI_AGENTS_AVAILABLE
)
from .output_guardrails import (
    check_output_guardrail,
    simple_output_check,
    OutputGuardrailCheck
)

__all__ = [
    "check_input_guardrail",
    "simple_input_check",
    "InputGuardrailCheck",
    "check_output_guardrail",
    "simple_output_check",
    "OutputGuardrailCheck",
    "OPENAI_AGENTS_AVAILABLE"
]


def get_input_guardrails():
    """
    Get input guardrails for agent configuration.

    Returns:
        List of input guardrail functions, or empty list if not available
    """
    if OPENAI_AGENTS_AVAILABLE and check_input_guardrail is not None:
        return [check_input_guardrail]
    return []


def get_output_guardrails():
    """
    Get output guardrails for agent configuration.

    Returns:
        List of output guardrail functions, or empty list if not available
    """
    if OPENAI_AGENTS_AVAILABLE and check_output_guardrail is not None:
        return [check_output_guardrail]
    return []

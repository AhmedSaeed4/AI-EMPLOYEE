"""
Cloud Agents Module

Contains specialized agents for different task types:
- TriageAgent: Routes tasks to specialists
- EmailAgent: Drafts email replies
- SocialAgent: Drafts social media content
- FinanceAgent: Handles financial tasks
"""

from .base_agent import create_base_agent
from .models import (
    EmailDraft,
    SocialPost,
    FinanceAction,
    AgentResponse,
    TriageDecision
)

__all__ = [
    "create_base_agent",
    "EmailDraft",
    "SocialPost",
    "FinanceAction",
    "AgentResponse",
    "TriageDecision",
]

"""
Social Agent Implementation

Drafts social media content for various platforms.
Maintains platform-appropriate style and brand voice.
"""

from typing import Optional

# Try to import OpenAI Agents SDK
try:
    from agents import Agent, Runner
    from .base_agent import create_base_agent, INSTRUCTIONS
    from .models import SocialPost, SocialPlatform, ConfidenceLevel
    from ..tools.vault_tools import read_email_style
    from ..config.settings import get_settings, get_run_config
    from ..guardrails import get_input_guardrails, get_output_guardrails
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    Agent = None
    Runner = None
    OPENAI_AGENTS_AVAILABLE = False


# Global agent instance
_social_agent: Optional['Agent'] = None


def create_social_agent() -> Optional['Agent']:
    """
    Create the Social Agent for social media content.

    Returns:
        Configured Social Agent or None if SDK not available
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return None

    # Get guardrails
    # NOTE: Social agent only uses OUTPUT guardrails
    # INPUT guardrails already ran at Triage level - prevents duplicate checking
    input_guards = []  # No input guardrails (already checked by triage)
    output_guards = get_output_guardrails()

    # Note: output_type removed because GLM doesn't support strict JSON schema
    # We parse text responses manually in parse_text_to_social_post()
    agent = create_base_agent(
        name="SocialAgent",
        instructions=INSTRUCTIONS.get("social", INSTRUCTIONS["general"]),
        # output_type=SocialPost,  # DISABLED - causes GLM schema errors
        input_guardrails=None,  # No input guardrails (triage already checked)
        output_guardrails=output_guards if output_guards else None
    )

    return agent


def get_social_agent() -> Optional['Agent']:
    """Get or create the global Social Agent instance."""
    global _social_agent
    if _social_agent is None:
        _social_agent = create_social_agent()
    return _social_agent


def parse_text_to_social_post(text: str, platform: SocialPlatform, post_type: str = "post") -> SocialPost:
    """
    Parse a text response from GLM into a SocialPost.
    Extracts post components from markdown/text format.

    Args:
        text: Raw text response from GLM
        platform: Target platform (use the passed platform, don't extract from text)
        post_type: Type of post (post, reply, comment)

    Returns:
        SocialPost with extracted or default values
    """
    import re

    # Extract content - look for main body text
    content = text
    hashtags = []

    # Try to find the actual post content (skip headers/metadata)
    lines = text.split('\n')
    content_lines = []
    in_content = False

    for line in lines:
        # Skip metadata headers
        if any(x in line.lower() for x in ['platform:', 'type:', 'character count:', 'confidence:', 'action:', 'suggested']):
            continue
        # Look for content start
        if 'content:' in line.lower() or in_content:
            if 'content:' in line.lower():
                in_content = True
                continue
            # Stop at end markers
            if any(x in line.lower() for x in ['---', 'hashtags:', 'character count:']):
                break
            # Extract hashtags
            if line.strip().startswith('#'):
                tags = [tag.strip() for tag in line.split('#') if tag.strip() and not tag.strip().isdigit()]
                hashtags.extend(tags)
            else:
                content_lines.append(line)

    # If we found content lines, use them; otherwise use cleaned original text
    if content_lines:
        content = '\n'.join(content_lines).strip()
    else:
        # Fallback: remove common headers from original text
        cleaned_lines = []
        skip_until_content = False
        for line in lines:
            if 'content:' in line.lower():
                skip_until_content = False
                continue
            if any(x in line.lower() for x in ['platform:', 'type:', 'confidence:', 'action:']):
                skip_until_content = True
                continue
            if not skip_until_content:
                cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines).strip()

    # Extract hashtags from content if they're at the end
    hashtag_pattern = r'#(\w+)'
    all_hashtags = re.findall(hashtag_pattern, content)
    if all_hashtags:
        hashtags = list(set(hashtags + all_hashtags))

    # Clean up hashtags from content (optional - keep them if they look good)
    # for tag in hashtags:
    #     content = content.replace(f'#{tag}', '').strip()

    # Ensure platform is an enum, not a string
    if isinstance(platform, str):
        platform = SocialPlatform(platform.lower())

    # Create the post
    return SocialPost(
        platform=platform,
        content=content[:280] if platform == SocialPlatform.TWITTER else content,
        hashtags=hashtags,
        confidence=ConfidenceLevel.MEDIUM,
        needs_approval=True,
        post_type=post_type,
        character_count=len(content)
    )


async def draft_social_post(
    content_request: str,
    platform: SocialPlatform = SocialPlatform.LINKEDIN,
    post_type: str = "post",
    context: str = ""
) -> SocialPost:
    """
    Draft a social media post.

    Args:
        content_request: What the post should be about
        platform: Target platform
        post_type: Type of content (post, reply, comment)
        context: Additional context

    Returns:
        SocialPost with the draft content
    """
    if not OPENAI_AGENTS_AVAILABLE:
        # Fallback: simple template
        return SocialPost(
            platform=platform,
            content=content_request[:280] if platform == SocialPlatform.TWITTER else content_request,
            confidence=ConfidenceLevel.LOW,
            needs_approval=True
        )

    agent = get_social_agent()
    if agent is None:
        return SocialPost(
            platform=platform,
            content="Error: Social agent not available.",
            confidence=ConfidenceLevel.LOW,
            needs_approval=True
        )

    try:
        settings = get_settings()
        config = get_run_config(settings)

        # Platform-specific guidance
        platform_limits = {
            SocialPlatform.TWITTER: "Max 280 characters for posts",
            SocialPlatform.LINKEDIN: "Professional tone, 3,000 character limit",
            SocialPlatform.FACEBOOK: "Engaging, conversational",
            SocialPlatform.INSTAGRAM: "Visual-friendly, use hashtags"
        }

        input_text = f"""Draft a {post_type} for {platform.value}.

Request: {content_request}

Platform Guidelines: {platform_limits.get(platform, 'Standard platform style')}
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
            return parse_text_to_social_post(raw_output, platform, post_type)
        else:
            # It's already a Pydantic model
            post = raw_output
            if post.platform != platform:
                post.platform = platform
            return post

    except Exception as e:
        return SocialPost(
            platform=platform,
            content=f"Error generating draft: {str(e)}",
            confidence=ConfidenceLevel.LOW,
            needs_approval=True
        )


async def draft_social_reply(
    original_post: str,
    reply_intent: str,
    platform: SocialPlatform = SocialPlatform.TWITTER,
    context: str = ""
) -> SocialPost:
    """
    Draft a reply to a social media post.

    Args:
        original_post: The post being replied to
        reply_intent: What the reply should convey
        platform: Target platform
        context: Additional context

    Returns:
        SocialPost with the reply draft
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return SocialPost(
            platform=platform,
            content=reply_intent[:280],
            post_type="reply",
            confidence=ConfidenceLevel.LOW
        )

    agent = get_social_agent()
    if agent is None:
        return SocialPost(
            platform=platform,
            content="Error: Social agent not available.",
            post_type="reply",
            confidence=ConfidenceLevel.LOW
        )

    try:
        settings = get_settings()
        config = get_run_config(settings)

        input_text = f"""Draft a reply for {platform.value}.

Original Post:
{original_post}

Reply Intent:
{reply_intent}
"""

        if context:
            input_text += f"\nAdditional Context:\n{context}"

        result = await Runner.run(
            agent,
            input=input_text,
            run_config=config
        )

        post = result.final_output
        post.post_type = "reply"
        if post.platform != platform:
            post.platform = platform

        return post

    except Exception as e:
        return SocialPost(
            platform=platform,
            content=f"Error: {str(e)}",
            post_type="reply",
            confidence=ConfidenceLevel.LOW
        )

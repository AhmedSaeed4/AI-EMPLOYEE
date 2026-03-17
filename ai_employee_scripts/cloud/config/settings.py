"""
Cloud Configuration Settings

Environment-based configuration for cloud agents.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Load .env file first
from dotenv import load_dotenv
# Try to load .env from the parent directory (ai_employee_scripts)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to loading from default locations
    load_dotenv()

# Try to import OpenAI Agents SDK components
try:
    from openai import AsyncOpenAI
    from agents import OpenAIChatCompletionsModel, RunConfig
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OpenAIChatCompletionsModel = None
    RunConfig = None
    OPENAI_AGENTS_AVAILABLE = False


@dataclass
class Settings:
    """Cloud agent configuration settings."""

    # API Configuration - GLM (Zhipu AI)
    glm_api_key: str = field(default_factory=lambda: os.getenv("GLM", ""))
    glm_base_url: str = field(default_factory=lambda: os.getenv("GLM_BASE_URL", "https://api.z.ai/v1/chat/completions"))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "glm-4.7-flash"))

    # OpenAI API Key (for testing)
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # Legacy Xiaomi fields (kept for compatibility)
    xiaomi_api_key: str = ""
    xiaomi_base_url: str = "https://api.xiaomimimo.com/v1/"

    # Vault Configuration
    vault_path: Path = field(default_factory=lambda: Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")))
    needs_action_folder: str = "Needs_Action"
    updates_folder: str = "Updates"  # Kept for backward compatibility
    pending_approval_folder: str = "Pending_Approval"  # Cloud writes drafts here
    in_progress_folder: str = "In_Progress"

    # Agent Configuration
    agent_type: str = field(default_factory=lambda: os.getenv("AGENT_TYPE", "cloud"))
    polling_interval: int = field(default_factory=lambda: int(os.getenv("POLLING_INTERVAL", "30")))
    max_retries: int = 3
    retry_delay: int = 5

    # Git Configuration
    git_remote: str = field(default_factory=lambda: os.getenv("GIT_REMOTE", "origin"))
    git_auto_sync: bool = field(default_factory=lambda: os.getenv("GIT_AUTO_SYNC", "true").lower() == "true")
    git_sync_interval: int = field(default_factory=lambda: int(os.getenv("GIT_SYNC_INTERVAL", "300")))

    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))

    def __post_init__(self):
        """Validate settings after initialization."""
        # Use GLM API key as the primary API key
        if self.glm_api_key:
            self.xiaomi_api_key = self.glm_api_key  # For backward compatibility
        # Only require API key if we're actually going to use the AI features
        # For testing and development, we can work without it
        pass

        # Ensure vault_path is a Path object
        if not isinstance(self.vault_path, Path):
            self.vault_path = Path(self.vault_path)

    @property
    def needs_action_path(self) -> Path:
        """Full path to Needs_Action folder."""
        return self.vault_path / self.needs_action_folder

    @property
    def updates_path(self) -> Path:
        """Full path to Updates folder (kept for backward compatibility)."""
        return self.vault_path / self.updates_folder

    @property
    def pending_approval_path(self) -> Path:
        """Full path to Pending_Approval folder (cloud writes drafts here)."""
        return self.vault_path / self.pending_approval_folder

    @property
    def in_progress_path(self) -> Path:
        """Full path to In_Progress folder."""
        return self.vault_path / self.in_progress_folder

    @property
    def cloud_progress_path(self) -> Path:
        """Full path to cloud working folder."""
        return self.in_progress_path / "cloud"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_model_client(settings: Optional[Settings] = None) -> Optional[AsyncOpenAI]:
    """
    Create and return an AsyncOpenAI client configured for GLM (Zhipu AI) API.

    Also returns a trace client if OPENAI_API_KEY is set for tracing/observability.

    Args:
        settings: Optional settings object. Uses global settings if not provided.

    Returns:
        AsyncOpenAI client or None if openai-agents is not installed
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return None

    if settings is None:
        settings = get_settings()

    # GLM for response
    api_key = settings.glm_api_key or settings.xiaomi_api_key
    base_url = settings.glm_base_url

    # OpenAI for trace (parallel - doesn't affect GLM response)
    if settings.openai_api_key:
        import os
        os.environ["OPENAI_API_KEY_FOR_TRACE"] = settings.openai_api_key

    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )


def get_run_config(
    settings: Optional[Settings] = None,
    client: Optional[AsyncOpenAI] = None
) -> Optional['RunConfig']:
    """
    Create and return a RunConfig for agent execution.

    Args:
        settings: Optional settings object. Uses global settings if not provided.
        client: Optional AsyncOpenAI client. Creates new one if not provided.

    Returns:
        RunConfig object or None if openai-agents is not installed
    """
    if not OPENAI_AGENTS_AVAILABLE:
        return None

    if settings is None:
        settings = get_settings()

    if client is None:
        client = get_model_client(settings)

    model = OpenAIChatCompletionsModel(
        model=settings.model_name,
        openai_client=client
    )

    return RunConfig(
        model=model,
        model_provider=client,
    )

"""LLM configuration for EasyTicket AI services."""

from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """Runtime settings for Gemini-backed AI services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
        description="API key used for live Gemini requests.",
    )
    gemini_model_name: str = Field(
        default="gemini-2.5-flash",
        validation_alias="GEMINI_MODEL_NAME",
        description="Gemini model used by EasyTicket AI services.",
    )
    ai_request_timeout_seconds: float = Field(
        default=30.0,
        validation_alias="AI_REQUEST_TIMEOUT_SECONDS",
        gt=0,
        description="Timeout for outbound AI requests.",
    )
    mock_ai_mode: bool = Field(
        default=True,
        validation_alias=AliasChoices("USE_MOCK_AI", "MOCK_AI_MODE"),
        description="When true, AI services should return deterministic mock output.",
    )

    @field_validator("gemini_model_name")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("GEMINI_MODEL_NAME cannot be empty.")
        return normalized

    @model_validator(mode="after")
    def require_api_key_for_live_mode(self) -> "LLMConfig":
        if not self.mock_ai_mode and self.gemini_api_key is None:
            raise ValueError("GEMINI_API_KEY is required when MOCK_AI_MODE=false.")
        return self

    @property
    def is_live_mode(self) -> bool:
        return not self.mock_ai_mode


@lru_cache
def get_llm_config() -> LLMConfig:
    """Return cached LLM configuration for app-wide reuse."""

    return LLMConfig()

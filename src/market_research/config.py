"""Validated configuration; never log raw credential values."""
from pathlib import Path
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8-sig",
        extra="ignore", hide_input_in_errors=True,
    )
    ydc_api_key: SecretStr
    openai_api_key: SecretStr
    openai_model: str = "gpt-4.1-mini"

    @field_validator("ydc_api_key", "openai_api_key")
    @classmethod
    def validate_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw.lower().startswith(("your_", "your-", "your ")):
            raise ValueError("Set a real API key in .env or the environment")
        return SecretStr(raw)

    @field_validator("openai_model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Model name cannot be blank")
        return value.strip()

def load_settings() -> Settings:
    """Read current settings, including edits saved since the previous call."""
    return Settings()

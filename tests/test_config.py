"""Use fake credentials; never load the user's .env in tests."""
import pytest
from pydantic import ValidationError
from market_research.config import Settings

def test_dotenv_loads_and_redacts_secrets(tmp_path, monkeypatch):
    monkeypatch.delenv("YDC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("YDC_API_KEY=fake-search-secret\nOPENAI_API_KEY=fake-model-secret\n")
    settings = Settings(_env_file=env)
    assert settings.ydc_api_key.get_secret_value() == "fake-search-secret"
    assert settings.openai_api_key.get_secret_value() == "fake-model-secret"
    for output in (repr(settings), settings.model_dump_json()):
        assert "fake-search-secret" not in output
        assert "fake-model-secret" not in output

def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("YDC_API_KEY=file-value\nOPENAI_API_KEY=file-model\n")
    monkeypatch.setenv("YDC_API_KEY", "environment-value")
    settings = Settings(_env_file=env)
    assert settings.ydc_api_key.get_secret_value() == "environment-value"

@pytest.mark.parametrize("key", ["", "   ", "your_api_key_here"])
def test_invalid_key_is_rejected_without_echoing_other_secret(key):
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, ydc_api_key=key, openai_api_key="fake-private-value")
    assert "fake-private-value" not in str(exc.value)

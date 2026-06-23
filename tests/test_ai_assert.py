import pytest

from src.ai_assert import ai_assert


class TestAiAssert:
    def test_missing_openai(self):
        with pytest.raises(ImportError):
            ai_assert("response should be ok", 200, "ok", {"AI_PROVIDER": "openai"})

    def test_missing_anthropic(self):
        with pytest.raises(ImportError):
            ai_assert("response should be ok", 200, "ok", {"AI_PROVIDER": "anthropic"})

    def test_default_provider_is_openai(self):
        with pytest.raises(ImportError):
            ai_assert("response should be ok", 200, "ok", {})

    def test_invalid_provider_returns_error(self):
        with pytest.raises(ImportError):
            ai_assert("test", 200, "body", {"AI_PROVIDER": "nonexistent"})

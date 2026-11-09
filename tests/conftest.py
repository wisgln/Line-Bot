"""Keep offline tests independent from a developer's local .env settings."""

import pytest


@pytest.fixture(autouse=True)
def disable_external_ai_by_default(monkeypatch):
    """Provider-specific tests opt in explicitly with patch.dict/monkeypatch."""
    for name in (
        "OPENAI_ENABLED",
        "OPENAI_API_KEY",
        "GROQ_ENABLED",
        "GROQ_API_KEY",
        "GEMINI_ENABLED",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

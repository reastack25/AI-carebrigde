import pytest

from app.config import Config


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        ("AI_RATE_LIMIT", 0, "AI_RATE_LIMIT must be greater than zero"),
        ("AI_RATE_LIMIT", -1, "AI_RATE_LIMIT must be greater than zero"),
        ("AI_RATE_WINDOW_SECONDS", 0, "AI_RATE_WINDOW_SECONDS must be greater than zero"),
        ("AI_RATE_WINDOW_SECONDS", -1, "AI_RATE_WINDOW_SECONDS must be greater than zero"),
    ],
)
def test_validate_rejects_non_positive_ai_rate_limit_settings(
    monkeypatch, attribute, value, message
):
    monkeypatch.setattr(Config, attribute, value)

    with pytest.raises(RuntimeError, match=message):
        Config.validate()

from unittest.mock import patch

from tests.helpers import register_and_login


def test_ai_rate_limit_rejects_request_before_ai_processing(client, monkeypatch):
    from app.config import Config

    monkeypatch.setattr(Config, "AI_RATE_LIMIT", 1)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", 60)
    token = register_and_login(client, "rate-limit-processing@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.routes.ai.generate_health_chat_response", return_value="response") as generate:
        first = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "First request"},
        )
        assert first.status_code == 200
        assert generate.call_count == 1

        blocked = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "Second request"},
        )

    assert blocked.status_code == 429
    assert generate.call_count == 1

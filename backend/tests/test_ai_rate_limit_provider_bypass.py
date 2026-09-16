from unittest.mock import patch

from tests.helpers import register_and_login


def test_rate_limited_symptom_check_skips_ai_provider(client, monkeypatch):
    from app.config import Config

    monkeypatch.setattr(Config, "AI_RATE_LIMIT", 1)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", 60)
    token = register_and_login(client, "rate-limit-symptom-provider@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    result = {
        "urgency": "routine",
        "summary": "Response",
        "possible_explanations": [],
        "next_steps": [],
        "red_flags": [],
        "disclaimer": "Not a diagnosis.",
    }

    with patch("app.routes.ai.generate_symptom_check_response", return_value=result) as generate:
        first = client.post(
            "/api/ai/symptom-check",
            headers=headers,
            json={"symptoms": "headache"},
        )
        assert first.status_code == 200
        assert generate.call_count == 1

        blocked = client.post(
            "/api/ai/symptom-check",
            headers=headers,
            json={"symptoms": "fever"},
        )

    assert blocked.status_code == 429
    assert generate.call_count == 1

from io import BytesIO
from unittest.mock import patch

from tests.helpers import register_and_login


def auth_headers(client, email):
    token = register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


def test_ai_rate_limit_is_shared_across_ai_endpoints(client, monkeypatch):
    from app.config import Config

    monkeypatch.setattr(Config, "AI_RATE_LIMIT", 1)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", 60)
    headers = auth_headers(client, "rate-limit-cross-endpoint@example.com")
    symptom_result = {
        "urgency": "routine",
        "summary": "Response",
        "possible_explanations": [],
        "next_steps": [],
        "red_flags": [],
        "disclaimer": "Not a diagnosis.",
    }

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        first = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "First request"},
        )
    assert first.status_code == 200

    with patch("app.routes.ai.generate_symptom_check_response", return_value=symptom_result):
        blocked_symptom = client.post(
            "/api/ai/symptom-check",
            headers=headers,
            json={"symptoms": "headache"},
        )
    assert blocked_symptom.status_code == 429

    second_headers = auth_headers(client, "rate-limit-cross-endpoint-document@example.com")
    with patch("app.routes.ai.generate_symptom_check_response", return_value=symptom_result):
        symptom = client.post(
            "/api/ai/symptom-check",
            headers=second_headers,
            json={"symptoms": "fever"},
        )
    assert symptom.status_code == 200

    with patch("app.routes.ai.analyze_health_document", return_value="Report"):
        blocked_document = client.post(
            "/api/ai/analyze-image",
            headers=second_headers,
            data={"image": (BytesIO(b"\x89PNG\r\n\x1a\nvalid"), "report.png")},
            content_type="multipart/form-data",
        )
    assert blocked_document.status_code == 429

from io import BytesIO
from unittest.mock import patch

from tests.helpers import register_and_login


def auth_headers(client, email="rate-limit@example.com"):
    token = register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


def configure_rate_limit(monkeypatch, limit=1, window_seconds=3600):
    from app.config import Config

    monkeypatch.setattr(Config, "AI_RATE_LIMIT", limit)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", window_seconds)


def test_ai_chat_returns_429_after_rate_limit(client, monkeypatch):
    configure_rate_limit(monkeypatch)
    headers = auth_headers(client)

    with patch("app.routes.ai.generate_health_chat_response", return_value="response") as mocked_gemini:
        first = client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        second = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.get_json()["message"] == "AI request limit exceeded. Please try again later."
    assert second.get_json()["retry_after_seconds"] == 3600
    assert second.headers["Retry-After"] == "3600"
    assert mocked_gemini.call_count == 1


def test_ai_rate_limit_is_per_user(client, monkeypatch):
    configure_rate_limit(monkeypatch)
    first_headers = auth_headers(client, "rate-limit-first@example.com")
    second_headers = auth_headers(client, "rate-limit-second@example.com")

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        first = client.post("/api/ai/chat", headers=first_headers, json={"message": "First user"})
        second = client.post("/api/ai/chat", headers=second_headers, json={"message": "Second user"})

    assert first.status_code == 200
    assert second.status_code == 200


def test_ai_rate_limit_applies_to_symptom_check_and_document_analysis(client, monkeypatch):
    configure_rate_limit(monkeypatch)
    headers = auth_headers(client, "rate-limit-endpoints@example.com")

    symptom_result = {
        "urgency": "routine",
        "summary": "Response",
        "possible_explanations": [],
        "next_steps": [],
        "red_flags": [],
        "disclaimer": "Not a diagnosis.",
    }
    with patch("app.routes.ai.generate_symptom_check_response", return_value=symptom_result):
        symptom = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "headache"})
        blocked = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "fever"})

    assert symptom.status_code == 200
    assert blocked.status_code == 429

    second_headers = auth_headers(client, "rate-limit-document@example.com")
    with patch("app.routes.ai.analyze_health_document", return_value="Report"):
        document = client.post(
            "/api/ai/analyze-image",
            headers=second_headers,
            data={"image": (BytesIO(b"\x89PNG\r\n\x1a\nvalid"), "report.png")},
            content_type="multipart/form-data",
        )
        blocked_document = client.post(
            "/api/ai/analyze-image",
            headers=second_headers,
            data={"image": (BytesIO(b"\x89PNG\r\n\x1a\nvalid"), "report.png")},
            content_type="multipart/form-data",
        )

    assert document.status_code == 200
    assert blocked_document.status_code == 429


def test_ai_rate_limit_window_is_configurable(client, monkeypatch):
    configure_rate_limit(monkeypatch, limit=1, window_seconds=120)
    headers = auth_headers(client, "rate-limit-window@example.com")

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        blocked = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert blocked.status_code == 429
    assert blocked.get_json()["retry_after_seconds"] == 120
    assert blocked.headers["Retry-After"] == "120"

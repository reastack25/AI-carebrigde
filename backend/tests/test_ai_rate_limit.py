from datetime import datetime, timedelta, timezone
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


def assert_rate_limit_response(response, window_seconds):
    assert response.status_code == 429
    retry_after = response.get_json()["retry_after_seconds"]
    assert 1 <= retry_after <= window_seconds
    assert response.headers["Retry-After"] == str(retry_after)


def test_ai_chat_returns_429_after_rate_limit(client, monkeypatch):
    configure_rate_limit(monkeypatch)
    headers = auth_headers(client)

    with patch("app.routes.ai.generate_health_chat_response", return_value="response") as mocked_gemini:
        first = client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        second = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert first.status_code == 200
    assert_rate_limit_response(second, 3600)
    assert second.get_json()["message"] == "AI request limit exceeded. Please try again later."
    assert mocked_gemini.call_count == 1


def test_ai_rate_limit_logs_violation(client, monkeypatch, caplog):
    configure_rate_limit(monkeypatch)
    headers = auth_headers(client, "rate-limit-logging@example.com")

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        with caplog.at_level("WARNING", logger="app.services.ai_rate_limit"):
            blocked = client.post(
                "/api/ai/chat",
                headers=headers,
                json={"message": "Second request"},
            )

    assert blocked.status_code == 429
    assert "AI rate limit exceeded" in caplog.text
    assert "/api/ai/chat" in caplog.text
    assert "limit=1" in caplog.text


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
    assert_rate_limit_response(blocked, 3600)

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
    assert_rate_limit_response(blocked_document, 3600)


def test_ai_rate_limit_window_is_configurable(client, monkeypatch):
    configure_rate_limit(monkeypatch, limit=1, window_seconds=120)
    headers = auth_headers(client, "rate-limit-window@example.com")

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        blocked = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert_rate_limit_response(blocked, 120)


def test_ai_rate_limit_ignores_requests_outside_window(client, monkeypatch):
    configure_rate_limit(monkeypatch, limit=1, window_seconds=60)
    headers = auth_headers(client, "rate-limit-expired@example.com")

    from app.extensions import db
    from app.models import Message

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        first = client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        assert first.status_code == 200

        user_message = db.session.query(Message).filter_by(sender="user").order_by(Message.id.desc()).first()
        user_message.created_at = datetime.now(timezone.utc) - timedelta(seconds=61)
        db.session.commit()

        second = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert second.status_code == 200


def test_ai_rate_limit_does_not_apply_to_get_requests(client, monkeypatch):
    configure_rate_limit(monkeypatch)

    response = client.get("/api/ai/chat")

    assert response.status_code == 405
    assert response.status_code != 429


def test_ai_rate_limit_does_not_apply_to_unrelated_post_requests(client, monkeypatch):
    configure_rate_limit(monkeypatch)

    response = client.post("/api/auth/login", json={})

    assert response.status_code == 401
    assert response.status_code != 429

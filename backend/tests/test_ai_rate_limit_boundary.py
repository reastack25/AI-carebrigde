from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from tests.helpers import register_and_login


class FixedDateTime(datetime):
    current = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls.current.replace(tzinfo=None)
        return cls.current.astimezone(tz)


def test_ai_rate_limit_includes_request_at_window_cutoff(client, monkeypatch):
    from app.config import Config
    from app.extensions import db
    from app.models import Message

    monkeypatch.setattr(Config, "AI_RATE_LIMIT", 1)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", 60)
    token = register_and_login(client, "rate-limit-boundary@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        first = client.post("/api/ai/chat", headers=headers, json={"message": "First request"})
        assert first.status_code == 200

        user_message = db.session.query(Message).filter_by(sender="user").order_by(Message.id.desc()).first()
        user_message.created_at = FixedDateTime.current - timedelta(seconds=60)
        db.session.commit()

        with patch("app.services.ai_rate_limit.datetime", FixedDateTime):
            blocked = client.post("/api/ai/chat", headers=headers, json={"message": "Second request"})

    assert blocked.status_code == 429

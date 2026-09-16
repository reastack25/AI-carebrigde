import logging
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func, select

from ..config import Config
from ..extensions import db
from ..models import Conversation, Message

logger = logging.getLogger(__name__)

AI_RATE_LIMITED_PATHS = {
    "/api/ai/chat",
    "/api/ai/symptom-check",
    "/api/ai/analyze-image",
}


def enforce_ai_rate_limit():
    if request.method != "POST" or request.path not in AI_RATE_LIMITED_PATHS:
        return None

    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    window_seconds = Config.AI_RATE_WINDOW_SECONDS
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    recent_requests = db.session.scalar(
        select(func.count(Message.id))
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user_id,
            Message.sender == "user",
            Message.created_at >= cutoff,
        )
    ) or 0

    if recent_requests >= Config.AI_RATE_LIMIT:
        logger.warning(
            "AI rate limit exceeded: user_id=%s path=%s recent_requests=%s limit=%s window_seconds=%s",
            user_id,
            request.path,
            recent_requests,
            Config.AI_RATE_LIMIT,
            window_seconds,
        )
        response = jsonify(
            {
                "message": "AI request limit exceeded. Please try again later.",
                "retry_after_seconds": window_seconds,
            }
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(window_seconds)
        return response

    return None

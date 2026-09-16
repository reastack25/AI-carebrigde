import logging
import math
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
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=window_seconds)

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
        oldest_request = db.session.scalar(
            select(func.min(Message.created_at))
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == user_id,
                Message.sender == "user",
                Message.created_at >= cutoff,
            )
        )
        retry_after = window_seconds
        if oldest_request is not None:
            if oldest_request.tzinfo is None:
                oldest_request = oldest_request.replace(tzinfo=timezone.utc)
            retry_after = max(
                1,
                math.ceil(
                    (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()
                ),
            )

        logger.warning(
            "AI rate limit exceeded: user_id=%s path=%s recent_requests=%s limit=%s window_seconds=%s retry_after=%s",
            user_id,
            request.path,
            recent_requests,
            Config.AI_RATE_LIMIT,
            window_seconds,
            retry_after,
        )
        response = jsonify(
            {
                "message": "AI request limit exceeded. Please try again later.",
                "retry_after_seconds": retry_after,
            }
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    return None

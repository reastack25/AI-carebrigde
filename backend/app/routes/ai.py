from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from ..extensions import db
from ..models import Conversation, Message
from ..services.gemini_service import GeminiServiceError, analyze_health_document, generate_health_chat_response

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
SUPPORTED_LANGUAGES = {"en", "sw", "luo", "kik", "kal"}
ALLOWED_DOCUMENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}


def _language():
    data = (request.get_json(silent=True) or {}) if request.is_json else {}
    language = data.get("language", "en") if request.is_json else request.form.get("language", "en")
    return language if language in SUPPORTED_LANGUAGES else "en"


def _conversation(user_id, conversation_id=None, title="Health conversation"):
    conversation = db.session.get(Conversation, conversation_id) if conversation_id else None
    if conversation and conversation.user_id != user_id:
        return None
    if not conversation:
        conversation = Conversation(user_id=user_id, title=title[:200] or "Health conversation")
        db.session.add(conversation)
        db.session.flush()
    return conversation


@ai_bp.get("/conversations")
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    conversations = db.session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    ).all()
    return jsonify({"conversations": [item.to_dict(include_messages=False) for item in conversations]}), 200


@ai_bp.get("/timeline")
@jwt_required()
def health_timeline():
    user_id = int(get_jwt_identity())
    conversations = db.session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    ).all()
    entries = []
    for conversation in conversations:
        messages = conversation.messages
        entries.append({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "message_count": len(messages),
            "last_message": messages[-1].content[:180] if messages else "No messages yet",
        })
    return jsonify({"timeline": entries}), 200


@ai_bp.get("/conversations/<int:conversation_id>")
@jwt_required()
def get_conversation(conversation_id):
    conversation = db.session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != int(get_jwt_identity()):
        return jsonify({"message": "conversation not found"}), 404
    return jsonify({"conversation": conversation.to_dict()}), 200


@ai_bp.post("/chat")
@jwt_required()
def health_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"message": "message is required"}), 400
    if len(message) > 4000:
        return jsonify({"message": "message must not exceed 4000 characters"}), 400
    language = data.get("language", "en") if data.get("language", "en") in SUPPORTED_LANGUAGES else "en"
    user_id = int(get_jwt_identity())
    try:
        response = generate_health_chat_response(message, language)
        conversation = _conversation(user_id, data.get("conversation_id"), message[:60])
        if not conversation:
            return jsonify({"message": "conversation not found"}), 404
        db.session.add(Message(conversation_id=conversation.id, sender="user", content=message, language=language))
        db.session.add(Message(conversation_id=conversation.id, sender="assistant", content=response, language=language))
        db.session.commit()
    except GeminiServiceError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 503
    except Exception:
        db.session.rollback()
        return jsonify({"message": "AI service is temporarily unavailable"}), 502
    return jsonify({"response": response, "conversation": conversation.to_dict()}), 200


@ai_bp.post("/analyze-image")
@jwt_required()
def analyze_image():
    uploaded_file = request.files.get("image")
    instruction = request.form.get("instruction", "").strip()
    language = _language()
    conversation_id = request.form.get("conversation_id", "").strip()
    if conversation_id and not conversation_id.isdigit():
        return jsonify({"message": "conversation_id must be an integer"}), 400
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"message": "document file is required"}), 400
    mime_type = uploaded_file.mimetype or ""
    if mime_type not in ALLOWED_DOCUMENT_TYPES:
        return jsonify({"message": "unsupported document type"}), 415
    file_bytes = uploaded_file.read()
    if not file_bytes:
        return jsonify({"message": "uploaded document is empty"}), 400
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({"message": "document must not exceed 10 MB"}), 413
    user_id = int(get_jwt_identity())
    try:
        response = analyze_health_document(file_bytes, mime_type, instruction, language)
        conversation = _conversation(user_id, int(conversation_id) if conversation_id else None, f"Document analysis: {uploaded_file.filename}")
        if not conversation:
            return jsonify({"message": "conversation not found"}), 404
        user_content = f"Document uploaded: {uploaded_file.filename}"
        if instruction:
            user_content += f"\nInstruction: {instruction}"
        db.session.add(Message(conversation_id=conversation.id, sender="user", content=user_content, language=language))
        db.session.add(Message(conversation_id=conversation.id, sender="assistant", content=response, language=language))
        db.session.commit()
    except GeminiServiceError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 503
    except Exception:
        db.session.rollback()
        return jsonify({"message": "AI document analysis is temporarily unavailable"}), 502
    return jsonify({"response": response, "conversation": conversation.to_dict()}), 200

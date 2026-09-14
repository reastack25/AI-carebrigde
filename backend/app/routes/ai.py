from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from ..extensions import db
from ..models import Conversation, Message
from ..services.gemini_service import GeminiServiceError, analyze_health_document, generate_health_chat_response, generate_symptom_check_response

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
SUPPORTED_LANGUAGES = {"en", "sw", "luo", "kik", "kal"}
ALLOWED_DOCUMENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}
MAX_MESSAGE_LENGTH = 4000
MAX_INSTRUCTION_LENGTH = 1000
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


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


def _conversation_id(value):
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise ValueError("conversation_id must be a positive integer")
    return int(value)


@ai_bp.get("/conversations")
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    conversations = db.session.scalars(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc())).all()
    return jsonify({"conversations": [item.to_dict(include_messages=False) for item in conversations]}), 200


@ai_bp.get("/timeline")
@jwt_required()
def health_timeline():
    user_id = int(get_jwt_identity())
    conversations = db.session.scalars(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).limit(10)).all()
    entries = []
    for conversation in conversations:
        messages = conversation.messages
        entries.append({"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at.isoformat(), "message_count": len(messages), "last_message": messages[-1].content[:180] if messages else "No messages yet"})
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
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"message": "message is required"}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"message": "message must not exceed 4000 characters"}), 400
    try:
        conversation_id = _conversation_id(data.get("conversation_id"))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    language = data.get("language", "en") if data.get("language", "en") in SUPPORTED_LANGUAGES else "en"
    user_id = int(get_jwt_identity())
    try:
        response = generate_health_chat_response(message, language)
        conversation = _conversation(user_id, conversation_id, message[:60])
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


@ai_bp.post("/symptom-check")
@jwt_required()
def symptom_check():
    data = request.get_json(silent=True) or {}
    symptoms = str(data.get("symptoms", "")).strip()
    age = str(data.get("age", "")).strip()
    duration = str(data.get("duration", "")).strip()
    if not symptoms:
        return jsonify({"message": "symptoms are required"}), 400
    if len(symptoms) > MAX_MESSAGE_LENGTH:
        return jsonify({"message": "symptoms must not exceed 4000 characters"}), 400
    if age and (not age.isdigit() or not 0 < int(age) <= 120):
        return jsonify({"message": "age must be a number between 1 and 120"}), 400
    try:
        conversation_id = _conversation_id(data.get("conversation_id"))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    language = data.get("language", "en") if data.get("language", "en") in SUPPORTED_LANGUAGES else "en"
    user_id = int(get_jwt_identity())
    try:
        result = generate_symptom_check_response(symptoms, age, duration, language)
        conversation = _conversation(user_id, conversation_id, "Symptom check")
        if not conversation:
            return jsonify({"message": "conversation not found"}), 404
        db.session.add(Message(conversation_id=conversation.id, sender="user", content=f"Symptoms: {symptoms}", language=language))
        db.session.add(Message(conversation_id=conversation.id, sender="assistant", content=result["summary"], language=language))
        db.session.commit()
        return jsonify({"result": result, "conversation": conversation.to_dict()}), 200
    except GeminiServiceError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 503
    except Exception:
        db.session.rollback()
        return jsonify({"message": "AI symptom checking is temporarily unavailable"}), 502


@ai_bp.post("/analyze-image")
@jwt_required()
def analyze_image():
    uploaded_file = request.files.get("image")
    instruction = request.form.get("instruction", "").strip()
    language = _language()
    try:
        conversation_id = _conversation_id(request.form.get("conversation_id", "").strip())
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    if len(instruction) > MAX_INSTRUCTION_LENGTH:
        return jsonify({"message": "instruction must not exceed 1000 characters"}), 400
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"message": "document file is required"}), 400
    mime_type = uploaded_file.mimetype or ""
    if mime_type not in ALLOWED_DOCUMENT_TYPES:
        return jsonify({"message": "unsupported document type"}), 415
    file_bytes = uploaded_file.read()
    if not file_bytes:
        return jsonify({"message": "uploaded document is empty"}), 400
    if len(file_bytes) > MAX_DOCUMENT_SIZE:
        return jsonify({"message": "document must not exceed 10 MB"}), 413
    user_id = int(get_jwt_identity())
    try:
        response = analyze_health_document(file_bytes, mime_type, instruction, language)
        conversation = _conversation(user_id, conversation_id, f"Document analysis: {uploaded_file.filename}")
        if not conversation:
            return jsonify({"message": "conversation not found"}), 404
        user_content = f"Document uploaded: {uploaded_file.filename}" + (f"\nInstruction: {instruction}" if instruction else "")
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

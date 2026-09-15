from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from ..extensions import db
from ..models import Conversation, HealthTimelineEvent, Medication, Message
from ..services.gemini_service import GeminiServiceError, extract_medications_from_document

medications_bp = Blueprint("medications", __name__, url_prefix="/api/ai")

SUPPORTED_LANGUAGES = {"en", "sw", "luo", "kik", "kal"}
ALLOWED_DOCUMENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}
MAX_INSTRUCTION_LENGTH = 1000
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


def _conversation(user_id, conversation_id=None):
    conversation = db.session.get(Conversation, conversation_id) if conversation_id else None
    if conversation and conversation.user_id != user_id:
        return None
    if not conversation:
        conversation = Conversation(user_id=user_id, title="Medication extraction")
        db.session.add(conversation)
        db.session.flush()
    return conversation


def _conversation_id(value):
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise ValueError("conversation_id must be a positive integer")
    return int(value)


@medications_bp.get("/medications")
@jwt_required()
def list_medications():
    user_id = int(get_jwt_identity())
    records = db.session.scalars(
        select(Medication)
        .where(Medication.user_id == user_id)
        .order_by(Medication.created_at.desc())
        .limit(50)
    ).all()
    return jsonify({"medications": [record.to_dict() for record in records]}), 200


@medications_bp.post("/extract-medications")
@jwt_required()
def extract_medications():
    uploaded_file = request.files.get("image")
    instruction = request.form.get("instruction", "").strip()
    language = request.form.get("language", "en")
    language = language if language in SUPPORTED_LANGUAGES else "en"

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
    conversation = _conversation(user_id, conversation_id)
    if not conversation:
        return jsonify({"message": "conversation not found"}), 404

    try:
        medications = extract_medications_from_document(file_bytes, mime_type, instruction, language)
        user_content = f"Medication document uploaded: {uploaded_file.filename}"
        if instruction:
            user_content += f"\nInstruction: {instruction}"
        db.session.add(Message(conversation_id=conversation.id, sender="user", content=user_content, language=language))

        records = []
        for item in medications:
            record = Medication(
                user_id=user_id,
                conversation_id=conversation.id,
                name=item["name"],
                dosage=item["dosage"] or None,
                frequency=item["frequency"] or None,
                duration=item["duration"] or None,
                instructions=item["instructions"] or None,
                warnings=[item["warnings"]] if item["warnings"] else [],
                source_filename=uploaded_file.filename[:255],
                language=language,
            )
            db.session.add(record)
            records.append(record)

        db.session.flush()
        summary = f"Extracted {len(records)} medication(s) from {uploaded_file.filename}."
        db.session.add(Message(conversation_id=conversation.id, sender="assistant", content=summary, language=language))
        db.session.add(
            HealthTimelineEvent(
                user_id=user_id,
                conversation_id=conversation.id,
                event_type="medication_extraction",
                title="Medication extraction",
                summary=summary,
                event_metadata={
                    "record_ids": [record.id for record in records],
                    "count": len(records),
                    "filename": uploaded_file.filename,
                    "language": language,
                },
            )
        )
        db.session.commit()
        return jsonify({"medications": medications, "records": [record.to_dict() for record in records], "conversation": conversation.to_dict()}), 200
    except GeminiServiceError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 503
    except Exception:
        db.session.rollback()
        return jsonify({"message": "AI medication extraction is temporarily unavailable"}), 502

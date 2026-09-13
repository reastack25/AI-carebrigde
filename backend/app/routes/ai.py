from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..services.gemini_service import (
    GeminiServiceError,
    analyze_health_image,
    generate_health_chat_response,
)

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
SUPPORTED_LANGUAGES = {"en", "sw", "luo", "kik", "kal"}


def _language():
    language = request.get_json(silent=True).get("language", "en") if request.is_json else request.form.get("language", "en")
    return language if language in SUPPORTED_LANGUAGES else "en"


@ai_bp.post("/chat")
@jwt_required()
def health_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"message": "message is required"}), 400
    if len(message) > 4000:
        return jsonify({"message": "message must not exceed 4000 characters"}), 400
    try:
        response = generate_health_chat_response(message, data.get("language", "en"))
    except GeminiServiceError as error:
        return jsonify({"message": str(error)}), 503
    except Exception:
        return jsonify({"message": "AI service is temporarily unavailable"}), 502
    return jsonify({"response": response}), 200


@ai_bp.post("/analyze-image")
@jwt_required()
def analyze_image():
    uploaded_file = request.files.get("image")
    instruction = request.form.get("instruction", "").strip()
    language = _language()
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"message": "image file is required"}), 400
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    mime_type = uploaded_file.mimetype or ""
    if mime_type not in allowed_types:
        return jsonify({"message": "unsupported image type"}), 415
    image_bytes = uploaded_file.read()
    if not image_bytes:
        return jsonify({"message": "uploaded image is empty"}), 400
    if len(image_bytes) > 10 * 1024 * 1024:
        return jsonify({"message": "image must not exceed 10 MB"}), 413
    try:
        response = analyze_health_image(image_bytes, mime_type, instruction, language)
    except GeminiServiceError as error:
        return jsonify({"message": str(error)}), 503
    except Exception:
        return jsonify({"message": "AI image analysis is temporarily unavailable"}), 502
    return jsonify({"response": response}), 200

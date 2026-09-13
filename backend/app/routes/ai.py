from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..services.gemini_service import GeminiServiceError, generate_health_chat_response

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


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
        response = generate_health_chat_response(message)
    except GeminiServiceError as error:
        return jsonify({"message": str(error)}), 503
    except Exception:
        return jsonify({"message": "AI service is temporarily unavailable"}), 502

    return jsonify({"response": response}), 200

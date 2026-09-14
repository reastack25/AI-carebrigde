import json

from google import genai
from google.genai import types

from ..config import Config


class GeminiServiceError(RuntimeError):
    """Raised when Gemini is unavailable or returns an unusable response."""


def _client():
    if not Config.GEMINI_API_KEY:
        raise GeminiServiceError("Gemini API key is not configured")
    return genai.Client(api_key=Config.GEMINI_API_KEY)


def _extract_text(response) -> str:
    text = (response.text or "").strip()
    if not text:
        raise GeminiServiceError("Gemini returned an empty response")
    return text


def _language_instruction(language: str) -> str:
    languages = {"en": "English", "sw": "Kiswahili", "luo": "Dholuo", "kik": "Kikuyu", "kal": "Kalenjin"}
    return f"Respond in {languages.get(language, 'English')}."


def generate_health_chat_response(message: str, language: str = "en") -> str:
    client = _client()
    prompt = ("You are CareBridge AI, a healthcare information assistant. Provide clear, cautious, educational information. "
              "Do not diagnose, prescribe, or claim certainty. Ask the user to seek urgent medical care for emergency warning signs. "
              f"Keep the response concise. {_language_instruction(language)}\n\nUser question: {message}")
    return _extract_text(client.models.generate_content(model="gemini-2.5-flash", contents=prompt))


def generate_symptom_check_response(symptoms: str, age: str = "", duration: str = "", language: str = "en") -> dict:
    client = _client()
    prompt = f'''You are CareBridge AI providing cautious healthcare education and triage support, not diagnosis.
Return ONLY valid JSON with exactly these keys: urgency, summary, possible_explanations, next_steps, red_flags, disclaimer.
urgency must be one of: routine, soon, urgent, emergency.
All list values must be arrays of short strings. Never invent certainty. If emergency warning signs may be present, set urgency to emergency and advise immediate emergency care. Explain that a clinician must assess the person.
{_language_instruction(language)}
Symptoms: {symptoms}
Age: {age or 'not provided'}
Duration: {duration or 'not provided'}'''
    raw = _extract_text(client.models.generate_content(model="gemini-2.5-flash", contents=prompt))
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as error:
        raise GeminiServiceError("Gemini returned an invalid symptom-check response") from error
    required = {"urgency", "summary", "possible_explanations", "next_steps", "red_flags", "disclaimer"}
    if set(result) != required or result["urgency"] not in {"routine", "soon", "urgent", "emergency"}:
        raise GeminiServiceError("Gemini returned an incomplete symptom-check response")
    if not all(isinstance(result[key], list) for key in ("possible_explanations", "next_steps", "red_flags")):
        raise GeminiServiceError("Gemini returned invalid symptom-check lists")
    return result


def analyze_health_document(file_bytes: bytes, mime_type: str, instruction: str, language: str = "en") -> str:
    client = _client()
    prompt = ("You are CareBridge AI reviewing a user-provided healthcare document or image. Explain only information that can reasonably be observed. "
              "Do not diagnose, prescribe, invent unreadable text, or present uncertain interpretations as facts. If unclear, say so. "
              f"Recommend a qualified healthcare professional for clinical decisions. {_language_instruction(language)}\n\nUser instruction: {instruction or 'Explain this healthcare document in plain language.'}")
    document_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    return _extract_text(client.models.generate_content(model="gemini-2.5-flash", contents=[prompt, document_part]))


def analyze_health_image(image_bytes: bytes, mime_type: str, instruction: str, language: str = "en") -> str:
    return analyze_health_document(image_bytes, mime_type, instruction, language)

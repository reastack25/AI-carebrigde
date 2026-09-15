import json
import re

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


def _history_context(history) -> str:
    history = history or []
    lines = []
    for item in history:
        sender = item.get("sender", "unknown")
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{sender}: {content}")
    return "\n".join(lines) or "No previous conversation context."


def generate_health_chat_response(message: str, language: str = "en", history=None) -> str:
    client = _client()
    prompt = ("You are CareBridge AI, a healthcare information assistant. Provide clear, cautious, educational information. "
              "Do not diagnose, prescribe, or claim certainty. Ask the user to seek urgent medical care for emergency warning signs. "
              f"Keep the response concise. {_language_instruction(language)}\n\n"
              "Use the conversation history only as context for continuity. Do not assume facts that are not present.\n"
              f"Conversation history:\n{_history_context(history)}\n\nCurrent user question: {message}")
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
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise GeminiServiceError("Gemini returned an invalid symptom-check response") from error
    required = {"urgency", "summary", "possible_explanations", "next_steps", "red_flags", "disclaimer"}
    if set(result) != required or result["urgency"] not in {"routine", "soon", "urgent", "emergency"}:
        raise GeminiServiceError("Gemini returned an incomplete symptom-check response")
    if not isinstance(result["summary"], str) or not isinstance(result["disclaimer"], str):
        raise GeminiServiceError("Gemini returned invalid symptom-check text")
    if not all(isinstance(result[key], list) and all(isinstance(item, str) for item in result[key]) for key in ("possible_explanations", "next_steps", "red_flags")):
        raise GeminiServiceError("Gemini returned invalid symptom-check lists")
    return result


def analyze_health_document(file_bytes: bytes, mime_type: str, instruction: str, language: str = "en", history=None) -> str:
    client = _client()
    prompt = ("You are CareBridge AI reviewing a user-provided healthcare document or image. Explain only information that can reasonably be observed. "
              "Do not diagnose, prescribe, invent unreadable text, or present uncertain interpretations as facts. If unclear, say so. "
              f"Recommend a qualified healthcare professional for clinical decisions. {_language_instruction(language)}\n\n"
              "Use prior conversation context only to understand the user's intent and maintain continuity. Do not treat prior AI statements as verified medical facts.\n"
              f"Prior conversation context:\n{_history_context(history)}\n\n"
              f"User instruction: {instruction or 'Explain this healthcare document in plain language.'}")
    document_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    return _extract_text(client.models.generate_content(model="gemini-2.5-flash", contents=[prompt, document_part]))


def extract_medications_from_document(file_bytes: bytes, mime_type: str, instruction: str = "", language: str = "en") -> list[dict]:
    """Extract only clearly readable medication details from a document or image."""
    client = _client()
    prompt = f'''You are CareBridge AI extracting medication information from a healthcare document.
Return ONLY valid JSON with exactly one key: medications.
medications must be an array. Each item must contain exactly these string keys: name, dosage, frequency, duration, instructions, warnings.
Use an empty string when a value is absent or unreadable. Do not guess, infer, or invent medication names or directions. Preserve uncertainty by leaving the field empty. If no medication is clearly identified, return an empty array.
This is extraction, not diagnosis or prescribing. {_language_instruction(language)}
User instruction: {instruction or 'Extract clearly readable medicines and their written directions.'}'''
    document_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    raw = _extract_text(client.models.generate_content(model="gemini-2.5-flash", contents=[prompt, document_part]))
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise GeminiServiceError("Gemini returned invalid medication extraction JSON") from error
    if set(result) != {"medications"} or not isinstance(result["medications"], list):
        raise GeminiServiceError("Gemini returned an invalid medication extraction response")
    fields = {"name", "dosage", "frequency", "duration", "instructions", "warnings"}
    normalized = []
    for item in result["medications"]:
        if not isinstance(item, dict) or set(item) != fields or not all(isinstance(item[key], str) for key in fields):
            raise GeminiServiceError("Gemini returned invalid medication details")
        if item["name"].strip():
            normalized.append({key: item[key].strip() for key in fields})
    return normalized


def analyze_health_image(image_bytes: bytes, mime_type: str, instruction: str, language: str = "en", history=None) -> str:
    return analyze_health_document(image_bytes, mime_type, instruction, language, history)

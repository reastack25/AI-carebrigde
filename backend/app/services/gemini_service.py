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
    languages = {
        "en": "English",
        "sw": "Kiswahili",
        "luo": "Dholuo",
        "kik": "Kikuyu",
        "kal": "Kalenjin",
    }
    return f"Respond in {languages.get(language, 'English')}."


def generate_health_chat_response(message: str, language: str = "en") -> str:
    client = _client()
    prompt = (
        "You are CareBridge AI, a healthcare information assistant. "
        "Provide clear, cautious, educational information. Do not diagnose, "
        "prescribe, or claim certainty. Ask the user to seek urgent medical "
        "care for emergency warning signs. Keep the response concise. "
        f"{_language_instruction(language)}\n\n"
        f"User question: {message}"
    )
    return _extract_text(
        client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    )


def analyze_health_image(image_bytes: bytes, mime_type: str, instruction: str, language: str = "en") -> str:
    client = _client()
    prompt = (
        "You are CareBridge AI reviewing a user-provided healthcare image. "
        "Explain only what can reasonably be observed. Do not diagnose, "
        "prescribe, or invent unreadable text. If the image is unclear, say so. "
        "Recommend a qualified healthcare professional for clinical decisions. "
        f"{_language_instruction(language)}\n\n"
        f"User instruction: {instruction or 'Explain this image in plain language.'}"
    )
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image_part],
    )
    return _extract_text(response)

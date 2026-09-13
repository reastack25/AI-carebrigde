from google import genai

from ..config import Config


class GeminiServiceError(RuntimeError):
    """Raised when Gemini is unavailable or returns an unusable response."""


def generate_health_chat_response(message: str) -> str:
    if not Config.GEMINI_API_KEY:
        raise GeminiServiceError("Gemini API key is not configured")

    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    prompt = (
        "You are CareBridge AI, a healthcare information assistant. "
        "Provide clear, cautious, educational information. Do not diagnose, "
        "prescribe, or claim certainty. Ask the user to seek urgent medical "
        "care for emergency warning signs. Keep the response concise.\n\n"
        f"User question: {message}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = (response.text or "").strip()

    if not text:
        raise GeminiServiceError("Gemini returned an empty response")

    return text

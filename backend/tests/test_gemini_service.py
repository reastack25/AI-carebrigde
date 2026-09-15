from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.gemini_service import (
    GeminiServiceError,
    generate_health_chat_response,
    generate_symptom_check_response,
)


class FakeModels:
    def __init__(self, response):
        self.response = response

    def generate_content(self, **kwargs):
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def fake_response(text):
    return SimpleNamespace(text=text)


def test_health_chat_rejects_empty_gemini_response():
    client = FakeClient(fake_response("   "))
    with patch("app.services.gemini_service._client", return_value=client):
        with pytest.raises(GeminiServiceError, match="empty response"):
            generate_health_chat_response("What is a healthy sleep routine?")


def test_health_chat_returns_trimmed_response():
    client = FakeClient(fake_response("  Stay hydrated and maintain a regular sleep schedule.  "))
    with patch("app.services.gemini_service._client", return_value=client):
        result = generate_health_chat_response("How can I improve my sleep?")
    assert result == "Stay hydrated and maintain a regular sleep schedule."


def valid_symptom_result():
    return (
        '{"urgency":"soon","summary":"Monitor the symptoms and consider clinical advice.",'
        '"possible_explanations":["A common cause"],'
        '"next_steps":["Speak with a clinician if symptoms persist"],'
        '"red_flags":["Severe worsening symptoms"],'
        '"disclaimer":"This is educational information, not a diagnosis."}'
    )


def test_symptom_check_accepts_valid_json():
    client = FakeClient(fake_response(valid_symptom_result()))
    with patch("app.services.gemini_service._client", return_value=client):
        result = generate_symptom_check_response("mild headache", "25", "1 day")
    assert result["urgency"] == "soon"
    assert result["possible_explanations"] == ["A common cause"]


def test_symptom_check_accepts_fenced_json():
    client = FakeClient(fake_response(f"```json\n{valid_symptom_result()}\n```"))
    with patch("app.services.gemini_service._client", return_value=client):
        result = generate_symptom_check_response("mild headache")
    assert result["urgency"] == "soon"


@pytest.mark.parametrize(
    "response_text, error_message",
    [
        ("not json", "invalid symptom-check response"),
        ('{"urgency":"soon","summary":"Only part of the response"}', "incomplete symptom-check response"),
        ('{"urgency":"unknown","summary":"x","possible_explanations":[],"next_steps":[],"red_flags":[],"disclaimer":"x"}', "incomplete symptom-check response"),
        ('{"urgency":"soon","summary":123,"possible_explanations":[],"next_steps":[],"red_flags":[],"disclaimer":"x"}', "invalid symptom-check text"),
        ('{"urgency":"soon","summary":"x","possible_explanations":"not a list","next_steps":[],"red_flags":[],"disclaimer":"x"}', "invalid symptom-check lists"),
    ],
)
def test_symptom_check_rejects_invalid_gemini_output(response_text, error_message):
    client = FakeClient(fake_response(response_text))
    with patch("app.services.gemini_service._client", return_value=client):
        with pytest.raises(GeminiServiceError, match=error_message):
            generate_symptom_check_response("headache")

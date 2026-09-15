from io import BytesIO
from unittest.mock import patch

from tests.helpers import register_and_login


def auth_headers(client, email="patient@example.com"):
    token = register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


def test_ai_requires_authentication(client):
    response = client.post("/api/ai/symptom-check", json={"symptoms": "headache"})
    assert response.status_code == 401


def test_symptom_check_requires_symptoms(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/symptom-check", headers=headers, json={})
    assert response.status_code == 400
    assert response.get_json()["message"] == "symptoms are required"


def test_symptom_check_rejects_invalid_age(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/symptom-check",
        headers=headers,
        json={"symptoms": "headache", "age": "121"},
    )
    assert response.status_code == 400


def test_symptom_check_rejects_oversized_duration(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/symptom-check",
        headers=headers,
        json={"symptoms": "headache", "duration": "x" * 201},
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "duration must not exceed 200 characters"


def test_symptom_check_rejects_invalid_conversation_id(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/symptom-check",
        headers=headers,
        json={"symptoms": "headache", "conversation_id": "abc"},
    )
    assert response.status_code == 400


def test_symptom_check_rejects_other_users_conversation(client):
    first_headers = auth_headers(client)
    with patch(
        "app.routes.ai.generate_symptom_check_response",
        return_value={
            "urgency": "routine",
            "summary": "Test summary",
            "possible_explanations": ["Test explanation"],
            "next_steps": ["Monitor symptoms"],
            "red_flags": ["Severe symptoms"],
            "disclaimer": "Educational information only.",
        },
    ):
        created = client.post(
            "/api/ai/symptom-check",
            headers=first_headers,
            json={"symptoms": "headache"},
        )
    conversation_id = created.get_json()["conversation"]["id"]

    second_headers = auth_headers(client, "other@example.com")
    response = client.post(
        "/api/ai/symptom-check",
        headers=second_headers,
        json={"symptoms": "headache", "conversation_id": conversation_id},
    )
    assert response.status_code == 404


def test_symptom_check_success_with_mocked_gemini(client):
    headers = auth_headers(client)
    result = {
        "urgency": "soon",
        "summary": "This is a test educational summary.",
        "possible_explanations": ["A common cause"],
        "next_steps": ["Consider speaking with a clinician"],
        "red_flags": ["Severe worsening symptoms"],
        "disclaimer": "This is not a diagnosis.",
    }
    with patch("app.routes.ai.generate_symptom_check_response", return_value=result):
        response = client.post(
            "/api/ai/symptom-check",
            headers=headers,
            json={"symptoms": "mild headache", "age": "25", "duration": "1 day"},
        )
    assert response.status_code == 200
    assert response.get_json()["result"] == result


def test_chat_success_with_mocked_gemini(client):
    headers = auth_headers(client)
    with patch(
        "app.routes.ai.generate_health_chat_response",
        return_value="Test educational response.",
    ):
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "What is a healthy sleep routine?", "language": "en"},
        )
    assert response.status_code == 200
    data = response.get_json()
    assert data["response"] == "Test educational response."
    assert len(data["conversation"]["messages"]) == 2
    assert data["conversation"]["messages"][0]["sender"] == "user"
    assert data["conversation"]["messages"][1]["sender"] == "assistant"


def test_chat_rejects_other_users_conversation(client):
    first_headers = auth_headers(client)
    with patch(
        "app.routes.ai.generate_health_chat_response",
        return_value="Private conversation response.",
    ):
        created = client.post(
            "/api/ai/chat",
            headers=first_headers,
            json={"message": "Private question"},
        )
    conversation_id = created.get_json()["conversation"]["id"]

    second_headers = auth_headers(client, "other-chat@example.com")
    with patch("app.routes.ai.generate_health_chat_response") as mocked_gemini:
        response = client.post(
            "/api/ai/chat",
            headers=second_headers,
            json={"message": "Should not access this", "conversation_id": conversation_id},
        )

    assert response.status_code == 404
    mocked_gemini.assert_not_called()


def test_chat_rejects_oversized_message(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/chat",
        headers=headers,
        json={"message": "x" * 4001},
    )
    assert response.status_code == 400


def test_analyze_image_rejects_unsupported_type(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/analyze-image",
        headers=headers,
        data={"image": (BytesIO(b"not an image"), "file.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415


def test_analyze_image_rejects_oversized_instruction(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/analyze-image",
        headers=headers,
        data={
            "instruction": "x" * 1001,
            "image": (BytesIO(b"fake"), "file.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_analyze_image_rejects_oversized_file(client):
    headers = auth_headers(client)
    with patch("app.routes.ai.MAX_DOCUMENT_SIZE", 4):
        response = client.post(
            "/api/ai/analyze-image",
            headers=headers,
            data={"image": (BytesIO(b"12345"), "file.png")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 413


def test_chat_returns_service_unavailable_when_gemini_fails(client):
    headers = auth_headers(client)
    with patch(
        "app.routes.ai.generate_health_chat_response",
        side_effect=Exception("Gemini unavailable"),
    ):
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "test"},
        )
    assert response.status_code == 502
    assert response.get_json()["message"] == "AI service is temporarily unavailable"

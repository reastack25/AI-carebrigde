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
    response = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "headache", "age": "121"})
    assert response.status_code == 400


def test_symptom_check_rejects_oversized_duration(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "headache", "duration": "x" * 201})
    assert response.status_code == 400
    assert response.get_json()["message"] == "duration must not exceed 200 characters"


def test_symptom_check_rejects_invalid_conversation_id(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "headache", "conversation_id": "abc"})
    assert response.status_code == 400


def test_symptom_check_rejects_other_users_conversation(client):
    first_headers = auth_headers(client)
    with patch("app.routes.ai.generate_symptom_check_response", return_value={"urgency": "routine", "summary": "Test summary", "possible_explanations": ["Test explanation"], "next_steps": ["Monitor symptoms"], "red_flags": ["Severe symptoms"], "disclaimer": "Educational information only."}):
        created = client.post("/api/ai/symptom-check", headers=first_headers, json={"symptoms": "headache"})
    conversation_id = created.get_json()["conversation"]["id"]
    second_headers = auth_headers(client, "other@example.com")
    response = client.post("/api/ai/symptom-check", headers=second_headers, json={"symptoms": "headache", "conversation_id": conversation_id})
    assert response.status_code == 404


def test_symptom_check_success_with_mocked_gemini(client):
    headers = auth_headers(client)
    result = {"urgency": "soon", "summary": "This is a test educational summary.", "possible_explanations": ["A common cause"], "next_steps": ["Consider speaking with a clinician"], "red_flags": ["Severe worsening symptoms"], "disclaimer": "This is not a diagnosis."}
    with patch("app.routes.ai.generate_symptom_check_response", return_value=result):
        response = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "mild headache", "age": "25", "duration": "1 day"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["result"] == result
    assert data["record"]["symptoms"] == "mild headache"
    assert data["record"]["age"] == 25
    assert data["record"]["urgency"] == "soon"


def test_symptom_check_creates_timeline_event(client, app):
    from app.models import HealthTimelineEvent, SymptomCheck
    headers = auth_headers(client)
    result = {"urgency": "soon", "summary": "Timeline summary.", "possible_explanations": [], "next_steps": [], "red_flags": [], "disclaimer": "Not a diagnosis."}
    with patch("app.routes.ai.generate_symptom_check_response", return_value=result):
        response = client.post("/api/ai/symptom-check", headers=headers, json={"symptoms": "headache", "age": "25", "duration": "1 day", "language": "sw"})
    assert response.status_code == 200
    with app.app_context():
        event = HealthTimelineEvent.query.one()
        record = SymptomCheck.query.one()
        assert event.event_type == "symptom_check"
        assert event.summary == result["summary"]
        assert event.event_metadata["urgency"] == "soon"
        assert event.event_metadata["language"] == "sw"
        assert event.event_metadata["record_id"] == record.id
        assert record.language == "sw"


def test_chat_success_with_mocked_gemini(client):
    headers = auth_headers(client)
    with patch("app.routes.ai.generate_health_chat_response", return_value="Test educational response."):
        response = client.post("/api/ai/chat", headers=headers, json={"message": "What is a healthy sleep routine?", "language": "en"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["response"] == "Test educational response."
    assert len(data["conversation"]["messages"]) == 2
    assert data["conversation"]["messages"][0]["sender"] == "user"
    assert data["conversation"]["messages"][1]["sender"] == "assistant"


def test_chat_creates_timeline_event(client, app):
    from app.models import HealthTimelineEvent
    headers = auth_headers(client)
    with patch("app.routes.ai.generate_health_chat_response", return_value="Saved health response."):
        response = client.post("/api/ai/chat", headers=headers, json={"message": "What is a healthy sleep routine?"})
    assert response.status_code == 200
    with app.app_context():
        event = HealthTimelineEvent.query.one()
        assert event.event_type == "health_chat"
        assert event.summary == "Saved health response."
        assert event.conversation_id == response.get_json()["conversation"]["id"]
        assert event.event_metadata == {"language": "en"}


def test_chat_passes_recent_history_to_gemini(client):
    headers = auth_headers(client)
    calls = []
    def fake_chat(message, language, history):
        calls.append((message, language, history))
        return "Context-aware response."
    with patch("app.routes.ai.generate_health_chat_response", side_effect=fake_chat):
        first = client.post("/api/ai/chat", headers=headers, json={"message": "I have a headache", "language": "sw"})
        conversation_id = first.get_json()["conversation"]["id"]
        second = client.post("/api/ai/chat", headers=headers, json={"message": "What should I do next?", "conversation_id": conversation_id, "language": "sw"})
    assert second.status_code == 200
    assert len(calls) == 2
    assert calls[0][2] == []
    assert calls[1][0] == "What should I do next?"
    assert calls[1][1] == "sw"
    assert calls[1][2] == [{"sender": "user", "content": "I have a headache"}, {"sender": "assistant", "content": "Context-aware response."}]


def test_chat_limits_history_to_recent_messages(client):
    headers = auth_headers(client)
    calls = []
    def fake_chat(message, language, history):
        calls.append(history)
        return "response"
    with patch("app.routes.ai.generate_health_chat_response", side_effect=fake_chat):
        first = client.post("/api/ai/chat", headers=headers, json={"message": "message 0"})
        conversation_id = first.get_json()["conversation"]["id"]
        for index in range(1, 8):
            response = client.post("/api/ai/chat", headers=headers, json={"message": f"message {index}", "conversation_id": conversation_id})
            assert response.status_code == 200
    assert len(calls[-1]) == 12
    assert calls[-1][0]["content"] == "message 1"
    assert calls[-1][-1]["content"] == "response"


def test_conversation_listing_is_paginated_and_user_isolated(client):
    headers = auth_headers(client, "conversation-list@example.com")
    other_headers = auth_headers(client, "conversation-other@example.com")
    with patch("app.routes.ai.generate_health_chat_response", return_value="response"):
        for index in range(3):
            response = client.post("/api/ai/chat", headers=headers, json={"message": f"conversation {index}"})
            assert response.status_code == 200
        response = client.post("/api/ai/chat", headers=other_headers, json={"message": "other conversation"})
        assert response.status_code == 200
    listed = client.get("/api/ai/conversations?limit=2&offset=0", headers=headers)
    assert listed.status_code == 200
    data = listed.get_json()
    assert len(data["conversations"]) == 2
    assert data["pagination"] == {"limit": 2, "offset": 0, "total": 3, "has_more": True}
    next_page = client.get("/api/ai/conversations?limit=2&offset=2", headers=headers)
    assert next_page.status_code == 200
    assert len(next_page.get_json()["conversations"]) == 1
    assert next_page.get_json()["pagination"]["has_more"] is False
    assert all(item["title"] != "other conversation" for item in data["conversations"])


def test_conversation_listing_rejects_invalid_pagination(client):
    headers = auth_headers(client, "conversation-pagination@example.com")
    for query in ("limit=0", "limit=51", "offset=-1", "limit=abc", "offset=abc"):
        response = client.get(f"/api/ai/conversations?{query}", headers=headers)
        assert response.status_code == 400


def test_document_analysis_passes_conversation_history(client):
    headers = auth_headers(client)
    calls = []
    def fake_document(file_bytes, mime_type, instruction, language, history):
        calls.append((file_bytes, mime_type, instruction, language, history))
        return "Document context response."
    with patch("app.routes.ai.analyze_health_document", side_effect=fake_document), patch("app.routes.ai.generate_health_chat_response", return_value="Earlier chat response."):
        first = client.post("/api/ai/chat", headers=headers, json={"message": "I am worried about my blood test."})
        conversation_id = first.get_json()["conversation"]["id"]
        response = client.post("/api/ai/analyze-image", headers=headers, data={"conversation_id": str(conversation_id), "language": "sw", "instruction": "Explain the key findings", "image": (BytesIO(b"fake-document"), "report.png")}, content_type="multipart/form-data")
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0][0] == b"fake-document"
    assert calls[0][1] == "image/png"
    assert calls[0][2] == "Explain the key findings"
    assert calls[0][3] == "sw"
    assert calls[0][4] == [{"sender": "user", "content": "I am worried about my blood test."}, {"sender": "assistant", "content": "Earlier chat response."}]


def test_document_analysis_creates_timeline_event(client, app):
    from app.models import HealthTimelineEvent, MedicalReport
    headers = auth_headers(client)
    with patch("app.routes.ai.analyze_health_document", return_value="Report summary saved."):
        response = client.post("/api/ai/analyze-image", headers=headers, data={"language": "en", "instruction": "Summarize", "image": (BytesIO(b"fake-document"), "report.png")}, content_type="multipart/form-data")
    assert response.status_code == 200
    with app.app_context():
        event = HealthTimelineEvent.query.one()
        record = MedicalReport.query.one()
        assert event.event_type == "document_analysis"
        assert event.summary == "Report summary saved."
        assert event.event_metadata["filename"] == "report.png"
        assert event.event_metadata["mime_type"] == "image/png"
        assert event.event_metadata["record_id"] == record.id
        assert record.summary == "Report summary saved."


def test_document_analysis_sanitizes_uploaded_filename(client, app):
    from app.models import HealthTimelineEvent, MedicalReport
    headers = auth_headers(client, "filename-safety@example.com")
    with patch("app.routes.ai.analyze_health_document", return_value="Sanitized report."):
        response = client.post("/api/ai/analyze-image", headers=headers, data={"image": (BytesIO(b"fake-document"), "../../patient-report final.pdf")}, content_type="multipart/form-data")
    assert response.status_code == 200
    data = response.get_json()
    assert data["report"]["filename"] == "patient-report_final.pdf"
    with app.app_context():
        event = HealthTimelineEvent.query.one()
        record = MedicalReport.query.one()
        assert record.filename == "patient-report_final.pdf"
        assert event.event_metadata["filename"] == "patient-report_final.pdf"
        assert ".." not in record.filename
        assert "/" not in record.filename


def test_document_analysis_rejects_filename_that_sanitizes_to_empty(client):
    headers = auth_headers(client, "invalid-filename@example.com")
    with patch("app.routes.ai.analyze_health_document") as mocked_gemini:
        response = client.post("/api/ai/analyze-image", headers=headers, data={"image": (BytesIO(b"fake-document"), "../../")}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json()["message"] == "document filename is invalid"
    mocked_gemini.assert_not_called()


def test_timeline_is_user_isolated_and_filterable(client):
    first_headers = auth_headers(client)
    with patch("app.routes.ai.generate_health_chat_response", return_value="Private event"):
        client.post("/api/ai/chat", headers=first_headers, json={"message": "Private question"})
    second_headers = auth_headers(client, "other-timeline@example.com")
    with patch("app.routes.ai.generate_health_chat_response", return_value="Other event"):
        client.post("/api/ai/chat", headers=second_headers, json={"message": "Other question"})
    response = client.get("/api/ai/timeline", headers=first_headers)
    assert response.status_code == 200
    data = response.get_json()["timeline"]
    assert len(data) == 1
    assert data[0]["summary"] == "Private event"
    assert data[0]["event_type"] == "health_chat"
    assert data[0]["metadata"] == {"language": "en"}
    filtered = client.get("/api/ai/timeline?type=symptom_check", headers=first_headers)
    assert filtered.status_code == 200
    assert filtered.get_json()["timeline"] == []


def test_structured_record_endpoints_are_user_isolated(client):
    first_headers = auth_headers(client)
    result = {"urgency": "routine", "summary": "Private symptom record", "possible_explanations": [], "next_steps": [], "red_flags": [], "disclaimer": "Not a diagnosis."}
    with patch("app.routes.ai.generate_symptom_check_response", return_value=result):
        client.post("/api/ai/symptom-check", headers=first_headers, json={"symptoms": "private symptom"})
    second_headers = auth_headers(client, "other-record@example.com")
    symptom_response = client.get("/api/ai/symptom-checks", headers=second_headers)
    report_response = client.get("/api/ai/medical-reports", headers=second_headers)
    assert symptom_response.status_code == 200
    assert report_response.status_code == 200
    assert symptom_response.get_json()["symptom_checks"] == []
    assert report_response.get_json()["medical_reports"] == []


def test_chat_rejects_other_users_conversation(client):
    first_headers = auth_headers(client)
    with patch("app.routes.ai.generate_health_chat_response", return_value="Private conversation response."):
        created = client.post("/api/ai/chat", headers=first_headers, json={"message": "Private question"})
    conversation_id = created.get_json()["conversation"]["id"]
    second_headers = auth_headers(client, "other-chat@example.com")
    with patch("app.routes.ai.generate_health_chat_response") as mocked_gemini:
        response = client.post("/api/ai/chat", headers=second_headers, json={"message": "Should not access this", "conversation_id": conversation_id})
    assert response.status_code == 404
    mocked_gemini.assert_not_called()


def test_document_analysis_rejects_other_users_conversation(client):
    first_headers = auth_headers(client)
    with patch("app.routes.ai.analyze_health_document", return_value="Private result"):
        created = client.post("/api/ai/analyze-image", headers=first_headers, data={"image": (BytesIO(b"private"), "report.png")}, content_type="multipart/form-data")
    conversation_id = created.get_json()["conversation"]["id"]
    second_headers = auth_headers(client, "other-document@example.com")
    with patch("app.routes.ai.analyze_health_document") as mocked_gemini:
        response = client.post("/api/ai/analyze-image", headers=second_headers, data={"conversation_id": str(conversation_id), "image": (BytesIO(b"private"), "report.png")}, content_type="multipart/form-data")
    assert response.status_code == 404
    mocked_gemini.assert_not_called()


def test_chat_rejects_oversized_message(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/chat", headers=headers, json={"message": "x" * 4001})
    assert response.status_code == 400


def test_analyze_image_rejects_unsupported_type(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/analyze-image", headers=headers, data={"image": (BytesIO(b"not an image"), "file.txt")}, content_type="multipart/form-data")
    assert response.status_code == 415

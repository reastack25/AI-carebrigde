from io import BytesIO
from unittest.mock import patch

from tests.helpers import register_and_login


def auth_headers(client, email="patient@example.com"):
    token = register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


def test_medications_requires_authentication(client):
    response = client.get("/api/ai/medications")
    assert response.status_code == 401


def test_extract_medications_requires_file(client):
    headers = auth_headers(client)
    response = client.post("/api/ai/extract-medications", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["message"] == "document file is required"


def test_extract_medications_rejects_unsupported_type(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/extract-medications",
        headers=headers,
        data={"image": (BytesIO(b"plain text"), "notes.txt", "text/plain")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415


def test_extract_medications_success_persists_records_and_timeline(client, app):
    headers = auth_headers(client)
    extracted = [
        {
            "name": "Paracetamol",
            "dosage": "500 mg",
            "frequency": "Twice daily",
            "duration": "3 days",
            "instructions": "Take after food",
            "warnings": "Do not exceed the recommended dose",
        }
    ]
    with patch("app.routes.medications.extract_medications_from_document", return_value=extracted):
        response = client.post(
            "/api/ai/extract-medications",
            headers=headers,
            data={
                "image": (BytesIO(b"fake image bytes"), "prescription.png", "image/png"),
                "language": "sw",
                "instruction": "Explain the prescription",
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["medications"] == extracted
    assert len(data["records"]) == 1
    assert data["records"][0]["name"] == "Paracetamol"
    assert data["records"][0]["language"] == "sw"
    assert data["records"][0]["warnings"] == ["Do not exceed the recommended dose"]

    with app.app_context():
        from app.models import HealthTimelineEvent, Medication

        record = Medication.query.one()
        event = HealthTimelineEvent.query.one()
        assert event.event_type == "medication_extraction"
        assert event.event_metadata["record_ids"] == [record.id]
        assert event.event_metadata["count"] == 1


def test_medications_are_user_isolated(client):
    first_headers = auth_headers(client, "first@example.com")
    extracted = [{"name": "Ibuprofen", "dosage": "200 mg", "frequency": "Once daily", "duration": "2 days", "instructions": "With food", "warnings": ""}]
    with patch("app.routes.medications.extract_medications_from_document", return_value=extracted):
        response = client.post(
            "/api/ai/extract-medications",
            headers=first_headers,
            data={"image": (BytesIO(b"fake"), "medicine.jpg", "image/jpeg")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 200

    second_headers = auth_headers(client, "second@example.com")
    response = client.get("/api/ai/medications", headers=second_headers)
    assert response.status_code == 200
    assert response.get_json()["medications"] == []


def test_extract_medications_rejects_oversized_instruction(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/ai/extract-medications",
        headers=headers,
        data={
            "instruction": "x" * 1001,
            "image": (BytesIO(b"fake"), "medicine.jpg", "image/jpeg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "instruction must not exceed 1000 characters"

from io import BytesIO
from unittest.mock import patch

from tests.helpers import register_and_login


VALID_PNG = b"\x89PNG\r\n\x1a\nvalid-test-png"
VALID_PDF = b"%PDF-1.7\nvalid-test-pdf"
VALID_HEIF = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00"


def auth_headers(client, email="patient@example.com"):
    token = register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


def test_analyze_image_rejects_mismatched_file_signature(client):
    headers = auth_headers(client, "signature-mismatch@example.com")
    with patch("app.routes.ai.analyze_health_document") as mocked_gemini:
        response = client.post(
            "/api/ai/analyze-image",
            headers=headers,
            data={"image": (BytesIO(b"not-a-png"), "report.png")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 415
    assert response.get_json()["message"] == "uploaded document content does not match its declared type"
    mocked_gemini.assert_not_called()


def test_analyze_image_accepts_valid_heif_signature(client):
    headers = auth_headers(client, "heif-signature@example.com")
    with patch("app.routes.ai.analyze_health_document", return_value="HEIF report") as mocked_gemini:
        response = client.post(
            "/api/ai/analyze-image",
            headers=headers,
            data={"image": (BytesIO(VALID_HEIF), "report.heic")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 200
    mocked_gemini.assert_called_once()


def test_analyze_image_rejects_invalid_heif_signature(client):
    headers = auth_headers(client, "invalid-heif-signature@example.com")
    with patch("app.routes.ai.analyze_health_document") as mocked_gemini:
        response = client.post(
            "/api/ai/analyze-image",
            headers=headers,
            data={"image": (BytesIO(b"not-heif"), "report.heic")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 415
    assert response.get_json()["message"] == "uploaded document content does not match its declared type"
    mocked_gemini.assert_not_called()

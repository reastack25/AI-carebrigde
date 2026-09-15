from tests.helpers import register_and_login


def login(client, email, role):
    return register_and_login(client, email, role=role)


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def user_id(client, token):
    return client.get("/api/auth/me", headers=headers(token)).get_json()["user"]["id"]


def test_patient_can_grant_and_revoke_doctor_consent(client):
    patient = login(client, "clinical-patient@example.com", "patient")
    doctor = login(client, "clinical-doctor@example.com", "doctor")
    doctor_id = user_id(client, doctor)
    grant = client.post("/api/clinical/consents", headers=headers(patient), json={"doctor_id": doctor_id})
    assert grant.status_code == 201
    consent = grant.get_json()["consent"]
    assert consent["active"] is True
    revoke = client.delete(f"/api/clinical/consents/{doctor_id}", headers=headers(patient))
    assert revoke.status_code == 200
    assert revoke.get_json()["consent"]["active"] is False


def test_doctor_can_read_records_only_with_active_consent(client):
    patient = login(client, "records-patient@example.com", "patient")
    doctor = login(client, "records-doctor@example.com", "doctor")
    patient_id = user_id(client, patient)
    doctor_id = user_id(client, doctor)
    denied = client.get(f"/api/clinical/patients/{patient_id}/records", headers=headers(doctor))
    assert denied.status_code == 403
    granted = client.post("/api/clinical/consents", headers=headers(patient), json={"doctor_id": doctor_id})
    assert granted.status_code == 201
    allowed = client.get(f"/api/clinical/patients/{patient_id}/records", headers=headers(doctor))
    assert allowed.status_code == 200
    assert allowed.get_json()["records"]["medications"] == []
    assert allowed.get_json()["records"]["medical_reports"] == []


def test_doctor_can_add_review_and_patient_can_read_it(client):
    patient = login(client, "review-patient@example.com", "patient")
    doctor = login(client, "review-doctor@example.com", "doctor")
    patient_id = user_id(client, patient)
    doctor_id = user_id(client, doctor)
    grant = client.post("/api/clinical/consents", headers=headers(patient), json={"doctor_id": doctor_id})
    assert grant.status_code == 201
    response = client.post(f"/api/clinical/patients/{patient_id}/reviews", headers=headers(doctor), json={"note": "Please discuss the reported symptoms with your clinician.", "status": "follow_up"})
    assert response.status_code == 201
    assert response.get_json()["review"]["status"] == "follow_up"
    reviews = client.get("/api/clinical/reviews", headers=headers(patient))
    assert reviews.status_code == 200
    assert len(reviews.get_json()["reviews"]) == 1


def test_patient_cannot_access_doctor_patient_endpoints(client):
    patient = login(client, "forbidden-patient@example.com", "patient")
    response = client.get("/api/clinical/patients", headers=headers(patient))
    assert response.status_code == 403
    response = client.post("/api/clinical/patients/1/reviews", headers=headers(patient), json={"note": "not allowed"})
    assert response.status_code == 403

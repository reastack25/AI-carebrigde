from app.extensions import db
from app.models import User


def register_and_login(client, email="patient@example.com", password="Password123", role="patient"):
    if role == "doctor":
        with client.application.app_context():
            doctor = User(
                name="Test Doctor",
                email=email,
                role="doctor",
                specialty="General Practice",
                facility="CareBridge Test Clinic",
            )
            doctor.set_password(password)
            db.session.add(doctor)
            db.session.commit()
    else:
        register_response = client.post(
            "/api/auth/register",
            json={"name": "Test User", "email": email, "password": password},
        )
        assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    return login_response.get_json()["access_token"]

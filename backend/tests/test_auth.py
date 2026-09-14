from conftest import register_and_login


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "carebridge-api"}


def test_register_patient(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Patient",
            "email": "patient@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["email"] == "patient@example.com"
    assert data["user"]["role"] == "patient"


def test_duplicate_email_is_rejected(client):
    register_and_login(client)
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Another Patient",
            "email": "patient@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 409


def test_weak_password_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Test Patient", "email": "patient@example.com", "password": "short"},
    )
    assert response.status_code == 400


def test_login_and_me(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "patient@example.com"


def test_invalid_login_is_rejected(client):
    register_and_login(client)
    response = client.post(
        "/api/auth/login",
        json={"email": "patient@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401

def register_and_login(client, email="patient@example.com", password="Password123"):
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test Patient", "email": email, "password": password},
    )
    assert register_response.status_code == 201
    login_response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    return login_response.get_json()["access_token"]

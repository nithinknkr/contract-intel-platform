import uuid


def _signup(client, email=None, password="TestPassword123!", org_name=None):
    email = email or f"test-{uuid.uuid4()}@example.com"
    org_name = org_name or f"Test Org {uuid.uuid4()}"
    return client.post(
        "/auth/signup",
        json={"email": email, "password": password, "organization_name": org_name},
    ), email, password


def test_signup_creates_user_and_returns_tokens(client):
    response, email, _ = _signup(client)
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_signup_duplicate_email_returns_409(client):
    response1, email, password = _signup(client)
    assert response1.status_code == 201

    response2, _, _ = _signup(client, email=email, password=password)
    assert response2.status_code == 409


def test_login_with_correct_credentials_succeeds(client):
    _, email, password = _signup(client)

    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_with_wrong_password_returns_401(client):
    _, email, _ = _signup(client)

    response = client.post("/auth/login", json={"email": email, "password": "WrongPassword123!"})
    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": f"nobody-{uuid.uuid4()}@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401


def test_login_error_message_identical_for_wrong_password_and_unknown_email(client):
    """
    Guards the deliberate anti-enumeration behavior documented in auth.py:
    same status code AND same detail message whether the email doesn't
    exist or the password is wrong, so an attacker can't distinguish the
    two cases from the response alone.
    """
    _, email, _ = _signup(client)

    wrong_password_response = client.post(
        "/auth/login", json={"email": email, "password": "WrongPassword123!"}
    )
    unknown_email_response = client.post(
        "/auth/login",
        json={"email": f"nobody-{uuid.uuid4()}@example.com", "password": "whatever123"},
    )

    assert wrong_password_response.status_code == unknown_email_response.status_code == 401
    assert wrong_password_response.json()["detail"] == unknown_email_response.json()["detail"]


def test_refresh_returns_new_access_token(client):
    signup_response, _, _ = _signup(client)
    refresh_token = signup_response.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    # No rotation by design (see decisions log) — same refresh token comes back
    assert body["refresh_token"] == refresh_token


def test_refresh_with_invalid_token_returns_401(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    signup_response, _, _ = _signup(client)
    refresh_token = signup_response.json()["refresh_token"]

    logout_response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    # The revoked token must no longer work at /auth/refresh
    refresh_after_logout = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_after_logout.status_code == 401


def test_logout_with_unknown_token_still_returns_204(client):
    """
    Logout on an already-invalid/unknown token shouldn't error — logging out
    twice, or logging out with a token that already expired, should be a
    harmless no-op from the client's perspective.
    """
    response = client.post("/auth/logout", json={"refresh_token": "already-invalid-token"})
    assert response.status_code == 204
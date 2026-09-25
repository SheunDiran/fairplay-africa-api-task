from tests.conftest import register


def test_register_success_hashes_password(client, app):
    response = register(client)
    assert response.status_code == 201
    assert response.json["data"]["email"] == "ada@example.com"
    assert "password_hash" not in response.json["data"]
    from app.extensions import db
    from app.models import User
    with app.app_context():
        user = db.session.get(User, 1)
        assert user.password_hash != "correct-horse-9"
        assert user.check_password("correct-horse-9")


def test_duplicate_email_is_case_insensitive(client):
    register(client)
    response = register(client, name="Another", email="ADA@example.com")
    assert response.status_code == 409
    assert response.json["error"]["code"] == "email_taken"


def test_registration_rejects_invalid_email_and_weak_password(client):
    invalid_email = register(client, email="not-an-email")
    weak_password = register(client, email="weak@example.com", password="short")
    assert invalid_email.status_code == 422
    assert weak_password.status_code == 422


def test_login_success_returns_bearer_token(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "correct-horse-9"})
    assert response.status_code == 200
    assert response.json["data"]["token_type"] == "Bearer"
    assert response.json["data"]["access_token"]


def test_login_rejects_wrong_password(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "incorrect"})
    assert response.status_code == 401
    assert response.json["error"]["code"] == "invalid_credentials"


def test_login_requires_credentials(client):
    response = client.post("/api/auth/login", json={"email": "ada@example.com"})
    assert response.status_code == 422

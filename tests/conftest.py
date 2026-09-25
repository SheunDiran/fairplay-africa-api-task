import pytest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-that-is-long-enough-for-testing-0001"
    JWT_SECRET_KEY = "test-jwt-secret-that-is-long-enough-for-testing-0002"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = False


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, name="Ada Lovelace", email="ada@example.com", password="correct-horse-9"):
    return client.post("/api/auth/register", json={"name": name, "email": email, "password": password})


def login(client, email="ada@example.com", password="correct-horse-9"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.json["data"]["access_token"]


@pytest.fixture()
def auth_headers(client):
    register(client)
    token = login(client)
    return {"Authorization": f"Bearer {token}"}

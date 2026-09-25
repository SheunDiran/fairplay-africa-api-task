from datetime import timedelta

from flask_jwt_extended import create_access_token

from tests.conftest import login, register

CONTENT = {"title": "My Short Film", "description": "An original short film.", "content_type": "video"}


def test_content_requires_authentication(client):
    response = client.post("/api/content", json=CONTENT)
    assert response.status_code == 401


def test_retrieval_requires_authentication(client):
    assert client.get("/api/content").status_code == 401
    assert client.get("/api/content/1").status_code == 401


def test_create_content_returns_registration_reference(client, auth_headers):
    response = client.post("/api/content", json=CONTENT, headers=auth_headers)
    assert response.status_code == 201
    assert response.json["data"]["title"] == CONTENT["title"]
    assert response.json["data"]["registration_reference"].startswith("FPA-")


def test_list_returns_only_authenticated_users_content(client, auth_headers):
    own = client.post("/api/content", json=CONTENT, headers=auth_headers)
    register(client, name="Grace Hopper", email="grace@example.com", password="another-password-1")
    other_headers = {"Authorization": "Bearer " + login(client, "grace@example.com", "another-password-1")}
    client.post("/api/content", json={**CONTENT, "title": "Grace's work"}, headers=other_headers)

    response = client.get("/api/content", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["meta"]["total"] == 1
    assert [item["id"] for item in response.json["data"]] == [own.json["data"]["id"]]


def test_get_own_content(client, auth_headers):
    created = client.post("/api/content", json=CONTENT, headers=auth_headers)
    content_id = created.json["data"]["id"]
    response = client.get(f"/api/content/{content_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["data"]["id"] == content_id


def test_cannot_get_another_users_content(client, auth_headers):
    created = client.post("/api/content", json=CONTENT, headers=auth_headers)
    register(client, name="Grace Hopper", email="grace@example.com", password="another-password-1")
    other_headers = {"Authorization": "Bearer " + login(client, "grace@example.com", "another-password-1")}
    response = client.get(f"/api/content/{created.json['data']['id']}", headers=other_headers)
    assert response.status_code == 404


def test_invalid_content_is_rejected(client, auth_headers):
    response = client.post("/api/content", json={"title": "", "content_type": "video"}, headers=auth_headers)
    assert response.status_code == 422
    assert response.json["error"]["code"] == "validation_error"


def test_nonexistent_content_returns_404(client, auth_headers):
    response = client.get("/api/content/999", headers=auth_headers)
    assert response.status_code == 404


def test_malformed_json_returns_json_error(client, auth_headers):
    response = client.post("/api/content", data="{", content_type="application/json", headers=auth_headers)
    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_json"


def test_non_json_content_type_is_rejected(client, auth_headers):
    response = client.post("/api/content", data="title=film", headers=auth_headers)
    assert response.status_code == 415


def test_invalid_token_is_rejected(client):
    response = client.get("/api/content", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_expired_token_is_rejected(client, app):
    with app.app_context():
        token = create_access_token(identity="1", expires_delta=timedelta(seconds=-1))
    response = client.get("/api/content", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json["error"]["code"] == "token_expired"


def test_pagination_validation(client, auth_headers):
    response = client.get("/api/content?page=0", headers=auth_headers)
    assert response.status_code == 400


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/unknown")
    assert response.status_code == 404
    assert response.json["error"]["code"] == "not_found"

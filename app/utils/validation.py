import re

from flask import jsonify, request

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def error_response(code, message, status):
    return jsonify({"success": False, "error": {"code": code, "message": message}}), status


def json_object():
    if not request.is_json:
        return None, error_response("unsupported_media_type", "Content-Type must be application/json.", 415)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, error_response("invalid_json", "Request body must be a valid JSON object.", 400)
    return payload, None


def validate_registration(payload):
    allowed = {"name", "email", "password"}
    if set(payload) - allowed:
        return "Only name, email, and password are accepted."
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        return "Name is required and must be at most 100 characters."
    if not isinstance(email, str) or len(email.strip()) > 254 or not EMAIL_PATTERN.fullmatch(email.strip()):
        return "A valid email address is required."
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        return "Password must be between 8 and 128 characters."
    return None


def validate_content(payload):
    allowed = {"title", "description", "content_type"}
    if set(payload) - allowed:
        return "Only title, description, and content_type are accepted."
    title = payload.get("title")
    description = payload.get("description", "")
    content_type = payload.get("content_type")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        return "Title is required and must be at most 200 characters."
    if not isinstance(description, str) or len(description) > 5000:
        return "Description must be a string of at most 5000 characters."
    if not isinstance(content_type, str) or not content_type.strip() or len(content_type.strip()) > 50:
        return "Content type is required and must be at most 50 characters."
    return None

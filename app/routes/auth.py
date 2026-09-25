from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import User
from app.utils.validation import error_response, json_object, validate_registration


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload, error = json_object()
    if error:
        return error
    validation_error = validate_registration(payload)
    if validation_error:
        return error_response("validation_error", validation_error, 422)

    email = payload["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return error_response("email_taken", "An account with this email already exists.", 409)

    user = User(name=payload["name"].strip(), email=email)
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat()},
    }), 201


@auth_bp.post("/login")
def login():
    payload, error = json_object()
    if error:
        return error
    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email.strip() or not password:
        return error_response("validation_error", "Email and password are required.", 422)

    user = User.query.filter_by(email=email.strip().lower()).first()
    if user is None or not user.check_password(password):
        return error_response("invalid_credentials", "Email or password is incorrect.", 401)

    token = create_access_token(identity=str(user.id))
    return jsonify({"success": True, "data": {"access_token": token, "token_type": "Bearer"}}), 200

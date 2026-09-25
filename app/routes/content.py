from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Content, User
from app.utils.validation import error_response, json_object, validate_content


content_bp = Blueprint("content", __name__)


def current_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


@content_bp.post("")
@jwt_required()
def create_content():
    user = current_user()
    if user is None:
        return error_response("invalid_token", "The token's user no longer exists.", 401)

    payload, error = json_object()
    if error:
        return error
    validation_error = validate_content(payload)
    if validation_error:
        return error_response("validation_error", validation_error, 422)

    item = Content(
        owner=user,
        title=payload["title"].strip(),
        description=payload.get("description", "").strip(),
        content_type=payload["content_type"].strip().lower(),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "data": item.to_dict()}), 201


@content_bp.get("")
@jwt_required()
def list_content():
    user = current_user()
    if user is None:
        return error_response("invalid_token", "The token's user no longer exists.", 401)

    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "20"))
    except ValueError:
        return error_response("invalid_pagination", "page and per_page must be integers.", 400)
    if page < 1 or per_page < 1 or per_page > 100:
        return error_response("invalid_pagination", "page must be positive and per_page must be between 1 and 100.", 400)

    query = Content.query.filter_by(user_id=user.id).order_by(Content.created_at.desc(), Content.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "success": True,
        "data": [item.to_dict() for item in pagination.items],
        "meta": {"page": page, "per_page": per_page, "total": pagination.total, "pages": pagination.pages},
    }), 200


@content_bp.get("/<int:content_id>")
@jwt_required()
def get_content(content_id):
    user = current_user()
    if user is None:
        return error_response("invalid_token", "The token's user no longer exists.", 401)

    # Filtering by owner makes another user's record indistinguishable from a missing ID.
    item = Content.query.filter_by(id=content_id, user_id=user.id).first()
    if item is None:
        return error_response("not_found", "Content was not found.", 404)
    return jsonify({"success": True, "data": item.to_dict()}), 200

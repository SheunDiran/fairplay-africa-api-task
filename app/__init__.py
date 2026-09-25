from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from config import Config
from app.extensions import db, jwt, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config.get("SECRET_KEY") or not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("SECRET_KEY and JWT_SECRET_KEY must be set in the environment.")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Import models before migrations inspect SQLAlchemy metadata.
    from app.models import Content, User  # noqa: F401
    from app.routes.auth import auth_bp
    from app.routes.content import content_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(content_bp, url_prefix="/api/content")

    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "data": {"status": "ok"}}), 200

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_error):
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": {"code": "conflict", "message": "The request conflicts with an existing record."},
        }), 409

    @app.errorhandler(400)
    def handle_bad_request(_error):
        return jsonify({
            "success": False,
            "error": {"code": "bad_request", "message": "Malformed or invalid request."},
        }), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        status = error.code or 500
        code = "not_found" if status == 404 else "http_error"
        message = "The requested resource was not found." if status == 404 else error.description
        return jsonify({"success": False, "error": {"code": code, "message": message}}), status

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return jsonify({
            "success": False,
            "error": {"code": "authentication_required", "message": "A valid Bearer token is required."},
        }), 401

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return jsonify({
            "success": False,
            "error": {"code": "invalid_token", "message": "The access token is invalid."},
        }), 401

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify({
            "success": False,
            "error": {"code": "token_expired", "message": "The access token has expired."},
        }), 401

    return app

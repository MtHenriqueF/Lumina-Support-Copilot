from __future__ import annotations

import logging

from flask import Flask, jsonify, render_template
from werkzeug.exceptions import HTTPException

from config import build_model_catalog, get_settings
from errors import APIError, InternalAPIError
from routes.support import support_bp
from services.openai_service import OpenAIService
from services.support_service import SupportCopilotService
from utils.logging import configure_logging, log_event


def create_app(test_config: dict | None = None, openai_service: OpenAIService | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(get_settings())

    if test_config:
        app.config.update(test_config)

    app.config["MODEL_CATALOG"] = build_model_catalog(app.config["MODEL_ALIASES"])
    if app.config["DEFAULT_MODEL_ALIAS"] not in app.config["MODEL_ALIASES"]:
        app.config["DEFAULT_MODEL_ALIAS"] = next(iter(app.config["MODEL_ALIASES"]), "balanced")

    configure_logging(app.config["LOG_LEVEL"])
    logger = logging.getLogger("lumina.app")

    provider = openai_service or OpenAIService(
        api_key=app.config["OPENAI_API_KEY"],
        timeout=app.config["OPENAI_TIMEOUT_SECONDS"],
    )
    app.extensions["support_service"] = SupportCopilotService(provider)

    app.register_blueprint(support_bp)

    @app.route("/", methods=["GET"])
    def index():
        return render_template(
            "index.html",
            app_name=app.config["APP_NAME"],
            app_subtitle=app.config["APP_SUBTITLE"],
            message_max_chars=app.config["MESSAGE_MAX_CHARS"],
            default_model=app.config["DEFAULT_MODEL_ALIAS"],
            model_catalog=app.config["MODEL_CATALOG"],
        )

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        log_event(
            logger,
            "warning" if error.status_code < 500 else "error",
            "api_error",
            code=error.code,
            error_type=type(error).__name__,
            status_code=error.status_code,
        )
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        api_error = APIError("bad_request", "A requisicao enviada e invalida.", 400)
        log_event(logger, "warning", "http_error", status_code=400, error_type=type(error).__name__)
        return jsonify(api_error.to_dict()), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        api_error = APIError("not_found", "O recurso solicitado nao foi encontrado.", 404)
        log_event(logger, "warning", "http_error", status_code=404, error_type=type(error).__name__)
        return jsonify(api_error.to_dict()), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        api_error = APIError("method_not_allowed", "Metodo nao permitido para este endpoint.", 405)
        log_event(logger, "warning", "http_error", status_code=405, error_type=type(error).__name__)
        return jsonify(api_error.to_dict()), 405

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if isinstance(error, HTTPException):
            api_error = APIError("http_error", "Nao foi possivel concluir a requisicao.", error.code or 500)
            log_event(
                logger,
                "error" if (error.code or 500) >= 500 else "warning",
                "http_exception",
                status_code=error.code or 500,
                error_type=type(error).__name__,
            )
            return jsonify(api_error.to_dict()), error.code or 500

        log_event(logger, "error", "unhandled_exception", error_type=type(error).__name__)
        api_error = InternalAPIError()
        return jsonify(api_error.to_dict()), api_error.status_code

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])

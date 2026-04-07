from __future__ import annotations

import logging
import time

from flask import Blueprint, current_app, jsonify, request

from errors import ValidationAPIError
from utils.logging import log_event

support_bp = Blueprint("support", __name__)

logger = logging.getLogger("lumina.routes.support")


@support_bp.post("/generate")
def generate():
    started_at = time.perf_counter()
    payload = request.get_json(silent=True)

    if payload is None or not isinstance(payload, dict):
        raise ValidationAPIError("json_required", "Envie um corpo JSON valido com os campos 'message' e 'model'.")

    message_value = payload.get("message")
    model_value = payload.get("model")
    message = "" if message_value is None else str(message_value).strip()
    model_alias = "" if model_value is None else str(model_value).strip().lower()

    if not message:
        raise ValidationAPIError("message_required", "A mensagem nao pode estar vazia.")

    if not model_alias:
        raise ValidationAPIError("model_required", "Selecione um modelo antes de enviar.")

    max_chars = current_app.config["MESSAGE_MAX_CHARS"]
    if len(message) > max_chars:
        raise ValidationAPIError(
            "message_too_long",
            f"A mensagem excede o limite de {max_chars} caracteres.",
        )

    model_aliases = current_app.config["MODEL_ALIASES"]
    if model_alias not in model_aliases:
        raise ValidationAPIError("invalid_model", "O modelo selecionado nao e suportado.")

    support_service = current_app.extensions["support_service"]
    result = support_service.generate_ticket_payload(
        user_message=message,
        model_alias=model_alias,
        model_id=model_aliases[model_alias],
    )

    duration = round(time.perf_counter() - started_at, 2)
    result.update(
        {
            "duration": duration,
            "model": model_alias,
        }
    )

    log_event(
        logger,
        "info",
        "request_completed",
        model_alias=model_alias,
        duration_ms=round(duration * 1000, 2),
        input_chars=len(message),
    )
    return jsonify(result)

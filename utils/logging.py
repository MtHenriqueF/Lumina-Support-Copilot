from __future__ import annotations

import json
import logging


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def log_event(logger: logging.Logger, level: str, event: str, **fields) -> None:
    payload = {"event": event, **fields}
    message = json.dumps(payload, ensure_ascii=False, default=str)
    log_method = getattr(logger, level, logger.info)
    log_method(message)

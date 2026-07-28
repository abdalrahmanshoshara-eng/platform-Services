"""Structured JSON logging with the request correlation id attached."""

import json
import logging

from .correlation import get_correlation_id

_EXTRA_KEYS = ("report_id", "task_id", "action", "duration", "user_id", "outcome")


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        for key in _EXTRA_KEYS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

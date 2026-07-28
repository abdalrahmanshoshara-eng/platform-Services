"""Phase 9: structured logging carries the correlation id."""

import json
import logging

from reports.shared.correlation import set_correlation_id
from reports.shared.logging import CorrelationIdFilter, JsonFormatter


def test_json_formatter_includes_correlation_id():
    set_correlation_id("cid-123")
    record = logging.LogRecord("reports", logging.INFO, __file__, 1, "hello", None, None)
    CorrelationIdFilter().filter(record)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["correlation_id"] == "cid-123"
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"

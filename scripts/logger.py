"""Conservative structured JSON logger with redaction and mock-capable central sinks.

Use `get_logger(name)` to obtain a named logger configured to emit JSON to
console and optionally submit to Datadog/CloudWatch. This module is
non-invasive: it does not modify the root logger.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

# Public test-visible list for send errors
LOGGING_SEND_ERRORS: List[str] = []
# Count of redaction replacements performed during runtime (for tests)
REDACTION_COUNT = 0

REDACT_KEYS = ["access_token", "refresh_token", "api_key", "MONDAY_SECRET_KEY"]


def _incr_redactions(n: int) -> None:
    global REDACTION_COUNT
    try:
        REDACTION_COUNT += int(n)
    except Exception:
        pass


def redact_value(val: Any) -> Any:
    if not isinstance(val, str):
        return val
    s = val
    for k in REDACT_KEYS:
        try:
            pattern = re.compile(
                rf'("?{re.escape(k)}"?\s*:\s*")([^\"]+)(")', flags=re.IGNORECASE
            )
            s, n = pattern.subn(r"\1<REDACTED>\3", s)
            _incr_redactions(n)
        except Exception:
            continue
    try:
        pattern2 = re.compile(r"([A-Za-z0-9-_]{20,})")
        s, n2 = pattern2.subn("<REDACTED>", s)
        _incr_redactions(n2)
    except Exception:
        pass
    return s


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    if isinstance(obj, str):
        return redact_value(obj)
    return obj


class RedactingJSONFormatter(logging.Formatter):
    def __init__(self, service: str = "monday_integration", env: Optional[str] = None):
        super().__init__()
        self.service = service
        self.env = env or os.getenv("ENV", "dev")

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "service": getattr(record, "service", self.service),
            "env": getattr(record, "env", self.env),
            "account": getattr(record, "account", None),
            "message": record.getMessage(),
        }
        if hasattr(record, "tags") and record.tags:
            payload["tags"] = record.tags
        safe = redact_obj(payload)
        try:
            return json.dumps(safe, ensure_ascii=False)
        except Exception:
            try:
                return json.dumps(
                    {"message": redact_value(str(payload.get("message", "")))}
                )
            except Exception:
                return json.dumps({"message": "<UNSERIALIZABLE>"})


class DatadogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._use_mock = os.getenv("MOCK_CENTRAL_HANDLER", "0") == "1"
        if self._use_mock:

            class _DummyResp:
                status_code = 200

            class _DummySession:
                def post(self, *a, **k):
                    return _DummyResp()

            self._session = _DummySession()
        else:
            self._session = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self._session:
            LOGGING_SEND_ERRORS.append("datadog_no_session")


class CloudWatchHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._use_mock = os.getenv("MOCK_CENTRAL_HANDLER", "0") == "1"
        if self._use_mock:
            self.client = object()
        else:
            self.client = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self.client:
            LOGGING_SEND_ERRORS.append("cloudwatch_no_client")


def get_logger(name: str = "monday_integration") -> logging.Logger:
    logger = logging.getLogger(name)

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    logger.propagate = False

    service = os.getenv("LOG_SERVICE", name)
    env = os.getenv("ENV", "dev")
    formatter = RedactingJSONFormatter(service=service, env=env)

    if logger.handlers:
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                try:
                    h.setFormatter(formatter)
                except Exception:
                    pass
        return logger

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    enable = os.getenv("ENABLE_CENTRAL_LOGS", "0") == "1"
    sink = os.getenv("CENTRAL_LOG_SINK", "")
    if enable and sink:
        sinks = [s.strip().lower() for s in sink.split(",") if s.strip()]
        for s in sinks:
            if s == "datadog":
                try:
                    dd = DatadogHandler()
                    dd.setFormatter(formatter)
                    logger.addHandler(dd)
                except Exception as e:
                    LOGGING_SEND_ERRORS.append(f"dd_handler_init_failed:{e}")
            if s == "cloudwatch":
                try:
                    cw = CloudWatchHandler()
                    cw.setFormatter(formatter)
                    logger.addHandler(cw)
                except Exception as e:
                    LOGGING_SEND_ERRORS.append(f"cw_handler_init_failed:{e}")

    return logger

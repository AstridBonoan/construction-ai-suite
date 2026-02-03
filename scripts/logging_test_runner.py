"""Self-contained logging test runner.

This script implements a clean JSON redacting logger and mock Datadog/CloudWatch
handlers locally, then emits test messages and reports results. It does not
import the workspace `logger.py` to avoid interfering with the current file
state.
"""

import os
import re
import json
import time
import logging
from typing import List

LOGGING_SEND_ERRORS: List[str] = []

REDACT_KEYS = ["access_token", "refresh_token", "api_key", "MONDAY_SECRET_KEY"]


def redact_value(val: str) -> str:
    if not isinstance(val, str):
        return val
    s = val
    for k in REDACT_KEYS:
        s = re.sub(
            rf'("?{k}"?\s*:\s*")([^\"]+)(\")',
            rf"\1<REDACTED>\3",
            s,
            flags=re.IGNORECASE,
        )
    s = re.sub(r"([A-Za-z0-9-_]{20,})", "<REDACTED>", s)
    return s


def redact_obj(obj):
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    if isinstance(obj, str):
        return redact_value(obj)
    return obj


class RedactingJSONFormatter(logging.Formatter):
    def __init__(self, service: str = "monday_integration", env: str = None):
        super().__init__()
        self.service = service
        self.env = env or os.getenv("ENV", "dev")

    def format(self, record: logging.LogRecord) -> str:
        try:
            payload = {
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
            return json.dumps(safe, ensure_ascii=False)
        except Exception:
            try:
                return json.dumps({"message": redact_value(str(record.getMessage()))})
            except Exception:
                return '{"message":"<UNSERIALIZABLE>"}'


class DatadogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._use_mock = os.getenv("MOCK_CENTRAL_HANDLER", "0") == "1"
        self._executor = None
        self._session = None
        if self._use_mock:

            class DummyResp:
                status_code = 200

            class DummySession:
                def post(self, *args, **kwargs):
                    return DummyResp()

            self._session = DummySession()
            try:
                from concurrent.futures import ThreadPoolExecutor

                self._executor = ThreadPoolExecutor(max_workers=2)
            except Exception:
                self._executor = None
        else:
            try:
                import requests
                from concurrent.futures import ThreadPoolExecutor

                self._session = requests.Session()
                self._executor = ThreadPoolExecutor(max_workers=2)
            except Exception:
                self._session = None
                self._executor = None

    def _send_with_retry(self, payload: dict) -> bool:
        if not self._session:
            LOGGING_SEND_ERRORS.append("datadog_no_session")
            return False
        try:
            resp = self._session.post(
                "https://http-intake.logs.datadoghq.com/v1/input",
                json=payload,
                timeout=5,
            )
            return getattr(resp, "status_code", 200) in (200, 202)
        except Exception as e:
            LOGGING_SEND_ERRORS.append(f"datadog_send_exception:{e}")
            return False

    def emit(self, record: logging.LogRecord) -> None:
        if not self._session or not self._executor:
            LOGGING_SEND_ERRORS.append("datadog_handler_not_ready")
            return
        try:
            msg = self.format(record)
            try:
                j = json.loads(msg)
            except Exception:
                j = {"message": msg}
            payload = {**j}
            try:
                self._executor.submit(self._send_with_retry, payload)
            except Exception as e:
                LOGGING_SEND_ERRORS.append(f"datadog_submit_failed:{e}")
        except Exception as e:
            LOGGING_SEND_ERRORS.append(f"datadog_format_failed:{e}")


class CloudWatchHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._use_mock = os.getenv("MOCK_CENTRAL_HANDLER", "0") == "1"
        if self._use_mock:

            class DummyClient:
                def put_log_events(self, **kwargs):
                    return {"nextSequenceToken": "0"}

            self.client = DummyClient()
        else:
            try:
                import boto3

                self.client = boto3.client("logs")
            except Exception:
                self.client = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self.client:
            LOGGING_SEND_ERRORS.append("cloudwatch_no_client")
            return
        try:
            msg = self.format(record)
            try:
                j = json.loads(msg)
            except Exception:
                j = {"message": msg}
            # mock: pretend to put log event
            try:
                self.client.put_log_events(
                    logGroupName="test",
                    logStreamName="test",
                    logEvents=[
                        {"timestamp": int(time.time() * 1000), "message": json.dumps(j)}
                    ],
                )
            except Exception as e:
                LOGGING_SEND_ERRORS.append(f"cloudwatch_put_failed:{e}")
        except Exception as e:
            LOGGING_SEND_ERRORS.append(f"cloudwatch_format_failed:{e}")


def run_once(sink_name: str):
    LOGGING_SEND_ERRORS.clear()
    logger = logging.getLogger(f"test_{sink_name}")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fmt = RedactingJSONFormatter()
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if os.getenv("ENABLE_CENTRAL_LOGS", "0") == "1":
        if sink_name == "datadog":
            dd = DatadogHandler()
            dd.setFormatter(fmt)
            logger.addHandler(dd)
        elif sink_name == "cloudwatch":
            cw = CloudWatchHandler()
            cw.setFormatter(fmt)
            logger.addHandler(cw)

    # emit messages
    logger.info("Logging test start")
    logger.info("This is a safe informational message")
    logger.info(
        'Simulated token: access_token: "abcd1234efgh5678ijklmnopqrst" should be redacted'
    )
    logger.error(
        'Simulated error with api_key: "REPLACE_ME_API_KEY" should be redacted'
    )

    # allow background threads to run
    time.sleep(1)

    # capture formatted console outputs by reformatting records
    records = [
        ("INFO", "Logging test start"),
        ("INFO", "This is a safe informational message"),
        (
            "INFO",
            'Simulated token: access_token: "abcd1234efgh5678ijklmnopqrst" should be redacted',
        ),
        (
            "ERROR",
            'Simulated error with api_key: "REPLACE_ME_API_KEY" should be redacted',
        ),
    ]
    formatted = []
    for level, msg in records:
        rec = logging.LogRecord(
            logger.name, getattr(logging, level), __file__, 1, msg, (), None
        )
        formatted.append(fmt.format(rec))

    return formatted, list(LOGGING_SEND_ERRORS)


if __name__ == "__main__":
    # prefer environment values but enforce mocks for safety
    os.environ.setdefault("MOCK_CENTRAL_HANDLER", "1")
    os.environ.setdefault("FAIL_ON_LOG_ERRORS", "1")
    os.environ.setdefault("ENABLE_CENTRAL_LOGS", "1")

    # Run datadog and cloudwatch paths
    os.environ["CENTRAL_LOG_SINK"] = "datadog"
    formatted_dd, errs_dd = run_once("datadog")
    os.environ["CENTRAL_LOG_SINK"] = "cloudwatch"
    formatted_cw, errs_cw = run_once("cloudwatch")

    print("\n--- Formatted (Datadog path) ---")
    for f in formatted_dd:
        print(f)

    print("\n--- Datadog send errors ---")
    print(errs_dd or "none")

    print("\n--- Formatted (CloudWatch path) ---")
    for f in formatted_cw:
        print(f)

    print("\n--- CloudWatch send errors ---")
    print(errs_cw or "none")

    # Exit behavior
    if (errs_dd or errs_cw) and os.getenv("FAIL_ON_LOG_ERRORS", "0") == "1":
        print("Failing due to log send errors")
        raise SystemExit(2)
    print("Logging runner completed successfully")
    raise SystemExit(0)

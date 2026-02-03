"""
Lightweight test to exercise centralized logging handlers without exposing secrets.

Usage:
  ENABLE_CENTRAL_LOGS=1 CENTRAL_LOG_SINK=datadog DATADOG_API_KEY=... python scripts/logging_test.py
  ENABLE_CENTRAL_LOGS=1 CENTRAL_LOG_SINK=cloudwatch python scripts/logging_test.py

The test sends a few log lines (including values that look like tokens) and verifies no exceptions.
"""

from logger import get_logger, LOGGING_SEND_ERRORS
import os
import sys
import time


def run_logging_test() -> int:
    logger = get_logger("logging_test")

    logger.info("Logging test start")
    logger.info("This is a safe informational message")
    logger.info(
        'Simulated token: access_token: "abcd1234efgh5678ijklmnopqrst" should be redacted'
    )
    logger.error(
        'Simulated error with api_key: "REPLACE_ME_API_KEY" should be redacted'
    )

    # give background threads a moment to flush
    time.sleep(1)

    errs = LOGGING_SEND_ERRORS
    if errs:
        print("Logging test detected send errors:", errs)
        # By default, treat send errors as non-fatal unless explicitly required
        if os.getenv("FAIL_ON_LOG_ERRORS", "0") == "1":
            print("Failing due to log send errors (FAIL_ON_LOG_ERRORS=1)")
            return 2
        else:
            print(
                "Send errors present but continuing (set FAIL_ON_LOG_ERRORS=1 to make CI fail)"
            )
            return 0

    print("Logging test completed successfully. No send errors detected.")
    return 0


if __name__ == "__main__":
    sys.exit(run_logging_test())

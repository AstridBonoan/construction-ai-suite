"""
Monday.com integration script (production-ready, multi-tenant, safe-by-default).

This script supports per-account JSON configs and can run against a single
config (`--config`) or a directory of configs (`--configs-dir`). Each config
contains the API key, board id and column id mappings. No code edits are
required per customer.

Usage (dry-run, safe):

    # dry-run prevents any live writes
    $env:DRY_RUN = '1'
    python scripts\monday_integration.py --configs-dir configs/

Create a per-account config with `scripts/monday_setup.py`.

To perform live updates (ONLY after onboarding and verifying each config):

    $env:DRY_RUN = '0'
    python scripts\monday_integration.py --configs-dir configs/

Security notes:
 - Do NOT commit config files containing API keys to source control.
 - Prefer using an encrypted secret store in production; this script reads
     configs from disk for convenience and testing.
"""

import os
import csv
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Guard network imports so pre-commit and CI-safe runs don't require network libs.
# When MOCK_CENTRAL_HANDLER=1 we avoid importing network packages to remain offline-safe.
if os.getenv("MOCK_CENTRAL_HANDLER", "0") == "1":
    requests = None
else:
    try:
        import requests
    except Exception:
        requests = None
try:
    from logger import get_logger
except Exception:
    try:
        from scripts.logger import get_logger
    except Exception:
        # fallback minimal logger
        import logging

        def get_logger(name: str = "monday_integration"):
            return logging.getLogger(name)

logger = get_logger("monday_integration")
try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

# Paths
INPUT_CSV = Path("data_splits/project_level_for_monday.csv")
REPORT_PATH = Path("reports/monday_integration_report.json")

# Safety defaults: dry-run unless explicitly changed in env
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
# Read credentials from env by default; can be overridden by a per-account JSON config.
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
MONDAY_CONFIG = os.getenv("MONDAY_CONFIG")  # path to per-account JSON config

# --- PLACEHOLDERS: replace these with your Monday.com column IDs ---
# Column where project_id is stored (if using a column to match items)
PROJECT_ID_COLUMN_ID = "PROJECT_ID_COLUMN_PLACEHOLDER"
# Column IDs for the fields we want to set/update
COL_PREDICTED_DELAY = "PREDICTED_DELAY_COLUMN_PLACEHOLDER"
COL_REVENUE = "REVENUE_COLUMN_PLACEHOLDER"
COL_RISK = "RISK_COLUMN_PLACEHOLDER"
COL_STATUS = "STATUS_COLUMN_PLACEHOLDER"
# ------------------------------------------------------------------

HEADERS = None

# Load per-account config if provided. The JSON should contain at least:
# { "api_key": "...", "board_id": 12345678, "columns": {"project_id": "col1", ...} }
if MONDAY_CONFIG:
    try:
        cfg_path = Path(MONDAY_CONFIG)
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as cf:
                cfg = json.load(cf)
            # prefer explicit config values
            MONDAY_API_KEY = cfg.get("api_key") or MONDAY_API_KEY
            MONDAY_BOARD_ID = cfg.get("board_id") or MONDAY_BOARD_ID
            cols = cfg.get("columns") or {}
            PROJECT_ID_COLUMN_ID = cols.get("project_id", PROJECT_ID_COLUMN_ID)
            COL_PREDICTED_DELAY = cols.get("predicted_delay", COL_PREDICTED_DELAY)
            COL_REVENUE = cols.get("revenue", COL_REVENUE)
            COL_RISK = cols.get("risk", COL_RISK)
            COL_STATUS = cols.get("status", COL_STATUS)
    except Exception as e:
        print(f"Warning: failed to read MONDAY_CONFIG {MONDAY_CONFIG}: {e}")

if MONDAY_API_KEY:
    HEADERS = {"Authorization": MONDAY_API_KEY, "Content-Type": "application/json"}


class MondayClient:
    """Encapsulates Monday API calls for a single account/board."""

    def __init__(
        self,
        api_key: str,
        board_id: int,
        columns: Dict[str, str],
        cfg: dict = None,
        cfg_path: Path = None,
        encrypted: bool = False,
    ):
        self.api_key = api_key
        self.board_id = int(board_id) if board_id is not None else None
        self.columns = columns or {}
        self.headers = (
            {"Authorization": api_key, "Content-Type": "application/json"}
            if api_key
            else None
        )
        # token metadata and persistence
        self.cfg = cfg
        self.cfg_path = cfg_path
        self.encrypted = encrypted
        # token info may be under cfg['token'] or legacy cfg['api_key']
        self.token_info = (cfg or {}).get("token") if cfg else None

    def _persist_token(self):
        if not self.cfg_path:
            return
        # update cfg token and save
        if self.token_info is not None:
            self.cfg["token"] = self.token_info
            save_config(self.cfg_path, self.cfg, self.encrypted)

    def run_query(self, query: str, variables: dict = None):
        if DRY_RUN:
            raise RuntimeError("run_query called in DRY_RUN mode")
        # ensure headers up-to-date from token
        if self.token_info:
            self.headers = {
                "Authorization": self.token_info.get("access_token"),
                "Content-Type": "application/json",
            }
        if not self.headers:
            raise RuntimeError("MONDAY_API_KEY not set for this account")
        url = "https://api.monday.com/v2"
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def find_item_by_project_id(self, project_id: str) -> Optional[str]:
        # ensure token valid
        self.ensure_token_valid()
        col = self.columns.get("project_id")
        if DRY_RUN:
            return None
        if not col:
            raise RuntimeError("project_id column not configured for this account")
        query = """
        query ($boardId:Int!, $columnId:String!, $value:String!) {
          items_by_column_values(board_id: $boardId, column_id: $columnId, column_value: $value) {
            id
            name
          }
        }
        """
        variables = {
            "boardId": self.board_id,
            "columnId": col,
            "value": str(project_id),
        }
        resp = self.run_query(query, variables)
        items = resp.get("data", {}).get("items_by_column_values", [])
        return items[0]["id"] if items else None

    def create_item(self, project_row: dict) -> Dict[str, Any]:
        if DRY_RUN:
            return {"action": "create", "project_id": project_row.get("project_id")}
        if not self.board_id:
            raise RuntimeError("board_id not set for this account")
        # ensure token valid
        self.ensure_token_valid()
        name = str(project_row.get("project_id"))
        create_mutation = """
        mutation ($boardId:Int!, $itemName:String!) {
          create_item (board_id:$boardId, item_name:$itemName) { id }
        }
        """
        resp = self.run_query(
            create_mutation, {"boardId": self.board_id, "itemName": name}
        )
        item_id = resp.get("data", {}).get("create_item", {}).get("id")

        # map provided columns only
        column_values = {}
        for key in ("predicted_delay", "revenue", "risk", "status"):
            col_id = self.columns.get(key)
            if col_id:
                column_values[col_id] = str(project_row.get(key, ""))

        if column_values:
            change_mutation = """
            mutation ($itemId:Int!, $boardId:Int!, $columnVals:JSON!) {
              change_multiple_column_values(item_id:$itemId, board_id:$boardId, column_values:$columnVals) { id }
            }
            """
            self.run_query(
                change_mutation,
                {
                    "itemId": int(item_id),
                    "boardId": int(self.board_id),
                    "columnVals": json.dumps(column_values),
                },
            )

        return {"action": "create", "item_id": item_id}

    def update_item(self, item_id: str, project_row: dict) -> Dict[str, Any]:
        if DRY_RUN:
            return {
                "action": "update",
                "item_id": item_id,
                "project_id": project_row.get("project_id"),
            }
        self.ensure_token_valid()
        column_values = {}
        for key in ("predicted_delay", "revenue", "risk", "status"):
            col_id = self.columns.get(key)
            if col_id:
                column_values[col_id] = str(project_row.get(key, ""))
        if column_values:
            change_mutation = """
            mutation ($itemId:Int!, $boardId:Int!, $columnVals:JSON!) {
              change_multiple_column_values(item_id:$itemId, board_id:$boardId, column_values:$columnVals) { id }
            }
            """
            self.run_query(
                change_mutation,
                {
                    "itemId": int(item_id),
                    "boardId": int(self.board_id),
                    "columnVals": json.dumps(column_values),
                },
            )
        return {"action": "update", "item_id": item_id}

    def ensure_token_valid(self):
        """Refresh token if it's expired or near expiry. Updates self.token_info and persists it."""
        if DRY_RUN:
            return
        token = self.token_info or {"access_token": self.api_key}
        # if we don't have token or no expiry, assume api_key provided and proceed
        expires_at = token.get("expires_at")
        now = int(time.time())
        # refresh if expires_at exists and is close
        if expires_at and now + 60 < int(expires_at):
            # still valid
            self.api_key = token.get("access_token")
            self.headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            }
            return

        # try to refresh if refresh_token present
        refresh_token = token.get("refresh_token")
        client_id = os.getenv("MONDAY_OAUTH_CLIENT_ID")
        client_secret = os.getenv("MONDAY_OAUTH_CLIENT_SECRET")
        if not refresh_token or not client_id or not client_secret:
            # cannot refresh
            self.api_key = token.get("access_token")
            self.headers = (
                {"Authorization": self.api_key, "Content-Type": "application/json"}
                if self.api_key
                else None
            )
            return

        # perform refresh
        token_url = "https://auth.monday.com/oauth2/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        # retry with exponential backoff
        backoff = 1
        last_exc = None
        for _ in range(4):
            try:
                resp = requests.post(token_url, data=payload, timeout=30)
                resp.raise_for_status()
                new_token = resp.json()
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                time.sleep(backoff)
                backoff *= 2
        if last_exc:
            raise RuntimeError(f"Failed to refresh token: {last_exc}")
        if new_token.get("expires_in"):
            new_token["expires_at"] = int(time.time()) + int(new_token["expires_in"])
        # update token_info and persist
        self.token_info = new_token
        self.api_key = new_token.get("access_token")
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            self._persist_token()
        except Exception:
            # do not fail operations due to persistence issues
            pass


def run_query(query: str, variables: dict = None):
    """Run a GraphQL query against Monday.com. Requires MONDAY_API_KEY and DRY_RUN=False."""
    if DRY_RUN:
        raise RuntimeError("run_query called in DRY_RUN mode")
    if not HEADERS:
        raise RuntimeError("MONDAY_API_KEY not set")
    url = "https://api.monday.com/v2"
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find_item_by_project_id(project_id: str):
    """Find an item by project_id column value. Returns item id or None.

    IMPORTANT: requires PROJECT_ID_COLUMN_ID to be set to the column's internal id.
    """
    if DRY_RUN:
        return None
    if PROJECT_ID_COLUMN_ID.startswith("PROJECT_ID_COLUMN_PLACEHOLDER"):
        raise RuntimeError(
            "Set PROJECT_ID_COLUMN_ID to your board's project id column ID before running live"
        )

    query = """
    query ($boardId:Int!, $columnId:String!, $value:String!) {
      items_by_column_values(board_id: $boardId, column_id: $columnId, column_value: $value) {
        id
        name
      }
    }
    """
    variables = {
        "boardId": int(MONDAY_BOARD_ID),
        "columnId": PROJECT_ID_COLUMN_ID,
        "value": str(project_id),
    }
    resp = run_query(query, variables)
    items = resp.get("data", {}).get("items_by_column_values", [])
    return items[0]["id"] if items else None


def create_item(project_row: dict):
    """Create an item on the board and set initial column values.

    The mutation below creates an item and then updates multiple column values.
    Replace or extend `column_values` mapping to match your board's column IDs.
    """
    if DRY_RUN:
        return {"action": "create", "project_id": project_row["project_id"]}
    if not MONDAY_BOARD_ID:
        raise RuntimeError("MONDAY_BOARD_ID not set")

    name = str(project_row["project_id"])
    create_mutation = """
    mutation ($boardId:Int!, $itemName:String!) {
      create_item (board_id:$boardId, item_name:$itemName) { id }
    }
    """
    resp = run_query(
        create_mutation, {"boardId": int(MONDAY_BOARD_ID), "itemName": name}
    )
    item_id = resp.get("data", {}).get("create_item", {}).get("id")

    # prepare column values mapping
    column_values = {
        COL_PREDICTED_DELAY: str(project_row.get("predicted_delay", "")),
        COL_REVENUE: str(project_row.get("revenue", "")),
        COL_RISK: str(project_row.get("risk", "")),
        COL_STATUS: str(project_row.get("status", "")),
    }
    # remove placeholders check
    if any(
        k.endswith("PLACEHOLDER")
        for k in (COL_PREDICTED_DELAY, COL_REVENUE, COL_RISK, COL_STATUS)
    ):
        raise RuntimeError("Replace column ID placeholders before running live")

    # change multiple column values
    change_mutation = """
    mutation ($itemId:Int!, $boardId:Int!, $columnVals:JSON!) {
      change_multiple_column_values(item_id:$itemId, board_id:$boardId, column_values:$columnVals) { id }
    }
    """
    run_query(
        change_mutation,
        {
            "itemId": int(item_id),
            "boardId": int(MONDAY_BOARD_ID),
            "columnVals": json.dumps(column_values),
        },
    )
    return {"action": "create", "item_id": item_id}


def update_item(item_id: str, project_row: dict):
    """Update an existing item with new column values."""
    if DRY_RUN:
        return {
            "action": "update",
            "item_id": item_id,
            "project_id": project_row["project_id"],
        }
    if any(
        k.endswith("PLACEHOLDER")
        for k in (COL_PREDICTED_DELAY, COL_REVENUE, COL_RISK, COL_STATUS)
    ):
        raise RuntimeError("Replace column ID placeholders before running live")

    column_values = {
        COL_PREDICTED_DELAY: str(project_row.get("predicted_delay", "")),
        COL_REVENUE: str(project_row.get("revenue", "")),
        COL_RISK: str(project_row.get("risk", "")),
        COL_STATUS: str(project_row.get("status", "")),
    }
    change_mutation = """
    mutation ($itemId:Int!, $boardId:Int!, $columnVals:JSON!) {
      change_multiple_column_values(item_id:$itemId, board_id:$boardId, column_values:$columnVals) { id }
    }
    """
    run_query(
        change_mutation,
        {
            "itemId": int(item_id),
            "boardId": int(MONDAY_BOARD_ID),
            "columnVals": json.dumps(column_values),
        },
    )
    return {"action": "update", "item_id": item_id}


def load_config(path: Path) -> dict:
    # use secret manager backend if configured
    try:
        from secret_manager import get_manager

        mgr = get_manager()
        cfg = mgr.load(path)
        # local manager returns plain dict; indicate if encrypted by checking raw file
        encrypted = False
        try:
            # if local file wrapped with _encrypted, mark encrypted true
            raw = json.load(open(path, "r", encoding="utf-8"))
            encrypted = isinstance(raw, dict) and raw.get("_encrypted") is True
        except Exception:
            encrypted = False
        return cfg, encrypted
    except Exception:
        # fallback to previous logic
        with open(path, "r", encoding="utf-8") as f:
            wrapper = json.load(f)
        # detect encrypted wrapper
        if isinstance(wrapper, dict) and wrapper.get("_encrypted"):
            secret = os.getenv("MONDAY_SECRET_KEY")
            if not secret:
                raise RuntimeError(
                    f"Config {path} is encrypted but MONDAY_SECRET_KEY is not set"
                )
            if Fernet is None:
                raise RuntimeError(
                    "cryptography package required to decrypt configs; pip install cryptography"
                )
            f = Fernet(secret.encode())
            raw = f.decrypt(wrapper["payload"].encode("utf-8"))
            cfg = json.loads(raw.decode("utf-8"))
            return cfg, True
        return wrapper, False


def save_config(path: Path, cfg: dict, encrypted: bool):
    try:
        from secret_manager import get_manager

        mgr = get_manager()
        mgr.save(path, cfg, encrypt=encrypted)
    except Exception:
        # fallback to local save
        path.parent.mkdir(parents=True, exist_ok=True)
        if encrypted:
            secret = os.getenv("MONDAY_SECRET_KEY")
            if not secret:
                raise RuntimeError(
                    "MONDAY_SECRET_KEY not set; cannot save encrypted config"
                )
            if Fernet is None:
                raise RuntimeError(
                    "cryptography package required to encrypt configs; pip install cryptography"
                )
            f = Fernet(secret.encode())
            raw = json.dumps(cfg).encode("utf-8")
            token = f.encrypt(raw).decode("utf-8")
            wrapper = {"_encrypted": True, "payload": token}
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(wrapper, fh, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(cfg, fh, indent=2)


def process_account_config(
    cfg: dict,
    cfg_name: str,
    input_csv: Path,
    report_dir: Path,
    cfg_path: Path = None,
    encrypted: bool = False,
):
    api_key = cfg.get("api_key") or (cfg.get("token") or {}).get("access_token")
    board_id = cfg.get("board_id")
    columns = cfg.get("columns", {})

    # Basic validation
    if not api_key and not DRY_RUN:
        raise RuntimeError(f"Config {cfg_name} missing 'api_key'.")
    if not board_id:
        raise RuntimeError(f"Config {cfg_name} missing 'board_id'.")
    if "project_id" not in columns:
        raise RuntimeError(
            f"Config {cfg_name} missing column mapping for 'project_id' (required)."
        )

    client = MondayClient(
        api_key, board_id, columns, cfg=cfg, cfg_path=cfg_path, encrypted=encrypted
    )

    report = {"created": 0, "updated": 0, "failed": [], "ops": []}

    with open(input_csv, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            project_id = row.get("project_id")
            if not project_id:
                report["failed"].append(
                    {"project_id": project_id, "error": "missing project_id"}
                )
                continue
            try:
                item_id = client.find_item_by_project_id(project_id)
                if item_id:
                    client.update_item(item_id, row)
                    report["updated"] += 1
                    report["ops"].append(
                        {
                            "action": "update",
                            "project_id": project_id,
                            "item_id": item_id,
                        }
                    )
                else:
                    res = client.create_item(row)
                    report["created"] += 1
                    report["ops"].append(
                        {
                            "action": "create",
                            "project_id": project_id,
                            "item_id": res.get("item_id"),
                        }
                    )
                time.sleep(0.05)
            except Exception as e:
                report["failed"].append({"project_id": project_id, "error": str(e)})

    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = report_dir / f"monday_integration_report_{cfg_name}.json"
    with open(out_path, "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)
    return out_path, report


def main():
    parser = argparse.ArgumentParser(
        description="Run Monday.com integration for one or more account configs"
    )
    parser.add_argument("--config", help="Path to a single account JSON config")
    parser.add_argument(
        "--configs-dir", help="Directory containing per-account JSON configs"
    )
    parser.add_argument("--input-csv", help="Input CSV path", default=str(INPUT_CSV))
    parser.add_argument(
        "--report-dir", help="Directory to write per-account reports", default="reports"
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    report_dir = Path(args.report_dir)

    if not input_csv.exists():
        logger.error(f"input file not found: {input_csv}")
        return

    configs = []
    if args.config:
        configs.append(Path(args.config))
    if args.configs_dir:
        p = Path(args.configs_dir)
        if not p.exists() or not p.is_dir():
            print(f"ERROR: configs-dir not found or not a directory: {p}")
            return
        configs.extend(
            sorted([x for x in p.iterdir() if x.suffix.lower() in (".json",)])
        )
    if MONDAY_CONFIG and not configs:
        configs.append(Path(MONDAY_CONFIG))

    if not configs:
        print(
            "No config provided. Use --config or --configs-dir, or set MONDAY_CONFIG env var."
        )
        return

    logger.info(f"DRY_RUN={DRY_RUN} | processing {len(configs)} config(s)")

    for cfg_path in configs:
        cfg_name = cfg_path.stem
        logger.info(f"Processing {cfg_name} -> {cfg_path}")
        try:
            cfg, encrypted = load_config(cfg_path)
            out_path, report = process_account_config(
                cfg,
                cfg_name,
                input_csv,
                report_dir,
                cfg_path=cfg_path,
                encrypted=encrypted,
            )
            logger.info(
                f"Wrote report {out_path} - created {report['created']}, updated {report['updated']}, failed {len(report['failed'])}"
            )
        except Exception as e:
            logger.error(f"ERROR processing {cfg_path}: {e}")


def readiness_check():
    """Simple readiness helper: confirms script and CSV presence."""
    ok = True
    if not INPUT_CSV.exists():
        print(f"MISSING: {INPUT_CSV}")
        ok = False
    if DRY_RUN:
        logger.info("DRY_RUN is enabled — no live API calls will be made")
    else:
        logger.info(
            "DRY_RUN disabled — script will attempt live API calls if credentials and column IDs are set"
        )

    placeholders = [
        PROJECT_ID_COLUMN_ID,
        COL_PREDICTED_DELAY,
        COL_REVENUE,
        COL_RISK,
        COL_STATUS,
    ]
    if any(p.endswith("PLACEHOLDER") for p in placeholders):
        print(
            "NOTE: Some column ID placeholders are still present — replace them before running live"
        )

    if ok:
        logger.info("Integration scripts ready.")
        logger.info(
            "Enter your MONDAY_API_KEY, MONDAY_BOARD_ID, and column IDs in monday_integration.py placeholders before live run."
        )


if __name__ == "__main__":
    readiness_check()
    main()

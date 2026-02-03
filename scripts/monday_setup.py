"""
Interactive helper to create a per-account Monday.com JSON config.

Features:
 - Manual: prompt for API key, list boards/columns, let user map columns.
 - OAuth: run a local OAuth server, have user authorize via browser, exchange
     code for token, then list boards/columns and let user map columns.

Usage (manual API key):
    python scripts\monday_setup.py --output configs/acme_monday.json

Usage (OAuth):
    # set MONDAY_OAUTH_CLIENT_ID and MONDAY_OAUTH_CLIENT_SECRET env vars
    python scripts\monday_setup.py --output configs/acme_acme.json --oauth --port 8000

Notes:
    - Do NOT commit created config files to source control; they contain API keys.
    - DRY_RUN=1 will simulate OAuth and will not persist real tokens.
"""

import os
import json
import argparse
from pathlib import Path
import getpass
import requests
from logger import get_logger

logger = get_logger("monday_setup")
import threading
import uuid
import time as _time
from pathlib import Path

from monday_oauth_server import run_server

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None


def encrypt_payload(obj: dict, key_b64: str) -> dict:
    if Fernet is None:
        raise RuntimeError("cryptography not installed; run pip install cryptography")
    f = Fernet(key_b64.encode())
    raw = json.dumps(obj).encode("utf-8")
    token = f.encrypt(raw)
    return {"_encrypted": True, "payload": token.decode("utf-8")}


def decrypt_payload(wrapper: dict, key_b64: str) -> dict:
    if Fernet is None:
        raise RuntimeError("cryptography not installed; run pip install cryptography")
    f = Fernet(key_b64.encode())
    raw = f.decrypt(wrapper["payload"].encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def run_query(api_key: str, query: str, variables: dict = None):
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    resp = requests.post(
        "https://api.monday.com/v2", json=payload, headers=headers, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def list_boards(api_key: str):
    q = "{ boards { id name } }"
    r = run_query(api_key, q)
    return r.get("data", {}).get("boards", [])


def list_columns(api_key: str, board_id: int):
    q = "query ($boardId:Int!) { boards(ids: $boardId) { columns { id title type } } }"
    r = run_query(api_key, q, {"boardId": int(board_id)})
    return r.get("data", {}).get("boards", [])[0].get("columns", [])


def interactive_map(columns):
    print("\nAvailable columns:")
    for i, c in enumerate(columns):
        print(f"{i}: {c['title']} (id={c['id']}, type={c.get('type')})")

    def pick(name):
        idx = input(
            f"Enter the index of the column to use for '{name}' (or leave blank to skip): "
        ).strip()
        if idx == "":
            return None
        try:
            return columns[int(idx)]["id"]
        except Exception:
            print("Invalid selection")
            return pick(name)

    mapping = {
        "project_id": pick("project_id (unique project identifier)"),
        "predicted_delay": pick("predicted_delay (numeric)"),
        "revenue": pick("revenue (numeric)"),
        "risk": pick("risk (status/text)"),
        "status": pick("status (status)"),
    }
    return mapping


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api-key", help="Monday.com API key (optional; will prompt)")
    p.add_argument("--output", "-o", help="Output config path", required=True)
    p.add_argument("--oauth", action="store_true", help="Launch OAuth onboarding flow")
    p.add_argument("--host", default="127.0.0.1", help="OAuth server host")
    p.add_argument("--port", default=8000, type=int, help="OAuth server port")
    args = p.parse_args()

    api_key = args.api_key or os.getenv("MONDAY_API_KEY")
    dry_run = os.getenv("DRY_RUN", "1") == "1"

    if args.oauth:
        # start oauth server in a thread and instruct user to open URL
        client_id = os.getenv("MONDAY_OAUTH_CLIENT_ID")
        client_secret = os.getenv("MONDAY_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            client_id = input("Enter Monday OAuth client_id: ").strip()
            client_secret = getpass.getpass(
                "Enter Monday OAuth client_secret (hidden): "
            )

        out_path = Path(args.output).with_suffix(
            ".oauth_tmp." + str(uuid.uuid4()) + ".json"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # run server in background thread
        def _run():
            run_server(
                client_id, client_secret, args.host, args.port, str(out_path), dry_run
            )

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        logger.info(
            "\nOAuth server started. Open the URL printed by the server in your browser to authorize."
        )
        logger.info("Waiting for OAuth callback and token...")

        # wait for token file
        waited = 0
        while waited < 300:
            if out_path.exists():
                logger.info(f"Found token result at {out_path}")
                break
            _time.sleep(1)
            waited += 1

        if not out_path.exists():
            logger.error("Timed out waiting for OAuth callback. Exiting.")
            return

        # read token (may be simulated if dry_run)
        token_obj = json.load(open(out_path, "r", encoding="utf-8"))
        api_key = token_obj.get("access_token")
        if dry_run:
            logger.info(
                "DRY_RUN enabled — token not saved. Proceeding in simulation mode."
            )
        else:
            logger.info("Received access token from OAuth flow.")

        # if the user saved mapping via the browser form, merge it
        map_path = Path(str(out_path) + ".mapping.json")
        if map_path.exists():
            try:
                mapping = json.load(open(map_path, "r", encoding="utf-8"))
                logger.info(f"Found mapping saved from browser at {map_path}")
            except Exception:
                mapping = None
        else:
            mapping = None

    if not api_key:
        api_key = getpass.getpass("Enter your Monday.com API key (input hidden): ")

    # If dry-run and we don't have a real token, prompt for simulated board id instead
    if dry_run and not api_key:
        print(
            "\nDRY_RUN simulation: please enter the target board id (or leave blank to skip fetching boards)"
        )
        b_in = input("Board id (simulated): ").strip()
        if b_in == "":
            boards = []
        else:
            boards = [{"id": int(b_in), "name": f"Simulated board {b_in}"}]
    else:
        try:
            boards = list_boards(api_key)
        except Exception as e:
            logger.error(f"Failed to list boards: {e}")
            return

    print("\nBoards:")
    for i, b in enumerate(boards):
        logger.info(f"{i}: {b.get('name')} (id={b.get('id')})")

    sel = input("Select board by index: ").strip()
    try:
        board = boards[int(sel)]
    except Exception:
        logger.error("Invalid selection")
        return

    board_id = int(board["id"])
    if dry_run and not api_key:
        print(
            "\nDRY_RUN simulation: please provide column IDs manually (leave blank to skip)"
        )

        def ask_col(name):
            v = input(f"Column id for {name}: ").strip()
            return v if v != "" else None

        mapping = {
            "project_id": ask_col("project_id (required)"),
            "predicted_delay": ask_col("predicted_delay"),
            "revenue": ask_col("revenue"),
            "risk": ask_col("risk"),
            "status": ask_col("status"),
        }
        columns = []
    else:
        try:
            columns = list_columns(api_key, board_id)
        except Exception as e:
            logger.error(f"Failed to list columns for board {board_id}: {e}")
            return

    if dry_run and not api_key:
        # mapping already collected above
        pass
    else:
        mapping = interactive_map(columns)

    # token_obj may exist from OAuth server; include token metadata as 'token'
    token_obj = locals().get("token_obj") if "token_obj" in locals() else None
    # merge mapping from browser if present
    if mapping:
        for k, v in mapping.items():
            if v:
                mapping_val = v
        # ensure mapping used for saving
        mapping_to_save = {k: v for k, v in mapping.items() if v}
    else:
        mapping_to_save = (
            {k: v for k, v in mapping.items()}
            if "mapping" in locals() and mapping
            else {k: v for k, v in mapping.items()} if "mapping" in locals() else {}
        )

    out = {
        "api_key": api_key if api_key else None,
        "board_id": board_id,
        "columns": (
            mapping_to_save
            if mapping_to_save
            else {k: v for k, v in mapping.items() if v is not None}
        ),
    }
    if token_obj:
        out["token"] = token_obj

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use secret manager if requested
    from secret_manager import get_manager

    mgr = get_manager()
    encrypt_flag = os.getenv("MONDAY_SECRET_BACKEND", "local") != "local" or bool(
        os.getenv("MONDAY_SECRET_KEY")
    )
    mgr.save(out_path, out, encrypt=encrypt_flag)
    logger.info(
        f'Config written to {out_path} via backend {os.getenv("MONDAY_SECRET_BACKEND", "local")} . Do NOT commit this file to source control.'
    )


if __name__ == "__main__":
    main()

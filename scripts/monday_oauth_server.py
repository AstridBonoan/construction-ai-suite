"""
Minimal OAuth server to handle Monday.com OAuth redirects and token exchange.

This server writes the exchanged access token JSON to a temp file path provided
via the `state` query parameter (URL-safe). The server is intentionally tiny
and meant for local onboarding flows only.

Usage:
  - Start server with host/port and provide MONDAY_OAUTH_CLIENT_ID/SECRET
  - The client (monday_setup.py) will construct the /auth/monday URL and open it
    in a browser. After the user authorizes, Monday redirects to /auth/monday/callback
    and this server exchanges the code and writes the token to the temp file.
"""

from flask import Flask, redirect, request, jsonify
import os
import json
import base64
import urllib.parse
import requests
from pathlib import Path
from secret_manager import get_manager
from logger import get_logger

logger = get_logger("monday_oauth_server")


def make_app(client_id: str, client_secret: str, redirect_base: str, dry_run: bool):
    app = Flask(__name__)

    @app.route("/auth/monday")
    def auth():
        # state: path to write token (urlencoded)
        state = request.args.get("state", "")
        redirect_uri = urllib.parse.urljoin(redirect_base, "/auth/monday/callback")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
        }
        auth_url = "https://auth.monday.com/oauth2/authorize?" + urllib.parse.urlencode(
            params
        )
        return redirect(auth_url)

    @app.route("/auth/monday/callback")
    def callback():
        code = request.args.get("code")
        state = request.args.get(
            "state"
        )  # expected to be an output file path (urlencoded)
        redirect_uri = urllib.parse.urljoin(redirect_base, "/auth/monday/callback")
        if not code:
            return "Missing code", 400

        if dry_run:
            # simulate token exchange
            token_obj = {"access_token": None, "note": "dry-run simulation"}
        else:
            token_url = "https://auth.monday.com/oauth2/token"
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            resp = requests.post(token_url, data=payload, timeout=30)
            try:
                resp.raise_for_status()
                token_obj = resp.json()
                # add computed expiry timestamp if expires_in present
                if isinstance(token_obj, dict) and token_obj.get("expires_in"):
                    import time

                    token_obj["expires_at"] = int(time.time()) + int(
                        token_obj["expires_in"]
                    )
            except Exception as e:
                return f"Failed to exchange token: {e} - {resp.text}", 500

        if state:
            out_path = urllib.parse.unquote(state)
            try:
                # if secret backend enabled, save into secret manager
                backend = os.getenv("MONDAY_SECRET_BACKEND", "local")
                if backend != "local":
                    mgr = get_manager()
                    # write token under secret named after out_path stem
                    mgr.save(Path(out_path), {"token": token_obj}, encrypt=False)
                    logger.info(f"Saved token to secret backend for {out_path}")
                else:
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(token_obj, f)
                    logger.info(f"Wrote token to file {out_path}")
            except Exception as e:
                logger.error(f"Failed to persist token: {e}")
                return f"Failed to write token file: {e}", 500

        # Provide a small browser UI to allow client to submit mapping JSON
        mapping_form = f"""
        <html><body>
        <h3>Authorization complete</h3>
        <p>You may close this window or provide a JSON mapping for board columns to save automatically.</p>
        <form method='post' action='/save_mapping'>
          <input type='hidden' name='state' value='{urllib.parse.quote(state or '')}' />
          <textarea name='mapping' rows='12' cols='80'>{{\n  "project_id": "<column_id>",\n  "predicted_delay": "<column_id>"\n}}</textarea><br/>
          <button type='submit'>Save mapping to config</button>
        </form>
        </body></html>
        """
        return mapping_form

    @app.route("/save_mapping", methods=["POST"])
    def save_mapping():
        state = request.form.get("state")
        mapping_json = request.form.get("mapping")
        if not state:
            return "Missing state", 400
        out_path = urllib.parse.unquote(state)
        try:
            mapping = json.loads(mapping_json)
        except Exception as e:
            return f"Invalid JSON mapping: {e}", 400

        # write mapping file alongside token file (client will merge)
        map_path = out_path + ".mapping.json"
        try:
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2)
        except Exception as e:
            return f"Failed to save mapping: {e}", 500

        return "Mapping saved. You can close this window and return to the CLI."

    return app


def run_server(
    client_id: str,
    client_secret: str,
    host: str,
    port: int,
    out_path: str,
    dry_run: bool,
):
    redirect_base = f"http://{host}:{port}"
    app = make_app(client_id, client_secret, redirect_base, dry_run)
    # instruct developer to open /auth/monday?state=<out_path>
    print(
        f"Run the following URL in a browser to start OAuth (state writes to {out_path}):"
    )
    auth_url = f"http://{host}:{port}/auth/monday?state=" + urllib.parse.quote(out_path)
    print(auth_url)
    app.run(host=host, port=port)

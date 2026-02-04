#!/usr/bin/env python3
"""Bring up the local compose stack, wait for services, run Playwright tests, tear down.

Usage: python scripts/integration_e2e/run_integration_e2e.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMPOSE_FILE = os.path.join(ROOT, "docker-compose.local.yml")
BACKEND_HEALTH = "http://127.0.0.1:5000/health"
FRONTEND_URL = "http://127.0.0.1:5173/"
FRONTEND_DIR = os.path.join(ROOT, "frontend_phase10")
BACKEND_OUTPUTS = "http://127.0.0.1:5000/phase9/outputs"


def run(cmd, cwd=None, env=None):
    if isinstance(cmd, (list, tuple)):
        display = " ".join(cmd)
    else:
        display = cmd
    print(f"-> {display} (cwd={cwd or '.'})")
    subprocess.run(cmd, cwd=cwd, check=True, env=env)


def wait_for(url: str, timeout: int = 180, interval: float = 2.0) -> bool:
    end = time.time() + timeout
    last_exc = None
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                status = getattr(r, 'status', None) or r.getcode()
                if status == 200:
                    print(f"{url} is healthy (HTTP {status})")
                    return True
        except Exception as exc:  # pragma: no cover - network ops
            last_exc = exc
        print('.', end='', flush=True)
        time.sleep(interval)
    print()
    print(f"Timed out waiting for {url}. Last error: {last_exc}")
    return False


def main() -> int:
    if not os.path.exists(COMPOSE_FILE):
        print(f"Compose file not found: {COMPOSE_FILE}")
        return 2

    try:
        run(["docker", "compose", "-f", COMPOSE_FILE, "up", "--build", "-d"])  # build & detach

        print("Waiting for backend /health ...")
        if not wait_for(BACKEND_HEALTH, timeout=180):
            return 3

        print("Waiting for frontend root ...")
        if not wait_for(FRONTEND_URL, timeout=180):
            return 4

        # Run Playwright inside a Node container so host doesn't need npm/node
        print("Running Playwright inside a Node container (no host npm required)...")
        project_name = os.path.basename(ROOT)
        network_name = f"{project_name}_default"
        node_image = "mcr.microsoft.com/playwright:latest"
        app_mount = os.path.abspath(FRONTEND_DIR)

        # install dependencies inside container
        run([
            "docker",
            "run",
            "--rm",
            "-v",
            f"{app_mount}:/usr/src/app",
            "-w",
            "/usr/src/app",
            "--network",
            network_name,
            node_image,
            "npm",
            "ci",
        ])

        run_playwright = os.environ.get("INTEGRATION_RUN_PLAYWRIGHT", "0") == "1"
        if run_playwright:
            # run tests inside Playwright image (includes browsers + deps)
            run([
                "docker",
                "run",
                "--rm",
                "-v",
                f"{app_mount}:/usr/src/app",
                "-w",
                "/usr/src/app",
                "--network",
                network_name,
                node_image,
                "bash",
                "-lc",
                "npm ci && npx playwright test --reporter=list",
            ])
        else:
            # Quick smoke checks when Playwright is skipped (local runs)
            print("Playwright run skipped (set INTEGRATION_RUN_PLAYWRIGHT=1 to enable).")
            try:
                print("Fetching frontend root HTML...")
                with urllib.request.urlopen(FRONTEND_URL, timeout=10) as r:
                    html = r.read(1024).decode(errors='ignore')
                    print("Frontend HTML length:", len(html))

                print("Fetching backend /phase9/outputs...")
                with urllib.request.urlopen(BACKEND_OUTPUTS, timeout=10) as r:
                    body = r.read(64*1024)
                    print("Backend outputs size:", len(body))
            except Exception as exc:
                print("Smoke check failed:", exc)
                return 5

        print("Integration E2E completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        return getattr(e, 'returncode', 1)
    finally:
        try:
            print("Tearing down compose stack...")
            run(["docker", "compose", "-f", COMPOSE_FILE, "down", "--volumes", "--remove-orphans"])  # best-effort
        except Exception:
            print("Warning: compose down failed (ignored)")


if __name__ == '__main__':
    raise SystemExit(main())

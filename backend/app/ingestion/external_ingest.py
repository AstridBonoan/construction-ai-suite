from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Any, Dict, List

from app.ml.schedule_dependency import feed_to_core_risk_engine

# Demo-only ingestion bridge for Phase 2.5. This file is intentionally small
# and reversible. It accepts canonical tasks and in DEMO_MODE forwards them
# to the demo schedule/risk engine via `feed_to_core_risk_engine`.

# project root is three levels up from this file (backend/app/ingestion -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORE_PATH = PROJECT_ROOT / "data" / "ingestion_log_demo.json"


def _ensure_store_path() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text("[]", encoding="utf-8")


def ingest_tasks(tenant_id: str, board_id: str, tasks: List[Dict[str, Any]], source: str = "monday") -> bool:
    """Demo-safe ingestion entry point.

    - Runs only when DEMO_MODE=true in the environment.
    - Forwards tasks to `feed_to_core_risk_engine` (demo stub) and
      writes a small demo artifact to `data/ingestion_log_demo.json`.

    Returns True on successful demo-ingest, False otherwise.
    """
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if not demo_mode:
        print(f"[INGEST][SKIP] DEMO_MODE disabled; skipping ingest for tenant {tenant_id}")
        return False

    # Build a simple ingestion payload
    payload = {
        "tenant_id": tenant_id,
        "board_id": board_id,
        "source": source,
        "tasks_count": len(tasks),
        "tasks_preview": tasks[:5],
    }

    print(f"[INGEST][DEMO] Ingesting {len(tasks)} tasks from {source} board {board_id} for tenant {tenant_id}")

    # Feed to demo schedule/risk engine (no-op in production if core engine absent)
    try:
        feed_to_core_risk_engine(payload)
    except Exception as e:
        print(f"[INGEST][ERROR] feed_to_core_risk_engine failed: {e}")
        return False

    # Persist a tiny demo artifact in the repo-level `data/` so local smoke tests can assert ingestion happened
    try:
        print(f"[INGEST][DEBUG] demo artifact path: {STORE_PATH}")
        _ensure_store_path()
        with STORE_PATH.open("r+", encoding="utf-8") as f:
            try:
                arr = json.load(f)
            except Exception:
                arr = []
            entry = {"tenant_id": tenant_id, "board_id": board_id, "tasks_count": len(tasks)}
            arr.append(entry)
            f.seek(0)
            json.dump(arr, f, indent=2, ensure_ascii=False)
            f.truncate()
    except Exception as e:
        print(f"[INGEST][WARN] Failed to write demo ingest artifact: {e}")

    print("[INGEST][SUCCESS] Tasks fed to demo schedule engine")
    return True

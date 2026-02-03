#!/usr/bin/env python3
"""Generate synthetic materials and equipment usage datasets.

Writes two CSVs to `construction_datasets/`:
- `materials_synthetic.csv`
- `equipment_synthetic.csv`

If `Capital_Project_Schedules_and_Budgets.csv` exists, sample project IDs/names from it.
Mark generated rows with `is_synthetic=True` and include a `source` field.
"""

from __future__ import annotations
import argparse
import csv
import os
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "construction_datasets")
SCHEDULES = os.path.join(DATA_DIR, "Capital_Project_Schedules_and_Budgets.csv")

MATERIALS = [
    ("cement", "tons", 120.0),
    ("steel", "tons", 900.0),
    ("lumber", "board_feet", 1.2),
    ("aggregate", "tons", 15.0),
    ("rebar", "tons", 700.0),
]

EQUIPMENT = [
    ("excavator", "hours", 150.0),
    ("crane", "hours", 500.0),
    ("bulldozer", "hours", 130.0),
    ("loader", "hours", 120.0),
    ("dump_truck", "hours", 95.0),
]

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def daterange(start_date: datetime, end_date: datetime):
    d = start_date
    while d <= end_date:
        yield d
        d += timedelta(days=1)


def sample_projects(n_projects: int) -> list[str]:
    projects = []
    if os.path.exists(SCHEDULES):
        try:
            with open(SCHEDULES, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                names = [
                    r.get("Project School Name")
                    or r.get("Project Building Identifier")
                    or r.get("Project Type")
                    for r in reader
                ]
                names = [n for n in names if n]
                if names:
                    random.shuffle(names)
                    return names[:n_projects]
        except Exception:
            pass
    # fallback synthetic project ids
    for i in range(1, n_projects + 1):
        projects.append(f"PROJ_{1000 + i}")
    return projects


def make_material_rows(
    project_id: str, date_list: list[datetime], rows_per_project: int
) -> list[dict]:
    rows = []
    for _ in range(rows_per_project):
        d = random.choice(date_list)
        mat, unit, base_price = random.choice(MATERIALS)
        qty = round(abs(random.gauss(5, 10)) + 0.1, 3)  # rough quantity
        unit_price = round(base_price * random.uniform(0.85, 1.25), 2)
        total_cost = round(qty * unit_price, 2)
        rows.append(
            {
                "project_id": project_id,
                "date": d.strftime("%Y-%m-%d"),
                "material": mat,
                "quantity": qty,
                "unit": unit,
                "unit_price_estimated": unit_price,
                "total_cost_estimated": total_cost,
                "is_synthetic": True,
                "source": "synthetic_generator_v1",
            }
        )
    return rows


def make_equipment_rows(
    project_id: str, date_list: list[datetime], rows_per_project: int
) -> list[dict]:
    rows = []
    for _ in range(rows_per_project):
        d = random.choice(date_list)
        eq, unit, base_hourly = random.choice(EQUIPMENT)
        hours = round(abs(random.gauss(6, 8)) + 0.5, 2)
        hourly_cost = round(base_hourly * random.uniform(0.8, 1.4), 2)
        maintenance_flag = random.random() < 0.05
        rows.append(
            {
                "project_id": project_id,
                "date": d.strftime("%Y-%m-%d"),
                "equipment": eq,
                "hours_used": hours,
                "hourly_cost_estimated": hourly_cost,
                "cost_estimated": round(hours * hourly_cost, 2),
                "maintenance_flag": maintenance_flag,
                "is_synthetic": True,
                "source": "synthetic_generator_v1",
            }
        )
    return rows


def write_csv(path: str, fieldnames: list[str], rows: list[dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--projects", type=int, default=20)
    parser.add_argument("--rows-per-project", type=int, default=30)
    parser.add_argument("--out-dir", default=DATA_DIR)
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    date_list = list(daterange(start, end))

    projects = sample_projects(args.projects)

    materials_rows = []
    equipment_rows = []

    for pid in projects:
        materials_rows.extend(make_material_rows(pid, date_list, args.rows_per_project))
        equipment_rows.extend(
            make_equipment_rows(pid, date_list, max(1, int(args.rows_per_project / 3)))
        )

    materials_path = os.path.join(args.out_dir, "materials_synthetic.csv")
    equipment_path = os.path.join(args.out_dir, "equipment_synthetic.csv")

    write_csv(
        materials_path,
        [
            "project_id",
            "date",
            "material",
            "quantity",
            "unit",
            "unit_price_estimated",
            "total_cost_estimated",
            "is_synthetic",
            "source",
        ],
        materials_rows,
    )
    write_csv(
        equipment_path,
        [
            "project_id",
            "date",
            "equipment",
            "hours_used",
            "hourly_cost_estimated",
            "cost_estimated",
            "maintenance_flag",
            "is_synthetic",
            "source",
        ],
        equipment_rows,
    )

    print(f"Wrote {len(materials_rows)} material rows to {materials_path}")
    print(f"Wrote {len(equipment_rows)} equipment rows to {equipment_path}")


if __name__ == "__main__":
    main()

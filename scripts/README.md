Synthetic Data Generator

This folder contains a small helper to generate synthetic materials and equipment usage datasets for development and model training.

Usage

Run from the repository root:

```bash
python3 scripts/generate_synthetic_construction_data.py \
  --start 2024-01-01 --end 2024-12-31 \
  --projects 50 --rows-per-project 40
```

Output

- `construction_datasets/materials_synthetic.csv` — synthetic materials consumption rows.
- `construction_datasets/equipment_synthetic.csv` — synthetic equipment usage rows.

Notes

- Rows include `is_synthetic=True` and `source=synthetic_generator_v1`.
- If `construction_datasets/Capital_Project_Schedules_and_Budgets.csv` exists, project names are sampled from that file; otherwise synthetic project IDs are generated.
- Adjust parameters to increase/decrease volume or date range.

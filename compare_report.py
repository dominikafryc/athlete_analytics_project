"""
Parity REPORT between the dbt mart (DuckDB) and the Python pipeline output (CSV).

This is not a pass/fail test. It measures, column by column, how much the two
implementations differ, so the differences can be documented (case study, section 7).

Run from the project root, AFTER `dbt build` and `python athlete_analytics_project.py`:
    python compare_report.py                      # writes parity_report.csv
    python compare_report.py parity_report_after.csv   # custom output name
"""
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DUCKDB_PATH = ROOT / "dev.duckdb"
DBT_TABLE = "fct_daily_readiness"
PYTHON_CSV = ROOT / "fct_daily_readiness.csv"
OUTPUT_CSV = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "parity_report.csv")

ATOL, RTOL = 0.01, 0.01          # tolerance for numeric columns (1%)
KEYS = ["user_id", "date"]

# Same metric, different name: {name_in_dbt: name_in_python} (after normalization).
RENAME_DBT_TO_PY = {
    "trimp_objective_scaled_daily": "trimp_objective_scaled",
}


def norm(col: str) -> str:
    """'Sleep Efficiency (pct)' / 'Sleep_Efficiency_pct' -> 'sleep_efficiency_pct'."""
    return re.sub(r"[^0-9a-z]+", "_", str(col).strip().lower()).strip("_")


def normalize_columns(df: pd.DataFrame, label: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [norm(c) for c in df.columns]
    dup = df.columns[df.columns.duplicated()].tolist()
    if dup:
        sys.exit(f"[{label}] duplicate column names after normalization: {dup}")
    missing = [k for k in KEYS if k not in df.columns]
    if missing:
        sys.exit(f"[{label}] missing key column(s) {missing}. Columns: {list(df.columns)[:15]}...")
    return df

for path in (DUCKDB_PATH, PYTHON_CSV):
    if not path.exists():
        sys.exit(f"File not found: {path}\n"
                 "Run `dbt build` and `python athlete_analytics_project.py` first, "
                 "from the project root.")

con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
dbt = con.execute(f"SELECT * FROM {DBT_TABLE}").df()
con.close()
py = pd.read_csv(PYTHON_CSV, encoding="utf-8-sig")

dbt = normalize_columns(dbt, "dbt").rename(columns=RENAME_DBT_TO_PY)
py = normalize_columns(py, "python")

for df in (dbt, py):
    df["user_id"] = df["user_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()

m = py.merge(dbt, on=KEYS, how="outer", suffixes=("_py", "_dbt"), indicator=True)
print("=== Row coverage (python vs dbt) ===")
print(m["_merge"].map({"both": "both", "left_only": "only in python",
                       "right_only": "only in dbt"}).value_counts().to_string())
both = m[m["_merge"] == "both"]
print(f"Rows compared: {len(both)}")

only_py_cols = sorted(set(py.columns) - set(dbt.columns))
only_dbt_cols = sorted(set(dbt.columns) - set(py.columns))
common = [c for c in py.columns if c in dbt.columns and c not in KEYS]
print(f"\nPython columns: {py.shape[1]}, dbt columns: {dbt.shape[1]}, common (excluding keys): {len(common)}")
print(f"Columns only in Python ({len(only_py_cols)}): {only_py_cols}")
print(f"Columns only in dbt ({len(only_dbt_cols)}): {only_dbt_cols}")

rows = []
for c in common:
    a, b = both[f"{c}_py"], both[f"{c}_dbt"]
    a_null, b_null = a.isna(), b.isna()
    both_val = ~a_null & ~b_null
    if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
        an = a[both_val].astype(float)
        bn = b[both_val].astype(float)
        n_diff = int((~np.isclose(an, bn, atol=ATOL, rtol=RTOL)).sum())
        mean_abs = float((an - bn).abs().mean()) if len(an) else np.nan
        max_abs = float((an - bn).abs().max()) if len(an) else np.nan
    else:
        sa = a[both_val].astype(str).str.replace(r"\.0$", "", regex=True)
        sb = b[both_val].astype(str).str.replace(r"\.0$", "", regex=True)
        n_diff = int((sa != sb).sum())
        mean_abs = max_abs = np.nan
    rows.append({
        "column": c,
        "compared_values": int(both_val.sum()),
        "differ_pct": round(100 * n_diff / max(int(both_val.sum()), 1), 2),
        "python_has_value_dbt_null": int((~a_null & b_null).sum()),
        "dbt_has_value_python_null": int((a_null & ~b_null).sum()),
        "mean_abs_diff": round(mean_abs, 4) if pd.notna(mean_abs) else None,
        "max_abs_diff": round(max_abs, 4) if pd.notna(max_abs) else None,
    })

report = pd.DataFrame(rows).sort_values(
    ["differ_pct", "python_has_value_dbt_null"], ascending=False)
print("\n=== Column report (sorted by % of differing values) ===")
print(report.to_string(index=False))
report.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved: {OUTPUT_CSV.name}")

print("\n=== Top 5 columns for the case study (markdown) ===")
print("| Column | % differing | Python value, dbt NULL | Cause |")
print("|---|---|---|---|")
for _, r in report.head(5).iterrows():
    print(f"| {r['column']} | {r['differ_pct']} | {r['python_has_value_dbt_null']} | (fill in) |")
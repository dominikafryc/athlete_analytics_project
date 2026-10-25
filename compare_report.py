"""
Parity REPORT between the dbt mart (DuckDB) and the Python pipeline output (CSV).
This is not a pass/fail test. It measures, column by column, how much the two differ.
Run:  py compare_report.py
"""
import numpy as np
import pandas as pd
import duckdb

DUCKDB_PATH = "dev.duckdb"
DBT_TABLE = "fct_daily_readiness"
PYTHON_CSV = r"C:\dbt_athlete\dbt_athlete\fct_daily_readiness .csv"
ATOL, RTOL = 0.01, 0.01          # tolerance for numeric columns (1%)
KEYS = ["user_id", "date"]

con = duckdb.connect(DUCKDB_PATH, read_only=True)
dbt = con.execute(f"SELECT * FROM {DBT_TABLE}").df()
con.close()
py = pd.read_csv(PYTHON_CSV, encoding="utf-8-sig")

for df in (dbt, py):
    df.columns = df.columns.str.lower()
dbt = dbt.rename(columns={"trimp_objective_scaled_daily": "trimp_objective_scaled"})
for df in (dbt, py):
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()

m = py.merge(dbt, on=KEYS, how="outer", suffixes=("_py", "_dbt"), indicator=True)
print("=== Row coverage (python vs dbt) ===")
print(m["_merge"].map({"both": "both", "left_only": "only in python",
                       "right_only": "only in dbt"}).value_counts().to_string())
both = m[m["_merge"] == "both"]
print(f"Rows compared: {len(both)}")

only_py_cols = sorted(set(py.columns) - set(dbt.columns))
only_dbt_cols = sorted(set(dbt.columns) - set(py.columns))
print(f"\nColumns only in Python ({len(only_py_cols)}): {only_py_cols}")
print(f"Columns only in dbt ({len(only_dbt_cols)}): {only_dbt_cols}")

common = [c for c in py.columns if c in dbt.columns and c not in KEYS]
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
report.to_csv("parity_report.csv", index=False)
print("\nSaved: parity_report.csv")
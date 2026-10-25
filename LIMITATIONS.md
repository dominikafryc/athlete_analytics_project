# Known Limitations

## Data and scope
- **Synthetic data only.** All 8 CSVs are algorithmically generated, not sourced from real wearables (Garmin, Whoop, Oura) or clinical records.
- **Not validated on real users or large-scale data.** Model metrics reflect performance on synthetic data only.
- **Non-clinical scope.** Recommendations are heuristic training-load guidance, not medical advice.
- **No intraday wear-time validation.** Inputs are pre-aggregated at a daily grain, so incomplete tracking days cannot be flagged or excluded before baselines are computed.

## Methodology
- **Data leakage in feature engineering.** The evaluation split is chronological (`TimeSeriesSplit`), but features are built before the split using full-data statistics:
  - KNN imputation is fitted on each user's full series.
  - Cycle-phase baselines and Z-scores (including the stress score) use full-history mean and standard deviation.
  - Static columns use `ffill().bfill()`, which carries future values backward.
  - Missing HRV is filled with the global mean of the whole table (Python and dbt).
  - TRIMP is min-max scaled over all workouts (Python and dbt).
  - IsolationForest, PCA and KMeans are fitted on all rows.

  Reported metrics are therefore optimistic.
- **The target is derived from HRV.** `Target_Readiness_Tomorrow` is tomorrow's HRV ratio vs. the 30-day baseline, and HRV is also a core feature. Autocorrelation can inflate metrics, and no naive baseline ("tomorrow equals today") is reported yet.
- **Users without sleep data are labelled low insomnia risk in Python.** The insomnia rule falls through to `LOW_RISK` / 0 when sleep inputs are missing (180 of 720 rows). dbt returns NULL for these rows.
- **The model does not beat a naive baseline.** Mean accuracy is 0.646 and macro-F1 0.399 across `TimeSeriesSplit` folds, versus 0.687 and 0.47 for a "tomorrow equals today" rule (computed on the whole sample, so indicative only). The target is HRV-derived and highly autocorrelated, the classes are imbalanced (`High` 78.4%), and the dataset is small (720 rows, 37 `Low` days).
- **Users without a tracker get artificial labels.** Missing HRV is replaced by a constant, so the ratio is 1 and the status is always `High`.
- **Baseline cold start.** Rolling baselines use `min_periods=1`, so the first day equals its own baseline. The window also includes the current day.
- **TRIMP scaling.** TRIMP is scaled per workout and then summed per day, so a day can exceed 1000. `Load_Discrepancy` compares sRPE with scaled TRIMP, and the two scales are not calibrated against each other.
- **Heuristic thresholds.** HRV ratios (0.85 / 0.95), CMJ and grip drops, and insomnia rules are heuristic choices, not validated cut-offs.
- **Experience is used only for discipline swaps.** Years of experience choose the alternative discipline but do not scale the load metrics.
- **CMJ/Grip strength require measurement equipment** available mainly to professional athletes and clubs. Python falls back to an HRV Z-score + DOMS layer for users without it, which is less precise. The dbt layer falls back to DOMS only.
- **No explicit consecutive-rest-day signal.** Rest days correctly reduce `Acute_Load_7d` (zero-fill before EWMA), but there is no feature capturing consecutive rest days as an independent recovery signal.

## Optional modules
- **PCA + KMeans is inactive on the sample dataset.** With only 8 synthetic users the blood-biomarker PCA space has low variance, so `Health_Cluster_ID` is set to -1 for every row. The module needs a larger or real dataset to be meaningful.

## Weather module
- **The weather gate is currently inactive.** `discipline_weather_config.csv` is comma-delimited but the loader reads every CSV with `;`, so the table loads as one column (`(30, 1)` in the log), no discipline match is found, and the pipeline defaults to "weather optimal". No recommendation in the sample output is driven by weather. It also still needs a check that discipline names in the config match those in `user_profile.csv`.
- **The capital-city fallback does not work.** The `restcountries` response is not handled correctly (`Failed to fetch capital coordinates: 0`), so only IP geolocation is effectively used.
- **One location for all users.** Weather is resolved from the IP address of the machine running the script (`ip-api.com`, called over HTTP), not from each user's location. Behind a VPN or proxy the location is the server's. If geolocation fails, the pipeline falls back to the country's capital, and if all requests fail it applies default safe values (20°C, 10 km/h wind, no storm). IP geolocation is approximate (in one local run it landed more than 100 km from the real location), and hosted notebooks such as Google Colab run on the provider's servers, so geolocation there does not reflect the user. Run the pipeline locally.
- **Latest day only.** The forecast (daytime window 08:00–20:00) is applied only to the latest date in the data. It is a safety gate on the final recommendation, not a model feature.

## Architecture
- **Python and dbt are not integrated.** The Python pipeline does not read the dbt marts, and there is no orchestration between the two.
- **Python and dbt outputs differ.** Differences come from imputation vs. NULLs, the CNS fallback layer, CMJ/grip baselines, the HR lookup in TRIMP, and division guards (see case study, section 7).
- **dbt SQL is DuckDB-specific** (`ASOF JOIN`, `generate_series` with `unnest`, `LEAST`/`GREATEST` NULL behavior) and is not portable 1:1 to other warehouses.
- **Single-script Python architecture.** The pipeline is organized into functions but lives in one file, not a Python package.

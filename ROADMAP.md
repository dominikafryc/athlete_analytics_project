# Roadmap

## Methodology and data quality
- [ ] Causal KNN imputation (fit on past data only, expanding window)
- [ ] Expanding-window Z-scores and cycle-phase baselines
- [ ] Remove `bfill` from static columns; compute global statistics (HRV fill, TRIMP scaling) on training data only
- [x] Flag days without a measured HRV in dbt (`HRV_Is_Missing`)
- [ ] Exclude imputed-HRV days from labels in the Python model
- [x] Minimum-observations rule for baselines in dbt (cold start)
- [ ] Minimum-observations rule for baselines in the Python pipeline
- [ ] Fold-matched naive baselines (persistence and majority class) logged next to the model metrics
- [ ] Sum TRIMP per day before scaling
- [ ] Wear-time completeness validation (flag `is_incomplete` days based on minimum tracking hours/sleep)
- [ ] Baselines computed strictly from complete rest days (training vs. non-training segmentation)
- [ ] Explicit consecutive-rest-days feature

## Architecture and engineering
- [x] Grain uniqueness, key and singular tests on the dbt models
- [x] dbt unit tests for the readiness-status rule
- [ ] dbt unit tests for the CNS fatigue and insomnia rules
- [x] Parity report after the methodology fixes (`parity_report_after.csv`) to compare with the baseline
- [x] Python reads the dbt mart (`load_mart`) for the logic dbt already implements
- [ ] Remove the remaining duplicated logic from Python (anything dbt already computes)
- [x] `run_pipeline.py` runs seed, build, the Python pipeline and the parity report in sequence
- [ ] Orchestration tool (Prefect, Dagster or Airflow) with retries and run history
- [ ] dbt exposures documenting the model as a downstream consumer of the mart
- [x] CI running `dbt build` and `pytest` (GitHub Actions)
- [x] Thresholds moved to dbt `vars`
- [ ] Add an `if __name__ == "__main__":` guard so importing the module does not run the whole pipeline
- [ ] Full modularization into a Python package (`config.py`, `weather.py`, etc.)

## Features
- [x] Normalize all datasets to one CSV format (comma delimiter, dot decimals) and read them from `seeds/`, so the weather gate becomes active
- [ ] Dashboard on the mart (Streamlit)
- [ ] Fix the capital-city fallback (handle the `restcountries` response)
- [ ] Per-user weather via IP geolocation, with country-capital fallback
- [ ] Larger synthetic dataset or real data so PCA + KMeans has enough variance
- [ ] Hourly weather forecast across the training window, not only the latest day
- [ ] Google Calendar integration (training window detection)
- [ ] Experience-weighted load metrics
- [ ] Device data standardization (Garmin, Whoop, Oura) for real-world testing

## Companion project
- [ ] Trainer-facing client churn prediction (rule-based heuristic first, XGBoost once sufficient labeled data exists)
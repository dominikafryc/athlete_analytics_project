# Roadmap

## Methodology and data quality
- [ ] Causal KNN imputation (fit on past data only, expanding window)
- [ ] Expanding-window Z-scores and cycle-phase baselines
- [ ] Remove `bfill` from static columns; compute global statistics (HRV fill, TRIMP scaling) on training data only
- [ ] Flag or exclude imputed-HRV days from labels
- [ ] Minimum-observations rule for baselines (cold start)
- [ ] Fold-matched naive baselines (persistence and majority class) logged next to the model metrics
- [ ] Sum TRIMP per day before scaling
- [ ] Wear-time completeness validation (flag `is_incomplete` days based on minimum tracking hours/sleep)
- [ ] Baselines computed strictly from complete rest days (training vs. non-training segmentation)
- [ ] Explicit consecutive-rest-days feature

## Architecture and engineering
- [ ] Python reads the dbt marts instead of recomputing the same logic
- [ ] Orchestration (Dagster, Prefect or Airflow) so each tool runs in sequence
- [ ] CI running `dbt build` and `pytest`
- [ ] Thresholds moved to dbt `vars`
- [ ] Add an `if __name__ == "__main__":` guard so importing the module does not run the whole pipeline
- [ ] Full modularization into a Python package (`config.py`, `weather.py`, etc.)

## Features
- [ ] Fix per-file CSV delimiter detection and verify discipline names match the weather config, so the weather gate becomes active
- [ ] Fix the capital-city fallback (handle the `restcountries` response)
- [ ] Per-user weather via IP geolocation, with country-capital fallback
- [ ] Larger synthetic dataset or real data so PCA + KMeans has enough variance
- [ ] Hourly weather forecast across the training window, not only the latest day
- [ ] Google Calendar integration (training window detection)
- [ ] Experience-weighted load metrics
- [ ] Device data standardization (Garmin, Whoop, Oura) for real-world testing

## Companion project
- [ ] Trainer-facing client churn prediction (rule-based heuristic first, XGBoost once sufficient labeled data exists)

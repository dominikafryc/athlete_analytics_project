# Athlete Analytics & Injury Prevention System

A data pipeline and ML model that analyzes biometric load, CNS fatigue, and hormonal cycle adaptation to predict next-day training readiness and recommend a concrete daily action: train as planned, swap discipline, or rest.

Built as a proof of concept on **synthetic data**. This is not a clinical tool.

## About The Project

Athletes and physically active people often experience CNS fatigue and training overload that is hard to detect through subjective feeling alone. This project integrates HRV, sleep architecture, training load, blood biomarkers, and menstrual cycle phase to flag early overtraining signals and recommend a specific daily action, not just a generic "you're tired" alert.

The thought process, design decisions, and the problems I ran into (including data leakage) are described in the **[case study](case_study.md)**.

## Architecture

The project has two layers that currently run side by side:

| Layer | What it does |
|-------|--------------|
| **Python** (`athlete_analytics_project.py`) | Complete pipeline and source of truth for the ML model: imputation, cycle-aware baselines, EWMA/ACWR, Z-scores, anomaly detection, Random Forest, SHAP, weather gate, recommendation engine |
| **dbt + DuckDB** (`models/`) | SQL reimplementation of the logic that fits SQL: calendar spine, rolling baselines, TRIMP, rule-based business logic |

The Python pipeline does **not** read the dbt outputs yet. dbt serves as a reference implementation I compare against Python. Known differences between the two are documented in the case study (section 7).

![dbt lineage](docs/lineage.png)

### Python: core vs. optional modules

**Core (required for prediction to run):**
- Calendar re-indexing (fills gaps in non-consecutive training logs)
- KNN imputation of missing biometrics, per user
- Cycle-aware HRV/RHR baseline (per user and menstrual phase)
- EWMA-based ACWR (Acute:Chronic Workload Ratio)
- Layered CNS fatigue detection (CMJ/Grip, with an HRV Z-score + DOMS fallback for users without measurement equipment)
- RandomForestClassifier evaluated with a chronological `TimeSeriesSplit`
- Rule-based training recommendation engine

**Optional (pipeline runs without them):**
- PCA + KMeans clustering on blood biomarkers (needs enough data; on the 8-user sample it is inactive)
- IsolationForest anomaly detection
- SHAP explainability
- Open-Meteo weather gate (discipline-specific limits, applied to the latest day only). Currently inactive in the sample run, see [LIMITATIONS.md](LIMITATIONS.md)

> **Note on evaluation:** the split is chronological, but features are built before the split using full-history statistics (see [LIMITATIONS.md](LIMITATIONS.md)). Reported metrics should be read as pipeline behavior on synthetic data, not as expected real-world performance.

### dbt layers

- **seeds**: the raw CSVs loaded by dbt (e.g. `daily_metrics`, `workouts_log`)
- **staging**: loading, cleaning, standardization
- **intermediate**: `int_user_calendar`, `int_rolling_baselines`, `int_trimp`, `int_business_logic`
- **marts**: `fct_daily_readiness`

Total: 13 models (8 staging, 4 intermediate, 1 mart) and 8 seeds, plus data tests defined in the model YAML files and in `tests/`.

## Built With
Python · pandas · NumPy · scikit-learn · SHAP · dbt · DuckDB

## Dataset

All 8 CSV datasets are synthetically generated. `user_profile.csv` is built around eight distinct athlete profiles to stress-test the pipeline against realistic edge cases (see the case study).

## Getting Started

### Prerequisites
- Python 3.9+

```sh
pip install pandas numpy scikit-learn shap requests joblib pytest dbt-duckdb
```

### Installation

```sh
git clone https://github.com/dominikafryc/athlete_analytics_project.git
cd athlete_analytics_project
```

Place all 8 CSV files in the project root before running.

## Usage

### Python pipeline

Run it locally rather than in a hosted notebook (e.g. Google Colab): the weather module geolocates from the IP of the machine running the script, so a hosted server gives the wrong location.

```sh
python athlete_analytics_project.py
```

Outputs:
- `fct_daily_readiness.csv`: enriched daily dataset for BI tools or ad-hoc analysis
- `readiness_model_v1.pkl`: trained model pipeline (preprocessing + classifier)

Note: the dbt mart `fct_daily_readiness` (built from `int_trimp` and `int_business_logic`, stored in DuckDB) and the CSV with the same name produced by Python are two independent implementations. Their comparison is described in the case study.

### dbt

Configure a DuckDB profile (the profile name must match `profile:` in `dbt_project.yml`):

```yaml
# ~/.dbt/profiles.yml
athlete_analytics:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: athlete.duckdb
```

Then:

```sh
dbt deps      # installs dbt_utils (see packages.yml)
dbt build     # runs models and tests
dbt docs generate && dbt docs serve
```

## Testing

**Python** (decision-logic unit tests): `is_weather_safe`, `get_adapted_discipline`, `get_cns_fatigue_level`, `check_discipline_swap`.

```sh
python -m pytest -v
```

**dbt** (data quality): uniqueness of the `User_ID` + `Date` grain, accepted values for categorical outputs, calendar completeness, consistency between level and index columns, and target alignment (`Target_Readiness_Tomorrow` equals the next day's status).

```sh
dbt test
```

## Status & Further Documentation

- Case study: [case_study.md](case_study.md)
- Known limitations: [LIMITATIONS.md](LIMITATIONS.md)
- Planned next steps: [ROADMAP.md](ROADMAP.md)

## License

Distributed under the MIT License.

## Contact

Dominika Fryc - dominikafryc48@gmail.com

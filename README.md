# Athlete Analytics & Injury Prevention System

Python data transformation pipeline analyzing biometric load, CNS fatigue, and hormonal cycle adaptation to model next-day training readiness and generate a clean, production-grade Data Mart.

## About The Project

Athletes and physically active people often experience CNS fatigue and training overload that's hard to detect through subjective feeling alone. This project integrates HRV, sleep architecture, training load, blood biomarkers, and menstrual cycle phase to clean, transform, and model raw physiological inputs into actionable training recommendations.

### Codebase Architecture: Core vs. Optional Modules

The pipeline runs as a single script (`athlete_analytics_project.py`), organized into two tiers:

**Core Data Transformation Modules:**
- Calendar re-indexing (ensures time-series continuity for rolling baselines)
- KNN imputation of missing biometrics per user (data quality control)
- Cycle-aware HRV/RHR baseline (personalized per user × menstrual phase)
- EWMA-based ACWR (Acute:Chronic Workload Ratio)
- Layered CNS fatigue detection (CMJ/Grip → HRV+DOMS fallback layer)
- RandomForestClassifier trained with leak-free `TimeSeriesSplit`
- Rule-based training recommendation engine

**Optional Feature Modules:**
- PCA + KMeans clustering on blood biomarkers
- IsolationForest anomaly detection
- SHAP explainability
- Open-Meteo weather API integration (discipline-specific safety limits)

### Built With
Python · pandas · NumPy · scikit-learn · SHAP · Data Modeling

## Dataset

All 8 CSV datasets are synthetically generated. `user_profile.csv` was intentionally designed around eight distinct athlete profiles to stress-test the pipeline against realistic edge cases.

## Getting Started

### Prerequisites
- Python 3.9+
- `pip install pandas numpy scikit-learn shap requests joblib pytest`

### Installation

```sh
git clone https://github.com/dominikafryc/athlete_analytics_project.git
cd athlete_analytics_project
```

Place all 8 CSV files in the project root directory before running.

## Usage

Run the main pipeline orchestrator:

```sh
python athlete_analytics_project.py
```

### Outputs
- `fct_daily_readiness.csv` - Production Data Mart (Fact Table) ready for downstream BI, ad-hoc SQL querying, or ML models.
- `readiness_model_v1.pkl` - Serialized inference model pipeline (preprocessing + classifier).

## Testing

Automated unit tests cover data quality contracts and core decision-logic functions (`is_weather_safe`, `get_adapted_discipline`, `get_cns_fatigue_level`, `check_discipline_swap`).

Execute tests via pytest:

```sh
python -m pytest tests/ -v
```

## Status & Further Documentation

- Known limitations: [LIMITATIONS.md](LIMITATIONS.md)
- Planned next steps: [ROADMAP.md](ROADMAP.md)

## License

Distributed under the MIT License.

## Contact

Dominika Fryc - dominikafryc48@gmail.com

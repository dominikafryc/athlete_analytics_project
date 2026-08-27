# Known Limitations

- **Synthetic data only.** All 8 CSVs are algorithmically generated, not
  sourced from real wearables (Garmin, Whoop, Oura) or clinical records.
- **Non-clinical scope.** Recommendations are heuristic, training-load
  guidance only - not medical or clinical advice.
- **No intraday wear-time validation.** Input datasets are pre-aggregated at a
  daily grain without hourly wear-time tracking, so incomplete tracking days
  cannot currently be dynamically flagged or excluded before calculating baselines.
- **In-memory processing.** Transformations run in-memory via Pandas rather
  than native SQL warehouse transformations (e.g., Snowflake/DuckDB).
- **Weather API uses a single static location**, not per-user GPS or IP
  geolocation.
- **Weather forecast is point-in-time ("now"), not full-day.** A storm later
  in the day isn't currently flagged in advance.
- **CMJ/Grip strength require measurement equipment** available mainly to
  professional athletes/clubs; the system falls back to HRV+DOMS for users
  without it, but this fallback layer is less precise.
- **Single-script architecture.** The pipeline is cleanly organized with
  modular functions but lives in one file, not yet split into a Python
  package.
- **Not validated on real users or large-scale data.** Model metrics reflect
  performance on synthetic data only.

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
- **CMJ/Grip strength require measurement equipment** available mainly to
  professional athletes/clubs; the system falls back to HRV+DOMS for users
  without it, but this fallback layer is less precise.
- **Single-script architecture.** The pipeline is cleanly organized with
  modular functions but lives in one file, not yet split into a Python
  package.
- **Not validated on real users or large-scale data.** Model metrics reflect
  performance on synthetic data only.
* **IP Geolocation Accuracy & VPN Trust:** The weather module heavily relies on third-party IP geolocation (`ip-api.com`). The system blindly trusts the resolved IP address; therefore, if a user is utilizing a VPN or proxy, the pipeline will fetch accurate weather data for the server's location rather than the user's actual physical location. Furthermore, in the event of a hard technical failure (e.g., API timeouts, network drops, or rate limits), the system gracefully falls back to the country's capital coordinates, or ultimately applies default safe weather parameters (e.g., 20°C, no storms) if all external requests fail.

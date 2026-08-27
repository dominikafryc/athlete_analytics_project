# Roadmap

- Per-user weather via IP geolocation, with country-capital fallback
- Full-day/hourly weather forecast instead of point-in-time
- Google Calendar integration (training window detection)
- Full modularization into a Python package (config.py, weather.py, etc.)
- Device data standardization (Garmin, Whoop, Oura) for real-world testing
- Wear-time completeness validation engine (flagging `is_incomplete` days based on min tracking hours/sleep)
- Clean baseline calculations computed strictly from complete rest days (training vs. non-training segmentation)
- Companion project: trainer-facing client churn prediction
      (rule-based heuristic first, XGBoost once sufficient labeled data exists)

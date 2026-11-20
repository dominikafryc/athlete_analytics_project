import subprocess
import sys

STEPS = [
    ["dbt", "seed"],
    ["dbt", "build"],
    [sys.executable, "athlete_analytics_project.py"],
    [sys.executable, "compare_report.py"],
]

for step in STEPS:
    print(f"\n>>> {' '.join(step)}")
    subprocess.run(step, check=True)
print("\nPipeline finished.")
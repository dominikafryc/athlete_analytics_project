import pandas as pd

files_to_fix = [
    'blood_biomarkers.csv',
    'daily_metrics.csv',
    'health_standards.csv',
    'population_benchmarks.csv',
    'user_profile.csv'
]

for file in files_to_fix:
    path = f"seeds/{file}"
    df = pd.read_csv(path, sep=';', decimal=',')
    
    df.to_csv(path, index=False)
    print(f"Format fixed: {file}")
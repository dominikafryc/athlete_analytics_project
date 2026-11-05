import os

files_to_fix = [
    'blood_biomarkers.csv',
    'daily_metrics.csv',
    'health_standards.csv',
    'population_benchmarks.csv',
    'user_profile.csv',
    'menstrual_cycle.csv',
    'workouts_log.csv',
    'discipline_weather_config.csv'
]

for file in files_to_fix:
    path = f"seeds/{file}"
    if not os.path.exists(path):
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace('\\,', ',')
    content = content.replace('\\', '')
    
    content = content.replace(';', ',')
    
    content = content.replace('"', '')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"fixed and cleaned: {file}")
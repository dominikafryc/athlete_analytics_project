import pandas as pd
import numpy as np
import requests
import os
import logging
from sklearn.impute import KNNImputer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
import shap
from sklearn.metrics import silhouette_score
import joblib
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

def load_all_datasets(data_dir='.', sep=';', decimal=','):
    csv_files = {
        'blood_biomarkers': 'blood_biomarkers.csv',
        'daily_metrics': 'daily_metrics.csv',
        'health_standards': 'health_standards.csv',
        'menstrual_cycle': 'menstrual_cycle.csv',
        'population_benchmarks': 'population_benchmarks.csv',
        'user_profile': 'user_profile.csv',
        'workouts_log': 'workouts_log.csv',
        'discipline_weather_config': 'discipline_weather_config.csv',
    }

    datasets = {}
    logging.info("Starting batch loading of datasets...")

    for key, filename in csv_files.items():
        file_path = os.path.join(data_dir, filename)
        datasets[key] = pd.read_csv(file_path, sep=sep, decimal=decimal, encoding='utf-8-sig')
        logging.info(f"Loaded '{key}': {datasets[key].shape}")

    return datasets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

data = load_all_datasets()

blood_biomarkers = data['blood_biomarkers']
daily_metrics = data['daily_metrics']
health_standards = data['health_standards']
menstrual_cycle = data['menstrual_cycle']
population_benchmarks = data['population_benchmarks']
user_profile = data['user_profile']
workouts_log = data['workouts_log']
discipline_weather_config = data['discipline_weather_config']

# merge dataframes
df_merged = pd.merge(daily_metrics, user_profile, on='User_ID', how='left')

# population benchmarks and health standards
logging.info("Integrating Population Benchmarks and Health Standards...")

#creating age group with age
if 'Age' in df_merged.columns:
    bins = [0, 17, 29, 39, 49, 100]
    labels = ['<18', '18-29', '30-39', '40-49', '50+']
    df_merged['Age_Group'] = pd.cut(df_merged['Age'], bins=bins, labels=labels)

# merging with avg_HRV instead of percentyles
if 'Age_Group' in df_merged.columns and 'Sex' in df_merged.columns and not population_benchmarks.empty:
    df_merged = df_merged.merge(
        population_benchmarks[['Age_Group', 'Sex', 'Avg_HRV']],
        on=['Age_Group', 'Sex'],
        how='left'
    )
    if 'Avg_HRV' in df_merged.columns:
        df_merged['HRV_Vs_Population_Pct'] = (df_merged['Daily_HRV'] / df_merged['Avg_HRV'] - 1) * 100

# ferritin
ferritin_threshold = 30.0
if not health_standards.empty and 'Metric_Name' in health_standards.columns:
    ferr_row = health_standards[health_standards['Metric_Name'] == 'Ferritin_ng_mL']
    if not ferr_row.empty:
        ferritin_threshold = ferr_row['Warning_Threshold'].iloc[0]

if not blood_biomarkers.empty and 'Ferritin_ng_mL' in blood_biomarkers.columns:
    latest_ferritin = blood_biomarkers['Ferritin_ng_mL'].iloc[-1]
    df_merged['Supplement_Alert'] = np.where(latest_ferritin < ferritin_threshold, 'Low Iron / Ferritin Alert', 'Optimal Biochemical Profile')

# date conversion & strict sorting
df_merged['Date'] = pd.to_datetime(df_merged['Date'])
df_merged = df_merged.sort_values(by=['User_ID', 'Date']).reset_index(drop=True)

#FIX: Date continuity - filling calendar gaps per user
logging.info("Filling calendar gaps to ensure true daily time-series analysis...")
filled_frames = []
for user_id, group in df_merged.groupby('User_ID'):
    group = group.sort_values(by='Date')
    full_range = pd.date_range(group['Date'].min(), group['Date'].max(), freq='D')
    group_reindexed = group.set_index('Date').reindex(full_range)
    group_reindexed['User_ID'] = user_id
    group_reindexed.index.name = 'Date'
    filled_frames.append(group_reindexed.reset_index())

df_merged = pd.concat(filled_frames, ignore_index=True)

# inspect data and missing values quality check
logging.info("Checking missing values across loaded DataFrames.")
logging.info(f"Blood Biomarkers missing values total: {blood_biomarkers.isnull().sum().sum()}")
logging.info(f"Daily Metrics missing values total: {daily_metrics.isnull().sum().sum()}")
logging.info(f"Health Standards missing values total: {health_standards.isnull().sum().sum()}")
logging.info(f"Menstrual Cycle missing values total: {menstrual_cycle.isnull().sum().sum()}")
logging.info(f"User Profile missing values total: {user_profile.isnull().sum().sum()}")

# defining NULLs, KNNImputer for individual users
numeric_cols = [
    'Daily_HRV', 'Daily_RHR', 'Sleep_Duration', 'Deep_Sleep_h', 'REM_Sleep_h',
    'Sleep_Efficiency_pct', 'Wake_Episodes_Count', 'Grip_Strength_kg', 'CMJ_Jump_cm',
    'Subjective_Mood', 'DOMS_Scale', 'Motivation_Level', 'sRPE'
]

valid_impute_cols = [col for col in numeric_cols if col in df_merged.columns]
imputer = KNNImputer(n_neighbors=5)

for user_id in df_merged['User_ID'].unique():
    user_mask = df_merged['User_ID'] == user_id
    user_data = df_merged.loc[user_mask, valid_impute_cols]
    valid_cols = user_data.columns[~user_data.isnull().all()]
    if len(valid_cols) > 0:
        df_merged.loc[user_mask, valid_cols] = imputer.fit_transform(user_data[valid_cols])

logging.info(f"KNN Imputation completed. Remaining NULL values: {df_merged[valid_impute_cols].isnull().sum().sum()}")

# addition for people without data
df_merged['Daily_HRV'] = df_merged['Daily_HRV'].fillna(df_merged['Daily_HRV'].mean())
df_merged['Sleep_Duration'] = df_merged['Sleep_Duration'].fillna(7.0)

# API weather and google calendar
url = 'https://api.open-meteo.com/v1/forecast'

user_lat = df_merged.get('Latitude', 52.2297)
user_lon = df_merged.get('Longitude', 21.0122)

lat = user_lat.iloc[0] if isinstance(user_lat, pd.Series) else user_lat
lon = user_lon.iloc[0] if isinstance(user_lon, pd.Series) else user_lon

params = {
    'latitude': lat,
    'longitude': lon,
    'current': 'temperature_2m,wind_speed_10m,weather_code',
    'timezone': 'auto'
}

try:
    response = requests.get(url, params=params, timeout=5).json()
    temp = response['current']['temperature_2m']
    wind = response['current']['wind_speed_10m']
    code = response['current']['weather_code']

    df_merged['Weather_Temperature'] = temp
    df_merged['Weather_Wind'] = wind
    df_merged['Weather_Condition'] = code
    df_merged['Weather_Storm'] = 1 if code >= 95 else 0

    logging.info(f"Dynamic Weather API fetched for [{lat}, {lon}]: {temp}°C, Wind: {wind} km/h")
except Exception as e:
    logging.error(f"Failed to fetch weather data for [{lat}, {lon}]: {e}. Fallback applied.")
    df_merged['Weather_Temperature'] = 20.0
    df_merged['Weather_Wind'] = 10.0
    df_merged['Weather_Condition'] = 0
    df_merged['Weather_Storm'] = 0

#cleaning and converting dta with API and configuration
df_merged['Weather_Temperature'] = pd.to_numeric(df_merged.get('Weather_Temperature', 20), errors='coerce').fillna(20.0)
df_merged['Weather_Wind'] = pd.to_numeric(df_merged.get('Weather_Wind', 10), errors='coerce').fillna(10.0)
df_merged['Weather_Storm'] = pd.to_numeric(df_merged.get('Weather_Storm', 0), errors='coerce').fillna(0).astype(int)

#connecting weather configuration per discipline
discipline_col = None
for candidate in ['Main_Discipline', 'Discipline']:
    if candidate in df_merged.columns:
        discipline_col = candidate
        break

config_key_col = None
for candidate in ['Discipline', 'Main_Discipline']:
    if candidate in discipline_weather_config.columns:
        config_key_col = candidate
        break

if discipline_col and config_key_col:
    df_merged = df_merged.merge(
        discipline_weather_config[[config_key_col, 'Temp_Min', 'Temp_Max', 'Wind_Max', 'No_Storm']],
        left_on=discipline_col, right_on=config_key_col, how='left'
    )
    logging.info(f"Discipline weather config merged on '{discipline_col}' <-> '{config_key_col}'.")
else:
    logging.warning("Could not merge discipline_weather_config: matching discipline column not found. "
                     "Is_Weather_Optimal will default to permissive (1) for all rows.")

def get_numeric_series(df, col_name):
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors='coerce')
    return pd.Series(np.nan, index=df.index)

temp_min = get_numeric_series(df_merged, 'Temp_Min')
temp_max = get_numeric_series(df_merged, 'Temp_Max')
wind_max = get_numeric_series(df_merged, 'Wind_Max')

if 'No_Storm' in df_merged.columns:
    no_storm = df_merged['No_Storm'].astype(str).str.lower().isin(['true', '1', '1.0'])
else:
    no_storm = pd.Series(False, index=df_merged.index)

# weather conditions
is_temp_ok = (temp_min.isna() | (df_merged['Weather_Temperature'] >= temp_min)) & \
             (temp_max.isna() | (df_merged['Weather_Temperature'] <= temp_max))

is_wind_ok = wind_max.isna() | (df_merged['Weather_Wind'] <= wind_max)

is_storm_ok = (~no_storm) | (df_merged['Weather_Storm'] == 0)

#final flag
df_merged['Is_Weather_Optimal'] = (is_temp_ok & is_wind_ok & is_storm_ok).astype(int)

# menstrual cycle module
logging.info("Starting calculation of Menstrual Cycle Metrics...")

if 'Cycle_Phase' in df_merged.columns:
    df_merged = df_merged.drop(columns=['Cycle_Phase'])

if 'menstrual_cycle' in locals() and not menstrual_cycle.empty and 'Cycle_Phase' in menstrual_cycle.columns:
    menstrual_cycle['Date'] = pd.to_datetime(menstrual_cycle['Date'])
    df_merged = df_merged.merge(
        menstrual_cycle[['User_ID', 'Date', 'Cycle_Phase']],
        on=['User_ID', 'Date'],
        how='left'
    )

df_merged['Cycle_Phase'] = df_merged['Cycle_Phase'].fillna('Not_Applicable')

df_merged['HRV_Phase_Baseline'] = df_merged.groupby(['User_ID', 'Cycle_Phase'])['Daily_HRV'].transform('mean')
df_merged['HRV_Phase_Std'] = df_merged.groupby(['User_ID', 'Cycle_Phase'])['Daily_HRV'].transform('std').fillna(1.0)
df_merged['HRV_ZScore_CyclAware'] = (
    (df_merged['Daily_HRV'] - df_merged['HRV_Phase_Baseline'])
    / (df_merged['HRV_Phase_Std'] + 1e-5)
)

df_merged['RHR_Phase_Baseline'] = df_merged.groupby(['User_ID', 'Cycle_Phase'])['Daily_RHR'].transform('mean')
df_merged['RHR_Hormonal_Adjusted'] = df_merged['Daily_RHR'] - df_merged['RHR_Phase_Baseline']

# ANS and mental stress metrics
logging.info("Starting calculation of Mental Health & Psychological Strain metrics...")

if 'Daily_HRV' in df_merged.columns and 'Daily_RHR' in df_merged.columns:
    df_merged['HRV_ZScore'] = df_merged.groupby('User_ID')['Daily_HRV'].transform(
        lambda x: (x - x.mean()) / np.where(x.std() > 0.01, x.std(), 1.0)
    )
    df_merged['RHR_ZScore'] = df_merged.groupby('User_ID')['Daily_RHR'].transform(
        lambda x: (x - x.mean()) / np.where(x.std() > 0.01, x.std(), 1.0)
    )
    df_merged['Psychological_Stress_Score'] = df_merged['RHR_ZScore'] - df_merged['HRV_ZScore']
else:
    df_merged['HRV_ZScore'] = 0.0
    df_merged['RHR_ZScore'] = 0.0
    df_merged['Psychological_Stress_Score'] = 0.0

# 5-day HRV trend slope
def calc_trend_slope(series, window=5):
    def slope(x):
        if len(x) < 3: return 0.0
        return np.polyfit(np.arange(len(x)), x.values, 1)[0]
    return series.rolling(window=window, min_periods=3).apply(slope, raw=False)

df_merged['HRV_Trend_5d'] = df_merged.groupby('User_ID')['Daily_HRV'].transform(calc_trend_slope)

# rolling baselines & relative deviations
df_merged['HRV_30day_Baseline'] = df_merged.groupby('User_ID')['Daily_HRV'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
df_merged['Sleep_30day_Baseline'] = df_merged.groupby('User_ID')['Sleep_Duration'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())

df_merged['HRV_Pct_Of_Baseline'] = df_merged['Daily_HRV'] / (df_merged['HRV_30day_Baseline'] + 1e-5)
df_merged['Sleep_Pct_Of_Baseline'] = df_merged['Sleep_Duration'] / (df_merged['Sleep_30day_Baseline'] + 1e-5)

df_merged['HRV_Deviation_Alert'] = np.select(
    [
        df_merged['HRV_ZScore_CyclAware'] < -2.0,
        df_merged['HRV_ZScore_CyclAware'] < -1.0,
    ],
    ['HRV_Significant_Drop', 'HRV_Mild_Drop'],
    default='Normal'
)

df_merged['HRV_EWMA_7'] = df_merged.groupby('User_ID')['Daily_HRV'].transform(lambda x: x.ewm(span=7, adjust=False).mean())

#ACWR based on EWMA (Exponentially Weighted Moving Average) with non-training days included as 0
logging.info("Calculating EWMA-based ACWR (Acute:Chronic Workload Ratio)...")
sRPE_filled = df_merged['sRPE'].fillna(0)

df_merged['Acute_Load_7d'] = df_merged.groupby('User_ID', group_keys=False).apply(
    lambda g: g['sRPE'].fillna(0).ewm(span=7, adjust=False).mean()
)
df_merged['Chronic_Load_28d'] = df_merged.groupby('User_ID', group_keys=False).apply(
    lambda g: g['sRPE'].fillna(0).ewm(span=28, adjust=False).mean()
)
df_merged['ACWR'] = df_merged['Acute_Load_7d'] / (df_merged['Chronic_Load_28d'] + 1e-5)

# TRIMP and load discrepancy
logging.info("Calculating TRIMP and Load Discrepancy...")

if 'workouts_log' in locals() and not workouts_log.empty:
    df_workouts = workouts_log.copy()
    df_workouts['Date'] = pd.to_datetime(df_workouts['Date'])

    hr_cols_to_merge = [c for c in ['HR_Max', 'HR_Rest'] if c in df_merged.columns]

    for c in hr_cols_to_merge:
        if c in df_workouts.columns:
            df_workouts = df_workouts.drop(columns=[c])

    df_workouts = df_workouts.merge(
        df_merged[['User_ID', 'Date'] + hr_cols_to_merge].drop_duplicates(subset=['User_ID', 'Date']),
        on=['User_ID', 'Date'],
        how='left'
    )

    avg_hr_col = None
    for candidate in ['Avg_Heart_Rate', 'Avg_HR', 'Average_Heart_Rate', 'Heart_Rate_Avg', 'Avg_HeartRate']:
        if candidate in df_workouts.columns:
            avg_hr_col = candidate
            break

    dur_col = None
    for candidate in ['Workout_Duration_min', 'Duration_min', 'Duration', 'Minutes']:
        if candidate in df_workouts.columns:
            dur_col = candidate
            break

    hr_rest = df_workouts['HR_Rest'].fillna(50.0) if 'HR_Rest' in df_workouts.columns else 50.0
    hr_max = df_workouts['HR_Max'].fillna(190.0) if 'HR_Max' in df_workouts.columns else 190.0

    if avg_hr_col:
        avg_hr = df_workouts[avg_hr_col].fillna(hr_rest + 40.0)
    else:
        avg_hr = hr_rest + (hr_max - hr_rest) * 0.65

    duration = df_workouts[dur_col].fillna(45.0) if dur_col else 45.0

    # TRIMP
    hr_reserve = ((avg_hr - hr_rest) / (hr_max - hr_rest + 1e-5)).clip(0.0, 1.0)
    df_workouts['TRIMP_Objective'] = duration * hr_reserve * np.exp(1.92 * hr_reserve)

    min_t, max_t = df_workouts['TRIMP_Objective'].min(), df_workouts['TRIMP_Objective'].max()
    if max_t > min_t:
        df_workouts['TRIMP_Objective_scaled'] = ((df_workouts['TRIMP_Objective'] - min_t) / (max_t - min_t + 1e-5)) * 1000.0
    else:
        df_workouts['TRIMP_Objective_scaled'] = 0.0

    trimp_daily = df_workouts.groupby(['User_ID', 'Date'])['TRIMP_Objective_scaled'].sum().reset_index()

    if 'TRIMP_Objective_scaled' in df_merged.columns:
        df_merged = df_merged.drop(columns=['TRIMP_Objective_scaled'])

    df_merged = df_merged.merge(trimp_daily, on=['User_ID', 'Date'], how='left')
else:
    df_merged['TRIMP_Objective_scaled'] = 0.0

df_merged['TRIMP_Objective_scaled'] = df_merged['TRIMP_Objective_scaled'].fillna(0.0)

# load discrepancy for day with sRPE
df_merged['Load_Discrepancy'] = np.where(
    df_merged['sRPE'].notnull(),
    df_merged['sRPE'] - df_merged['TRIMP_Objective_scaled'],
    np.nan
)

# insomnia and sleep metrics
logging.info("Starting calculation of Insomnia and Sleep Architecture metrics...")

if 'Deep_Sleep_h' in df_merged.columns and 'REM_Sleep_h' in df_merged.columns and 'Sleep_Duration' in df_merged.columns:
    df_merged['Restorative_Sleep_h'] = df_merged['Deep_Sleep_h'] + df_merged['REM_Sleep_h']
    df_merged['Restorative_Sleep_Pct'] = (df_merged['Restorative_Sleep_h'] / (df_merged['Sleep_Duration'] + 1e-5)) * 100
    logging.info("Restorative sleep percentage successfully computed.")
else:
    logging.warning("Sleep stage columns missing. Skipping Restorative Sleep calculation.")

if all(col in df_merged.columns for col in ['Wake_Episodes_Count', 'Sleep_Efficiency_pct', 'Deep_Sleep_h']):
    insomnia_conditions = [
        (df_merged['Wake_Episodes_Count'] >= 3) & (df_merged['Sleep_Efficiency_pct'] < 80) & (df_merged['Deep_Sleep_h'] < 1.0),
        (df_merged['Wake_Episodes_Count'] >= 2) | (df_merged['Sleep_Efficiency_pct'] < 85),
    ]
    insomnia_choices = ['HIGH_RISK', 'MODERATE_RISK']
    df_merged['Insomnia_Risk_Level'] = np.select(insomnia_conditions, insomnia_choices, default='LOW_RISK')

    risk_mapping = {'LOW_RISK': 0, 'MODERATE_RISK': 1, 'HIGH_RISK': 2}
    df_merged['Insomnia_Index'] = df_merged['Insomnia_Risk_Level'].map(risk_mapping)
    logging.info("Insomnia Risk Score and Insomnia Index successfully derived.")
else:
    logging.warning("Required columns for Insomnia scoring not found.")

# mental fatigue and mood disruption index
if all(col in df_merged.columns for col in ['Subjective_Mood', 'Motivation_Level']):
    df_merged['Mental_Fatigue_Flag'] = np.where(
        (df_merged['Subjective_Mood'] <= 4) & (df_merged['Motivation_Level'] <= 4),
        1, 0
    )
    logging.info("Mental Fatigue Flag successfully computed based on subjective metrics.")
else:
    logging.warning("Subjective Mood or Motivation columns missing.")

if 'sRPE' in df_merged.columns and 'Psychological_Stress_Score' in df_merged.columns:
    df_merged['Stress_to_Load_Ratio'] = df_merged['Psychological_Stress_Score'] / (df_merged['sRPE'] + 1.0)
    logging.info("Stress to Load Ratio successfully calculated.")

# Hybrid readiness engine & Unsupervised anomaly detection
iso_features = [col for col in ['Daily_HRV', 'RHR_Hormonal_Adjusted', 'Sleep_Duration', 'Wake_Episodes_Count'] if col in df_merged.columns]
X_iso = SimpleImputer(strategy='mean').fit_transform(df_merged[iso_features])

iso = IsolationForest(contamination=0.05, random_state=42)
preds = iso.fit_predict(X_iso)
df_merged['Anomaly_Flag'] = np.where(preds == -1, 1, 0)

# CNS load test - checking CMJ Jump and Grip Strength
df_merged['CMJ_Jump_cm_30day'] = df_merged.groupby('User_ID')['CMJ_Jump_cm'].transform(
    lambda x: x.rolling(window=30, min_periods=1).mean()
)
df_merged['Grip_Strength_kg_30day'] = df_merged.groupby('User_ID')['Grip_Strength_kg'].transform(
    lambda x: x.rolling(window=30, min_periods=1).mean()
)
df_merged['CMJ_Drop_%'] = (df_merged['CMJ_Jump_cm'] - df_merged['CMJ_Jump_cm_30day']) / df_merged['CMJ_Jump_cm_30day']
df_merged['Grip_Drop_%'] = (df_merged['Grip_Strength_kg'] - df_merged['Grip_Strength_kg_30day']) / df_merged['Grip_Strength_kg_30day']

# CNS/neuromuscular fatigue
def get_cns_fatigue_level(row):
    if pd.notnull(row.get('CMJ_Drop_%')):
        if row['CMJ_Drop_%'] < -0.15:
            return 'Severe'
        elif row['CMJ_Drop_%'] < -0.07:
            return 'Moderate'
        return 'Normal'
    elif pd.notnull(row.get('Grip_Drop_%')):
        if row['Grip_Drop_%'] < -0.10:
            return 'Severe'
        elif row['Grip_Drop_%'] < -0.05:
            return 'Moderate'
        return 'Normal'
    else:
        hrv_z = row.get('HRV_ZScore_CyclAware', 0)
        doms = row.get('DOMS_Scale', 0)
        if pd.isnull(hrv_z):
            hrv_z = 0
        if pd.isnull(doms):
            doms = 0
        if hrv_z < -2.0 or doms >= 8:
            return 'Severe'
        elif hrv_z < -1.0 or doms >= 6:
            return 'Moderate'
        return 'Normal'

df_merged['CNS_Fatigue_Level'] = df_merged.apply(get_cns_fatigue_level, axis=1)
cns_fatigue_mapping = {'Normal': 0, 'Moderate': 1, 'Severe': 2}
df_merged['CNS_Fatigue_Index'] = df_merged['CNS_Fatigue_Level'].map(cns_fatigue_mapping)

# Helper function to find a valid secondary discipline with sufficient experience
def get_adapted_discipline(row, min_experience_years=2.0):
    candidates = [
        (row.get('Second_Discipline'), pd.to_numeric(row.get('Experience_Second_Sport_Yrs', 0), errors='coerce')),
        (row.get('Third_Discipline'), pd.to_numeric(row.get('Experience_Third_Sport_Yrs', 0), errors='coerce')),
    ]
    valid = [
        (name, years) for name, years in candidates
        if pd.notnull(name) and pd.notnull(years) and years >= min_experience_years
    ]
    if not valid:
        return None
    return max(valid, key=lambda x: x[1])[0]

#weather function
def is_weather_safe(is_weather_optimal_flag):
    return is_weather_optimal_flag == 1

# Discipline swap function - with neuro-muscular adaptation check
def check_discipline_swap(row):
    if not is_weather_safe(row.get('Is_Weather_Optimal', 1)):
        return 'Weather_Unsafe_Swap_Indoor'

    if row.get('Is_Injured_Flag', 0) == 1:
        return 'Rest_Required_Injury'

    cns_level = row.get('CNS_Fatigue_Level', 'Normal')

    if cns_level == 'Severe' or row.get('Anomaly_Flag', 0) == 1 or row.get('Insomnia_Index', 0) == 2:
        return 'Rest_Required'

    elif cns_level == 'Moderate' or row.get('Mental_Fatigue_Flag', 0) == 1:
        adapted = get_adapted_discipline(row, min_experience_years=2.0)
        if adapted:
            return f"Swap to: {adapted}"
        else:
            return 'Rest_Required_Low_Adaptation'

    else:
        return 'As_Scheduled'

df_merged['Training_Recommendation'] = df_merged.apply(check_discipline_swap, axis=1)

df_merged['HRV_30d'] = df_merged.groupby('User_ID')['Daily_HRV'].transform(lambda x: x.rolling(30, min_periods=1).mean())
df_merged['HRV_Ratio'] = df_merged['Daily_HRV'] / (df_merged['HRV_30d'] + 1e-5)

df_merged['Readiness_Status_Today'] = np.where(
    df_merged['HRV_Ratio'] < 0.85, 'Low',
    np.where(df_merged['HRV_Ratio'] < 0.95, 'Moderate', 'High')
)

df_merged['Readiness_Status'] = df_merged['Readiness_Status_Today']
df_merged['Target_Readiness_Tomorrow'] = df_merged.groupby('User_ID')['Readiness_Status_Today'].shift(-1)

# PCA for blood_biomarkers
def process_blood_pca_and_clustering(blood_biomarkers, df_merged):
    logging.info("Starting leak-free PCA and Clustering for Blood Biomarkers...")
    numeric_blood_cols = blood_biomarkers.select_dtypes(include=['float64', 'int64']).columns
    numeric_blood_cols = [c for c in numeric_blood_cols if c not in ['User_ID', 'ID', 'Test_ID']]

    if len(numeric_blood_cols) < 2:
        logging.warning("Insufficient numeric blood columns for PCA. Assigning defaults.")
        df_merged['PCA_Blood_1'] = 0.0
        df_merged['PCA_Blood_2'] = 0.0
        df_merged['Health_Cluster_ID'] = -1
        return df_merged

    blood_pca_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=2, random_state=42))
    ])

    X_blood_raw = blood_biomarkers[numeric_blood_cols]
    X_pca_transformed = blood_pca_pipeline.fit_transform(X_blood_raw)

    df_blood_pca = blood_biomarkers[['User_ID', 'Test_Date']].copy()
    df_blood_pca['Date'] = pd.to_datetime(df_blood_pca['Test_Date'])
    df_blood_pca['PCA_Blood_1'] = X_pca_transformed[:, 0]
    df_blood_pca['PCA_Blood_2'] = X_pca_transformed[:, 1]
    df_blood_pca = df_blood_pca.sort_values('Date')

    df_merged = df_merged.sort_values('Date').reset_index(drop=True)
    df_merged = pd.merge_asof(
        df_merged,
        df_blood_pca[['User_ID', 'Date', 'PCA_Blood_1', 'PCA_Blood_2']],
        on='Date',
        by='User_ID',
        direction='backward'
    )

    if 'PCA_Blood_1' not in df_merged.columns:
        df_merged['PCA_Blood_1'] = 0.0
    else:
        df_merged['PCA_Blood_1'] = df_merged.groupby('User_ID')['PCA_Blood_1'].ffill().fillna(0.0)

    if 'PCA_Blood_2' not in df_merged.columns:
        df_merged['PCA_Blood_2'] = 0.0
    else:
        df_merged['PCA_Blood_2'] = df_merged.groupby('User_ID')['PCA_Blood_2'].ffill().fillna(0.0)

    pca_features = df_merged[['PCA_Blood_1', 'PCA_Blood_2']].values

    if np.unique(pca_features, axis=0).shape[0] > 4:
        silhouette_scores = {}
        for k in range(2, 5):
            kmeans_test = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans_test.fit_predict(pca_features)
            if len(np.unique(labels)) > 1:
                silhouette_scores[k] = silhouette_score(pca_features, labels)

        if silhouette_scores:
            best_k = max(silhouette_scores, key=silhouette_scores.get)
            kmeans_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            df_merged['Health_Cluster_ID'] = kmeans_final.fit_predict(pca_features)
            logging.info(f"KMeans Clustering successful! Optimal k={best_k} (Silhouette: {silhouette_scores[best_k]:.4f})")
        else:
            df_merged['Health_Cluster_ID'] = -1
            logging.warning("Clustering fallback applied: Insufficient distinct clusters. Assigned Cluster ID -1.")
    else:
        df_merged['Health_Cluster_ID'] = -1
        logging.warning("Low variance in PCA space. Health_Cluster_ID set to -1.")

    return df_merged

# execute PCA clustering on df_merged
df_merged = process_blood_pca_and_clustering(blood_biomarkers, df_merged)

# refresh ML dataset after adding PCA features
df_clean_ml = df_merged.dropna(subset=['Target_Readiness_Tomorrow']).copy()
df_clean_ml = df_clean_ml.sort_values('Date').reset_index(drop=True)

# prepare ML feature matrix (including Stress_to_Load_Ratio)
possible_features = [
    'Daily_HRV', 'HRV_EWMA_7', 'HRV_Trend_5d', 'HRV_Pct_Of_Baseline', 'Sleep_Pct_Of_Baseline',
    'RHR_Hormonal_Adjusted', 'Sleep_Duration', 'Deep_Sleep_h', 'REM_Sleep_h',
    'Sleep_Efficiency_pct', 'Wake_Episodes_Count', 'CMJ_Jump_cm', 'Grip_Strength_kg',
    'Subjective_Mood', 'DOMS_Scale', 'Motivation_Level', 'Acute_Load_7d', 'Chronic_Load_28d', 'Training_Monotony',
    'Training_Strain', 'Load_Discrepancy', 'PCA_Blood_1', 'PCA_Blood_2',
    'Restorative_Sleep_Pct', 'Insomnia_Index', 'Psychological_Stress_Score',
    'Mental_Fatigue_Flag', 'Stress_to_Load_Ratio'
]

feature_cols = [col for col in possible_features if col in df_clean_ml.columns]

X_raw = df_clean_ml[feature_cols].values
y_raw = df_clean_ml['Target_Readiness_Tomorrow'].values

ml_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
    ('model', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42))
])

tscv = TimeSeriesSplit(n_splits=5)
accuracies, precisions, recalls, f1s = [], [], [], []

for train_index, test_index in tscv.split(X_raw):
    X_train, X_test = X_raw[train_index], X_raw[test_index]
    y_train, y_test = y_raw[train_index], y_raw[test_index]

    ml_pipeline.fit(X_train, y_train)
    y_pred = ml_pipeline.predict(X_test)

    accuracies.append(accuracy_score(y_test, y_pred))
    precisions.append(precision_score(y_test, y_pred, average='macro', zero_division=0))
    recalls.append(recall_score(y_test, y_pred, average='macro', zero_division=0))
    f1s.append(f1_score(y_test, y_pred, average='macro', zero_division=0))

# fit pipeline on the complete dataset
ml_pipeline.fit(X_raw, y_raw)

logging.info("MODEL EVALUATION METRICS (TimeSeriesSplit)")
logging.info(f"Accuracy:  {np.mean(accuracies):.3f}")
logging.info(f"Precision: {np.mean(precisions):.3f}")
logging.info(f"Recall:    {np.mean(recalls):.3f}")
logging.info(f"F1-Score:  {np.mean(f1s):.3f}")

# SHAP + Explanation
X_transformed = ml_pipeline.named_steps['scaler'].transform(
    ml_pipeline.named_steps['imputer'].transform(X_raw)
)
rf_model = ml_pipeline.named_steps['model']

explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X_transformed)

sample_idx = len(df_clean_ml) - 1
sample_x = X_transformed[sample_idx:sample_idx+1]
pred_class = rf_model.predict(sample_x)[0]
class_idx = np.where(rf_model.classes_ == pred_class)[0][0]

if isinstance(shap_values, list):
    sample_shap = np.abs(shap_values[class_idx][sample_idx])
else:
    sample_shap = np.abs(shap_values[sample_idx, :, class_idx])

total_shap = sample_shap.sum()
percentages = (sample_shap / total_shap) * 100 if total_shap > 0 else np.zeros_like(sample_shap)

top_indices = np.argsort(percentages)[::-1][:2]
driver_1, pct_1 = feature_cols[top_indices[0]], percentages[top_indices[0]]
driver_2, pct_2 = feature_cols[top_indices[1]], percentages[top_indices[1]]

shap_explanation = f"Status {pred_class} is {pct_1:.0f}% driven by {driver_1} and {pct_2:.0f}% driven by {driver_2}."

logging.info("SHAP EXPLANATION OUTPUT")
logging.info(f"Prediction Output: '{shap_explanation}'")

# Export Production Data Mart (fct_daily_readiness)
logging.info("READINESS STATUS DISTRIBUTION")
logging.info(f"\n{df_merged['Readiness_Status'].value_counts().to_string()}")

logging.info("TRAINING RECOMMENDATION DISTRIBUTION")
logging.info(f"\n{df_merged['Training_Recommendation'].value_counts().to_string()}")

logging.info(f"Detected Anomaly Days (IsolationForest): {df_merged['Anomaly_Flag'].sum()} days")

output_csv_filename = 'fct_daily_readiness.csv'
df_merged.to_csv(output_csv_filename, index=False, encoding='utf-8-sig')

# trained RandomForest to .pkl
model_pkl_filename = 'readiness_model_v1.pkl'
joblib.dump(ml_pipeline, model_pkl_filename)

logging.info("EXPORT COMPLETED SUCCESSFULLY")
logging.info(f"Dataset successfully exported to: '{output_csv_filename}' (Analytics Mart Ready)")
logging.info(f"Trained RandomForest model saved to: '{model_pkl_filename}'")

import pandas as pd


def is_weather_safe(is_weather_optimal_flag):
    return is_weather_optimal_flag == 1


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
        hrv_z = 0 if pd.isnull(hrv_z) else hrv_z
        doms = 0 if pd.isnull(doms) else doms
        
        if hrv_z < -2.0 or doms >= 8:
            return 'Severe'
        elif hrv_z < -1.0 or doms >= 6:
            return 'Moderate'
        return 'Normal'


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

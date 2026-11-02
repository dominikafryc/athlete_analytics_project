{{ config(materialized='table') }}

WITH rolling_data AS (
    SELECT * 
    FROM {{ ref('int_rolling_baselines') }}
),

business_logic AS (
    SELECT 
        *, 

        CASE 
            WHEN Age < 18 THEN '<18'
            WHEN Age BETWEEN 18 AND 29 THEN '18-29'
            WHEN Age BETWEEN 30 AND 39 THEN '30-39'
            WHEN Age BETWEEN 40 AND 49 THEN '40-49'
            WHEN Age >= 50 THEN '50+'
            ELSE 'Unknown'
        END AS Age_Group,

        CASE 
            WHEN Subjective_Mood <= 4 AND Motivation_Level <= 4 THEN 1 
            WHEN Subjective_Mood IS NOT NULL AND Motivation_Level IS NOT NULL THEN 0
            ELSE NULL
        END AS Mental_Fatigue_Flag,

        CASE 
            WHEN Wake_Episodes_Count >= 3 AND Sleep_Efficiency_pct < 80 AND Deep_Sleep_h < 1.0 THEN 'HIGH_RISK'
            WHEN Wake_Episodes_Count >= 2 OR Sleep_Efficiency_pct < 85 THEN 'MODERATE_RISK'
            WHEN Wake_Episodes_Count IS NOT NULL THEN 'LOW_RISK'
            ELSE NULL
        END AS Insomnia_Risk_Level,

        CASE 
            WHEN Wake_Episodes_Count >= 3 AND Sleep_Efficiency_pct < 80 AND Deep_Sleep_h < 1.0 THEN 2
            WHEN Wake_Episodes_Count >= 2 OR Sleep_Efficiency_pct < 85 THEN 1
            WHEN Wake_Episodes_Count IS NOT NULL THEN 0
            ELSE NULL
        END AS Insomnia_Index,

        CASE 
            WHEN (Daily_HRV / NULLIF(HRV_30day_Baseline, 0)) < 0.85 THEN 'Low'
            WHEN (Daily_HRV / NULLIF(HRV_30day_Baseline, 0)) < 0.95 THEN 'Moderate'
            WHEN Daily_HRV IS NOT NULL THEN 'High'
            ELSE NULL
        END AS Readiness_Status_Today,

        LEAD(
            CASE 
                WHEN (Daily_HRV / NULLIF(HRV_30day_Baseline, 0)) < 0.85 THEN 'Low'
                WHEN (Daily_HRV / NULLIF(HRV_30day_Baseline, 0)) < 0.95 THEN 'Moderate'
                WHEN Daily_HRV IS NOT NULL THEN 'High'
                ELSE NULL
            END
        ) OVER (PARTITION BY User_ID ORDER BY Date ASC) AS Target_Readiness_Tomorrow,

        CASE 
            WHEN CMJ_Jump_cm IS NOT NULL 
                 AND ((CMJ_Jump_cm - CMJ_Jump_cm_30day) / NULLIF(CMJ_Jump_cm_30day, 0)) < -0.15 THEN 'Severe'
            WHEN CMJ_Jump_cm IS NOT NULL 
                 AND ((CMJ_Jump_cm - CMJ_Jump_cm_30day) / NULLIF(CMJ_Jump_cm_30day, 0)) < -0.07 THEN 'Moderate'
            WHEN CMJ_Jump_cm IS NOT NULL THEN 'Normal'
            
            WHEN Grip_Strength_kg IS NOT NULL 
                 AND ((Grip_Strength_kg - Grip_Strength_kg_30day) / NULLIF(Grip_Strength_kg_30day, 0)) < -0.10 THEN 'Severe'
            WHEN Grip_Strength_kg IS NOT NULL 
                 AND ((Grip_Strength_kg - Grip_Strength_kg_30day) / NULLIF(Grip_Strength_kg_30day, 0)) < -0.05 THEN 'Moderate'
            WHEN Grip_Strength_kg IS NOT NULL THEN 'Normal'
            
            WHEN DOMS_Scale >= 8 THEN 'Severe'
            WHEN DOMS_Scale >= 6 THEN 'Moderate'
            WHEN DOMS_Scale IS NOT NULL THEN 'Normal'
            ELSE NULL
        END AS CNS_Fatigue_Level,

        CASE 
            WHEN CMJ_Jump_cm IS NOT NULL 
                 AND ((CMJ_Jump_cm - CMJ_Jump_cm_30day) / NULLIF(CMJ_Jump_cm_30day, 0)) < -0.15 THEN 2
            WHEN CMJ_Jump_cm IS NOT NULL 
                 AND ((CMJ_Jump_cm - CMJ_Jump_cm_30day) / NULLIF(CMJ_Jump_cm_30day, 0)) < -0.07 THEN 1
            WHEN CMJ_Jump_cm IS NOT NULL THEN 0
            
            WHEN Grip_Strength_kg IS NOT NULL 
                 AND ((Grip_Strength_kg - Grip_Strength_kg_30day) / NULLIF(Grip_Strength_kg_30day, 0)) < -0.10 THEN 2
            WHEN Grip_Strength_kg IS NOT NULL 
                 AND ((Grip_Strength_kg - Grip_Strength_kg_30day) / NULLIF(Grip_Strength_kg_30day, 0)) < -0.05 THEN 1
            WHEN Grip_Strength_kg IS NOT NULL THEN 0
            
            WHEN DOMS_Scale >= 8 THEN 2
            WHEN DOMS_Scale >= 6 THEN 1
            WHEN DOMS_Scale IS NOT NULL THEN 0
            ELSE NULL
        END AS CNS_Fatigue_Index

    FROM rolling_data
)

SELECT * FROM business_logic
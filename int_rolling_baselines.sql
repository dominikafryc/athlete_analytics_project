{{ config(
    materialized='table'
) }}

WITH calendar AS (
    SELECT * FROM {{ ref('int_user_calendar') }}
),

daily_metrics AS (
    SELECT * FROM {{ ref('stg_daily_metrics') }}
),

user_profile AS (
    SELECT * FROM {{ ref('stg_user_profile') }}
),

global_stats AS (
    SELECT AVG(Daily_HRV) as global_avg_hrv 
    FROM daily_metrics
),

joined_data AS (
    SELECT 
        c.User_ID,
        c.calendar_date AS Date,
    
        COALESCE(dm.Daily_HRV, g.global_avg_hrv) AS Daily_HRV,
        COALESCE(dm.Sleep_Duration, 7.0) AS Sleep_Duration,
        
        dm.CMJ_Jump_cm,
        dm.Grip_Strength_kg,
        dm.Subjective_Mood,
        dm.Motivation_Level,
        dm.Wake_Episodes_Count,
        dm.Sleep_Efficiency_pct,
        dm.Deep_Sleep_h,
        dm.DOMS_Scale,
        up.Age

    FROM calendar c
    LEFT JOIN daily_metrics dm 
        ON c.User_ID = dm.User_ID AND c.calendar_date = dm.Date
    LEFT JOIN user_profile up 
        ON c.User_ID = up.User_ID
    CROSS JOIN global_stats g
),

rolling_averages AS (
    SELECT
        *, 
        
        AVG(Daily_HRV) OVER (
            PARTITION BY User_ID 
            ORDER BY Date ASC 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS HRV_30day_Baseline,

        AVG(Sleep_Duration) OVER (
            PARTITION BY User_ID 
            ORDER BY Date ASC 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS Sleep_30day_Baseline,

        AVG(CMJ_Jump_cm) OVER (
            PARTITION BY User_ID 
            ORDER BY Date ASC 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS CMJ_Jump_cm_30day,

        AVG(Grip_Strength_kg) OVER (
            PARTITION BY User_ID 
            ORDER BY Date ASC 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS Grip_Strength_kg_30day

    FROM joined_data
)

SELECT * FROM rolling_averages
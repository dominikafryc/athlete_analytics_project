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

joined_data AS (
    SELECT 
        c.User_ID,
        c.calendar_date AS Date,
    
        dm.Daily_HRV AS Daily_HRV,
        (dm.Daily_HRV IS NULL) AS HRV_Is_Missing,
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
),

   rolling_averages AS (
       SELECT
           *,
           CASE WHEN COUNT(Daily_HRV) OVER w >= {{ var('min_baseline_days') }}
                THEN AVG(Daily_HRV) OVER w END AS HRV_30day_Baseline,
           CASE WHEN COUNT(Sleep_Duration) OVER w >= {{ var('min_baseline_days') }}
                THEN AVG(Sleep_Duration) OVER w END AS Sleep_30day_Baseline,
           CASE WHEN COUNT(CMJ_Jump_cm) OVER w >= {{ var('min_baseline_days') }}
                THEN AVG(CMJ_Jump_cm) OVER w END AS CMJ_Jump_cm_30day,
           CASE WHEN COUNT(Grip_Strength_kg) OVER w >= {{ var('min_baseline_days') }}
                THEN AVG(Grip_Strength_kg) OVER w END AS Grip_Strength_kg_30day
       FROM joined_data
       WINDOW w AS (
           PARTITION BY User_ID
           ORDER BY Date ASC
           ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
       )
   )

SELECT * FROM rolling_averages
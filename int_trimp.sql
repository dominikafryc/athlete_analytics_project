{{ config(materialized='table') }}

WITH workouts AS (
    SELECT * FROM {{ ref('stg_workouts_log') }}
),
hr_history AS (
    SELECT user_id, date, hr_max, hr_rest
    FROM {{ ref('stg_daily_metrics') }}
    WHERE hr_max IS NOT NULL AND hr_rest IS NOT NULL
),

prep_workouts AS (
    SELECT
        w.user_id,
        w.date,
        COALESCE(h.hr_rest, 50.0) AS safe_hr_rest,
        COALESCE(h.hr_max, 190.0) AS safe_hr_max,
        COALESCE(w.workout_duration_min, 45.0) AS safe_duration,
        COALESCE(w.avg_heart_rate, COALESCE(h.hr_rest, 50.0) + 40.0) AS safe_avg_hr
    FROM workouts w
    ASOF LEFT JOIN hr_history h
        ON w.user_id = h.user_id AND w.date >= h.date
),

calc_reserve AS (
    SELECT *,
        (safe_avg_hr - safe_hr_rest) / NULLIF((safe_hr_max - safe_hr_rest), 0) AS raw_hr_reserve
    FROM prep_workouts
),

clip_reserve AS (
    SELECT *, LEAST(GREATEST(raw_hr_reserve, 0.0), 1.0) AS clipped_hr_reserve
    FROM calc_reserve
),

calc_base_trimp AS (
    SELECT *,
        safe_duration * clipped_hr_reserve * EXP(1.92 * clipped_hr_reserve) AS TRIMP_Objective
    FROM clip_reserve
),

find_min_max AS (
    SELECT *,
        MIN(TRIMP_Objective) OVER () AS min_t,
        MAX(TRIMP_Objective) OVER () AS max_t
    FROM calc_base_trimp
),

scale_trimp AS (
    SELECT *,
        CASE WHEN max_t > min_t
             THEN (TRIMP_Objective - min_t) / (max_t - min_t) * 1000.0
             ELSE 0.0 END AS TRIMP_Objective_scaled
    FROM find_min_max
)

SELECT user_id AS User_ID, date AS Date, SUM(TRIMP_Objective_scaled) AS TRIMP_Objective_scaled_Daily
FROM scale_trimp
GROUP BY user_id, date
{{ config(materialized='table') }}

WITH user_ranges AS (
    SELECT
        User_ID,
        MIN(CAST(Date AS DATE)) AS min_date,
        MAX(CAST(Date AS DATE)) AS max_date
    FROM {{ ref('stg_daily_metrics') }}
    GROUP BY User_ID
)

SELECT
    User_ID,
    CAST(unnest(generate_series(min_date, max_date, INTERVAL 1 DAY)) AS DATE) AS calendar_date
FROM user_ranges
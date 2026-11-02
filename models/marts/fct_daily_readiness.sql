{{ config(
    materialized='table'
) }}

WITH business_logic AS (
    SELECT * 
    FROM {{ ref('int_business_logic') }}
),

daily_trimp AS (
    SELECT * 
    FROM {{ ref('int_trimp') }}
)

SELECT
    b.*,
    COALESCE(t.TRIMP_Objective_scaled_Daily, 0.0) AS TRIMP_Objective_scaled_Daily

FROM business_logic b
LEFT JOIN daily_trimp t
    ON b.User_ID = t.User_ID 
   AND b.Date = t.Date

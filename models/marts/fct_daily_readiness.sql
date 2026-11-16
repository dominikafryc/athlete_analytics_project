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
    COALESCE(t.trimp_objective_scaled, 0.0) AS trimp_objective_scaled

FROM business_logic b
LEFT JOIN daily_trimp t
    ON b.User_ID = t.User_ID 
   AND b.Date = t.Date

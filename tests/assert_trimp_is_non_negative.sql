-- Scaled daily TRIMP cannot be negative (min-max scaling starts at 0 and workouts sum up).
select
    User_ID,
    Date,
    TRIMP_Objective_scaled_Daily
from {{ ref('int_trimp') }}
where TRIMP_Objective_scaled_Daily < 0

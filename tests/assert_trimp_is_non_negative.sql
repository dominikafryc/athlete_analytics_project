-- Scaled daily TRIMP cannot be negative (min-max scaling starts at 0 and workouts sum up).
select
    User_ID,
    Date,
    trimp_objective_scaled
from {{ ref('int_trimp') }}
where trimp_objective_scaled < 0

-- The HRV baseline must be positive (it is a divisor) and, being an average,
-- must lie within the user's observed HRV range.
with user_range as (
    select User_ID, min(Daily_HRV) as min_hrv, max(Daily_HRV) as max_hrv
    from {{ ref('int_rolling_baselines') }}
    group by User_ID
)
select
    b.User_ID,
    b.Date,
    b.HRV_30day_Baseline
from {{ ref('int_rolling_baselines') }} b
join user_range r using (User_ID)
where b.HRV_30day_Baseline <= 0
   or b.HRV_30day_Baseline < r.min_hrv - 1e-9
   or b.HRV_30day_Baseline > r.max_hrv + 1e-9

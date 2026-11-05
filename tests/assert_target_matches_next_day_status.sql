-- Target_Readiness_Tomorrow must equal the next calendar day's Readiness_Status_Today.
-- On each user's last day both sides are NULL, which counts as a match.
with b as (
    select User_ID, Date, Readiness_Status_Today, Target_Readiness_Tomorrow
    from {{ ref('int_business_logic') }}
)
select
    t.User_ID,
    t.Date,
    t.Target_Readiness_Tomorrow,
    n.Readiness_Status_Today as next_day_status
from b t
left join b n
    on t.User_ID = n.User_ID
   and n.Date = t.Date + interval 1 day
where t.Target_Readiness_Tomorrow is distinct from n.Readiness_Status_Today

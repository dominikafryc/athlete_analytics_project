-- Fails if the final model has a different number of rows than the calendar spine
-- (a join fan-out or dropped days would change the count).
with calendar as (
    select count(*) as n from {{ ref('int_user_calendar') }}
),
final as (
    select count(*) as n from {{ ref('int_business_logic') }}
)
select
    calendar.n as calendar_rows,
    final.n as business_logic_rows
from calendar
cross join final
where calendar.n != final.n

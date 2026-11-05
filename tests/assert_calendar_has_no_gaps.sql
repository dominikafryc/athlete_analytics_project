-- Fails for any user whose calendar has missing days between first and last date.
select
    User_ID
from {{ ref('int_user_calendar') }}
group by User_ID
having count(*) != date_diff('day', min(calendar_date), max(calendar_date)) + 1

with source as (
    select * from {{ ref('menstrual_cycle') }}
),

renamed as (
    select
        cast("User_ID" as varchar) as user_id,
        cast("Date" as date) as date,
        cast("Cycle_Day" as integer) as cycle_day,
        cast("Cycle_Phase" as varchar) as cycle_phase,
        cast("Is_Period_Day" as integer) as is_period_day

    from source
)

select * from renamed

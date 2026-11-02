with source as (
    select * from {{ ref('workouts_log') }}
),

renamed as (
    select
        cast("User_ID" as varchar) as user_id,
        cast("Date" as date) as date,
        cast("Workout_Duration_min" as double) as workout_duration_min,
        cast("Avg_Heart_Rate" as double) as avg_heart_rate,
        cast("sRPE" as integer) as srpe
    from source
)

select * from renamed
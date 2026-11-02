with source as (
    select distinct * from {{ ref('daily_metrics') }}
),

renamed as (
    select
        cast("User_ID" as varchar) as user_id,
        cast("Date" as date) as date,
        cast("Daily_HRV" as double) as daily_hrv,
        cast("Daily_RHR" as double) as daily_rhr,
        cast("HR_Max" as double) as hr_max,
        cast("HR_Rest" as double) as hr_rest,
        cast("Sleep_Duration" as double) as sleep_duration,
        cast("Deep_Sleep_h" as double) as deep_sleep_h,
        cast("REM_Sleep_h" as double) as rem_sleep_h,
        cast("Sleep_Efficiency_pct" as double) as sleep_efficiency_pct,
        cast("Wake_Episodes_Count" as integer) as wake_episodes_count,
        cast("Grip_Strength_kg" as double) as grip_strength_kg,
        cast("CMJ_Jump_cm" as double) as cmj_jump_cm,
        cast("Subjective_Mood" as integer) as subjective_mood,
        cast("DOMS_Scale" as integer) as doms_scale,
        cast("Motivation_Level" as integer) as motivation_level,
        cast("sRPE" as integer) as srpe

    from source
)

select * from renamed
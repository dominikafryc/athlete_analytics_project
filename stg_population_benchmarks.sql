with source as (
    select * from {{ ref('population_benchmarks') }}
),

renamed as (
    select
        cast("Age_Group" as string) as age_group,
        cast("Sex" as string) as sex,
        cast("Avg_RHR" as double) as avg_rhr,
        cast("Avg_HRV" as double) as avg_hrv,
        cast("Avg_Sleep_h" as double) as avg_sleep_h

    from source
)

select * from renamed
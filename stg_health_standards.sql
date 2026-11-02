with source as (
    select * from {{ ref('health_standards') }}
),

renamed as (
    select
        cast("Metric_Name" as string) as metric_name,
        cast("Sex" as string) as sex,
        cast("Min_Optimal" as double) as min_optimal,
        cast("Max_Optimal" as double) as max_optimal,
        cast("Warning_Threshold" as double) as warning_threshold,
        cast("Unit" as string) as unit

    from source
)

select * from renamed
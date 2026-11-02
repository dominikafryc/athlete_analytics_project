with source as (
    select * from {{ ref('discipline_weather_config') }}
),

renamed as (
    select
        cast("Discipline" as string) as discipline,
        cast("Category" as string) as category,
        cast("Temp_Min" as double) as temp_min,
        cast("Temp_Max" as double) as temp_max,
        cast("Wind_Max" as double) as wind_max,
        cast("No_Storm" as boolean) as no_storm,
        cast("Max_Precip_mm" as double) as max_precip_mm,
        cast("Description" as string) as description
        
    from source
)

select * from renamed

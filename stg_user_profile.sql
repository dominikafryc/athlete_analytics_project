with source as (
    select * from {{ ref('user_profile') }}
),

renamed as (
    select
        cast("User_ID" as string) as user_id,
        cast("Name" as string) as name,
        cast("Age" as integer) as age,
        cast("Sex" as string) as sex,
        cast("Weight_kg" as double) as weight_kg,
        cast("Main_Discipline" as string) as main_discipline,
        cast("Experience_Main_Sport_Yrs" as double) as experience_main_sport_yrs,
        cast("Second_Discipline" as string) as second_discipline,
        cast("Experience_Second_Sport_Yrs" as double) as experience_second_sport_yrs,
        cast("Third_Discipline" as string) as third_discipline,
        cast("Experience_Third_Sport_Yrs" as double) as experience_third_sport_yrs,
        cast("Disciplines_Count" as integer) as disciplines_count,
        cast("Chronic_Disease_Flag" as integer) as chronic_disease_flag,
        cast("Is_Injured_Flag" as integer) as is_injured_flag

    from source
)

select * from renamed
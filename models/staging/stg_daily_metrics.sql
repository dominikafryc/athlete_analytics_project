with source as (
    select * from {{ ref('blood_biomarkers')}}
),

renamed as (
    select
        cast("User_ID" as string) as user_id,
        cast("Test_date" as date) as metric_date,
        cast("Cortisol_Morning" as double) as cortisol_morning,
        cast("Testosterone_ng_dL" as double) as testosterone_ng_dl,
        cast("Creatine_Kinase_CK" as double) as creatine_kinase_ck,
        cast("CRP_mg_L" as double) as crp_mg_l,
        cast("Ferritin_ng_mL" as double) as ferritin_ng_ml,
        cast("Vitamin_D3_ng_mL" as double) as vitamin_d3_ng_ml,
        cast("TSH_uIU_mL" as double) as tsh_uiu_ml,
        cast("Glucose_Fasting_mg_dL" as double) as glucose_fasting_mg_dl

    from source
)

select * from renamed

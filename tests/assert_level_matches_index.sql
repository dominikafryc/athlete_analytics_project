-- Level (text) and Index (number) columns are computed by separate CASE blocks.
-- Fails when they disagree, which would happen if thresholds are edited in one place only.
select
    User_ID,
    Date,
    Insomnia_Risk_Level,
    Insomnia_Index,
    CNS_Fatigue_Level,
    CNS_Fatigue_Index
from {{ ref('int_business_logic') }}
where Insomnia_Index is distinct from case Insomnia_Risk_Level
        when 'HIGH_RISK' then 2
        when 'MODERATE_RISK' then 1
        when 'LOW_RISK' then 0
      end
   or CNS_Fatigue_Index is distinct from case CNS_Fatigue_Level
        when 'Severe' then 2
        when 'Moderate' then 1
        when 'Normal' then 0
      end

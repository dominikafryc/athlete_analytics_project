import unittest
import pandas as pd
from logic import is_weather_safe, get_adapted_discipline, get_cns_fatigue_level, check_discipline_swap


class TestLogicSystem(unittest.TestCase):

    def test_weather_optimal_is_safe(self):
        self.assertTrue(is_weather_safe(1))

    def test_weather_not_optimal_is_unsafe(self):
        self.assertFalse(is_weather_safe(0))

    def test_adapted_discipline_returns_none_when_below_threshold(self):
        row = pd.Series({'Second_Discipline': 'box', 'Experience_Second_Sport_Yrs': 1,
                          'Third_Discipline': 'roller blades', 'Experience_Third_Sport_Yrs': 0.5})
        self.assertIsNone(get_adapted_discipline(row, min_experience_years=2.0))

    def test_adapted_discipline_picks_second_when_only_second_qualifies(self):
        row = pd.Series({'Second_Discipline': 'cycling', 'Experience_Second_Sport_Yrs': 6,
                          'Third_Discipline': 'swimming', 'Experience_Third_Sport_Yrs': 1})
        self.assertEqual(get_adapted_discipline(row, min_experience_years=2.0), 'cycling')

    def test_adapted_discipline_picks_longer_tenure_when_both_qualify(self):
        row = pd.Series({'Second_Discipline': 'running', 'Experience_Second_Sport_Yrs': 3,
                          'Third_Discipline': 'swimming', 'Experience_Third_Sport_Yrs': 5})
        self.assertEqual(get_adapted_discipline(row, min_experience_years=2.0), 'swimming')

    def test_cns_cmj_severe_and_moderate(self):
        self.assertEqual(get_cns_fatigue_level(pd.Series({'CMJ_Drop_%': -0.20})), 'Severe')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'CMJ_Drop_%': -0.10})), 'Moderate')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'CMJ_Drop_%': -0.02})), 'Normal')

    def test_cns_grip_severe_and_moderate(self):
        self.assertEqual(get_cns_fatigue_level(pd.Series({'Grip_Drop_%': -0.12})), 'Severe')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'Grip_Drop_%': -0.07})), 'Moderate')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'Grip_Drop_%': -0.02})), 'Normal')

    def test_cns_fallback_hrv_and_doms(self):
        self.assertEqual(get_cns_fatigue_level(pd.Series({'HRV_ZScore_CyclAware': -2.5, 'DOMS_Scale': 3})), 'Severe')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'HRV_ZScore_CyclAware': 0, 'DOMS_Scale': 9})), 'Severe')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'HRV_ZScore_CyclAware': -1.5, 'DOMS_Scale': 2})), 'Moderate')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'HRV_ZScore_CyclAware': 0, 'DOMS_Scale': 6})), 'Moderate')
        self.assertEqual(get_cns_fatigue_level(pd.Series({'HRV_ZScore_CyclAware': -0.5, 'DOMS_Scale': 2})), 'Normal')

    def test_swap_weather_and_injury_priorities(self):
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 0, 'Is_Injured_Flag': 1})), 'Weather_Unsafe_Swap_Indoor')
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 1, 'Is_Injured_Flag': 1})), 'Rest_Required_Injury')

    def test_swap_rest_required_triggers(self):
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 1, 'Anomaly_Flag': 1})), 'Rest_Required')
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 1, 'Insomnia_Index': 2})), 'Rest_Required')
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 1, 'CNS_Fatigue_Level': 'Severe'})), 'Rest_Required')

    def test_swap_adaptation_scenarios(self):
        row_swap = pd.Series({'Is_Weather_Optimal': 1, 'CNS_Fatigue_Level': 'Moderate', 'Second_Discipline': 'running', 'Experience_Second_Sport_Yrs': 4})
        self.assertEqual(check_discipline_swap(row_swap), 'Swap to: running')

        row_low_adapt = pd.Series({'Is_Weather_Optimal': 1, 'Mental_Fatigue_Flag': 1, 'Second_Discipline': 'swimming', 'Experience_Second_Sport_Yrs': 1})
        self.assertEqual(check_discipline_swap(row_low_adapt), 'Rest_Required_Low_Adaptation')

    def test_swap_normal_as_scheduled(self):
        self.assertEqual(check_discipline_swap(pd.Series({'Is_Weather_Optimal': 1, 'Is_Injured_Flag': 0, 'CNS_Fatigue_Level': 'Normal'})), 'As_Scheduled')

if __name__ == '__main__':
    unittest.main()

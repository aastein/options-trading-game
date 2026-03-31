from __future__ import annotations

import unittest
from datetime import datetime

from utils.types import HMMParams, DistributionParams, IVParams, TickerConfig
from market.regime_generator import RegimeGenerator


class TestRegimeGenerator(unittest.TestCase):
    
    def setUp(self):
        hmm_params = HMMParams(
            n_states=4,
            transition_matrix=[
                [0.7, 0.1, 0.1, 0.1],
                [0.1, 0.7, 0.1, 0.1],
                [0.1, 0.1, 0.7, 0.1],
                [0.1, 0.1, 0.1, 0.7]
            ],
            means=[0.0005, -0.002, 0.001, -0.005],
            stds=[0.01, 0.015, 0.02, 0.04],
            start_probs=[0.25, 0.25, 0.25, 0.25]
        )
        
        dist_params = DistributionParams(
            atr_mean=2.0,
            atr_std=1.0,
            h_o_quantiles={"q0": (0.5, 0.2), "q1": (0.5, 0.2), "q2": (0.5, 0.2), "q3": (0.5, 0.2), "q4": (0.5, 0.2)},
            o_l_quantiles={"q0": (0.5, 0.2), "q1": (0.5, 0.2), "q2": (0.5, 0.2), "q3": (0.5, 0.2), "q4": (0.5, 0.2)},
            touch_time_hist=[0.1] * 10,
            realized_vol_mean=0.15,
            realized_vol_std=0.05
        )
        
        iv_params = IVParams(
            atm_iv_base=0.18,
            risk_premium=1.15,
            term_structure={"0-7": 1.15, "8-14": 1.08, "15-32": 1.0, "60": 0.95},
            skew_coef=-1.5
        )
        
        self.config = TickerConfig(
            ticker="SPY",
            hmm_params=hmm_params,
            distribution_params=dist_params,
            iv_params=iv_params,
            strike_increment=1.0
        )
    
    def test_generate_regime_sequence(self):
        generator = RegimeGenerator(self.config, seed=42)
        sequence = generator.generate_regime_sequence(252)
        
        self.assertEqual(len(sequence), 252)
        
        for state in sequence:
            self.assertIn(state, [0, 1, 2, 3])
    
    def test_generate_daily_ohlc(self):
        generator = RegimeGenerator(self.config, seed=42)
        sequence = generator.generate_regime_sequence(252)
        
        start_date = datetime(2024, 1, 2)
        ohlc_bars = generator.generate_daily_ohlc(sequence, start_date, 450.0)
        
        self.assertEqual(len(ohlc_bars), 252)
        
        for bar in ohlc_bars:
            self.assertIsNotNone(bar.timestamp)
            self.assertGreater(bar.open, 0)
            self.assertGreater(bar.high, 0)
            self.assertGreater(bar.low, 0)
            self.assertGreater(bar.close, 0)
            
            self.assertGreaterEqual(bar.high, bar.open)
            self.assertGreaterEqual(bar.high, bar.close)
            self.assertLessEqual(bar.low, bar.open)
            self.assertLessEqual(bar.low, bar.close)


if __name__ == '__main__':
    unittest.main()

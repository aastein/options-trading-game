from __future__ import annotations

import unittest
from datetime import datetime

import numpy as np

from utils.types import OHLCBar, HMMParams, DistributionParams, IVParams, TickerConfig
from market.tick_generator import TickGenerator


class TestTickGenerator(unittest.TestCase):
    
    def setUp(self):
        hmm_params = HMMParams(
            n_states=4,
            transition_matrix=[[0.25] * 4] * 4,
            means=[0.0] * 4,
            stds=[0.01] * 4,
            start_probs=[0.25] * 4
        )
        
        dist_params = DistributionParams(
            atr_mean=2.0,
            atr_std=1.0,
            h_o_quantiles={"q0": (0.5, 0.2), "q1": (0.5, 0.2), "q2": (0.5, 0.2), "q3": (0.5, 0.2), "q4": (0.5, 0.2)},
            o_l_quantiles={"q0": (0.5, 0.2), "q1": (0.5, 0.2), "q2": (0.5, 0.2), "q3": (0.5, 0.2), "q4": (0.5, 0.2)},
            touch_time_hist=[1.0/13] * 13,
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
    
    def test_generate_day_ticks(self):
        generator = TickGenerator(self.config)
        
        ohlc = OHLCBar(
            timestamp=datetime(2024, 1, 2, 9, 30),
            open=450.0,
            high=455.0,
            low=448.0,
            close=452.0
        )
        
        ticks = generator.generate_day_ticks(ohlc, seed=42)
        
        self.assertEqual(len(ticks), 4560)
        
        self.assertAlmostEqual(ticks[0], 450.0, delta=0.01)
        self.assertAlmostEqual(ticks[-1], 452.0, delta=0.01)
        
        max_tick = np.max(ticks)
        min_tick = np.min(ticks)
        
        self.assertLessEqual(max_tick, 455.0)
        self.assertGreaterEqual(min_tick, 448.0)


if __name__ == '__main__':
    unittest.main()

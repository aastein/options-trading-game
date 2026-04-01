from __future__ import annotations

import unittest
from datetime import datetime
import time

from utils.types import HMMParams, DistributionParams, IVParams, TickerConfig
from market.regime_generator import RegimeGenerator
from market.tick_generator import TickGenerator
from options.chain_generator import OptionChainGenerator
from portfolio.portfolio_manager import PortfolioManager


class TestIntegration(unittest.TestCase):
    
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
    
    def test_full_pipeline(self):
        regime_gen = RegimeGenerator(self.config, seed=42)
        tick_gen = TickGenerator(self.config)
        chain_gen = OptionChainGenerator(self.config)
        portfolio = PortfolioManager(100000.0)
        
        sequence = regime_gen.generate_regime_sequence(10)
        ohlc_bars = regime_gen.generate_daily_ohlc(sequence, datetime(2024, 1, 2), 450.0)
        
        self.assertEqual(len(ohlc_bars), 10)
        
        ohlc_bar = ohlc_bars[0]
        ticks = tick_gen.generate_day_ticks(ohlc_bar, seed=42)
        
        self.assertEqual(len(ticks), TickGenerator.TICKS_PER_DAY)
        
        current_time = datetime(2024, 1, 2, 10, 0)
        spot_price = float(ticks[100])
        
        chain = chain_gen.generate_chain(spot_price, current_time)
        
        self.assertGreater(len(chain), 0)
        
        call_options = [q for q in chain if q.option_type == "call"]
        if call_options:
            quote = call_options[0]
            
            success = portfolio.execute_order(
                ticker=quote.ticker,
                expiration=quote.expiration,
                strike=quote.strike,
                option_type=quote.option_type,
                side="buy",
                quantity=1,
                price=quote.mid,
                timestamp=current_time
            )
            
            self.assertTrue(success)
            self.assertEqual(len(portfolio.open_positions), 1)
    
    def test_day_generation_performance(self):
        regime_gen = RegimeGenerator(self.config, seed=42)
        tick_gen = TickGenerator(self.config)
        
        sequence = regime_gen.generate_regime_sequence(1)
        ohlc_bars = regime_gen.generate_daily_ohlc(sequence, datetime(2024, 1, 2), 450.0)
        
        start_time = time.time()
        ticks = tick_gen.generate_day_ticks(ohlc_bars[0], seed=42)
        elapsed = time.time() - start_time
        
        self.assertLess(elapsed, 0.5)
    
    def test_chain_generation_performance(self):
        chain_gen = OptionChainGenerator(self.config)
        
        current_time = datetime(2024, 1, 2, 10, 0)
        spot_price = 450.0
        
        start_time = time.time()
        chain = chain_gen.generate_chain(spot_price, current_time)
        elapsed = time.time() - start_time
        
        self.assertLess(elapsed, 0.1)


if __name__ == '__main__':
    unittest.main()

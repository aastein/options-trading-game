from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

import numpy as np

from utils.types import HMMParams, OHLCBar, TickerConfig
from market.calendar import TradingCalendar

logger = logging.getLogger(__name__)


class RegimeGenerator:
    
    def __init__(
        self, 
        ticker_config: TickerConfig, 
        seed: int, 
        jitter_pct: float = 0.10
    ):
        self.ticker_config = ticker_config
        self.hmm_params = ticker_config.hmm_params
        self.jitter_pct = jitter_pct
        
        self.rng = np.random.RandomState(seed)
        
        self._apply_jitter()
    
    def _apply_jitter(self) -> None:
        n_states = self.hmm_params.n_states
        
        jittered_trans = []
        for i in range(n_states):
            row = []
            for j in range(n_states):
                orig_prob = self.hmm_params.transition_matrix[i][j]
                jitter = self.rng.uniform(-self.jitter_pct, self.jitter_pct)
                new_prob = max(0.01, min(0.99, orig_prob * (1.0 + jitter)))
                row.append(new_prob)
            
            row_sum = sum(row)
            row = [p / row_sum for p in row]
            jittered_trans.append(row)
        
        self.transition_matrix = np.array(jittered_trans)
        
        self.means = []
        for mean in self.hmm_params.means:
            jitter = self.rng.uniform(-self.jitter_pct, self.jitter_pct)
            jittered_mean = mean * (1.0 + jitter)
            self.means.append(jittered_mean)
        
        self.stds = []
        for std in self.hmm_params.stds:
            jitter = self.rng.uniform(-self.jitter_pct, self.jitter_pct)
            jittered_std = std * (1.0 + jitter)
            self.stds.append(jittered_std)
        
        logger.debug(f"Applied ±{self.jitter_pct*100}% jitter to HMM parameters")
    
    def generate_regime_sequence(self, n_days: int) -> List[int]:
        start_probs = np.array(self.hmm_params.start_probs)
        current_state = self.rng.choice(len(start_probs), p=start_probs)
        
        regime_sequence = [current_state]
        
        for _ in range(n_days - 1):
            trans_probs = self.transition_matrix[current_state]
            next_state = self.rng.choice(len(trans_probs), p=trans_probs)
            regime_sequence.append(next_state)
            current_state = next_state
        
        logger.info(f"Generated regime sequence for {n_days} days")
        return regime_sequence
    
    def generate_daily_ohlc(
        self, 
        regime_sequence: List[int], 
        start_date: datetime,
        initial_price: float = 450.0
    ) -> List[OHLCBar]:
        trading_days = TradingCalendar.generate_trading_days(start_date, len(regime_sequence))
        
        ohlc_bars = []
        current_price = initial_price
        
        for day_idx, (regime, date) in enumerate(zip(regime_sequence, trading_days)):
            mean = self.means[regime]
            std = self.stds[regime]
            
            daily_return = self.rng.normal(mean, std)

            # Split return into overnight gap and intraday move.
            # Gap std scales with regime volatility (~30% of daily vol).
            gap_std = std * 0.3
            overnight_gap = self.rng.normal(0, gap_std)
            intraday_return = daily_return - overnight_gap

            open_price = current_price * np.exp(overnight_gap)
            close_price = open_price * np.exp(intraday_return)
            
            intraday_range = abs(self.rng.normal(0, std * 0.5))
            
            high_price = max(open_price, close_price) * (1.0 + intraday_range)
            low_price = min(open_price, close_price) * (1.0 - intraday_range)
            
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            bar = OHLCBar(
                timestamp=TradingCalendar.get_market_open(date),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price
            )
            
            ohlc_bars.append(bar)
            current_price = close_price
        
        logger.info(f"Generated {len(ohlc_bars)} daily OHLC bars")
        return ohlc_bars

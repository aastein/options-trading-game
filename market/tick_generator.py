from __future__ import annotations

import logging
from datetime import datetime, timedelta

import numpy as np

from utils.types import OHLCBar, TickerConfig
from market.fbm_bridge import FractionalBrownianBridge

logger = logging.getLogger(__name__)


class TickGenerator:
    
    TICKS_PER_DAY = 4681
    
    def __init__(self, ticker_config: TickerConfig):
        self.ticker_config = ticker_config
        self.dist_params = ticker_config.distribution_params
        self.fbm_bridge = FractionalBrownianBridge(hurst=0.45)
    
    def sample_touch_times(self, seed: int | None = None) -> tuple[float, float]:
        rng = np.random.RandomState(seed)
        
        touch_hist = np.array(self.dist_params.touch_time_hist)
        touch_hist = touch_hist / touch_hist.sum()
        
        bin_edges = np.linspace(0, 1, len(touch_hist) + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        high_time = rng.choice(bin_centers, p=touch_hist)
        low_time = rng.choice(bin_centers, p=touch_hist)
        
        if abs(high_time - low_time) < 0.05:
            if high_time < 0.5:
                low_time = min(high_time + 0.1, 0.95)
            else:
                low_time = max(high_time - 0.1, 0.05)
        
        return float(high_time), float(low_time)
    
    def generate_day_ticks(
        self, 
        ohlc_bar: OHLCBar, 
        seed: int | None = None
    ) -> np.ndarray:
        open_price = ohlc_bar.open
        high_price = ohlc_bar.high
        low_price = ohlc_bar.low
        close_price = ohlc_bar.close
        
        high_touch_time, low_touch_time = self.sample_touch_times(seed)
        
        path = self.fbm_bridge.generate_constrained_path(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            n_ticks=self.TICKS_PER_DAY,
            high_touch_time=high_touch_time,
            low_touch_time=low_touch_time,
            seed=seed
        )
        
        return path
    
    def get_tick_timestamp(self, ohlc_bar: OHLCBar, tick_index: int) -> datetime:
        market_open = ohlc_bar.timestamp
        seconds_elapsed = tick_index * 5
        return market_open + timedelta(seconds=seconds_elapsed)

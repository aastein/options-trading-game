from __future__ import annotations

import json
import logging
from pathlib import Path

from utils.types import (
    TickerConfig,
    HMMParams,
    DistributionParams,
    IVParams
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
    
    def load_ticker_config(self, ticker: str) -> TickerConfig:
        config_path = self.config_dir / f"{ticker}_config.json"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Run calibration first: python -m calibration.calibration_runner --tickers {ticker}"
            )
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        hmm_params = HMMParams(
            n_states=data['hmm_params']['n_states'],
            transition_matrix=data['hmm_params']['transition_matrix'],
            means=data['hmm_params']['means'],
            stds=data['hmm_params']['stds'],
            start_probs=data['hmm_params']['start_probs']
        )
        
        dist_params = DistributionParams(
            atr_mean=data['distribution_params']['atr_mean'],
            atr_std=data['distribution_params']['atr_std'],
            h_o_quantiles=data['distribution_params']['h_o_quantiles'],
            o_l_quantiles=data['distribution_params']['o_l_quantiles'],
            touch_time_hist=data['distribution_params']['touch_time_hist'],
            realized_vol_mean=data['distribution_params']['realized_vol_mean'],
            realized_vol_std=data['distribution_params']['realized_vol_std']
        )
        
        iv_params = IVParams(
            atm_iv_base=data['iv_params']['atm_iv_base'],
            risk_premium=data['iv_params']['risk_premium'],
            term_structure=data['iv_params']['term_structure'],
            skew_coef=data['iv_params']['skew_coef']
        )
        
        config = TickerConfig(
            ticker=data['ticker'],
            hmm_params=hmm_params,
            distribution_params=dist_params,
            iv_params=iv_params,
            strike_increment=data['strike_increment']
        )
        
        logger.info(f"Loaded configuration for {ticker}")
        return config
    
    def check_config_exists(self, ticker: str) -> bool:
        config_path = self.config_dir / f"{ticker}_config.json"
        return config_path.exists()

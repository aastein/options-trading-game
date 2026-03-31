from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from calibration.hmm_calibrator import HMMCalibrator
from calibration.distribution_calibrator import DistributionCalibrator
from calibration.iv_calibrator import IVCalibrator
from utils.types import TickerConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CalibrationRunner:
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.hmm_calibrator = HMMCalibrator(n_states=4)
        self.dist_calibrator = DistributionCalibrator()
        self.iv_calibrator = IVCalibrator()
    
    def get_strike_increment(self, ticker: str) -> float:
        if ticker in ["SPY", "QQQ", "IWM"]:
            return 1.0
        else:
            return 5.0
    
    def calibrate_ticker(self, ticker: str) -> TickerConfig:
        logger.info(f"=" * 60)
        logger.info(f"Calibrating {ticker}")
        logger.info(f"=" * 60)
        
        logger.info("Step 1/3: HMM calibration")
        hmm_params = self.hmm_calibrator.calibrate(ticker)
        
        logger.info("Step 2/3: Distribution calibration")
        dist_params = self.dist_calibrator.calibrate(ticker)
        
        logger.info("Step 3/3: IV surface calibration")
        iv_params = self.iv_calibrator.calibrate(ticker, dist_params)
        
        strike_increment = self.get_strike_increment(ticker)
        
        config = TickerConfig(
            ticker=ticker,
            hmm_params=hmm_params,
            distribution_params=dist_params,
            iv_params=iv_params,
            strike_increment=strike_increment
        )
        
        return config
    
    def save_config(self, config: TickerConfig) -> None:
        config_path = self.config_dir / f"{config.ticker}_config.json"
        
        config_dict = {
            "ticker": config.ticker,
            "hmm_params": {
                "n_states": config.hmm_params.n_states,
                "transition_matrix": config.hmm_params.transition_matrix,
                "means": config.hmm_params.means,
                "stds": config.hmm_params.stds,
                "start_probs": config.hmm_params.start_probs
            },
            "distribution_params": {
                "atr_mean": config.distribution_params.atr_mean,
                "atr_std": config.distribution_params.atr_std,
                "h_o_quantiles": config.distribution_params.h_o_quantiles,
                "o_l_quantiles": config.distribution_params.o_l_quantiles,
                "touch_time_hist": config.distribution_params.touch_time_hist,
                "realized_vol_mean": config.distribution_params.realized_vol_mean,
                "realized_vol_std": config.distribution_params.realized_vol_std
            },
            "iv_params": {
                "atm_iv_base": config.iv_params.atm_iv_base,
                "risk_premium": config.iv_params.risk_premium,
                "term_structure": config.iv_params.term_structure,
                "skew_coef": config.iv_params.skew_coef
            },
            "strike_increment": config.strike_increment
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
    
    def run(self, tickers: list[str]) -> None:
        logger.info(f"Starting calibration for {len(tickers)} tickers")
        
        for ticker in tickers:
            try:
                config = self.calibrate_ticker(ticker)
                self.save_config(config)
                logger.info(f"✓ {ticker} calibration complete\n")
            except Exception as e:
                logger.error(f"✗ Failed to calibrate {ticker}: {e}\n")
                raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate tickers for option trading game")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["SPY", "QQQ", "IWM"],
        help="Tickers to calibrate"
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Directory to save calibration configs"
    )
    
    args = parser.parse_args()
    
    runner = CalibrationRunner(config_dir=args.config_dir)
    runner.run(args.tickers)
    
    logger.info("All calibrations complete!")


if __name__ == "__main__":
    main()

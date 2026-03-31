from __future__ import annotations

import logging

from utils.types import IVParams, DistributionParams

logger = logging.getLogger(__name__)


class IVCalibrator:

    def __init__(self, risk_premium: float = 1.15):
        self.risk_premium = risk_premium

    def get_skew_coefficient(self, ticker: str) -> float:
        etf_tickers = {"SPY", "QQQ", "IWM", "DIA", "EEM", "XLE", "XLF"}

        if ticker.upper() in etf_tickers:
            return 1.5
        else:
            return 2.0

    def calibrate(self, ticker: str, dist_params: DistributionParams) -> IVParams:
        atm_iv_base = dist_params.realized_vol_mean * self.risk_premium

        logger.info(
            f"ATM IV base: {atm_iv_base:.4f} "
            f"(realized vol: {dist_params.realized_vol_mean:.4f}, "
            f"risk premium: {self.risk_premium})"
        )

        term_structure = {
            "0-7": 1.15,
            "8-14": 1.08,
            "15-32": 1.0,
            "60": 0.95
        }

        skew_coef = self.get_skew_coefficient(ticker)
        logger.info(f"Skew coefficient: {skew_coef}")

        return IVParams(
            atm_iv_base=atm_iv_base,
            risk_premium=self.risk_premium,
            term_structure=term_structure,
            skew_coef=skew_coef
        )

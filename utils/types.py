from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class OHLCBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class OptionQuote:
    ticker: str
    strike: float
    expiration: datetime
    option_type: Literal["call", "put"]
    bid: float
    ask: float
    mid: float
    iv: float
    greeks: Greeks


@dataclass
class Position:
    ticker: str
    expiration: datetime
    strike: float
    option_type: Literal["call", "put"]
    quantity: int
    entry_price: float
    entry_timestamp: datetime
    current_price: float = 0.0

    def mark_to_market(self, current_price: float) -> None:
        self.current_price = current_price

    def get_pnl(self) -> float:
        return float(self.quantity * (self.current_price - self.entry_price) * 100)


@dataclass
class StockPosition:
    ticker: str
    quantity: int
    entry_price: float
    entry_timestamp: datetime
    current_price: float = 0.0

    def mark_to_market(self, current_price: float) -> None:
        self.current_price = current_price

    def get_pnl(self) -> float:
        return float(self.quantity * (self.current_price - self.entry_price))


@dataclass
class HMMParams:
    n_states: int
    transition_matrix: list[list[float]]
    means: list[float]
    stds: list[float]
    start_probs: list[float]


@dataclass
class DistributionParams:
    atr_mean: float
    atr_std: float
    h_o_quantiles: dict[str, tuple[float, float]]
    o_l_quantiles: dict[str, tuple[float, float]]
    touch_time_hist: list[float]
    realized_vol_mean: float
    realized_vol_std: float


@dataclass
class IVParams:
    atm_iv_base: float
    risk_premium: float
    term_structure: dict[str, float]
    skew_coef: float


@dataclass
class TickerConfig:
    ticker: str
    hmm_params: HMMParams
    distribution_params: DistributionParams
    iv_params: IVParams
    strike_increment: float

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from utils.types import DistributionParams

logger = logging.getLogger(__name__)


class DistributionCalibrator:

    def __init__(self, atr_period: int = 14, realized_vol_period: int = 21):
        self.atr_period = atr_period
        self.realized_vol_period = realized_vol_period

    def download_data(self, ticker: str) -> pd.DataFrame:
        logger.info(f"Downloading historical data for {ticker}")
        data = yf.download(ticker, period="max", progress=False, auto_adjust=True)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data

    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        high = data['High']
        low = data['Low']
        close = data['Close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()

        return atr

    def calculate_daily_return(self, data: pd.DataFrame) -> pd.Series:
        close = data['Close']
        returns = (close - close.shift(1)) / close.shift(1)
        return returns

    def calculate_h_o_ratio(self, data: pd.DataFrame, atr: pd.Series) -> pd.Series:
        high = data['High']
        open_price = data['Open']

        h_o = (high - open_price) / atr
        return h_o

    def calculate_o_l_ratio(self, data: pd.DataFrame, atr: pd.Series) -> pd.Series:
        low = data['Low']
        open_price = data['Open']

        o_l = (open_price - low) / atr
        return o_l

    def bin_by_return_quantile(
        self,
        returns: pd.Series,
        values: pd.Series,
        n_bins: int = 5
    ) -> dict[str, Tuple[float, float]]:
        valid_mask = ~(returns.isna() | values.isna())
        valid_returns = returns[valid_mask]
        valid_values = values[valid_mask]

        quantiles = {}
        quantile_edges = np.linspace(0, 1, n_bins + 1)

        for i in range(n_bins):
            lower_q = quantile_edges[i]
            upper_q = quantile_edges[i + 1]

            lower_threshold = valid_returns.quantile(lower_q)
            upper_threshold = valid_returns.quantile(upper_q)

            mask = (valid_returns >= lower_threshold) & (valid_returns <= upper_threshold)
            bin_values = valid_values[mask]

            if len(bin_values) > 0:
                mean = float(bin_values.mean())
                std = float(bin_values.std())
            else:
                mean = 0.0
                std = 0.0

            quantiles[f"q{i}"] = (mean, std)

        return quantiles

    def calculate_touch_time_distribution(
        self,
        data: pd.DataFrame
    ) -> list[float]:
        n_bins = 13
        touch_times = []

        for idx in range(1, len(data)):
            row = data.iloc[idx]

            if pd.notna(row['High']) and pd.notna(row['Low']) and pd.notna(row['Open']) and pd.notna(row['Close']):
                open_p = float(row['Open'])
                close_p = float(row['Close'])
                high_p = float(row['High'])
                low_p = float(row['Low'])

                price_range = high_p - low_p
                if price_range < 1e-10:
                    continue

                if close_p >= open_p:
                    high_time = (high_p - open_p) / price_range
                    low_time = (open_p - low_p) / price_range
                    high_time = min(max(high_time, 0.0), 1.0)
                    low_time = min(max(low_time, 0.0), 1.0)
                    if low_time > high_time:
                        low_time, high_time = high_time, low_time
                else:
                    high_time = (high_p - close_p) / price_range
                    low_time = (close_p - low_p) / price_range
                    high_time = min(max(high_time, 0.0), 1.0)
                    low_time = min(max(low_time, 0.0), 1.0)
                    if high_time > low_time:
                        high_time, low_time = low_time, high_time

                touch_times.append(high_time)
                touch_times.append(low_time)

        if not touch_times:
            return [1.0 / n_bins] * n_bins

        hist, _ = np.histogram(touch_times, bins=n_bins, range=(0, 1))
        hist_normalized = (hist / hist.sum()).tolist()

        return hist_normalized

    def calculate_realized_volatility(self, data: pd.DataFrame) -> Tuple[float, float]:
        close = data['Close']
        returns = np.log(close / close.shift(1))

        realized_vol = returns.rolling(window=self.realized_vol_period).std() * np.sqrt(252)

        rv_mean = float(realized_vol.mean())
        rv_std = float(realized_vol.std())

        return rv_mean, rv_std

    def calibrate(self, ticker: str) -> DistributionParams:
        data = self.download_data(ticker)

        atr = self.calculate_atr(data)
        returns = self.calculate_daily_return(data)

        atr_mean = float(atr.mean())
        atr_std = float(atr.std())

        logger.info(f"ATR statistics: mean={atr_mean:.4f}, std={atr_std:.4f}")

        h_o_ratio = self.calculate_h_o_ratio(data, atr)
        o_l_ratio = self.calculate_o_l_ratio(data, atr)

        h_o_quantiles = self.bin_by_return_quantile(returns, h_o_ratio)
        o_l_quantiles = self.bin_by_return_quantile(returns, o_l_ratio)

        logger.info("H-O quantile distributions calculated")
        logger.info("O-L quantile distributions calculated")

        touch_time_hist = self.calculate_touch_time_distribution(data)
        logger.info("Touch time distribution calculated")

        rv_mean, rv_std = self.calculate_realized_volatility(data)
        logger.info(f"Realized volatility: mean={rv_mean:.4f}, std={rv_std:.4f}")

        return DistributionParams(
            atr_mean=atr_mean,
            atr_std=atr_std,
            h_o_quantiles=h_o_quantiles,
            o_l_quantiles=o_l_quantiles,
            touch_time_hist=touch_time_hist,
            realized_vol_mean=rv_mean,
            realized_vol_std=rv_std
        )

from __future__ import annotations

from datetime import datetime
from typing import List

import numpy as np

from utils.types import OptionQuote, TickerConfig, Greeks
from options.bs_pricer import BlackScholesPricer
from options.iv_surface import IVSurface
from options.greeks import GreeksCalculator
from market.calendar import TradingCalendar


class OptionChainGenerator:
    """Generates full option chains using vectorized Black-Scholes."""

    def __init__(self, ticker_config: TickerConfig):
        self.ticker_config = ticker_config
        self.ticker = ticker_config.ticker

        self.bs_pricer = BlackScholesPricer()
        self.iv_surface = IVSurface(ticker_config.iv_params)
        self.greeks_calc = GreeksCalculator(self.bs_pricer, self.iv_surface)

        self.strike_increment = ticker_config.strike_increment

    def get_strikes(self, spot: float) -> List[float]:
        """Return sorted unique strikes within 80%-120% of spot."""
        lower = max(1.0, spot * 0.80)
        upper = spot * 1.20

        strikes = []
        strike = lower
        while strike <= upper:
            strikes.append(round(strike))
            strike += self.strike_increment

        return sorted(list(set(float(s) for s in strikes if s > 0)))

    def get_active_expirations(self, current_time: datetime) -> List[datetime]:
        """Return active expirations for the given date."""
        expirations = TradingCalendar.get_expirations_for_date(current_time)
        return expirations

    def calculate_bid_ask_spread(self, mid_price: float, strike: float, spot: float) -> tuple[float, float]:
        """Calculate bid/ask from mid price based on moneyness."""
        moneyness = abs(strike / spot - 1.0)

        if moneyness < 0.02:
            spread_pct = 0.025
        else:
            spread_pct = 0.075

        spread = mid_price * spread_pct

        bid = max(0.01, mid_price - spread / 2.0)
        ask = mid_price + spread / 2.0

        return float(bid), float(ask)

    def generate_option_quote(
        self,
        strike: float,
        expiration: datetime,
        spot: float,
        current_time: datetime,
        option_type: str
    ) -> OptionQuote:
        """Generate a single option quote (scalar path, used by other callers)."""
        iv = self.iv_surface.calculate_iv(strike, spot, expiration, current_time)

        time_to_expiry = self.greeks_calc.calculate_time_to_expiry(expiration, current_time)

        mid_price = self.bs_pricer.price(spot, strike, time_to_expiry, iv, option_type)

        bid, ask = self.calculate_bid_ask_spread(mid_price, strike, spot)

        greeks = self.greeks_calc.calculate_greeks(
            spot, strike, expiration, current_time, option_type
        )

        return OptionQuote(
            ticker=self.ticker,
            strike=strike,
            expiration=expiration,
            option_type=option_type,
            bid=bid,
            ask=ask,
            mid=mid_price,
            iv=iv,
            greeks=greeks
        )

    def generate_chain(
        self,
        spot: float,
        current_time: datetime
    ) -> List[OptionQuote]:
        """Generate full option chain using vectorized Black-Scholes."""
        strikes_list = self.get_strikes(spot)
        expirations = self.get_active_expirations(current_time)

        if not strikes_list or not expirations:
            return []

        n_strikes = len(strikes_list)
        n_exps = len(expirations)
        n_per_exp = n_strikes * 2
        n_total = n_exps * n_per_exp

        all_strikes = np.empty(n_total)
        all_tte = np.empty(n_total)
        all_ivs = np.empty(n_total)
        all_is_call = np.empty(n_total, dtype=bool)
        all_expirations: List[datetime] = []

        idx = 0
        for expiration in expirations:
            time_diff = expiration - current_time
            tte = max(0.0, time_diff.total_seconds() / (24 * 3600 * 365.0))
            dte = (expiration - current_time).days

            term_mult = self.iv_surface.get_term_structure_multiplier(max(0, dte))
            atm_iv = self.iv_surface.iv_params.atm_iv_base * term_mult
            skew_coef = self.iv_surface.iv_params.skew_coef

            for strike in strikes_list:
                moneyness = strike / spot
                skew_adj = 1.0 + skew_coef * ((moneyness - 1.0) ** 2)
                iv = max(0.01, atm_iv * skew_adj)

                all_strikes[idx] = strike
                all_tte[idx] = tte
                all_ivs[idx] = iv
                all_is_call[idx] = True
                all_expirations.append(expiration)
                idx += 1

                all_strikes[idx] = strike
                all_tte[idx] = tte
                all_ivs[idx] = iv
                all_is_call[idx] = False
                all_expirations.append(expiration)
                idx += 1

        mid_prices, deltas, gammas, thetas, vegas, rhos = self.bs_pricer.price_and_greeks_batch(
            spot, all_strikes, all_tte, all_ivs, all_is_call
        )

        moneyness_arr = np.abs(all_strikes / spot - 1.0)
        spread_pct = np.where(moneyness_arr < 0.02, 0.025, 0.075)
        spreads = mid_prices * spread_pct
        bids = np.maximum(0.01, mid_prices - spreads / 2.0)
        asks = mid_prices + spreads / 2.0

        chain: List[OptionQuote] = []
        ticker = self.ticker
        for i in range(n_total):
            chain.append(OptionQuote(
                ticker=ticker,
                strike=float(all_strikes[i]),
                expiration=all_expirations[i],
                option_type="call" if all_is_call[i] else "put",
                bid=float(bids[i]),
                ask=float(asks[i]),
                mid=float(mid_prices[i]),
                iv=float(all_ivs[i]),
                greeks=Greeks(
                    delta=float(deltas[i]),
                    gamma=float(gammas[i]),
                    theta=float(thetas[i]),
                    vega=float(vegas[i]),
                    rho=float(rhos[i])
                )
            ))

        return chain

    def update_chain(
        self,
        existing_chain: List[OptionQuote],
        spot: float,
        current_time: datetime
    ) -> List[OptionQuote]:
        """Regenerate the full chain."""
        return self.generate_chain(spot, current_time)

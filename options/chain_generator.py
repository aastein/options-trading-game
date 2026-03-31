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

    def __init__(self, ticker_config: TickerConfig):
        self.ticker_config = ticker_config
        self.ticker = ticker_config.ticker

        self.bs_pricer = BlackScholesPricer()
        self.iv_surface = IVSurface(ticker_config.iv_params)
        self.greeks_calc = GreeksCalculator(self.bs_pricer, self.iv_surface)

        self.strike_increment = ticker_config.strike_increment

    def get_strikes(self, spot: float) -> List[float]:
        lower = max(1.0, spot * 0.80)
        upper = spot * 1.20

        strikes = []
        strike = lower
        while strike <= upper:
            strikes.append(round(strike))
            strike += self.strike_increment

        return sorted(list(set(float(s) for s in strikes if s > 0)))

    def get_active_expirations(self, current_time: datetime) -> List[datetime]:
        expirations = TradingCalendar.get_expirations_for_date(current_time)
        return expirations

    def calculate_bid_ask_spread(self, mid_price: float, strike: float, spot: float) -> tuple[float, float]:
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
        strikes = self.get_strikes(spot)
        expirations = self.get_active_expirations(current_time)

        chain = []

        for expiration in expirations:
            for strike in strikes:
                call_quote = self.generate_option_quote(
                    strike, expiration, spot, current_time, "call"
                )
                chain.append(call_quote)

                put_quote = self.generate_option_quote(
                    strike, expiration, spot, current_time, "put"
                )
                chain.append(put_quote)

        return chain

    def update_chain(
        self,
        existing_chain: List[OptionQuote],
        spot: float,
        current_time: datetime
    ) -> List[OptionQuote]:
        return self.generate_chain(spot, current_time)

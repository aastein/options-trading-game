from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.stats import norm


class BlackScholesPricer:
    """Black-Scholes option pricer with both scalar and vectorized batch methods."""

    def __init__(self, risk_free_rate: float = 0.045):
        self.risk_free_rate = risk_free_rate

    def calculate_d1(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
        """Calculate d1 for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d1 = (
            np.log(spot / strike)
            + (self.risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * np.sqrt(time_to_expiry))

        return float(d1)

    def calculate_d2(
        self,
        d1: float,
        volatility: float,
        time_to_expiry: float
    ) -> float:
        """Calculate d2 for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        return float(d2)

    def price_call(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
        """Price a single call option."""
        if time_to_expiry <= 0:
            return max(0.0, spot - strike)

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = self.calculate_d2(d1, volatility, time_to_expiry)

        call_price = (
            spot * norm.cdf(d1)
            - strike * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2)
        )

        return float(max(0.0, call_price))

    def price_put(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
        """Price a single put option."""
        if time_to_expiry <= 0:
            return max(0.0, strike - spot)

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = self.calculate_d2(d1, volatility, time_to_expiry)

        put_price = (
            strike * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            - spot * norm.cdf(-d1)
        )

        return float(max(0.0, put_price))

    def price(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: Literal["call", "put"]
    ) -> float:
        """Price a single option."""
        if option_type == "call":
            return self.price_call(spot, strike, time_to_expiry, volatility)
        else:
            return self.price_put(spot, strike, time_to_expiry, volatility)

    def calculate_delta(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: Literal["call", "put"]
    ) -> float:
        """Calculate delta for a single option."""
        if time_to_expiry <= 0:
            if option_type == "call":
                return 1.0 if spot > strike else 0.0
            else:
                return -1.0 if spot < strike else 0.0

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)

        if option_type == "call":
            return float(norm.cdf(d1))
        else:
            return float(norm.cdf(d1) - 1.0)

    def calculate_gamma(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
        """Calculate gamma for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)

        gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))

        return float(gamma)

    def calculate_theta(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: Literal["call", "put"]
    ) -> float:
        """Calculate theta for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = self.calculate_d2(d1, volatility, time_to_expiry)

        term1 = -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry))

        if option_type == "call":
            term2 = -self.risk_free_rate * strike * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2)
            theta = (term1 + term2) / 365.0
        else:
            term2 = self.risk_free_rate * strike * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            theta = (term1 + term2) / 365.0

        return float(theta)

    def calculate_vega(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
        """Calculate vega for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)

        vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100.0

        return float(vega)

    def calculate_rho(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: Literal["call", "put"]
    ) -> float:
        """Calculate rho for a single option."""
        if time_to_expiry <= 0:
            return 0.0

        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = self.calculate_d2(d1, volatility, time_to_expiry)

        if option_type == "call":
            rho = strike * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100.0
        else:
            rho = -strike * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100.0

        return float(rho)

    def price_and_greeks_batch(
        self,
        spot: float,
        strikes: np.ndarray,
        times_to_expiry: np.ndarray,
        ivs: np.ndarray,
        is_call: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Price options and compute all greeks in one vectorized pass.

        Args:
            spot: Current spot price (scalar).
            strikes: Array of strike prices.
            times_to_expiry: Array of times to expiry in years.
            ivs: Array of implied volatilities.
            is_call: Boolean array, True for calls.

        Returns:
            Tuple of (mid_prices, deltas, gammas, thetas, vegas, rhos) arrays.
        """
        r = self.risk_free_rate
        n = len(strikes)

        mid_prices = np.zeros(n)
        deltas = np.zeros(n)
        gammas = np.zeros(n)
        thetas = np.zeros(n)
        vegas = np.zeros(n)
        rhos = np.zeros(n)

        expired = times_to_expiry <= 0
        live = ~expired

        if expired.any():
            intrinsic_call = np.maximum(0.0, spot - strikes[expired])
            intrinsic_put = np.maximum(0.0, strikes[expired] - spot)
            mid_prices[expired] = np.where(is_call[expired], intrinsic_call, intrinsic_put)
            deltas[expired] = np.where(
                is_call[expired],
                np.where(spot > strikes[expired], 1.0, 0.0),
                np.where(spot < strikes[expired], -1.0, 0.0)
            )

        if not live.any():
            return mid_prices, deltas, gammas, thetas, vegas, rhos

        s_live = strikes[live]
        t_live = times_to_expiry[live]
        iv_live = ivs[live]
        call_live = is_call[live]

        sqrt_t = np.sqrt(t_live)
        d1 = (np.log(spot / s_live) + (r + 0.5 * iv_live ** 2) * t_live) / (iv_live * sqrt_t)
        d2 = d1 - iv_live * sqrt_t

        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d1 = norm.cdf(-d1)
        cdf_neg_d2 = norm.cdf(-d2)
        pdf_d1 = norm.pdf(d1)

        discount = np.exp(-r * t_live)

        call_price = spot * cdf_d1 - s_live * discount * cdf_d2
        put_price = s_live * discount * cdf_neg_d2 - spot * cdf_neg_d1

        mid_prices[live] = np.maximum(0.0, np.where(call_live, call_price, put_price))

        deltas[live] = np.where(call_live, cdf_d1, cdf_d1 - 1.0)

        gammas[live] = pdf_d1 / (spot * iv_live * sqrt_t)

        term1 = -(spot * pdf_d1 * iv_live) / (2 * sqrt_t)
        theta_call = (term1 - r * s_live * discount * cdf_d2) / 365.0
        theta_put = (term1 + r * s_live * discount * cdf_neg_d2) / 365.0
        thetas[live] = np.where(call_live, theta_call, theta_put)

        vegas[live] = spot * pdf_d1 * sqrt_t / 100.0

        rho_call = s_live * t_live * discount * cdf_d2 / 100.0
        rho_put = -s_live * t_live * discount * cdf_neg_d2 / 100.0
        rhos[live] = np.where(call_live, rho_call, rho_put)

        return mid_prices, deltas, gammas, thetas, vegas, rhos

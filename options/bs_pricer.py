from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.stats import norm


class BlackScholesPricer:
    
    def __init__(self, risk_free_rate: float = 0.045):
        self.risk_free_rate = risk_free_rate
    
    def calculate_d1(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float
    ) -> float:
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
        if time_to_expiry <= 0:
            return 0.0
        
        d1 = self.calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = self.calculate_d2(d1, volatility, time_to_expiry)
        
        if option_type == "call":
            rho = strike * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100.0
        else:
            rho = -strike * time_to_expiry * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100.0
        
        return float(rho)

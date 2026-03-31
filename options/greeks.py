from __future__ import annotations

from datetime import datetime
from typing import Literal

from utils.types import Greeks
from options.bs_pricer import BlackScholesPricer
from options.iv_surface import IVSurface


class GreeksCalculator:
    
    def __init__(self, bs_pricer: BlackScholesPricer, iv_surface: IVSurface):
        self.bs_pricer = bs_pricer
        self.iv_surface = iv_surface
    
    def calculate_time_to_expiry(
        self, 
        expiration: datetime, 
        current_time: datetime
    ) -> float:
        time_diff = expiration - current_time
        days_to_expiry = time_diff.total_seconds() / (24 * 3600)
        years_to_expiry = days_to_expiry / 365.0
        return float(max(0.0, years_to_expiry))
    
    def calculate_greeks(
        self,
        spot: float,
        strike: float,
        expiration: datetime,
        current_time: datetime,
        option_type: Literal["call", "put"]
    ) -> Greeks:
        iv = self.iv_surface.calculate_iv(strike, spot, expiration, current_time)
        
        time_to_expiry = self.calculate_time_to_expiry(expiration, current_time)
        
        delta = self.bs_pricer.calculate_delta(
            spot, strike, time_to_expiry, iv, option_type
        )
        
        gamma = self.bs_pricer.calculate_gamma(
            spot, strike, time_to_expiry, iv
        )
        
        theta = self.bs_pricer.calculate_theta(
            spot, strike, time_to_expiry, iv, option_type
        )
        
        vega = self.bs_pricer.calculate_vega(
            spot, strike, time_to_expiry, iv
        )
        
        rho = self.bs_pricer.calculate_rho(
            spot, strike, time_to_expiry, iv, option_type
        )
        
        return Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )

from __future__ import annotations

from datetime import datetime

from utils.types import IVParams


class IVSurface:
    
    def __init__(self, iv_params: IVParams):
        self.iv_params = iv_params
    
    def get_term_structure_multiplier(self, dte: int) -> float:
        if dte <= 7:
            return self.iv_params.term_structure["0-7"]
        elif dte <= 14:
            return self.iv_params.term_structure["8-14"]
        elif dte <= 32:
            return self.iv_params.term_structure["15-32"]
        else:
            return self.iv_params.term_structure["60"]
    
    def calculate_iv(
        self,
        strike: float,
        spot: float,
        expiration: datetime,
        current_time: datetime
    ) -> float:
        dte = (expiration - current_time).days
        
        if dte < 0:
            return 0.0
        
        term_mult = self.get_term_structure_multiplier(dte)
        
        atm_iv = self.iv_params.atm_iv_base * term_mult
        
        moneyness = strike / spot
        skew_adjustment = 1.0 + self.iv_params.skew_coef * ((moneyness - 1.0) ** 2)
        
        iv = atm_iv * skew_adjustment
        
        return float(max(0.01, iv))

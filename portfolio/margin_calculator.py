from __future__ import annotations

from typing import List

from utils.types import Position, OptionQuote


class MarginCalculator:
    
    def __init__(self, margin_rate: float = 0.15):
        self.margin_rate = margin_rate
    
    def calculate_delta_dollars(
        self,
        positions: List[Position],
        option_chain: List[OptionQuote],
        spot_prices: dict[str, float]
    ) -> float:
        greeks_map = {}
        for quote in option_chain:
            key = (quote.ticker, quote.expiration, quote.strike, quote.option_type)
            greeks_map[key] = quote.greeks
        
        total_delta_dollars = 0.0
        
        for pos in positions:
            key = (pos.ticker, pos.expiration, pos.strike, pos.option_type)
            
            if key in greeks_map:
                delta = greeks_map[key].delta
                spot_price = spot_prices.get(pos.ticker, 0.0)
                
                delta_dollars = pos.quantity * delta * 100 * spot_price
                total_delta_dollars += delta_dollars
        
        return float(total_delta_dollars)
    
    def calculate_required_margin(self, delta_dollars: float) -> float:
        return float(abs(delta_dollars) * self.margin_rate)
    
    def calculate_available_margin(self, cash: float, required_margin: float) -> float:
        return float(cash - required_margin)
    
    def check_margin_requirement(self, cash: float, required_margin: float) -> bool:
        return cash >= required_margin

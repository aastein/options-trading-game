from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class StagedOrder:
    ticker: str
    expiration: datetime
    strike: float
    option_type: str
    side: str
    quantity: int
    price: float
    timestamp: datetime
    
    def get_total_cost(self) -> float:
        multiplier = 100
        cost = abs(self.quantity * self.price * multiplier)
        return cost if self.side == "buy" else -cost
    
    def to_display_dict(self) -> dict[str, str]:
        return {
            "Ticker": self.ticker,
            "Exp": self.expiration.strftime("%m/%d/%y"),
            "Strike": f"{self.strike:.1f}",
            "Type": self.option_type.upper(),
            "Side": self.side.upper(),
            "Qty": str(self.quantity),
            "Price": f"${self.price:.2f}",
            "Total": f"${self.get_total_cost():.2f}"
        }

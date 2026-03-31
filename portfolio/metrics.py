from __future__ import annotations

import numpy as np
from typing import List


class MetricsCalculator:

    def __init__(self, starting_capital: float):
        self.starting_capital = starting_capital
        self.daily_values: List[float] = [starting_capital]

    def add_daily_value(self, value: float) -> None:
        self.daily_values.append(value)

    def calculate_roi(self, current_value: float) -> float:
        if self.starting_capital == 0:
            return 0.0
        roi = (current_value - self.starting_capital) / self.starting_capital
        return float(roi)

    def calculate_sharpe_ratio(self) -> float:
        if len(self.daily_values) < 2:
            return 0.0

        values = np.array(self.daily_values)
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        mean_return = returns.mean()
        std_return = returns.std()

        sharpe = (mean_return / std_return) * np.sqrt(252)
        return float(sharpe)

    def calculate_max_drawdown(self) -> float:
        if len(self.daily_values) < 2:
            return 0.0

        values = np.array(self.daily_values)

        running_max = np.maximum.accumulate(values)
        drawdowns = (values - running_max) / running_max

        max_drawdown = drawdowns.min()
        return float(abs(max_drawdown))

    def calculate_win_rate(self, trade_history: List[dict]) -> float:
        if not trade_history:
            return 0.0

        closed_trades: dict[tuple, List[dict]] = {}

        for trade in trade_history:
            key = (trade['ticker'], trade['expiration'], trade['strike'], trade['option_type'])

            if key not in closed_trades:
                closed_trades[key] = []

            closed_trades[key].append(trade)

        winning_trades = 0
        total_closed = 0

        for key, trades in closed_trades.items():
            if len(trades) >= 2:
                total_closed += 1

                first = trades[0]
                last = trades[-1]

                if first['side'] == 'sell':
                    pnl = (first['price'] - last['price'])
                else:
                    pnl = (last['price'] - first['price'])

                if pnl > 0:
                    winning_trades += 1

        if total_closed == 0:
            return 0.0

        return float(winning_trades / total_closed)

    def calculate_avg_pnl_per_trade(self, trade_history: List[dict]) -> float:
        if not trade_history:
            return 0.0

        total_pnl = 0.0
        trade_count = 0

        closed_trades: dict[tuple, List[dict]] = {}

        for trade in trade_history:
            key = (trade['ticker'], trade['expiration'], trade['strike'], trade['option_type'])

            if key not in closed_trades:
                closed_trades[key] = []

            closed_trades[key].append(trade)

        for key, trades in closed_trades.items():
            if len(trades) >= 2:
                first = trades[0]
                last = trades[-1]
                quantity = first['quantity']

                if first['side'] == 'sell':
                    pnl = (first['price'] - last['price']) * quantity * 100
                else:
                    pnl = (last['price'] - first['price']) * quantity * 100

                total_pnl += pnl
                trade_count += 1

        if trade_count == 0:
            return 0.0

        return float(total_pnl / trade_count)

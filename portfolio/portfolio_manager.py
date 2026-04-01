from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Literal, TYPE_CHECKING

from utils.types import Position, StockPosition, OptionQuote

if TYPE_CHECKING:
    from options.chain_generator import OptionChainGenerator

logger = logging.getLogger(__name__)


class PortfolioManager:

    def __init__(self, starting_capital: float, chain_generator: OptionChainGenerator | None = None):
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.chain_generator = chain_generator

        self.open_positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.stock_positions: List[StockPosition] = []

        self.trade_history: List[dict] = []

    def execute_order(
        self,
        ticker: str,
        expiration: datetime,
        strike: float,
        option_type: Literal["call", "put"],
        side: Literal["buy", "sell"],
        quantity: int,
        price: float,
        timestamp: datetime
    ) -> bool:
        cost = quantity * price * 100
        existing_position = self._find_position(ticker, expiration, strike, option_type)

        if side == "buy":
            if self.cash < cost:
                logger.warning(f"Insufficient cash: need ${cost:.2f}, have ${self.cash:.2f}")
                return False

            self.cash -= cost

            if existing_position is not None:
                existing_position.quantity += quantity

                if existing_position.quantity == 0:
                    self.open_positions.remove(existing_position)
                    self.closed_positions.append(existing_position)

                logger.info(f"BUY-TO-CLOSE {quantity} {ticker} {strike}{option_type[0].upper()} @ ${price:.2f}")
            else:
                position = Position(
                    ticker=ticker,
                    expiration=expiration,
                    strike=strike,
                    option_type=option_type,
                    quantity=quantity,
                    entry_price=price,
                    entry_timestamp=timestamp,
                    current_price=price
                )
                self.open_positions.append(position)

                logger.info(f"BUY-TO-OPEN {quantity} {ticker} {strike}{option_type[0].upper()} @ ${price:.2f}")

        else:
            self.cash += cost

            if existing_position is not None:
                existing_position.quantity -= quantity

                if existing_position.quantity == 0:
                    self.open_positions.remove(existing_position)
                    self.closed_positions.append(existing_position)

                logger.info(f"SELL-TO-CLOSE {quantity} {ticker} {strike}{option_type[0].upper()} @ ${price:.2f}")
            else:
                position = Position(
                    ticker=ticker,
                    expiration=expiration,
                    strike=strike,
                    option_type=option_type,
                    quantity=-quantity,
                    entry_price=price,
                    entry_timestamp=timestamp,
                    current_price=price
                )
                self.open_positions.append(position)

                logger.info(f"SELL-TO-OPEN {quantity} {ticker} {strike}{option_type[0].upper()} @ ${price:.2f}")

        self.trade_history.append({
            "timestamp": timestamp,
            "ticker": ticker,
            "expiration": expiration,
            "strike": strike,
            "option_type": option_type,
            "side": side,
            "quantity": quantity,
            "price": price
        })

        return True

    def _find_position(
        self,
        ticker: str,
        expiration: datetime,
        strike: float,
        option_type: Literal["call", "put"]
    ) -> Position | None:
        for pos in self.open_positions:
            if (pos.ticker == ticker and
                pos.expiration == expiration and
                pos.strike == strike and
                pos.option_type == option_type):
                return pos
        return None

    def update_positions(self, option_chain: List[OptionQuote], spot_prices: dict[str, float] | None = None, current_time: datetime | None = None) -> None:
        price_map = {}
        for quote in option_chain:
            key = (quote.ticker, quote.expiration, quote.strike, quote.option_type)
            price_map[key] = quote.mid

        for pos in self.open_positions:
            key = (pos.ticker, pos.expiration, pos.strike, pos.option_type)
            if key in price_map:
                pos.mark_to_market(price_map[key])
            elif self.chain_generator is not None and spot_prices is not None and current_time is not None:
                spot_price = spot_prices.get(pos.ticker)
                if spot_price is not None:
                    price = self._calculate_option_price(
                        pos.ticker,
                        pos.strike,
                        pos.expiration,
                        spot_price,
                        current_time,
                        pos.option_type
                    )
                    pos.mark_to_market(price)

        if spot_prices:
            for stock_pos in self.stock_positions:
                if stock_pos.ticker in spot_prices:
                    stock_pos.mark_to_market(spot_prices[stock_pos.ticker])

    def handle_expiration(self, current_timestamp: datetime, spot_price: float) -> None:
        expired_positions = []

        for pos in self.open_positions:
            if pos.expiration.date() == current_timestamp.date():
                if current_timestamp.hour >= 16:
                    expired_positions.append(pos)

        for pos in expired_positions:
            if pos.option_type == "call":
                if spot_price > pos.strike:
                    shares_per_contract = 100
                    total_shares = pos.quantity * shares_per_contract

                    if pos.quantity > 0:
                        cost = total_shares * pos.strike
                        self.cash -= cost
                        self._add_stock_position(pos.ticker, total_shares, pos.strike, current_timestamp)
                        logger.info(f"Call assigned: Long {total_shares} {pos.ticker} @ ${pos.strike:.2f}")
                    else:
                        proceeds = abs(total_shares) * pos.strike
                        self.cash += proceeds
                        self._add_stock_position(pos.ticker, total_shares, pos.strike, current_timestamp)
                        logger.info(f"Call assigned: Short {abs(total_shares)} {pos.ticker} @ ${pos.strike:.2f}")
                else:
                    logger.info(f"Call expired OTM: {pos.ticker} {pos.strike}C")
            else:
                if spot_price < pos.strike:
                    shares_per_contract = 100
                    total_shares = pos.quantity * shares_per_contract

                    if pos.quantity > 0:
                        proceeds = total_shares * pos.strike
                        self.cash += proceeds
                        self._add_stock_position(pos.ticker, -total_shares, pos.strike, current_timestamp)
                        logger.info(f"Put assigned: Short {total_shares} {pos.ticker} @ ${pos.strike:.2f}")
                    else:
                        cost = abs(total_shares) * pos.strike
                        self.cash -= cost
                        self._add_stock_position(pos.ticker, -total_shares, pos.strike, current_timestamp)
                        logger.info(f"Put assigned: Long {abs(total_shares)} {pos.ticker} @ ${pos.strike:.2f}")
                else:
                    logger.info(f"Put expired OTM: {pos.ticker} {pos.strike}P")

            is_itm = (
                (pos.option_type == "call" and spot_price > pos.strike)
                or (pos.option_type == "put" and spot_price < pos.strike)
            )
            exit_price = 0.0
            if is_itm:
                exit_price = abs(spot_price - pos.strike)

            self.trade_history.append({
                "timestamp": current_timestamp,
                "ticker": pos.ticker,
                "expiration": pos.expiration,
                "strike": pos.strike,
                "option_type": pos.option_type,
                "side": "assignment" if is_itm else "expiration",
                "quantity": abs(pos.quantity),
                "price": exit_price,
            })

            self.open_positions.remove(pos)
            self.closed_positions.append(pos)

    def _add_stock_position(self, ticker: str, quantity: int, price: float, timestamp: datetime) -> None:
        existing = None
        for stock_pos in self.stock_positions:
            if stock_pos.ticker == ticker:
                existing = stock_pos
                break

        if existing:
            total_quantity = existing.quantity + quantity
            if total_quantity == 0:
                self.stock_positions.remove(existing)
                logger.info(f"Stock position closed: {ticker}")
            else:
                avg_price = ((existing.quantity * existing.entry_price) + (quantity * price)) / total_quantity
                existing.quantity = total_quantity
                existing.entry_price = avg_price
                logger.info(f"Stock position updated: {total_quantity} {ticker} @ ${avg_price:.2f}")
        else:
            stock_pos = StockPosition(
                ticker=ticker,
                quantity=quantity,
                entry_price=price,
                entry_timestamp=timestamp,
                current_price=price
            )
            self.stock_positions.append(stock_pos)
            logger.info(f"New stock position: {quantity} {ticker} @ ${price:.2f}")

    def get_total_value(self) -> float:
        options_market_value = sum(
            pos.quantity * pos.current_price * 100 for pos in self.open_positions
        )
        stocks_market_value = sum(
            stock.quantity * stock.current_price for stock in self.stock_positions
        )
        return float(self.cash + options_market_value + stocks_market_value)

    def get_unrealized_pnl(self) -> float:
        options_pnl = sum(pos.get_pnl() for pos in self.open_positions)
        stocks_pnl = sum(stock.get_pnl() for stock in self.stock_positions)
        return float(options_pnl + stocks_pnl)

    def get_realized_pnl(self) -> float:
        return float(self.get_total_value() - self.starting_capital - self.get_unrealized_pnl())

    def get_total_pnl(self) -> float:
        return float(self.get_total_value() - self.starting_capital)

    def _calculate_option_price(
        self,
        ticker: str,
        strike: float,
        expiration: datetime,
        spot: float,
        current_time: datetime,
        option_type: str
    ) -> float:
        if self.chain_generator is None:
            logger.warning(f"Cannot price {ticker} {strike}{option_type[0].upper()} - no chain generator")
            return 0.0

        iv = self.chain_generator.iv_surface.calculate_iv(strike, spot, expiration, current_time)
        time_to_expiry = self.chain_generator.greeks_calc.calculate_time_to_expiry(expiration, current_time)

        if time_to_expiry <= 0:
            return 0.0

        price = self.chain_generator.bs_pricer.price(spot, strike, time_to_expiry, iv, option_type)
        return float(price)

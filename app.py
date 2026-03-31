from __future__ import annotations

import faulthandler
import logging
import sys
import time
import signal
from datetime import datetime, timedelta
from typing import List

faulthandler.enable()

import numpy as np
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QSpinBox, QComboBox, QGroupBox, QHBoxLayout, QMessageBox
from PySide6.QtCore import QTimer

from utils.config_loader import ConfigLoader
from utils.types import TickerConfig, OHLCBar, OptionQuote
from utils.styles import DARK_THEME_STYLESHEET
from market.calendar import TradingCalendar
from market.regime_generator import RegimeGenerator
from market.tick_generator import TickGenerator
from options.chain_generator import OptionChainGenerator
from portfolio.portfolio_manager import PortfolioManager
from portfolio.margin_calculator import MarginCalculator
from portfolio.metrics import MetricsCalculator
from ui.main_window import MainWindow
from ui.staged_orders import StagedOrder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameSetupDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Setup")
        self.setModal(True)

        self.ticker = "SPY"
        self.starting_capital = 100000.0
        self.start_date = datetime(2024, 1, 2)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.setStyleSheet(DARK_THEME_STYLESHEET)

        ticker_group = QGroupBox("Select Ticker")
        ticker_layout = QHBoxLayout(ticker_group)

        self.ticker_combo = QComboBox()
        self.ticker_combo.addItems(["SPY", "QQQ", "IWM"])
        ticker_layout.addWidget(self.ticker_combo)

        layout.addWidget(ticker_group)

        capital_group = QGroupBox("Starting Capital ($)")
        capital_layout = QHBoxLayout(capital_group)

        self.capital_spin = QSpinBox()
        self.capital_spin.setMinimum(10000)
        self.capital_spin.setMaximum(10000000)
        self.capital_spin.setSingleStep(10000)
        self.capital_spin.setValue(100000)
        capital_layout.addWidget(self.capital_spin)

        layout.addWidget(capital_group)

        start_btn = QPushButton("Start Game")
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

    def get_settings(self) -> tuple[str, float, datetime]:
        ticker = self.ticker_combo.currentText()
        capital = float(self.capital_spin.value())
        return ticker, capital, self.start_date


class GameEngine:

    def __init__(
        self,
        ticker: str,
        starting_capital: float,
        start_date: datetime,
        ticker_config: TickerConfig
    ):
        self.ticker = ticker
        self.starting_capital = starting_capital
        self.start_date = start_date
        self.ticker_config = ticker_config

        seed = int(time.time())
        self.regime_generator = RegimeGenerator(ticker_config, seed)
        self.tick_generator = TickGenerator(ticker_config)
        self.chain_generator = OptionChainGenerator(ticker_config)

        self.portfolio_manager = PortfolioManager(starting_capital, self.chain_generator)
        self.margin_calculator = MarginCalculator()
        self.metrics_calculator = MetricsCalculator(starting_capital)

        self.trading_days: List[datetime] = []
        self.daily_ohlc: List[OHLCBar] = []
        self.current_day_ticks: np.ndarray = np.array([])
        self.intraday_bars: List[tuple[datetime, float, float, float, float]] = []
        self.completed_daily_bars: List[OHLCBar] = []

        self.current_day_index = 0
        self.current_tick_index = 0
        self.current_time: datetime = start_date
        self.current_spot_price = 0.0

        self.option_chain: List[OptionQuote] = []
        self._chain_cache_tick = -1
        self._chain_cache_spot = 0.0
        self._chain_regen_interval = 60
        self._chain_spot_threshold = 0.005

        self.playback_speed = 1

        self._initialize_game()

    def _initialize_game(self) -> None:
        logger.info("Generating 252 trading days...")

        self.trading_days = TradingCalendar.generate_trading_days(self.start_date, 252)

        regime_sequence = self.regime_generator.generate_regime_sequence(252)

        initial_price = 450.0 if self.ticker == "SPY" else 380.0 if self.ticker == "QQQ" else 200.0

        self.daily_ohlc = self.regime_generator.generate_daily_ohlc(
            regime_sequence,
            self.start_date,
            initial_price
        )

        logger.info("Game initialization complete")

        self._start_new_day()

    def _start_new_day(self, target: str = "close") -> None:
        if self.current_day_index >= len(self.daily_ohlc):
            logger.info("Game complete - all 252 days played")
            return

        ohlc_bar = self.daily_ohlc[self.current_day_index]

        logger.info(f"Starting day {self.current_day_index + 1}: {ohlc_bar.timestamp.date()} (target={target})")

        seed = self.current_day_index + int(time.time())
        self.current_day_ticks = self.tick_generator.generate_day_ticks(ohlc_bar, seed)

        if target == "open":
            self.current_tick_index = 0
        elif target == "midday":
            market_open = TradingCalendar.get_market_open(ohlc_bar.timestamp)
            target_time = market_open.replace(hour=13, minute=0, second=0)
            seconds_since_open = (target_time - market_open).total_seconds()
            self.current_tick_index = min(int(seconds_since_open / 5), len(self.current_day_ticks) - 1)
        else:  # close
            self.current_tick_index = len(self.current_day_ticks) - 1

        self.current_spot_price = float(self.current_day_ticks[self.current_tick_index])
        self.current_time = self.tick_generator.get_tick_timestamp(ohlc_bar, self.current_tick_index)

        self._update_option_chain(force=True)
        spot_prices = {self.ticker: self.current_spot_price}
        self.portfolio_manager.update_positions(self.option_chain, spot_prices, self.current_time)

        self.metrics_calculator.add_daily_value(self.portfolio_manager.get_total_value())

        if target == "close":
            close_time = TradingCalendar.get_market_close(ohlc_bar.timestamp)
            self.portfolio_manager.handle_expiration(close_time, self.current_spot_price)
            self.current_tick_index = len(self.current_day_ticks)  # Mark day as complete

    def tick(self) -> bool:
        if self.current_tick_index >= len(self.current_day_ticks):
            self._end_day()
            return False

        self.current_spot_price = float(self.current_day_ticks[self.current_tick_index])

        ohlc_bar = self.daily_ohlc[self.current_day_index]
        self.current_time = self.tick_generator.get_tick_timestamp(ohlc_bar, self.current_tick_index)

        self._update_option_chain()

        spot_prices = {self.ticker: self.current_spot_price}
        self.portfolio_manager.update_positions(self.option_chain, spot_prices, self.current_time)

        self.current_tick_index += 1

        return True

    def _end_day(self) -> None:
        logger.info(f"Day {self.current_day_index + 1} complete")

        close_time = TradingCalendar.get_market_close(self.daily_ohlc[self.current_day_index].timestamp)
        self.portfolio_manager.handle_expiration(close_time, self.current_spot_price)

        self.current_day_index += 1

        if self.current_day_index < len(self.daily_ohlc):
            self._start_new_day()  # defaults to close

    def _update_option_chain(self, force: bool = False) -> None:
        ticks_elapsed = self.current_tick_index - self._chain_cache_tick
        enough_ticks = ticks_elapsed >= self._chain_regen_interval

        if self._chain_cache_spot > 0:
            spot_change = abs(self.current_spot_price - self._chain_cache_spot) / self._chain_cache_spot
        else:
            spot_change = 1.0

        spot_moved = spot_change >= self._chain_spot_threshold

        if force or enough_ticks or spot_moved or not self.option_chain:
            self.option_chain = self.chain_generator.generate_chain(
                self.current_spot_price,
                self.current_time
            )
            self._chain_cache_tick = self.current_tick_index
            self._chain_cache_spot = self.current_spot_price

    def _finalize_current_day(self) -> None:
        """Handle expiration for current day if not already at close."""
        if self.current_tick_index < len(self.current_day_ticks):
            ohlc_bar = self.daily_ohlc[self.current_day_index]
            close_price = float(self.current_day_ticks[-1])
            close_time = TradingCalendar.get_market_close(ohlc_bar.timestamp)
            self.portfolio_manager.handle_expiration(close_time, close_price)

    def _advance_to_next_day(self, target: str = "close") -> None:
        """Finalize current day and advance to next day at the given target."""
        self._finalize_current_day()
        self.current_day_index += 1

        if self.current_day_index >= len(self.daily_ohlc):
            logger.info("No more trading days")
            self.current_day_index = len(self.daily_ohlc) - 1
            return

        self._start_new_day(target=target)
        logger.info(f"Advanced to next day ({target}): {self.current_time}")

    def jump_to_next_day_open(self) -> None:
        self._advance_to_next_day(target="open")

    def jump_to_next_day_midday(self) -> None:
        self._advance_to_next_day(target="midday")

    def jump_to_next_day(self) -> None:
        self._advance_to_next_day(target="close")

    def place_order(
        self,
        quote: OptionQuote,
        side: str,
        quantity: int
    ) -> bool:
        success = self.portfolio_manager.execute_order(
            ticker=quote.ticker,
            expiration=quote.expiration,
            strike=quote.strike,
            option_type=quote.option_type,
            side=side,
            quantity=quantity,
            price=quote.mid,
            timestamp=self.current_time
        )

        return success

    def get_progress(self) -> float:
        if len(self.current_day_ticks) == 0:
            return 0.0
        return float(self.current_tick_index / len(self.current_day_ticks))

    def get_intraday_bars(self) -> List[tuple[datetime, float, float, float, float]]:
        bars = []
        ohlc_bar = self.daily_ohlc[self.current_day_index]
        market_open = TradingCalendar.get_market_open(ohlc_bar.timestamp)

        bar_size = 360
        for i in range(0, self.current_tick_index, bar_size):
            end_idx = min(i + bar_size, self.current_tick_index)
            segment = self.current_day_ticks[i:end_idx]

            if len(segment) == 0:
                continue

            bar_time = market_open + timedelta(seconds=i * 5)
            bar_open = float(segment[0])
            bar_high = float(np.max(segment))
            bar_low = float(np.min(segment))
            bar_close = float(segment[-1])

            bars.append((bar_time, bar_open, bar_high, bar_low, bar_close))

        return bars

    def get_current_daily_bar(self) -> OHLCBar:
        ohlc_bar = self.daily_ohlc[self.current_day_index]
        current_segment = self.current_day_ticks[:self.current_tick_index+1]

        if len(current_segment) == 0:
            return ohlc_bar

        current_open = float(self.current_day_ticks[0])
        current_high = float(np.max(current_segment))
        current_low = float(np.min(current_segment))
        current_close = float(current_segment[-1])

        return OHLCBar(
            timestamp=ohlc_bar.timestamp,
            open=current_open,
            high=current_high,
            low=current_low,
            close=current_close
        )

    def get_completed_daily_bars(self) -> List[OHLCBar]:
        return self.daily_ohlc[:self.current_day_index]

    def get_trade_history(self) -> List[dict]:
        trades: List[dict] = []

        grouped: dict[tuple, List[dict]] = {}
        for trade in self.portfolio_manager.trade_history:
            key = (trade['ticker'], trade['expiration'], trade['strike'], trade['option_type'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(trade)

        for key, group in grouped.items():
            if len(group) < 2:
                continue

            first = group[0]
            last = group[-1]

            if first['side'] == 'sell':
                entry_price = float(first['price'])
                exit_price = float(last['price'])
                quantity = int(first['quantity'])
                side = 'sell'
                pnl = (entry_price - exit_price) * quantity * 100
            else:
                entry_price = float(first['price'])
                exit_price = float(last['price'])
                quantity = int(first['quantity'])
                side = 'buy'
                pnl = (exit_price - entry_price) * quantity * 100

            pnl_pct = 0.0
            if entry_price > 0 and quantity > 0:
                pnl_pct = (pnl / (entry_price * quantity * 100)) * 100

            trades.append({
                'exit_time': last['timestamp'],
                'ticker': first['ticker'],
                'expiration': first['expiration'],
                'strike': first['strike'],
                'option_type': first['option_type'],
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })

        return trades


class OptionTradingGame:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(DARK_THEME_STYLESHEET)
        self.config_loader = ConfigLoader()

        self.game_engine: GameEngine | None = None
        self.main_window: MainWindow | None = None

        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)

        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def run(self) -> None:
        setup_dialog = GameSetupDialog()

        if not setup_dialog.exec():
            return

        ticker, starting_capital, start_date = setup_dialog.get_settings()

        if not self.config_loader.check_config_exists(ticker):
            QMessageBox.critical(
                None,
                "Configuration Missing",
                f"Configuration for {ticker} not found.\n"
                f"Please run calibration first:\n"
                f"python -m calibration.calibration_runner --tickers {ticker}"
            )
            return

        ticker_config = self.config_loader.load_ticker_config(ticker)

        self.game_engine = GameEngine(ticker, starting_capital, start_date, ticker_config)

        self.main_window = MainWindow(ticker)

        self._connect_signals()

        self._update_ui()

        self.main_window.show()

        sys.exit(self.app.exec())

    def _connect_signals(self) -> None:
        if self.main_window is None or self.game_engine is None:
            return

        controls = self.main_window.controls_panel
        controls.new_game_clicked.connect(self._on_new_game)
        controls.play_clicked.connect(self._on_play)
        controls.pause_clicked.connect(self._on_pause)
        controls.jump_to_next_open_clicked.connect(self._on_jump_next_open)
        controls.jump_to_next_midday_clicked.connect(self._on_jump_next_midday)
        controls.jump_to_next_day_clicked.connect(self._on_jump_next_day)
        controls.speed_changed.connect(self._on_speed_changed)

        chain_panel = self.main_window.chain_panel
        chain_panel.bid_clicked.connect(self._on_bid_clicked)
        chain_panel.ask_clicked.connect(self._on_ask_clicked)

        staging_panel = self.main_window.order_staging_panel
        staging_panel.orders_confirmed.connect(self._on_orders_confirmed)

    def _on_play(self) -> None:
        interval = int(5000 / self.game_engine.playback_speed)
        self.timer.start(interval)

    def _on_pause(self) -> None:
        self.timer.stop()

    def _on_timer_tick(self) -> None:
        if self.game_engine is None:
            return

        continues = self.game_engine.tick()

        if not continues:
            self.timer.stop()
            if self.main_window:
                self.main_window.controls_panel.reset_play_button()

        self._update_ui()

    def _on_jump_next_open(self) -> None:
        if self.game_engine:
            self.game_engine.jump_to_next_day_open()
            self._update_ui()

    def _on_jump_next_midday(self) -> None:
        if self.game_engine:
            self.game_engine.jump_to_next_day_midday()
            self._update_ui()

    def _on_jump_next_day(self) -> None:
        if self.game_engine:
            self.game_engine.jump_to_next_day()
            self._update_ui()

    def _on_speed_changed(self, speed: int) -> None:
        if self.game_engine:
            self.game_engine.playback_speed = speed

            if self.timer.isActive():
                interval = int(5000 / speed)
                self.timer.setInterval(interval)

    def _on_new_game(self) -> None:
        if self.main_window and self.game_engine:
            reply = QMessageBox.question(
                self.main_window,
                "New Game",
                "Start a new game? Current progress will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.timer.stop()
                if self.main_window:
                    self.main_window.close()
                self.run()

    def _on_bid_clicked(self, ticker: str, expiration: datetime, strike: float, option_type: str, price: float) -> None:
        if self.main_window:
            self.main_window.order_staging_panel.add_order(
                ticker, expiration, strike, option_type, "sell", price, 1
            )

    def _on_ask_clicked(self, ticker: str, expiration: datetime, strike: float, option_type: str, price: float) -> None:
        if self.main_window:
            self.main_window.order_staging_panel.add_order(
                ticker, expiration, strike, option_type, "buy", price, 1
            )

    def _on_orders_confirmed(self, staged_orders: List[StagedOrder]) -> None:
        if not self.game_engine:
            return

        executed = 0
        for order in staged_orders:
            success = self.game_engine.portfolio_manager.execute_order(
                ticker=order.ticker,
                expiration=order.expiration,
                strike=order.strike,
                option_type=order.option_type,
                side=order.side,
                quantity=order.quantity,
                price=order.price,
                timestamp=self.game_engine.current_time
            )
            if success:
                executed += 1

        if self.main_window:
            QMessageBox.information(
                self.main_window,
                "Orders Executed",
                f"Successfully executed {executed} out of {len(staged_orders)} orders."
            )

    def _update_ui(self) -> None:
        if self.main_window is None or self.game_engine is None:
            return

        engine = self.game_engine

        self.main_window.update_time_display(engine.current_time)
        self.main_window.update_spot_price(engine.current_spot_price)

        intraday_bars = engine.get_intraday_bars()
        self.main_window.market_panel.update_intraday_chart(intraday_bars)

        completed_bars = engine.get_completed_daily_bars()
        current_bar = engine.get_current_daily_bar()
        self.main_window.market_panel.update_daily_chart(completed_bars, current_bar)

        self.main_window.chain_panel.update_chain(engine.option_chain, engine.current_spot_price, engine.current_time)
        self.main_window.order_staging_panel.update_prices(engine.option_chain)

        portfolio = engine.portfolio_manager
        total_value = portfolio.get_total_value()
        unrealized_pnl = portfolio.get_unrealized_pnl()
        total_pnl = portfolio.get_total_pnl()
        roi = engine.metrics_calculator.calculate_roi(total_value)
        sharpe = engine.metrics_calculator.calculate_sharpe_ratio()
        max_dd = engine.metrics_calculator.calculate_max_drawdown()

        self.main_window.portfolio_panel.update_metrics(
            portfolio.cash,
            total_value,
            unrealized_pnl,
            total_pnl,
            roi,
            sharpe,
            max_dd
        )

        self.main_window.portfolio_panel.update_positions(portfolio.open_positions)
        self.main_window.portfolio_panel.update_stocks(portfolio.stock_positions)

        trade_history = engine.get_trade_history()
        self.main_window.portfolio_panel.history_panel.update_history(trade_history)

        spot_prices = {engine.ticker: engine.current_spot_price}
        delta_dollars = engine.margin_calculator.calculate_delta_dollars(
            portfolio.open_positions,
            engine.option_chain,
            spot_prices
        )
        required_margin = engine.margin_calculator.calculate_required_margin(delta_dollars)
        available_margin = engine.margin_calculator.calculate_available_margin(
            portfolio.cash, required_margin
        )

        self.main_window.update_portfolio_display(
            total_value,
            total_pnl,
            required_margin,
            available_margin
        )

        progress = engine.get_progress()
        self.main_window.controls_panel.update_progress(progress)


def main() -> None:
    game = OptionTradingGame()
    game.run()


if __name__ == "__main__":
    main()

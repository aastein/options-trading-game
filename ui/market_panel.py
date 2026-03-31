from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
)
from PySide6.QtCore import Signal

from ui.charts.intraday_chart import IntradayChartWidget
from ui.charts.daily_chart import DailyChartWidget
from utils.types import OHLCBar


class MarketPanel(QWidget):

    def __init__(self, ticker: str):
        super().__init__()

        self.current_ticker = ticker
        self.current_spot_price = 0.0

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        ticker_group = QGroupBox(f"{self.current_ticker} Market Data")
        ticker_layout = QVBoxLayout(ticker_group)

        self.spot_label = QLabel("Spot: $0.00")
        self.spot_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        ticker_layout.addWidget(self.spot_label)

        ticker_group.setStyleSheet("""
            QGroupBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout.addWidget(ticker_group)

        intraday_group = QGroupBox("Intraday (5-Second)")
        intraday_layout = QVBoxLayout(intraday_group)
        intraday_layout.setContentsMargins(2, 2, 2, 2)

        self.intraday_chart = IntradayChartWidget()
        self.intraday_chart.setMinimumHeight(300)
        intraday_layout.addWidget(self.intraday_chart)

        intraday_group.setStyleSheet("""
            QGroupBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout.addWidget(intraday_group, stretch=1)

        daily_group = QGroupBox("Daily Chart")
        daily_layout = QVBoxLayout(daily_group)
        daily_layout.setContentsMargins(2, 2, 2, 2)

        self.daily_chart = DailyChartWidget()
        self.daily_chart.setMinimumHeight(250)
        daily_layout.addWidget(self.daily_chart)

        daily_group.setStyleSheet("""
            QGroupBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout.addWidget(daily_group, stretch=1)

    def update_spot_price(self, spot_price: float) -> None:
        self.current_spot_price = spot_price
        self.spot_label.setText(f"Spot: ${spot_price:.2f}")

    def update_intraday_chart(self, bars: List[Tuple[datetime, float, float, float, float]]) -> None:
        self.intraday_chart.update_data(bars)

    def update_daily_chart(self, completed_bars: List[OHLCBar], current_bar: OHLCBar | None = None) -> None:
        self.daily_chart.update_data(completed_bars, current_bar)

    def clear_charts(self) -> None:
        self.intraday_chart.clear()
        self.daily_chart.clear()

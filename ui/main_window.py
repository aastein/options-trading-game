from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
)

if TYPE_CHECKING:
    from ui.market_panel import MarketPanel
    from ui.chain_panel import ChainPanel
    from ui.portfolio_panel import PortfolioPanel
    from ui.controls_panel import ControlsPanel
    from ui.order_staging_panel import OrderStagingPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self, ticker: str):
        super().__init__()

        self.ticker = ticker
        self.setWindowTitle(f"Option Trading Game - {ticker}")
        self.setGeometry(100, 100, 1800, 1000)

        self.current_time: datetime | None = None
        self.current_spot_price: float = 0.0

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        self.status_bar = self._create_status_bar()
        main_layout.addWidget(self.status_bar)

        splitter = QSplitter(Qt.Horizontal)

        from ui.market_panel import MarketPanel
        from ui.chain_panel import ChainPanel
        from ui.portfolio_panel import PortfolioPanel
        from ui.order_staging_panel import OrderStagingPanel

        self.market_panel = MarketPanel(self.ticker)
        self.chain_panel = ChainPanel()
        self.portfolio_panel = PortfolioPanel()

        splitter.addWidget(self.market_panel)
        splitter.addWidget(self.chain_panel)
        splitter.addWidget(self.portfolio_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        main_layout.addWidget(splitter, stretch=3)

        self.order_staging_panel = OrderStagingPanel()
        main_layout.addWidget(self.order_staging_panel)

        from ui.controls_panel import ControlsPanel
        self.controls_panel = ControlsPanel()
        main_layout.addWidget(self.controls_panel)

    def _create_status_bar(self) -> QWidget:
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 2, 5, 2)

        self.time_label = QLabel("Time: --:--")
        self.time_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        status_layout.addWidget(self.time_label)

        status_layout.addStretch()

        self.portfolio_value_label = QLabel("Portfolio: $0.00")
        self.portfolio_value_label.setStyleSheet("font-size: 11px; color: #ffffff;")
        status_layout.addWidget(self.portfolio_value_label)

        self.pnl_label = QLabel("P&L: $0.00")
        self.pnl_label.setStyleSheet("font-size: 11px; color: #ffffff;")
        status_layout.addWidget(self.pnl_label)

        self.margin_label = QLabel("Margin: $0.00 / $0.00")
        self.margin_label.setStyleSheet("font-size: 11px; color: #ffffff;")
        status_layout.addWidget(self.margin_label)

        status_widget.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border-bottom: 1px solid #4a4a4a;
            }
        """)

        return status_widget

    def update_time_display(self, current_time: datetime) -> None:
        self.current_time = current_time
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"Time: {time_str}")

    def update_portfolio_display(
        self,
        portfolio_value: float,
        total_pnl: float,
        required_margin: float,
        available_margin: float
    ) -> None:
        self.portfolio_value_label.setText(f"Portfolio: ${portfolio_value:,.2f}")

        pnl_color = "green" if total_pnl >= 0 else "red"
        self.pnl_label.setText(f"P&L: ${total_pnl:,.2f}")
        self.pnl_label.setStyleSheet(f"font-size: 11px; color: {pnl_color};")

        self.margin_label.setText(
            f"Margin: ${required_margin:,.2f} / ${available_margin:,.2f}"
        )

    def update_spot_price(self, spot_price: float) -> None:
        self.current_spot_price = spot_price
        self.market_panel.update_spot_price(spot_price)

from __future__ import annotations

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QLabel,
    QTabWidget,
)
from PySide6.QtCore import Qt

from utils.types import Position, StockPosition
from ui.trade_history_panel import TradeHistoryPanel


class PortfolioPanel(QWidget):

    def __init__(self):
        super().__init__()

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        metrics_group = QGroupBox("Portfolio Metrics")
        metrics_layout = QVBoxLayout(metrics_group)

        self.cash_label = QLabel("Cash: $0.00")
        self.total_value_label = QLabel("Total Value: $0.00")
        self.unrealized_pnl_label = QLabel("Unrealized P&L: $0.00")
        self.total_pnl_label = QLabel("Total P&L: $0.00")
        self.roi_label = QLabel("ROI: 0.00%")
        self.sharpe_label = QLabel("Sharpe: 0.00")
        self.max_dd_label = QLabel("Max DD: 0.00%")

        for label in [self.cash_label, self.total_value_label, self.unrealized_pnl_label,
                      self.total_pnl_label, self.roi_label, self.sharpe_label, self.max_dd_label]:
            label.setStyleSheet("font-size: 11px; color: #ffffff;")
            metrics_layout.addWidget(label)

        metrics_group.setStyleSheet("""
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

        layout.addWidget(metrics_group)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                min-height: 28px;
                padding: 4px 12px;
                background-color: #3a3a3a;
                color: #888888;
                border: 1px solid #4a4a4a;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1a5f1a;
                color: #ffffff;
                border: 1px solid #2a8f2a;
            }
            QTabBar::tab:hover:!selected {
                background-color: #4a4a4a;
                color: #aaaaaa;
            }
        """)

        positions_widget = QWidget()
        positions_layout = QVBoxLayout(positions_widget)
        positions_layout.setContentsMargins(0, 0, 0, 0)

        self.positions_table = QTableWidget(0, 8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticker", "Exp", "Strike", "Type", "Qty", "Entry", "Current", "P&L"
        ])

        header = self.positions_table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        self.positions_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3a3a3a;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #4a4a4a;
                font-weight: bold;
                font-size: 10px;
            }
        """)

        positions_layout.addWidget(self.positions_table)

        stocks_widget = QWidget()
        stocks_layout = QVBoxLayout(stocks_widget)
        stocks_layout.setContentsMargins(0, 0, 0, 0)

        self.stocks_table = QTableWidget(0, 6)
        self.stocks_table.setHorizontalHeaderLabels([
            "Ticker", "Qty", "Entry", "Current", "P&L", "P&L%"
        ])

        stocks_header = self.stocks_table.horizontalHeader()
        for i in range(6):
            stocks_header.setSectionResizeMode(i, QHeaderView.Stretch)

        self.stocks_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3a3a3a;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #4a4a4a;
                font-weight: bold;
                font-size: 10px;
            }
        """)

        stocks_layout.addWidget(self.stocks_table)

        self.history_panel = TradeHistoryPanel()

        self.tab_widget.addTab(positions_widget, "Options")
        self.tab_widget.addTab(stocks_widget, "Stocks")
        self.tab_widget.addTab(self.history_panel, "History")

        layout.addWidget(self.tab_widget, stretch=1)

    def update_metrics(
        self,
        cash: float,
        total_value: float,
        unrealized_pnl: float,
        total_pnl: float,
        roi: float,
        sharpe: float,
        max_dd: float
    ) -> None:
        self.cash_label.setText(f"Cash: ${cash:,.2f}")
        self.total_value_label.setText(f"Total Value: ${total_value:,.2f}")

        unrealized_color = "green" if unrealized_pnl >= 0 else "red"
        self.unrealized_pnl_label.setText(f"Unrealized P&L: ${unrealized_pnl:,.2f}")
        self.unrealized_pnl_label.setStyleSheet(f"font-size: 11px; color: {unrealized_color};")

        pnl_color = "green" if total_pnl >= 0 else "red"
        self.total_pnl_label.setText(f"Total P&L: ${total_pnl:,.2f}")
        self.total_pnl_label.setStyleSheet(f"font-size: 12px; color: {pnl_color}; font-weight: bold;")

        roi_color = "green" if roi >= 0 else "red"
        self.roi_label.setText(f"ROI: {roi:.2%}")
        self.roi_label.setStyleSheet(f"font-size: 12px; color: {roi_color};")

        self.sharpe_label.setText(f"Sharpe: {sharpe:.2f}")
        self.max_dd_label.setText(f"Max DD: {max_dd:.2%}")

    def update_positions(self, positions: List[Position]) -> None:
        self.positions_table.setRowCount(len(positions))

        for row, pos in enumerate(positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(pos.ticker))
            self.positions_table.setItem(row, 1, QTableWidgetItem(
                pos.expiration.strftime('%m/%d')
            ))
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"${pos.strike:.2f}"))
            self.positions_table.setItem(row, 3, QTableWidgetItem(pos.option_type[0].upper()))
            self.positions_table.setItem(row, 4, QTableWidgetItem(str(pos.quantity)))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"${pos.entry_price:.2f}"))
            self.positions_table.setItem(row, 6, QTableWidgetItem(f"${pos.current_price:.2f}"))

            pnl = pos.get_pnl()
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")

            if pnl >= 0:
                pnl_item.setForeground(Qt.green)
            else:
                pnl_item.setForeground(Qt.red)

            self.positions_table.setItem(row, 7, pnl_item)

    def update_stocks(self, stock_positions: List[StockPosition]) -> None:
        self.stocks_table.setRowCount(len(stock_positions))

        for row, stock in enumerate(stock_positions):
            self.stocks_table.setItem(row, 0, QTableWidgetItem(stock.ticker))
            self.stocks_table.setItem(row, 1, QTableWidgetItem(str(stock.quantity)))
            self.stocks_table.setItem(row, 2, QTableWidgetItem(f"${stock.entry_price:.2f}"))
            self.stocks_table.setItem(row, 3, QTableWidgetItem(f"${stock.current_price:.2f}"))

            pnl = stock.get_pnl()
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")

            if pnl >= 0:
                pnl_item.setForeground(Qt.green)
            else:
                pnl_item.setForeground(Qt.red)

            self.stocks_table.setItem(row, 4, pnl_item)

            if stock.entry_price != 0:
                pnl_pct = (stock.current_price - stock.entry_price) / abs(stock.entry_price)
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.2%}")

                if pnl_pct >= 0:
                    pnl_pct_item.setForeground(Qt.green)
                else:
                    pnl_pct_item.setForeground(Qt.red)

                self.stocks_table.setItem(row, 5, pnl_pct_item)
            else:
                self.stocks_table.setItem(row, 5, QTableWidgetItem("N/A"))

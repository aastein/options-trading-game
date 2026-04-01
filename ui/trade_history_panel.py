from __future__ import annotations

from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class TradeHistoryPanel(QWidget):

    def __init__(self):
        super().__init__()

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.summary_label = QLabel("No trades yet")
        self.summary_label.setStyleSheet("color: #888888; padding: 2px; font-size: 9px;")
        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Time", "Ticker", "Exp", "Strike", "Type", "Side", "Qty", "Entry $", "Exit $", "P&L", "P&L %"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3a3a3a;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 1px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 2px;
                border: 1px solid #4a4a4a;
                font-weight: bold;
                font-size: 8px;
            }
        """)

        layout.addWidget(self.table)

    def update_history(self, trades: List[Dict]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(trades))

        total_pnl = 0.0
        winning_trades = 0

        for row, trade in enumerate(trades):
            time_str = trade['exit_time'].strftime("%m/%d %H:%M")
            self.table.setItem(row, 0, QTableWidgetItem(time_str))
            self.table.setItem(row, 1, QTableWidgetItem(trade['ticker']))
            self.table.setItem(row, 2, QTableWidgetItem(trade['expiration'].strftime("%m/%d")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{trade['strike']:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(trade['option_type'].upper()))
            self.table.setItem(row, 5, QTableWidgetItem(trade['side'].upper()))
            self.table.setItem(row, 6, QTableWidgetItem(str(trade['quantity'])))
            self.table.setItem(row, 7, QTableWidgetItem(f"${trade['entry_price']:.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"${trade['exit_price']:.2f}"))

            pnl = trade['pnl']
            pnl_pct = trade['pnl_pct']
            total_pnl += pnl

            if pnl > 0:
                winning_trades += 1

            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.1f}%")

            color = QColor("#4CAF50") if pnl >= 0 else QColor("#F44336")
            pnl_item.setForeground(color)
            pnl_pct_item.setForeground(color)

            self.table.setItem(row, 9, pnl_item)
            self.table.setItem(row, 10, pnl_pct_item)

        self.table.setSortingEnabled(True)
        self.table.sortItems(0, Qt.SortOrder.DescendingOrder)

        if trades:
            win_rate = (winning_trades / len(trades)) * 100
            self.summary_label.setText(
                f"{len(trades)} trades | Total P&L: ${total_pnl:.2f} | Win Rate: {win_rate:.1f}%"
            )
        else:
            self.summary_label.setText("No trades yet")

    def clear(self) -> None:
        self.table.setRowCount(0)
        self.summary_label.setText("No trades yet")

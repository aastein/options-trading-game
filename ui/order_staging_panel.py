from __future__ import annotations

from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from ui.staged_orders import StagedOrder


class OrderStagingPanel(QWidget):

    orders_confirmed = Signal(list)
    orders_cleared = Signal()

    def __init__(self):
        super().__init__()

        self.staged_orders: List[StagedOrder] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header_layout = QHBoxLayout()

        title_label = QLabel("Staged Orders")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.summary_label = QLabel("Total: $0.00")
        self.summary_label.setStyleSheet("font-size: 12px; color: #ffffff;")
        header_layout.addWidget(self.summary_label)

        self.confirm_btn = QPushButton("Confirm Orders")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._on_confirm_clicked)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5f1a;
                color: #ffffff;
                border: 1px solid #2a8f2a;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #2a8f2a;
            }
            QPushButton:pressed {
                background-color: #0a4f0a;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666666;
                border: 1px solid #444444;
            }
        """)
        header_layout.addWidget(self.confirm_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: #ffffff;
                border: 1px solid #A52A2A;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #A52A2A;
            }
            QPushButton:pressed {
                background-color: #6B0000;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666666;
                border: 1px solid #444444;
            }
        """)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Ticker", "Exp", "Strike", "Type", "Side", "Qty", "Price", "Total"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.setMinimumHeight(120)
        self.table.setMaximumHeight(200)

        self.table.setStyleSheet("""
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

        layout.addWidget(self.table)

    def add_order(
        self,
        ticker: str,
        expiration: datetime,
        strike: float,
        option_type: str,
        side: str,
        price: float,
        quantity: int = 1
    ) -> None:
        order = StagedOrder(
            ticker=ticker,
            expiration=expiration,
            strike=strike,
            option_type=option_type,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now()
        )

        self.staged_orders.append(order)
        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.staged_orders))

        for row, order in enumerate(self.staged_orders):
            display = order.to_display_dict()

            for col, key in enumerate(["Ticker", "Exp", "Strike", "Type", "Side", "Qty", "Price", "Total"]):
                item = QTableWidgetItem(display[key])

                if key == "Side":
                    if order.side == "buy":
                        item.setForeground(QColor("#6699ff"))
                    else:
                        item.setForeground(QColor("#ff6666"))

                if key == "Total":
                    cost = order.get_total_cost()
                    if cost < 0:
                        item.setForeground(QColor("#4CAF50"))
                    else:
                        item.setForeground(QColor("#F44336"))

                self.table.setItem(row, col, item)

        total_cost = sum(order.get_total_cost() for order in self.staged_orders)
        self.summary_label.setText(f"Total: ${total_cost:.2f}")

        has_orders = len(self.staged_orders) > 0
        self.confirm_btn.setEnabled(has_orders)
        self.clear_btn.setEnabled(has_orders)

    def _on_confirm_clicked(self) -> None:
        if not self.staged_orders:
            return

        self.orders_confirmed.emit(self.staged_orders.copy())
        self.staged_orders.clear()
        self._refresh_table()

    def _on_clear_clicked(self) -> None:
        self.staged_orders.clear()
        self._refresh_table()
        self.orders_cleared.emit()

    def _on_context_menu(self, pos) -> None:
        if not self.staged_orders:
            return

        item = self.table.itemAt(pos)
        if item is None:
            return

        row = item.row()
        if row < 0 or row >= len(self.staged_orders):
            return

        menu = QMenu(self)
        remove_action = menu.addAction("Remove Order")

        action = menu.exec(self.table.mapToGlobal(pos))
        if action == remove_action:
            del self.staged_orders[row]
            self._refresh_table()

    def clear_all(self) -> None:
        self.staged_orders.clear()
        self._refresh_table()

    def update_prices(self, option_chain: List) -> None:
        """Update staged order prices from current option chain"""
        if not self.staged_orders:
            return

        for order in self.staged_orders:
            for opt in option_chain:
                if (opt.ticker == order.ticker and
                    opt.expiration == order.expiration and
                    opt.strike == order.strike and
                    opt.option_type == order.option_type):

                    if order.side == "buy":
                        order.price = opt.ask
                    else:
                        order.price = opt.bid
                    break

        self._refresh_table()

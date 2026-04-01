from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Tuple

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QBrush

from utils.types import OptionQuote


class ChainPanel(QWidget):

    bid_clicked = Signal(str, datetime, float, str, float)
    ask_clicked = Signal(str, datetime, float, str, float)

    def __init__(self):
        super().__init__()

        self.current_chain: List[OptionQuote] = []
        self.current_spot: float = 0.0
        self.current_time: datetime = datetime.now()
        self._last_chain_hash: int = 0

        self._itm_call_even = QColor(0, 40, 60)
        self._itm_call_odd = QColor(0, 50, 75)
        self._itm_put_even = QColor(60, 30, 30)
        self._itm_put_odd = QColor(75, 38, 38)
        self._delta_highlight = QColor(60, 50, 25)
        self._normal_even = QColor(35, 35, 35)
        self._normal_odd = QColor(45, 45, 45)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("No chain data")
        self.status_label.setStyleSheet("color: #888888; padding: 2px; font-size: 9px;")
        layout.addWidget(self.status_label)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                min-height: 20px;
                padding: 2px 4px;
                background-color: #3a3a3a;
                color: #888888;
                border: 1px solid #4a4a4a;
                margin-right: 1px;
                font-size: 9px;
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
        layout.addWidget(self.tab_widget)

    def _destroy_chain_widgets(self) -> None:
        """Explicitly destroy all cell widgets in all tabs before clearing."""
        for tab_idx in range(self.tab_widget.count()):
            table = self.tab_widget.widget(tab_idx)
            if not isinstance(table, QTableWidget):
                continue
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    widget = table.cellWidget(row, col)
                    if widget is not None:
                        table.removeCellWidget(row, col)
                        widget.deleteLater()

    def update_chain(self, chain: List[OptionQuote], spot_price: float, current_time: datetime | None = None) -> None:
        self.current_chain = chain
        self.current_spot = spot_price
        if current_time:
            self.current_time = current_time

        if not chain:
            self.status_label.setText("No options available")
            return

        chain_hash = hash((
            len(chain),
            tuple(sorted(set((q.expiration, q.strike, q.option_type) for q in chain)))
        ))

        if chain_hash != self._last_chain_hash:
            self._last_chain_hash = chain_hash
            self._destroy_chain_widgets()
            self.tab_widget.clear()

            expirations = sorted(set(quote.expiration for quote in chain))

            for expiration in expirations:
                exp_chain = [q for q in chain if q.expiration == expiration]

                table = self._create_chain_table(exp_chain, expiration, spot_price)

                dte = (expiration.date() - self.current_time.date()).days
                tab_label = f"{expiration.strftime('%m/%d')}\n{dte}d"

                self.tab_widget.addTab(table, tab_label)

        self.status_label.setText(f"{len(chain)} options @ ${spot_price:.2f}")

    def _create_chain_table(self, chain: List[OptionQuote], expiration: datetime, spot_price: float) -> QTableWidget:
        calls = sorted([q for q in chain if q.option_type == "call"], key=lambda x: x.strike)
        puts = sorted([q for q in chain if q.option_type == "put"], key=lambda x: x.strike)

        strikes = sorted(set(q.strike for q in chain))

        headers = ["OI", "VOL", "BID", "ASK", "MID", "IV", "Δ", "Γ", "Θ",
                   "STRIKE",
                   "Θ", "Γ", "Δ", "IV", "MID", "ASK", "BID", "VOL", "OI"]

        table = QTableWidget(len(strikes), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(14)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3a3a3a;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 0px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 1px;
                border: 1px solid #4a4a4a;
                font-weight: bold;
                font-size: 8px;
            }
        """)

        call_map = {c.strike: c for c in calls}
        put_map = {p.strike: p for p in puts}

        for row, strike in enumerate(strikes):
            is_odd = row % 2 == 1
            call_itm = strike < spot_price
            put_itm = strike > spot_price

            call_bg = (self._itm_call_odd if is_odd else self._itm_call_even) if call_itm else (self._normal_odd if is_odd else self._normal_even)
            put_bg = (self._itm_put_odd if is_odd else self._itm_put_even) if put_itm else (self._normal_odd if is_odd else self._normal_even)

            if strike in call_map:
                call = call_map[strike]
                self._populate_option_row(table, row, 0, call, call_bg, expiration, True)
            else:
                self._populate_empty_row(table, row, 0, call_bg, 9)

            strike_item = QTableWidgetItem(f"{strike:.1f}")
            strike_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            strike_bg = self._compute_strike_color(strike, spot_price, strikes)
            strike_item.setBackground(strike_bg)
            font = strike_item.font()
            font.setBold(True)
            strike_item.setFont(font)
            table.setItem(row, 9, strike_item)

            if strike in put_map:
                put = put_map[strike]
                self._populate_option_row(table, row, 10, put, put_bg, expiration, False)
            else:
                self._populate_empty_row(table, row, 10, put_bg, 9)

        atm_row = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
        atm_item = table.item(atm_row, 9)
        if atm_item:
            table.scrollToItem(atm_item, QTableWidget.ScrollHint.PositionAtCenter)

        return table

    def _populate_option_row(
        self,
        table: QTableWidget,
        row: int,
        col_offset: int,
        opt: OptionQuote,
        bg_color: QColor | None,
        expiration: datetime,
        is_call: bool
    ) -> None:
        if is_call:
            self._set_cell(table, row, col_offset + 0, "-", bg_color)
            self._set_cell(table, row, col_offset + 1, "-", bg_color)
            self._set_bid_button(table, row, col_offset + 2, opt, bg_color, expiration)
            self._set_ask_button(table, row, col_offset + 3, opt, bg_color, expiration)
            self._set_cell(table, row, col_offset + 4, f"{opt.mid:.2f}" if opt.mid > 0 else "-", bg_color)
            self._set_cell(table, row, col_offset + 5, f"{opt.iv*100:.1f}%" if opt.iv > 0 else "-", bg_color)
            delta_bg = self._blend_delta_color(bg_color)
            self._set_cell(table, row, col_offset + 6, f"{opt.greeks.delta:.2f}" if opt.greeks.delta != 0 else "-", delta_bg)
            self._set_cell(table, row, col_offset + 7, f"{opt.greeks.gamma:.3f}" if opt.greeks.gamma != 0 else "-", bg_color)
            self._set_cell(table, row, col_offset + 8, f"{opt.greeks.theta:.2f}" if opt.greeks.theta != 0 else "-", bg_color)
        else:
            self._set_cell(table, row, col_offset + 0, f"{opt.greeks.theta:.2f}" if opt.greeks.theta != 0 else "-", bg_color)
            self._set_cell(table, row, col_offset + 1, f"{opt.greeks.gamma:.3f}" if opt.greeks.gamma != 0 else "-", bg_color)
            delta_bg = self._blend_delta_color(bg_color)
            self._set_cell(table, row, col_offset + 2, f"{opt.greeks.delta:.2f}" if opt.greeks.delta != 0 else "-", delta_bg)
            self._set_cell(table, row, col_offset + 3, f"{opt.iv*100:.1f}%" if opt.iv > 0 else "-", bg_color)
            self._set_cell(table, row, col_offset + 4, f"{opt.mid:.2f}" if opt.mid > 0 else "-", bg_color)
            self._set_ask_button(table, row, col_offset + 5, opt, bg_color, expiration)
            self._set_bid_button(table, row, col_offset + 6, opt, bg_color, expiration)
            self._set_cell(table, row, col_offset + 7, "-", bg_color)
            self._set_cell(table, row, col_offset + 8, "-", bg_color)

    def _populate_empty_row(self, table: QTableWidget, row: int, col_offset: int, bg_color: QColor | None, count: int) -> None:
        for i in range(count):
            self._set_cell(table, row, col_offset + i, "-", bg_color)

    def _set_cell(self, table: QTableWidget, row: int, col: int, text: str, bg_color: QColor | None) -> None:
        item = QTableWidgetItem(text)
        if bg_color:
            item.setBackground(bg_color)
        table.setItem(row, col, item)

    def _set_bid_button(
        self,
        table: QTableWidget,
        row: int,
        col: int,
        opt: OptionQuote,
        bg_color: QColor | None,
        expiration: datetime
    ) -> None:
        bid_text = f"{opt.bid:.2f}" if opt.bid > 0 else "-"
        btn = QPushButton(bid_text)
        btn.setFlat(True)
        btn.setProperty("strike", opt.strike)
        btn.setProperty("option_type", opt.option_type)
        btn.setProperty("ticker", opt.ticker)
        btn.setProperty("expiration", expiration)
        btn.setEnabled(opt.bid > 0)

        if opt.bid > 0:
            btn.clicked.connect(lambda checked=False, o=opt, exp=expiration: self.bid_clicked.emit(
                o.ticker, exp, o.strike, o.option_type, o.bid
            ))

        bg_style = ""
        if bg_color:
            bg_style = f"background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});"

        btn.setStyleSheet(f"""
            QPushButton {{
                {bg_style}
                color: #ff6666;
                border: none;
                padding: 0px;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 8px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #5a2a2a;
                color: #ffffff;
            }}
            QPushButton:disabled {{
                color: #666666;
            }}
        """)
        table.setCellWidget(row, col, btn)

    def _set_ask_button(
        self,
        table: QTableWidget,
        row: int,
        col: int,
        opt: OptionQuote,
        bg_color: QColor | None,
        expiration: datetime
    ) -> None:
        ask_text = f"{opt.ask:.2f}" if opt.ask > 0 else "-"
        btn = QPushButton(ask_text)
        btn.setFlat(True)
        btn.setProperty("strike", opt.strike)
        btn.setProperty("option_type", opt.option_type)
        btn.setProperty("ticker", opt.ticker)
        btn.setProperty("expiration", expiration)
        btn.setEnabled(opt.ask > 0)

        if opt.ask > 0:
            btn.clicked.connect(lambda checked=False, o=opt, exp=expiration: self.ask_clicked.emit(
                o.ticker, exp, o.strike, o.option_type, o.ask
            ))

        bg_style = ""
        if bg_color:
            bg_style = f"background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});"

        btn.setStyleSheet(f"""
            QPushButton {{
                {bg_style}
                color: #6699ff;
                border: none;
                padding: 0px;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 8px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #2a4a6a;
                color: #ffffff;
            }}
            QPushButton:disabled {{
                color: #666666;
            }}
        """)
        table.setCellWidget(row, col, btn)

    def _blend_delta_color(self, base_color: QColor | None) -> QColor:
        if base_color is None:
            return self._delta_highlight
        r = (base_color.red() + self._delta_highlight.red()) // 2
        g = (base_color.green() + self._delta_highlight.green()) // 2
        b = (base_color.blue() + self._delta_highlight.blue()) // 2
        return QColor(r, g, b)

    def _compute_strike_color(self, strike: float, spot: float, all_strikes: List[float]) -> QColor:
        if not all_strikes or spot <= 0:
            return QColor(60, 65, 75)

        max_distance = max(
            abs(all_strikes[0] - spot),
            abs(all_strikes[-1] - spot),
        )
        if max_distance == 0:
            return QColor(70, 80, 120)

        distance = abs(strike - spot)
        proximity = 1.0 - (distance / max_distance)
        r = int(50 + (1 - proximity) * 30)
        g = int(55 + (1 - proximity) * 35)
        b = int(80 + proximity * 50)
        return QColor(r, g, b)

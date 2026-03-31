from __future__ import annotations

from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QPushButton,
    QDialog,
    QLabel,
    QSpinBox,
    QComboBox,
    QHBoxLayout,
    QGroupBox,
)
from PySide6.QtCore import Signal, Qt

from utils.types import OptionQuote


class OrderDialog(QDialog):
    
    def __init__(self, quote: OptionQuote, parent: QWidget | None = None):
        super().__init__(parent)
        
        self.quote = quote
        self.quantity = 1
        self.side = "buy"
        
        self.setWindowTitle("Place Order")
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            f"{self.quote.ticker} ${self.quote.strike} {self.quote.option_type.upper()}\n"
            f"Exp: {self.quote.expiration.strftime('%Y-%m-%d')}\n"
            f"Mid Price: ${self.quote.mid:.2f}"
        )
        info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)
        
        side_group = QGroupBox("Side")
        side_layout = QHBoxLayout(side_group)
        
        self.side_combo = QComboBox()
        self.side_combo.addItems(["buy", "sell"])
        side_layout.addWidget(self.side_combo)
        
        layout.addWidget(side_group)
        
        qty_group = QGroupBox("Quantity")
        qty_layout = QHBoxLayout(qty_group)
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(100)
        self.qty_spin.setValue(1)
        qty_layout.addWidget(self.qty_spin)
        
        layout.addWidget(qty_group)
        
        cost_label = QLabel()
        self._update_cost_label(cost_label)
        self.qty_spin.valueChanged.connect(lambda: self._update_cost_label(cost_label))
        layout.addWidget(cost_label)
        
        button_layout = QHBoxLayout()
        
        submit_btn = QPushButton("Submit Order")
        submit_btn.clicked.connect(self.accept)
        button_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _update_cost_label(self, label: QLabel) -> None:
        qty = self.qty_spin.value()
        cost = qty * self.quote.mid * 100
        label.setText(f"Total Cost: ${cost:.2f}")
    
    def get_order_details(self) -> tuple[str, int]:
        return self.side_combo.currentText(), self.qty_spin.value()


class ChainPanel(QWidget):
    
    order_placed = Signal(OptionQuote, str, int)
    
    def __init__(self):
        super().__init__()
        
        self.current_chain: List[OptionQuote] = []
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
    
    def update_chain(self, chain: List[OptionQuote]) -> None:
        self.current_chain = chain
        
        self.tab_widget.clear()
        
        expirations = sorted(set(quote.expiration for quote in chain))
        
        for expiration in expirations:
            exp_chain = [q for q in chain if q.expiration == expiration]
            
            table = self._create_chain_table(exp_chain)
            
            dte = (expiration - datetime.now()).days
            tab_label = f"{expiration.strftime('%m/%d')} ({dte}d)"
            
            self.tab_widget.addTab(table, tab_label)
    
    def _create_chain_table(self, chain: List[OptionQuote]) -> QTableWidget:
        calls = sorted([q for q in chain if q.option_type == "call"], key=lambda x: x.strike)
        puts = sorted([q for q in chain if q.option_type == "put"], key=lambda x: x.strike)
        
        strikes = sorted(set(q.strike for q in chain))
        
        table = QTableWidget(len(strikes), 11)
        table.setHorizontalHeaderLabels([
            "C Bid", "C Ask", "C Mid", "C IV", "C Delta",
            "Strike",
            "P Delta", "P IV", "P Mid", "P Ask", "P Bid"
        ])
        
        header = table.horizontalHeader()
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        call_map = {c.strike: c for c in calls}
        put_map = {p.strike: p for p in puts}
        
        for row, strike in enumerate(strikes):
            if strike in call_map:
                call = call_map[strike]
                table.setItem(row, 0, QTableWidgetItem(f"${call.bid:.2f}"))
                table.setItem(row, 1, QTableWidgetItem(f"${call.ask:.2f}"))
                table.setItem(row, 2, QTableWidgetItem(f"${call.mid:.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{call.iv:.2%}"))
                table.setItem(row, 4, QTableWidgetItem(f"{call.greeks.delta:.3f}"))
            
            strike_item = QTableWidgetItem(f"${strike:.2f}")
            strike_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 5, strike_item)
            
            if strike in put_map:
                put = put_map[strike]
                table.setItem(row, 6, QTableWidgetItem(f"{put.greeks.delta:.3f}"))
                table.setItem(row, 7, QTableWidgetItem(f"{put.iv:.2%}"))
                table.setItem(row, 8, QTableWidgetItem(f"${put.mid:.2f}"))
                table.setItem(row, 9, QTableWidgetItem(f"${put.ask:.2f}"))
                table.setItem(row, 10, QTableWidgetItem(f"${put.bid:.2f}"))
        
        table.cellDoubleClicked.connect(
            lambda row, col: self._on_cell_double_clicked(row, col, strikes, call_map, put_map)
        )
        
        return table
    
    def _on_cell_double_clicked(
        self, 
        row: int, 
        col: int, 
        strikes: List[float], 
        call_map: dict, 
        put_map: dict
    ) -> None:
        if row >= len(strikes):
            return
        
        strike = strikes[row]
        
        if col < 5 and strike in call_map:
            quote = call_map[strike]
        elif col > 5 and strike in put_map:
            quote = put_map[strike]
        else:
            return
        
        dialog = OrderDialog(quote, self)
        if dialog.exec():
            side, quantity = dialog.get_order_details()
            self.order_placed.emit(quote, side, quantity)

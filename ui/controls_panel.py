from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QProgressBar,
)
from PySide6.QtCore import Signal


class ControlsPanel(QWidget):

    new_game_clicked = Signal()
    jump_to_next_open_clicked = Signal()
    jump_to_next_midday_clicked = Signal()
    jump_to_next_day_clicked = Signal()
    speed_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.setFixedWidth(100)
        self.new_game_btn.clicked.connect(self.new_game_clicked.emit)
        self.new_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5f1a;
                color: #ffffff;
                border: 1px solid #2a8f2a;
                border-radius: 4px;
                padding: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a8f2a;
            }
            QPushButton:pressed {
                background-color: #0a4f0a;
            }
        """)
        layout.addWidget(self.new_game_btn)

        layout.addSpacing(10)

        speed_label = QLabel("Speed:")
        layout.addWidget(speed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1x", "2x", "5x"])
        self.speed_combo.setFixedWidth(80)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_combo)

        layout.addSpacing(10)

        self.jump_open_btn = QPushButton("Opening")
        self.jump_open_btn.clicked.connect(self.jump_to_next_open_clicked.emit)
        layout.addWidget(self.jump_open_btn)

        self.jump_midday_btn = QPushButton("Mid Session")
        self.jump_midday_btn.clicked.connect(self.jump_to_next_midday_clicked.emit)
        layout.addWidget(self.jump_midday_btn)

        self.jump_next_day_btn = QPushButton("Next Day")
        self.jump_next_day_btn.clicked.connect(self.jump_to_next_day_clicked.emit)
        layout.addWidget(self.jump_next_day_btn)

        layout.addSpacing(10)

        progress_label = QLabel("Day Progress:")
        layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def _on_speed_changed(self, index: int) -> None:
        speeds = [1, 2, 5]
        self.speed_changed.emit(speeds[index])

    def update_progress(self, progress: float) -> None:
        """Update the day progress bar."""
        self.progress_bar.setValue(int(progress * 100))

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable jump buttons during background computation."""
        self.jump_open_btn.setEnabled(enabled)
        self.jump_midday_btn.setEnabled(enabled)
        self.jump_next_day_btn.setEnabled(enabled)


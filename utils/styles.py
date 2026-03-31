from __future__ import annotations


DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #2b2b2b;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QPushButton {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 5px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border: 1px solid #5a5a5a;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

QPushButton:disabled {
    background-color: #3a3a3a;
    color: #666666;
    border: 1px solid #444444;
}

QComboBox {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 4px;
}

QComboBox:hover {
    border: 1px solid #5a5a5a;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    color: #ffffff;
    selection-background-color: #1a5f1a;
}

QSpinBox {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 4px;
}

QProgressBar {
    background-color: #3a3a3a;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #1a5f1a;
    border-radius: 3px;
}

QDialog {
    background-color: #2b2b2b;
}

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

QStatusBar {
    background-color: #3a3a3a;
    color: #ffffff;
}

QSplitter::handle {
    background-color: #4a4a4a;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from PySide6.QtCharts import QCandlestickSeries, QCandlestickSet, QChart, QChartView, QDateTimeAxis, QValueAxis
from PySide6.QtCore import Qt, QDateTime, QMargins
from PySide6.QtGui import QColor, QPainter

from utils.types import OHLCBar


class DailyChartWidget(QChartView):

    def __init__(self):
        self._chart = QChart()
        self._chart.setTitle("Daily Chart")
        self._chart.setBackgroundBrush(QColor("#2b2b2b"))
        self._chart.setTitleBrush(QColor("#ffffff"))
        self._chart.setMargins(QMargins(5, 5, 5, 5))

        super().__init__(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRubberBand(QChartView.RubberBand.RectangleRubberBand)

        self._series: QCandlestickSeries | None = None
        self._x_axis: QDateTimeAxis | None = None
        self._y_axis: QValueAxis | None = None

        self._setup_series()

    def _setup_series(self) -> None:
        self._series = QCandlestickSeries()
        self._series.setIncreasingColor(QColor("#4CAF50"))
        self._series.setDecreasingColor(QColor("#F44336"))
        self._series.setBodyWidth(0.8)

        self._chart.addSeries(self._series)

        self._x_axis = QDateTimeAxis()
        self._x_axis.setFormat("MM/dd")
        self._x_axis.setTitleText("Date")
        self._x_axis.setLabelsColor(QColor("#ffffff"))
        self._x_axis.setGridLineColor(QColor("#4a4a4a"))
        self._x_axis.setLabelsAngle(-45)
        self._x_axis.setTitleVisible(False)

        self._y_axis = QValueAxis()
        self._y_axis.setTitleText("Price ($)")
        self._y_axis.setLabelsColor(QColor("#ffffff"))
        self._y_axis.setGridLineColor(QColor("#4a4a4a"))
        self._y_axis.setTitleVisible(False)
        self._y_axis.setLabelFormat("%.2f")

        self._chart.addAxis(self._x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)

        self._series.attachAxis(self._x_axis)
        self._series.attachAxis(self._y_axis)

        self._chart.legend().setVisible(False)

    def update_data(self, bars: List[OHLCBar], current_bar: OHLCBar | None = None) -> None:
        if not bars and not current_bar:
            return

        if self._series is None:
            return

        self._series.clear()

        min_price = float('inf')
        max_price = float('-inf')

        all_bars = bars.copy()
        if current_bar:
            all_bars.append(current_bar)

        for bar in all_bars:
            candle = QCandlestickSet(bar.open, bar.high, bar.low, bar.close)
            candle.setTimestamp(QDateTime(bar.timestamp).toMSecsSinceEpoch())
            self._series.append(candle)

            min_price = min(min_price, bar.low)
            max_price = max(max_price, bar.high)

        if all_bars:
            first_time = QDateTime(all_bars[0].timestamp)
            last_time = QDateTime(all_bars[-1].timestamp)

            self._x_axis.setRange(first_time, last_time)

            padding = (max_price - min_price) * 0.1
            self._y_axis.setRange(min_price - padding, max_price + padding)

    def clear(self) -> None:
        if self._series:
            self._series.clear()

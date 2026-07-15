# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Various custom UI components.
"""
import pyqtgraph as pg
from pyqtgraph.Qt.QtCore import QRect, Qt, Signal, QPoint
from pyqtgraph.Qt.QtGui import QPainter, QBrush, QPalette, QPen, QColor
from pyqtgraph.Qt.QtWidgets import QRubberBand, QWidget, QSizePolicy

class TransparentRubberBand(QRubberBand):
    def __init__(self, shape, parent):
        QRubberBand.__init__(self, shape, parent)

    def paintEvent(self, event):
        pal = QPalette()
        pal.setBrush(QPalette.ColorRole.Highlight, QBrush(Qt.GlobalColor.black))
        self.setPalette(pal)
        pen = QPen()
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setColor(Qt.GlobalColor.darkGreen)
        pen.setWidth(2)
        painter = QPainter(self)
        painter.setOpacity(1)
        painter.setPen(pen)
        rectangle = QRubberBand.geometry(self)
        rectangle2 = QRect(0,0,rectangle.width()-1, rectangle.height()-1)
        painter.drawRect(rectangle2)
        painter.end()

class RoiMidLines(QWidget):
    def __init__(self, xleft, yleft, xtop, ytop, parent=None):
        QWidget.__init__(self, parent)
        self.xleft = int(xleft)
        self.yleft = int(yleft)
        self.xtop = int(xtop)
        self.ytop = int(ytop)

    def paintEvent(self, event):
        pal = QPalette()
        pal.setBrush(QPalette.ColorRole.Highlight, QBrush(Qt.GlobalColor.black))
        self.setPalette(pal)
        pen = QPen()
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setColor(Qt.GlobalColor.darkGreen)
        pen.setWidth(2)
        painter = QPainter(self)
        painter.setPen(pen)
        painter.drawLine(0, self.yleft, self.xleft, self.yleft)
        painter.drawLine(self.xtop, 0, self.xtop, self.ytop)
        painter.end()


class RangeSlider(QWidget):
    """
    A horizontal slider with two handles defining a [lower, upper] range,
    used to set the image black (lower) and white (upper) levels on a single
    bar. Values are floats and the handles cannot cross
    (minimum <= lower <= upper <= maximum).

    A subset of the QSlider/QAbstractSlider API is mirrored so this can be
    wired like the QSliders it replaces.
    """

    lowerValueChanged = Signal(float)
    upperValueChanged = Signal(float)

    HANDLE_RADIUS = 7
    GROOVE_HEIGHT = 6

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._minimum = 0.0
        self._maximum = 1.0
        self._lower = 0.0
        self._upper = 1.0
        self._active = None  # 'lower', 'upper' or None while not dragging
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(2 * self.HANDLE_RADIUS + 6)
        self.setMinimumWidth(6 * self.HANDLE_RADIUS)

    # ---- QSlider-like API ---------------------------------------------------
    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def setMinimum(self, value):
        self.setRange(value, self._maximum)

    def setMaximum(self, value):
        self.setRange(self._minimum, value)

    def setRange(self, minimum, maximum):
        minimum = float(minimum)
        maximum = float(maximum)
        if maximum < minimum:
            maximum = minimum
        self._minimum = minimum
        self._maximum = maximum
        # Re-clamp current values into the (possibly new) range.
        self._lower = min(max(self._lower, minimum), maximum)
        self._upper = min(max(self._upper, minimum), maximum)
        if self._upper < self._lower:
            self._upper = self._lower
        self.update()

    def lowerValue(self):
        return self._lower

    def upperValue(self):
        return self._upper

    def setLowerValue(self, value):
        value = min(max(float(value), self._minimum), self._maximum)
        if value > self._upper:
            value = self._upper
        if value != self._lower:
            self._lower = value
            self.update()
            self.lowerValueChanged.emit(self._lower)

    def setUpperValue(self, value):
        value = min(max(float(value), self._minimum), self._maximum)
        if value < self._lower:
            value = self._lower
        if value != self._upper:
            self._upper = value
            self.update()
            self.upperValueChanged.emit(self._upper)

    # ---- geometry helpers ---------------------------------------------------
    def _track_rect(self):
        # Inset by the handle radius so handles stay fully inside the widget.
        r = self.HANDLE_RADIUS
        return QRect(r, 0, max(1, self.width() - 2 * r), self.height())

    def _value_to_x(self, value):
        track = self._track_rect()
        span = self._maximum - self._minimum
        frac = 0.0 if span <= 0 else (value - self._minimum) / span
        return track.left() + frac * track.width()

    def _x_to_value(self, x):
        track = self._track_rect()
        if track.width() <= 0:
            return self._minimum
        frac = min(max((x - track.left()) / track.width(), 0.0), 1.0)
        return self._minimum + frac * (self._maximum - self._minimum)

    # ---- painting -----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cy = self.height() // 2
        top = cy - self.GROOVE_HEIGHT // 2

        x_low = self._value_to_x(self._lower)
        x_high = self._value_to_x(self._upper)
        track = self._track_rect()

        # Groove
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRoundedRect(QRect(track.left(), top, track.width(), self.GROOVE_HEIGHT), 2, 2)

        # Selected span between the two handles
        painter.setBrush(QBrush(QColor(70, 130, 220)))
        painter.drawRoundedRect(QRect(int(x_low), top, int(x_high - x_low), self.GROOVE_HEIGHT), 2, 2)

        # Handles
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.setBrush(QBrush(QColor(235, 235, 235)))
        for x in (x_low, x_high):
            painter.drawEllipse(QPoint(int(x), cy), self.HANDLE_RADIUS, self.HANDLE_RADIUS)
        painter.end()

    # ---- mouse interaction --------------------------------------------------
    def _event_x(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        return pos.x()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = self._event_x(event)
        x_low = self._value_to_x(self._lower)
        x_high = self._value_to_x(self._upper)
        if x_low == x_high:
            # Handles overlap: pick the one the drag pulls away from.
            self._active = 'upper' if x >= x_low else 'lower'
        elif abs(x - x_low) <= abs(x - x_high):
            self._active = 'lower'
        else:
            self._active = 'upper'
        self._move_active_to(x)

    def mouseMoveEvent(self, event):
        if self._active is not None:
            self._move_active_to(self._event_x(event))

    def mouseReleaseEvent(self, event):
        self._active = None

    def _move_active_to(self, x):
        value = self._x_to_value(x)
        if self._active == 'lower':
            self.setLowerValue(value)
        elif self._active == 'upper':
            self.setUpperValue(value)

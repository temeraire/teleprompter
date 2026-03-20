#!/usr/bin/env python3
"""
Teleprompter — a frameless, always-on-top scrolling text window
positioned at the top-center of the screen, near the Mac camera.
A separate control panel sits to the right.
Settings persist between sessions.
"""

import json
import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QSlider, QFileDialog, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


WINDOW_WIDTH = 210
WINDOW_HEIGHT = 150
CLOSE_BAR_HEIGHT = 30
TOTAL_HEIGHT = WINDOW_HEIGHT + CLOSE_BAR_HEIGHT
TEXT_MARGIN = 12
PANEL_WIDTH = 70
PANEL_GAP = 4

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)

DEFAULTS = {
    "font_size": 24,
    "scroll_speed": 0.5,
}

BUTTON_STYLE = """
    QPushButton {
        color: #ccc;
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px;
        font-size: 18px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #555;
        color: white;
    }
"""


def load_settings():
    try:
        with open(SETTINGS_PATH, "r") as f:
            saved = json.load(f)
        # Merge with defaults in case new keys are added
        settings = dict(DEFAULTS)
        settings.update(saved)
        return settings
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)


def save_settings(font_size, scroll_speed):
    with open(SETTINGS_PATH, "w") as f:
        json.dump({"font_size": font_size, "scroll_speed": scroll_speed}, f)


class ControlPanel(QWidget):
    """Narrow panel to the right of the teleprompter with speed and font controls."""

    def __init__(self, teleprompter):
        super().__init__()
        self.tp = teleprompter

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color: #1a1a1a;")
        # Position to the right of the teleprompter
        tp_geo = self.tp.geometry()
        x = tp_geo.x() + tp_geo.width() + PANEL_GAP
        y = tp_geo.y()
        self.setGeometry(x, y, PANEL_WIDTH, TOTAL_HEIGHT)

        self._setup_ui()

    def _setup_ui(self):
        btn_h = 26
        btn_w = PANEL_WIDTH - 8
        x = 4
        cur_y = 4

        # Speed label
        speed_label = QLabel("Speed", self)
        speed_label.setStyleSheet("color: #ddd; font-size: 11px;")
        speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        speed_label.setGeometry(x, cur_y, btn_w, 14)
        cur_y += 16

        # Speed +
        self.speed_up = QPushButton("+", self)
        self.speed_up.setGeometry(x, cur_y, btn_w, btn_h)
        self.speed_up.setStyleSheet(BUTTON_STYLE)
        self.speed_up.clicked.connect(self._speed_up)
        cur_y += btn_h + 2

        # Speed -
        self.speed_down = QPushButton("−", self)
        self.speed_down.setGeometry(x, cur_y, btn_w, btn_h)
        self.speed_down.setStyleSheet(BUTTON_STYLE)
        self.speed_down.clicked.connect(self._speed_down)
        cur_y += btn_h + 8

        # Font label
        font_label = QLabel("Font", self)
        font_label.setStyleSheet("color: #ddd; font-size: 11px;")
        font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_label.setGeometry(x, cur_y, btn_w, 14)
        cur_y += 16

        # Font +
        self.font_up = QPushButton("ᴛT ↑", self)
        self.font_up.setGeometry(x, cur_y, btn_w, btn_h)
        self.font_up.setStyleSheet(BUTTON_STYLE)
        self.font_up.clicked.connect(self._font_up)
        cur_y += btn_h + 2

        # Font -
        self.font_down = QPushButton("Tᴛ ↓", self)
        self.font_down.setGeometry(x, cur_y, btn_w, btn_h)
        self.font_down.setStyleSheet(BUTTON_STYLE)
        self.font_down.clicked.connect(self._font_down)

    def _speed_up(self):
        self.tp.scroll_speed = min(self.tp.scroll_speed + 0.15, 5.0)
        save_settings(self.tp.font_size, self.tp.scroll_speed)

    def _speed_down(self):
        self.tp.scroll_speed = max(self.tp.scroll_speed - 0.15, 0.1)
        save_settings(self.tp.font_size, self.tp.scroll_speed)

    def _font_up(self):
        self.tp.font_size = min(self.tp.font_size + 2, 60)
        self.tp._update_font()
        save_settings(self.tp.font_size, self.tp.scroll_speed)

    def _font_down(self):
        self.tp.font_size = max(self.tp.font_size - 2, 16)
        self.tp._update_font()
        save_settings(self.tp.font_size, self.tp.scroll_speed)


class Teleprompter(QWidget):
    def __init__(self, text: str, settings: dict):
        super().__init__()
        self.text = text
        self.started = False
        self.scrolling = False
        self.scroll_offset = 0.0
        self.scroll_speed = settings["scroll_speed"]
        self.font_size = settings["font_size"]

        self._setup_window()
        self._setup_ui()
        self._setup_timer()

    def _setup_window(self):
        """Frameless, always-on-top, black background, positioned at top-center."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color: black;")

        # Center the teleprompter + panel combo horizontally
        screen = QApplication.primaryScreen().availableGeometry()
        total_width = WINDOW_WIDTH + PANEL_GAP + PANEL_WIDTH
        x = (screen.width() - total_width) // 2
        y = screen.y()
        self.setGeometry(x, y, WINDOW_WIDTH, TOTAL_HEIGHT)

    def _setup_ui(self):
        """Text label, scrollbar, and close button."""
        text_width = WINDOW_WIDTH - TEXT_MARGIN * 2

        # Clipping container — confines the label so it can't overlap the close button
        self.text_container = QWidget(self)
        self.text_container.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.text_container.setStyleSheet("background-color: black;")

        # Scrolling text label (child of container, not of self)
        self.label = QLabel(self.text, self.text_container)
        self.label.setFont(QFont("Helvetica Neue", self.font_size))
        self.label.setStyleSheet("color: white; background-color: black;")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.label.setFixedWidth(text_width)
        self.label.adjustSize()

        # Scrollbar to manually scrub through text position
        self.scrollbar = QSlider(Qt.Orientation.Vertical, self)
        self.scrollbar.setMinimum(0)
        self._update_scrollbar_range()
        self.scrollbar.setValue(0)
        self.scrollbar.setGeometry(WINDOW_WIDTH - 14, 0, 14, WINDOW_HEIGHT)
        self.scrollbar.setStyleSheet("""
            QSlider::groove:vertical {
                background: #222;
                width: 8px;
                border-radius: 4px;
            }
            QSlider::handle:vertical {
                background: #666;
                height: 20px;
                margin: 0 -3px;
                border-radius: 4px;
            }
        """)
        self.scrollbar.setInvertedAppearance(True)
        self.scrollbar.valueChanged.connect(self._scrollbar_moved)
        self._scrollbar_updating = False

        # Close button below the text area
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(0, WINDOW_HEIGHT, WINDOW_WIDTH, CLOSE_BAR_HEIGHT)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: #ccc;
                background-color: #222;
                border: none;
                border-top: 1px solid #444;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #444;
                color: white;
            }
        """)
        self.close_btn.clicked.connect(QApplication.quit)
        self.close_btn.raise_()

        # "Click to begin" overlay
        self.start_label = QLabel("Click to begin", self)
        self.start_label.setFont(QFont("Helvetica Neue", 18))
        self.start_label.setStyleSheet("color: #aaa; background-color: black;")
        self.start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_label.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.start_label.raise_()

        # Start with text just below the visible window
        self._reset_position()

    def _update_scrollbar_range(self):
        """Set scrollbar range based on total text height."""
        max_scroll = self.label.height() + WINDOW_HEIGHT
        self.scrollbar.setMaximum(max_scroll)

    def _scrollbar_moved(self, value):
        """User dragged the scrollbar — jump to that position."""
        if self._scrollbar_updating:
            return
        self.scroll_offset = float(value)
        new_y = WINDOW_HEIGHT - self.scroll_offset
        self.label.move(TEXT_MARGIN, int(new_y))

    def _reset_position(self):
        """Reset text to starting position (just below visible area)."""
        self.scroll_offset = 0.0
        self.label.move(TEXT_MARGIN, WINDOW_HEIGHT)
        self._scrollbar_updating = True
        self.scrollbar.setValue(0)
        self._scrollbar_updating = False

    def _update_font(self):
        """Update font size and re-layout the label."""
        self.label.setFont(QFont("Helvetica Neue", self.font_size))
        self.label.adjustSize()
        self._update_scrollbar_range()
        new_y = WINDOW_HEIGHT - self.scroll_offset
        self.label.move(TEXT_MARGIN, int(new_y))

    def _setup_timer(self):
        """Timer drives the smooth scroll."""
        self.timer = QTimer(self)
        self.timer.setInterval(30)  # ~33 fps
        self.timer.timeout.connect(self._tick)

    def _tick(self):
        """Move the label upward by scroll_speed pixels."""
        self.scroll_offset += self.scroll_speed
        new_y = WINDOW_HEIGHT - self.scroll_offset

        # When last line scrolls past the top, loop back to beginning
        if new_y + self.label.height() < 0:
            self._reset_position()
            return

        self.label.move(TEXT_MARGIN, int(new_y))

        # Sync scrollbar to current position
        self._scrollbar_updating = True
        self.scrollbar.setValue(int(self.scroll_offset))
        self._scrollbar_updating = False

    def mousePressEvent(self, event):
        """Click anywhere on the text area to toggle start/stop."""
        click_x = int(event.position().x())
        click_y = int(event.position().y())
        # Ignore clicks on the scrollbar area
        if click_x >= WINDOW_WIDTH - 20:
            return
        # Ignore clicks on the close button area
        if click_y >= WINDOW_HEIGHT:
            return

        # First click: dismiss "Click to begin" and start scrolling
        if not self.started:
            self.started = True
            self.start_label.hide()
            self.scrolling = True
            self.timer.start()
            return

        if self.scrolling:
            self.scrolling = False
            self.timer.stop()
        else:
            self.scrolling = True
            self.timer.start()

    def keyPressEvent(self, event):
        """Escape to quit."""
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)

    # Open file picker
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select your script",
        "",
        "Text files (*.txt);;All files (*)"
    )
    if not file_path:
        sys.exit(0)

    with open(file_path, "r") as f:
        text = f.read().strip()

    if not text:
        sys.exit(0)

    settings = load_settings()

    window = Teleprompter(text, settings)
    window.show()

    panel = ControlPanel(window)
    panel.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

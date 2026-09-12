"""Run the desktop application with `uv run eve-wormhole`."""

import sys

from PySide6.QtWidgets import QApplication

from eve_wormhole.window import BookmarkWindow

STYLESHEET = """
QWidget {
    background: #12191e;
    color: #e1e7eb;
    font-family: "DejaVu Sans", sans-serif;
    font-size: 12px;
    font-style: normal;
}
QLabel { background: transparent; }
QLabel#heading { font-size: 23px; font-weight: 600; }
QLabel#muted { color: #94a7b2; font-size: 11px; }
QPlainTextEdit, QLineEdit, QComboBox {
    background: #1b252d;
    border: 1px solid #354652;
    border-radius: 5px;
    padding: 7px;
    selection-background-color: #346960;
}
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus { border-color: #8dd8b8; }
QLineEdit[conflict="true"], QComboBox[conflict="true"] { border-color: #e7ac74; }
QComboBox QAbstractItemView { background: #1b252d; selection-background-color: #346960; }
QPushButton {
    background: #24323c;
    border: 1px solid #3d5361;
    border-radius: 5px;
    padding: 8px 13px;
}
QPushButton:hover { background: #314652; }
QPushButton:focus { border-color: #8dd8b8; }
QPushButton#primaryButton { background: #8dd8b8; color: #101c18; font-weight: 600; }
QPushButton#primaryButton:hover { background: #a8e6cc; }
QPushButton:disabled, QPushButton#primaryButton:disabled {
    background: #1f2b33; color: #768a97; border-color: #2e3e49;
}
QFrame#previewCard { background: #0c1216; border: 1px solid #354652; border-radius: 7px; }
QLabel#preview { font-family: "DejaVu Sans Mono", monospace; font-size: 17px; }
QLabel#feedback { color: #e7ac74; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator:unchecked { border: 1px solid #718794; border-radius: 2px; background: #1b252d; }
"""


def configure_app(app: QApplication) -> None:
    app.setApplicationName("eve-wormhole")
    app.setApplicationDisplayName("Wormhole bookmarks")
    app.setDesktopFileName("eve-wormhole")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)


def main() -> None:
    app = QApplication(sys.argv)
    configure_app(app)
    window = BookmarkWindow()
    window.show()
    sys.exit(app.exec())

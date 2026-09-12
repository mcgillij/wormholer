"""The floating bookmark editor and explicit clipboard interactions."""

from html import escape

from PySide6.QtCore import QEvent, QMimeData, Qt, Signal
from PySide6.QtGui import QClipboard, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eve_wormhole.models import DIRECTIONS, LIFETIMES, MASSES, SIZES, SPACE_TYPES
from eve_wormhole.state import BookmarkState

FIELD_LABELS = {
    "signature": "Signature",
    "wormhole_type": "Wormhole type",
    "space_type": "Destination class",
    "direction": "Direction",
    "size": "Ship size",
    "destination": "Destination name / label",
    "lifetime": "Lifetime",
    "mass": "Mass stability",
}


class PasteEdit(QPlainTextEdit):
    pasted = Signal(str)

    def insertFromMimeData(self, source: QMimeData) -> None:
        if source.hasText():
            text = source.text()
            self.setPlainText(text)
            self.pasted.emit(text)


class BookmarkWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state = BookmarkState()
        self.last_copied: str | None = None
        self._clipboard_error = ""
        self._editing_fields: set[str] = set()
        self.setWindowTitle("Wormhole bookmarks")
        self.setObjectName("bookmarkWindow")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.resize(520, 730)
        self.setMinimumWidth(420)
        self.inputs: dict[str, QLineEdit | QComboBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        heading = QLabel("Wormhole bookmarks")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        subtitle = QLabel("Paste EVE information, then fill in what's missing.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        self.paste_edit = PasteEdit()
        self.paste_edit.setObjectName("pasteInput")
        self.paste_edit.setAccessibleName("Paste wormhole information")
        self.paste_edit.setPlaceholderText(
            "Paste wormhole info here · Ctrl+V\n"
            "You can also paste a signature, K162, or a J-number."
        )
        self.paste_edit.setMinimumHeight(100)
        self.paste_edit.setMaximumHeight(150)
        self.paste_edit.pasted.connect(self.receive_paste)
        layout.addWidget(self.paste_edit)

        source_actions = QHBoxLayout()
        use_text = QPushButton("Parse edited text")
        use_text.clicked.connect(
            lambda: self.receive_paste(self.paste_edit.toPlainText())
        )
        source_actions.addWidget(use_text)
        source_actions.addStretch()
        self.new_button = QPushButton("New hole")
        self.new_button.setToolTip(
            "Clear this wormhole without changing the clipboard (Ctrl+N)."
        )
        self.new_button.clicked.connect(self.new_hole)
        source_actions.addWidget(self.new_button)
        layout.addLayout(source_actions)

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(7)
        for index, field in enumerate(FIELD_LABELS):
            if field in ("signature", "wormhole_type", "destination"):
                widget = QLineEdit()
                widget.setPlaceholderText(
                    {
                        "signature": "YRU-123",
                        "wormhole_type": "K162 (optional)",
                        "destination": "J123456, 533, or a system name",
                    }[field]
                )
                widget.textEdited.connect(
                    lambda text, key=field: self._draft(key, text)
                )
                widget.editingFinished.connect(lambda key=field: self._commit_edit(key))
            else:
                widget = QComboBox()
                if field == "space_type":
                    options = dict.fromkeys(SPACE_TYPES)
                    options = {key: key for key in options}
                else:
                    options = {
                        "direction": DIRECTIONS,
                        "size": SIZES,
                        "lifetime": LIFETIMES,
                        "mass": MASSES,
                    }[field]
                if field != "direction":
                    widget.addItem(
                        "Choose…", None if field in ("lifetime", "mass") else ""
                    )
                for value, name in options.items():
                    label = (
                        name
                        if field in ("space_type", "lifetime", "mass")
                        else f"{value} · {name}"
                    )
                    widget.addItem(label, value)
                widget.currentIndexChanged.connect(
                    lambda _index, key=field: self._select(key)
                )
            widget.setObjectName(field)
            widget.setAccessibleName(FIELD_LABELS[field])
            self.inputs[field] = widget
            label = QLabel(FIELD_LABELS[field])
            label.setBuddy(widget)
            row, column = divmod(index, 2)
            form.addWidget(label, row * 2, column)
            form.addWidget(widget, row * 2 + 1, column)
        layout.addLayout(form)

        self.candidate_label = QLabel()
        self.candidate_label.setObjectName("muted")
        self.candidate_label.setWordWrap(True)
        layout.addWidget(self.candidate_label)

        options_row = QHBoxLayout()
        self.home_check = QCheckBox("Leads home (--)")
        self.home_check.toggled.connect(self._home_changed)
        options_row.addWidget(self.home_check)
        options_row.addStretch()
        self.auto_copy = QCheckBox("Auto-copy")
        self.auto_copy.setChecked(True)
        self.auto_copy.toggled.connect(self._auto_copy_changed)
        options_row.addWidget(self.auto_copy)
        layout.addLayout(options_row)

        card = QFrame()
        card.setObjectName("previewCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        caption = QLabel("BOOKMARK PREVIEW")
        caption.setObjectName("muted")
        card_layout.addWidget(caption)
        self.preview = QLabel()
        self.preview.setObjectName("preview")
        self.preview.setTextFormat(Qt.TextFormat.RichText)
        self.preview.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(35)
        card_layout.addWidget(self.preview)
        layout.addWidget(card)

        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.feedback = QLabel()
        self.feedback.setObjectName("feedback")
        self.feedback.setTextFormat(Qt.TextFormat.PlainText)
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

        actions = QHBoxLayout()
        self.keep_button = QPushButton("Keep my values")
        self.keep_button.clicked.connect(self._keep_manual)
        actions.addWidget(self.keep_button)
        actions.addStretch()
        self.copy_button = QPushButton("Copy bookmark")
        self.copy_button.setObjectName("primaryButton")
        self.copy_button.clicked.connect(self.copy_bookmark)
        actions.addWidget(self.copy_button)
        layout.addLayout(actions)

        self.new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_shortcut.activated.connect(self.new_hole)
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self._clipboard_changed)
        self._refresh()
        self.paste_edit.setFocus()

    def receive_paste(self, text: str) -> None:
        self._editing_fields.clear()
        self._clipboard_error = ""
        accepted = self.state.paste(text)
        self.last_copied = None
        self._refresh(copy=accepted)

    def _draft(self, field: str, value: str) -> None:
        self._editing_fields.add(field)
        self._clipboard_error = ""
        self.state.set_manual(field, value)
        # Copy during the input event, while the helper still has keyboard focus.
        self._refresh(copy=True, sync_inputs=False)

    def _commit_edit(self, field: str) -> None:
        if field not in self._editing_fields:
            return
        self._editing_fields.discard(field)
        # The edit was already applied and copied by textEdited. Normalizing the
        # displayed value on focus-out must not overwrite a newer clipboard item.
        self._refresh()

    def _auto_copy_changed(self, checked: bool) -> None:
        self._clipboard_error = ""
        self._refresh(copy=checked, sync_inputs=False)

    def _select(self, field: str) -> None:
        self.state.set_manual(field, self.inputs[field].currentData())
        self._refresh(copy=True)

    def _home_changed(self, checked: bool) -> None:
        self.state.set_manual("home", checked)
        self._refresh(copy=True)

    def _keep_manual(self) -> None:
        self.state.keep_manual_values()
        self._refresh(copy=True)

    def new_hole(self) -> None:
        self._editing_fields.clear()
        self._clipboard_error = ""
        self.state.reset()
        self.last_copied = None
        self.paste_edit.clear()
        self._refresh()
        self.paste_edit.setFocus()

    def copy_bookmark(self) -> None:
        if bookmark := self.state.bookmark:
            self.last_copied = None
            self._clipboard_error = ""
            if (
                QApplication.platformName().startswith("wayland")
                and not self.isActiveWindow()
            ):
                self._clipboard_error = "Could not copy while the helper was unfocused. Click Copy bookmark."
            else:
                self.clipboard.setText(bookmark, QClipboard.Mode.Clipboard)
                if self.clipboard.text(QClipboard.Mode.Clipboard) == bookmark:
                    self.last_copied = bookmark
                else:
                    self._clipboard_error = (
                        "Could not update the clipboard. Click Copy bookmark to retry."
                    )
            self._refresh(sync_inputs=False)

    def _clipboard_changed(self) -> None:
        # Clipboard changes affect the badge only; they never feed the parser.
        if self.last_copied and self.clipboard.text() != self.last_copied:
            self.last_copied = None
            self._refresh(sync_inputs=False)

    def _refresh(self, *, copy: bool = False, sync_inputs: bool = True) -> None:
        record = self.state.record
        errors = self.state.errors
        if sync_inputs:
            for field, widget in self.inputs.items():
                widget.blockSignals(True)
                value = getattr(record, field)
                if isinstance(widget, QLineEdit):
                    widget.setText(value)
                else:
                    widget.setCurrentIndex(widget.findData(value))
                widget.blockSignals(False)
            self.home_check.blockSignals(True)
            self.home_check.setChecked(record.home)
            self.home_check.blockSignals(False)
        for field, widget in self.inputs.items():
            widget.setToolTip(errors.get(field, ""))
            widget.setProperty(
                "conflict", field in self.state.conflicts or field in self.state.issues
            )
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        candidates = " / ".join(self.state.candidates)
        self.candidate_label.setText(
            f"Destination reported by EVE: {candidates}" if candidates else ""
        )
        self.candidate_label.setVisible(bool(candidates))

        def colored(value: str, color: str) -> str:
            return f'<span style="color: {color}">{escape(value)}</span>'

        preview = (
            colored("--" if record.home else "-", "#d9d96b")
            + colored(record.signature[:3] or "SIG", "#84dc93")
            + " "
            + colored(
                f"{record.space_type or 'C?'}{record.direction}{record.size or '?'}",
                "#fa9292",
            )
            + " "
            + colored(record.destination or "destination", "#73d5e7")
        )
        flags = " ".join(flag for flag in (record.lifetime, record.mass) if flag)
        if flags:
            preview += " " + colored(flags, "#dca0ef")
        self.preview.setText(preview)
        bookmark = self.state.bookmark
        if self.last_copied != bookmark:
            self.last_copied = None
        self.copy_button.setEnabled(bookmark is not None)
        if errors:
            names = [FIELD_LABELS.get(field, field).lower() for field in errors]
            self.status.setText("Not copied: needs " + ", ".join(names))
        else:
            self.status.setText(
                "Copied · ready to paste in EVE"
                if self.last_copied
                else "Ready to copy"
            )
        details = list(self.state.conflicts.values()) + list(self.state.issues.values())
        self.feedback.setText(
            self._clipboard_error
            or self.state.message
            or "\n".join(dict.fromkeys(details))
        )
        self.feedback.setVisible(bool(self.feedback.text()))
        self.keep_button.setVisible(
            bool(
                self.state.conflicts
                or self.state.manual_fields.intersection(self.state.issues)
            )
        )
        if copy and bookmark and self.auto_copy.isChecked():
            self.copy_bookmark()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if (
            event.type() == QEvent.Type.ActivationChange
            and self.isActiveWindow()
            and hasattr(self, "paste_edit")
        ):
            self.paste_edit.setFocus()

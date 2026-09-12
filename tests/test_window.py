from copy import deepcopy

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from eve_wormhole.app import configure_app
from eve_wormhole.window import BookmarkWindow


@pytest.fixture
def window(qtbot, qapp):
    assert qapp.platformName() == "offscreen", (
        "GUI tests must not use the desktop clipboard"
    )
    configure_app(qapp)
    widget = BookmarkWindow()
    qtbot.addWidget(widget)
    widget.show()
    qapp.processEvents()
    widget.clipboard.clear()
    return widget


def paste(qtbot, window, text):
    window.clipboard.setText(text)
    window.paste_edit.setFocus()
    qtbot.keyClick(window.paste_edit, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)


def fill(qtbot, window, sample, *, commit=True):
    paste(qtbot, window, sample)
    assert window.clipboard.text() == sample
    assert not window.copy_button.isEnabled()
    paste(qtbot, window, "Wormhole K162")
    paste(qtbot, window, "YRU-123")
    space_type = window.inputs["space_type"]
    space_type.setCurrentIndex(space_type.findData("C2"))
    destination = window.inputs["destination"]
    destination.setFocus()
    qtbot.keyClicks(destination, "533")
    expected = "-YRU C2iL 533 EOL" if window.auto_copy.isChecked() else "YRU-123"
    assert window.clipboard.text() == expected
    if commit:
        qtbot.keyClick(destination, Qt.Key.Key_Tab)


def test_paste_fill_and_auto_copy(qtbot, window, sample):
    fill(qtbot, window, sample)
    assert window.clipboard.text() == "-YRU C2iL 533 EOL"
    assert window.copy_button.isEnabled()
    assert window.status.text() == "Copied · ready to paste in EVE"
    assert window.paste_edit.toPlainText() == "YRU-123"


def test_captured_descriptions_copy_after_missing_fields_are_filled(
    qtbot, window, description_variant
):
    source, candidates, size, lifetime = description_variant
    paste(qtbot, window, source)
    assert not window.state.issues
    assert not window.copy_button.isEnabled()
    assert window.clipboard.text() == source
    paste(qtbot, window, "Wormhole K162")
    paste(qtbot, window, "YRU-123")
    if len(candidates) > 1:
        space_type = window.inputs["space_type"]
        space_type.setCurrentIndex(space_type.findData(candidates[0]))
    assert not window.copy_button.isEnabled()
    destination = window.inputs["destination"]
    destination.setFocus()
    qtbot.keyClicks(destination, "533")
    expected = f"-YRU {candidates[0]}i{size} 533"
    if lifetime:
        expected += f" {lifetime}"
    assert window.clipboard.text() == expected
    assert window.copy_button.isEnabled()
    assert window.status.text() == "Copied · ready to paste in EVE"


def test_last_text_field_copies_without_tab_or_focus_change(qtbot, window, sample):
    fill(qtbot, window, sample, commit=False)
    assert window.inputs["destination"].hasFocus()
    assert window.clipboard.text() == "-YRU C2iL 533 EOL"
    assert window.last_copied == window.state.bookmark


def test_enabling_auto_copy_copies_an_already_complete_record(qtbot, window, sample):
    window.auto_copy.setChecked(False)
    fill(qtbot, window, sample)
    window.auto_copy.setChecked(True)
    assert window.clipboard.text() == "-YRU C2iL 533 EOL"


def test_failed_clipboard_write_does_not_claim_success(
    qtbot, window, sample, monkeypatch
):
    window.auto_copy.setChecked(False)
    fill(qtbot, window, sample)
    monkeypatch.setattr(window.clipboard, "setText", lambda *_args: None)
    window.copy_bookmark()
    assert window.last_copied is None
    assert "could not" in window.feedback.text().lower()


def test_leaving_field_does_not_recopy_over_new_clipboard_contents(
    qtbot, window, sample
):
    fill(qtbot, window, sample, commit=False)
    window.clipboard.setText("new clipboard contents")
    qtbot.keyClick(window.inputs["destination"], Qt.Key.Key_Tab)
    assert window.clipboard.text() == "new clipboard contents"
    assert window.last_copied is None


def test_incomplete_edits_are_not_copied(qtbot, window, sample):
    fill(qtbot, window, sample, commit=False)
    destination = window.inputs["destination"]
    destination.selectAll()
    qtbot.keyClick(destination, Qt.Key.Key_Backspace)
    assert window.clipboard.text() == "-YRU C2iL 533 EOL"
    assert not window.copy_button.isEnabled()
    assert window.last_copied is None
    assert window.status.text().startswith("Not copied:")


def test_other_window_can_paste_without_committing_the_final_field(
    qtbot, window, sample
):
    fill(qtbot, window, sample, commit=False)
    target = QLineEdit()
    qtbot.addWidget(target)
    target.show()
    target.activateWindow()
    target.setFocus()
    qtbot.keyClick(target, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    assert target.text() == "-YRU C2iL 533 EOL"


def test_unfocused_wayland_copy_does_not_claim_success(
    qtbot, window, sample, monkeypatch
):
    window.auto_copy.setChecked(False)
    fill(qtbot, window, sample)
    monkeypatch.setattr(QApplication, "platformName", staticmethod(lambda: "wayland"))
    monkeypatch.setattr(window, "isActiveWindow", lambda: False)
    window.copy_bookmark()
    assert window.clipboard.text() == "YRU-123"
    assert window.last_copied is None
    assert "unfocused" in window.feedback.text()


def test_clipboard_changes_never_reparse_or_recopy(qtbot, window, sample):
    fill(qtbot, window, sample)
    before = deepcopy(window.state.record)
    window.clipboard.setText("unrelated clipboard contents")
    assert window.state.record == before
    assert window.clipboard.text() == "unrelated clipboard contents"
    assert window.status.text() == "Ready to copy"


def test_auto_copy_can_be_disabled(qtbot, window, sample):
    window.auto_copy.setChecked(False)
    fill(qtbot, window, sample)
    assert window.clipboard.text() == "YRU-123"
    qtbot.mouseClick(window.copy_button, Qt.MouseButton.LeftButton)
    assert window.clipboard.text() == "-YRU C2iL 533 EOL"


def test_reset_leaves_clipboard_and_preferences_alone(qtbot, window, sample):
    fill(qtbot, window, sample)
    window.auto_copy.setChecked(False)
    window.home_check.setChecked(True)
    window.clipboard.setText("leave this alone")
    qtbot.mouseClick(window.new_button, Qt.MouseButton.LeftButton)
    assert window.clipboard.text() == "leave this alone"
    assert not window.auto_copy.isChecked()
    assert not window.home_check.isChecked()
    assert not window.copy_button.isEnabled()
    assert window.inputs["signature"].text() == ""
    assert window.paste_edit.toPlainText() == ""


def test_rejected_signature_leaves_clipboard_alone(qtbot, window, sample):
    fill(qtbot, window, sample)
    paste(qtbot, window, "ABC-456")
    assert window.clipboard.text() == "ABC-456"
    assert window.state.record.signature == "YRU-123"
    assert "New hole" in window.feedback.text()


def test_refocusing_without_editing_does_not_overwrite_new_input(qtbot, window, sample):
    fill(qtbot, window, sample)
    window.inputs["destination"].setFocus()
    paste(qtbot, window, sample.replace("More than 50%", "Less than 10%"))
    assert window.clipboard.text() == "-YRU C2iL 533 EOL CRIT"


def test_new_hole_does_not_commit_pending_text_to_clipboard(qtbot, window, sample):
    fill(qtbot, window, sample)
    destination = window.inputs["destination"]
    destination.setFocus()
    qtbot.keyClicks(destination, "4")
    window.clipboard.setText("keep me")
    qtbot.mouseClick(window.new_button, Qt.MouseButton.LeftButton)
    assert window.clipboard.text() == "keep me"


def test_conflicting_evidence_blocks_copy_until_acknowledged(qtbot, window, sample):
    fill(qtbot, window, sample)
    size = window.inputs["size"]
    size.setCurrentIndex(size.findData("M"))
    paste(qtbot, window, sample)
    assert window.clipboard.text() == sample
    assert not window.copy_button.isEnabled()
    assert window.keep_button.isVisible()
    qtbot.mouseClick(window.keep_button, Qt.MouseButton.LeftButton)
    assert window.clipboard.text() == "-YRU C2iM 533 EOL"


def test_preview_escapes_destination_markup(qtbot, window, sample):
    fill(qtbot, window, sample)
    window.state.set_manual("destination", "<b>533</b>")
    window._refresh()
    assert "&lt;b&gt;533&lt;/b&gt;" in window.preview.text()
    window.copy_bookmark()
    assert window.clipboard.text() == "-YRU C2iL <b>533</b> EOL"


def test_unknown_pasted_status_can_keep_an_existing_manual_choice(
    qtbot, window, sample
):
    fill(qtbot, window, sample)
    mass = window.inputs["mass"]
    mass.setCurrentIndex(mass.findData("DSTB"))
    paste(qtbot, window, sample.replace("More than 50% remaining", "Unfamiliar status"))
    assert not window.copy_button.isEnabled()
    assert window.keep_button.isVisible()
    qtbot.mouseClick(window.keep_button, Qt.MouseButton.LeftButton)
    assert window.clipboard.text() == "-YRU C2iL 533 EOL DSTB"

"""Tests for hotkey combo conflict detection and the action-only hotkey mode."""
import pytest

from readtome.hotkey import HotkeyManager, combos_conflict


@pytest.mark.parametrize(
    "a, b",
    [
        ("alt+shift", "shift+alt"),              # same combo, different order
        ("left alt+shift", "alt+right shift"),   # left/right variants
        ("alt+shift", "ctrl+alt+shift"),         # modifier-only subset
        ("ctrl+shift", "ctrl+shift+s"),          # modifier-only subset of key combo
    ],
)
def test_conflicting_combos(a, b):
    assert combos_conflict(a, b)
    assert combos_conflict(b, a)


@pytest.mark.parametrize(
    "a, b",
    [
        ("alt+shift", "ctrl+alt"),               # the two defaults
        ("ctrl+shift+s", "ctrl+shift+d"),        # distinct trigger keys
    ],
)
def test_non_conflicting_combos(a, b):
    assert not combos_conflict(a, b)
    assert not combos_conflict(b, a)


def test_action_only_mode_invokes_callback_without_capture():
    calls = []
    manager = HotkeyManager("ctrl+alt", lambda: calls.append("stop"), capture_text=False)
    manager._on_hotkey()
    assert calls == ["stop"]


def test_action_only_mode_suppressed_while_capturing():
    calls = []
    manager = HotkeyManager("ctrl+alt", lambda: calls.append("stop"), capture_text=False)
    manager._capturing = True
    manager._on_hotkey()
    assert calls == []

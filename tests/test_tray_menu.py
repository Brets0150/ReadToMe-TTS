"""Tests for the tray menu structure, built against a fake pystray so no
display or real tray backend is needed."""
import types

import pytest

import readtome.tray as tray_mod
from readtome.config import SENTENCE_PAUSE_PRESETS


class FakeMenuItem:
    def __init__(self, text, action=None, checked=None, enabled=True):
        self.text = text
        self.action = action
        self.checked = checked
        self.enabled = enabled


class FakeMenu:
    SEPARATOR = "---"

    def __init__(self, *items):
        self.items = items


@pytest.fixture
def tray(monkeypatch):
    monkeypatch.setattr(
        tray_mod, "pystray",
        types.SimpleNamespace(Menu=FakeMenu, MenuItem=FakeMenuItem, Icon=None),
    )
    return tray_mod.TrayIcon(
        on_quit=None,
        on_toggle_pause=None,
        on_configure_shortcut=None,
        on_configure_stop_shortcut=None,
        on_stop_speaking=None,
        on_change_voice=None,
        on_change_speed=None,
        on_change_pitch=None,
        on_change_sentence_pause=lambda v: None,
        on_change_comma_pause=lambda v: None,
        on_toggle_startup=None,
        on_check_update=None,
        is_paused=lambda: False,
        get_status=lambda: "Ready",
        get_voices=lambda: [],
        get_current_voice=lambda: "",
        get_current_speed=lambda: 1.0,
        get_current_pitch=lambda: 1.0,
        get_current_sentence_pause=lambda: 150,
        get_current_comma_pause=lambda: 100,
    )


def menu_labels(menu):
    return [
        item.text
        for item in menu.items
        if isinstance(item, FakeMenuItem) and isinstance(item.text, str)
    ]


@pytest.mark.parametrize(
    "label",
    [
        "Stop Speaking",
        "Voice",
        "Speed",
        "Pitch",
        "Sentence Pause",
        "Comma Pause",
        "Pause",
        "Configure Read Shortcut",
        "Configure Stop Shortcut",
        "Start on Login",
        "Check for Updates",
        "Quit",
    ],
)
def test_menu_contains_item(tray, label):
    assert label in menu_labels(tray._build_menu())


def test_current_pause_preset_is_checkmarked(tray):
    submenu = tray._build_pause_menu(
        SENTENCE_PAUSE_PRESETS, lambda: 150, lambda v: None
    )
    checked = [i.text for i in submenu.items if i.checked and i.checked(None)]
    assert checked == ["Normal (150 ms)"]


def test_custom_pause_value_shows_no_checkmark(tray):
    submenu = tray._build_pause_menu(
        SENTENCE_PAUSE_PRESETS, lambda: 123, lambda v: None
    )
    checked = [i.text for i in submenu.items if i.checked and i.checked(None)]
    assert checked == []


def test_pause_menu_actions_pass_preset_value(tray):
    received = []
    submenu = tray._build_pause_menu(
        SENTENCE_PAUSE_PRESETS, lambda: 150, received.append
    )
    for item in submenu.items:
        item.action(None, None)
    assert received == list(SENTENCE_PAUSE_PRESETS.values())

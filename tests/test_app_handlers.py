"""Tests for ReadToMeApp handlers: stop speaking, pause changes, and
shortcut capture with conflict rejection."""
import types

import pytest

from readtome.app import ReadToMeApp


class FakePlayer:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeTray:
    def __init__(self):
        self.tooltip = ""

    def update_tooltip(self, text):
        self.tooltip = text


class FakeConfig:
    def __init__(self):
        self.hotkey = "alt+shift"
        self.stop_hotkey = "ctrl+alt"
        self.sentence_pause_ms = 150
        self.comma_pause_ms = 100
        self.saved = False

    def save(self):
        self.saved = True


class FakeHotkeyManager:
    def __init__(self, hotkey):
        self.current_hotkey = hotkey
        self.rebound = None

    def rebind(self, hotkey):
        self.rebound = hotkey
        self.current_hotkey = hotkey


@pytest.fixture
def app(monkeypatch):
    """A ReadToMeApp with fake collaborators and no real tray/hotkeys."""
    app = ReadToMeApp.__new__(ReadToMeApp)
    app._player = FakePlayer()
    app._tray = FakeTray()
    app._config = FakeConfig()
    app._hotkey = FakeHotkeyManager("alt+shift")
    app._stop_hotkey = FakeHotkeyManager("ctrl+alt")
    app._tts = types.SimpleNamespace(is_loaded=False)
    app._speaking = False
    app._update_ready_tooltip = lambda: None
    # _reject_shortcut sleeps 2s to show its tooltip; skip that in tests
    monkeypatch.setattr("readtome.app.time.sleep", lambda s: None)
    return app


def test_stop_speaking_stops_player_when_speaking(app):
    app._speaking = True
    app._stop_speaking()
    assert app._player.stopped


def test_stop_speaking_noop_when_idle(app):
    app._stop_speaking()
    assert not app._player.stopped


def test_pause_handlers_update_and_save_config(app):
    app._change_sentence_pause(400)
    app._change_comma_pause(0)
    assert app._config.sentence_pause_ms == 400
    assert app._config.comma_pause_ms == 0
    assert app._config.saved


def test_stop_shortcut_conflicting_with_read_rejected(app):
    app._on_stop_hotkey_captured("shift+alt")  # same as read shortcut
    assert app._stop_hotkey.rebound is None
    assert not app._config.saved


def test_stop_shortcut_valid_rebinds_and_saves(app):
    app._on_stop_hotkey_captured("ctrl+windows")
    assert app._stop_hotkey.rebound == "ctrl+windows"
    assert app._config.stop_hotkey == "ctrl+windows"
    assert app._config.saved


def test_stop_shortcut_invalid_capture_rejected(app):
    app._on_stop_hotkey_captured(None)
    assert app._stop_hotkey.rebound is None


def test_read_shortcut_conflicting_with_stop_rejected(app):
    app._on_hotkey_captured("alt+ctrl")  # same as stop shortcut
    assert app._hotkey.rebound is None


def test_read_shortcut_valid_rebinds_and_saves(app):
    app._on_hotkey_captured("alt+windows")
    assert app._hotkey.rebound == "alt+windows"
    assert app._config.hotkey == "alt+windows"
    assert app._config.saved

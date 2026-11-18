"""Tests for Config defaults, persistence, and forward compatibility."""
import json

from readtome.config import (
    COMMA_PAUSE_PRESETS,
    Config,
    SENTENCE_PAUSE_PRESETS,
)


def test_defaults():
    cfg = Config()
    assert cfg.hotkey == "alt+shift"
    assert cfg.stop_hotkey == "ctrl+alt"
    assert cfg.sentence_pause_ms == 150
    assert cfg.comma_pause_ms == 100


def test_default_pause_values_are_menu_presets():
    assert Config().sentence_pause_ms in SENTENCE_PAUSE_PRESETS.values()
    assert Config().comma_pause_ms in COMMA_PAUSE_PRESETS.values()


def test_old_config_loads_with_new_fields_defaulted(tmp_path, monkeypatch):
    """A config.json written by an older version (missing newer fields,
    possibly containing fields we no longer know) must load cleanly."""
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        json.dumps({"hotkey": "ctrl+windows", "speed": 1.5, "unknown_field": 1})
    )
    monkeypatch.setattr(Config, "_config_file", staticmethod(lambda: cfg_file))

    cfg = Config.load()
    assert cfg.hotkey == "ctrl+windows"
    assert cfg.speed == 1.5
    assert cfg.stop_hotkey == "ctrl+alt"  # new field gets its default


def test_save_load_round_trip(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr(Config, "_config_file", staticmethod(lambda: cfg_file))

    cfg = Config()
    cfg.sentence_pause_ms = 250
    cfg.comma_pause_ms = 0
    cfg.stop_hotkey = "ctrl+windows"
    cfg.save()

    loaded = Config.load()
    assert loaded.sentence_pause_ms == 250
    assert loaded.comma_pause_ms == 0
    assert loaded.stop_hotkey == "ctrl+windows"

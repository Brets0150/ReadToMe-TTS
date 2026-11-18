"""Shared test setup.

The application depends on Windows-oriented packages (sounddevice, keyboard,
pyperclip, pystray, Pillow) that may not be installed or importable in the
test environment (e.g. CI runners without audio hardware or a display). Any
of these that cannot be imported are replaced with minimal stub modules
before the application code imports them, so the test suite runs anywhere.

Tests that exercise real synthesis or audio output are intentionally out of
scope here; the suite covers the pure-logic parts of the application.
"""
import sys
import types
from pathlib import Path

# Make the project importable when tests run from a source checkout without
# an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _stub_module(name: str, **attrs):
    """Install a stub module under `name` if the real one cannot be imported."""
    if name in sys.modules:
        return
    try:
        __import__(name)
    except Exception:
        mod = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[name] = mod


_stub_module("sounddevice")
_stub_module("keyboard", KeyboardEvent=type("KeyboardEvent", (), {}))
_stub_module("pyperclip")
_stub_module(
    "pystray",
    Icon=type("Icon", (), {}),
    Menu=type("Menu", (), {"SEPARATOR": object()}),
    MenuItem=type("MenuItem", (), {}),
)

try:
    from PIL import Image, ImageDraw, ImageFont  # noqa: F401
except Exception:
    pil = types.ModuleType("PIL")
    sys.modules["PIL"] = pil
    for sub in ("Image", "ImageDraw", "ImageFont"):
        mod = types.ModuleType(f"PIL.{sub}")
        sys.modules[f"PIL.{sub}"] = mod
        setattr(pil, sub, mod)
    sys.modules["PIL.Image"].Image = type("Image", (), {})

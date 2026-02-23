import logging
import threading
import time

import keyboard
import pyperclip

logger = logging.getLogger(__name__)

# Keys that the `keyboard` library treats as modifiers.
# add_hotkey() requires a non-modifier "trigger" key, so combos made
# entirely of these keys need special handling.
_MODIFIER_NAMES = frozenset({
    "ctrl", "control", "left ctrl", "right ctrl",
    "shift", "left shift", "right shift",
    "alt", "left alt", "right alt",
    "windows", "left windows", "right windows",
    "win", "left win", "right win",
})


def _is_modifier_only(hotkey: str) -> bool:
    """Return True if every key in the hotkey string is a modifier."""
    parts = [p.strip().lower() for p in hotkey.split("+")]
    return all(p in _MODIFIER_NAMES for p in parts)


def _normalize_modifier(name: str) -> str:
    """Map modifier key names to a canonical form for comparison."""
    n = name.lower().strip()
    if n in ("ctrl", "control", "left ctrl", "right ctrl"):
        return "ctrl"
    if n in ("shift", "left shift", "right shift"):
        return "shift"
    if n in ("alt", "left alt", "right alt"):
        return "alt"
    if n in ("windows", "left windows", "right windows", "win", "left win", "right win"):
        return "windows"
    return n


class HotkeyManager:
    def __init__(self, hotkey: str, callback):
        self._hotkey = hotkey
        self._callback = callback
        self._registered = False
        self._capturing = False
        # For modifier-only hotkeys
        self._hook_handle = None
        self._required_mods: set[str] = set()
        self._mod_fired = False

    @property
    def current_hotkey(self) -> str:
        return self._hotkey

    def register(self):
        if _is_modifier_only(self._hotkey):
            self._register_modifier_only()
        else:
            keyboard.add_hotkey(self._hotkey, self._on_hotkey, suppress=True)
        self._registered = True
        logger.info("Registered global hotkey: %s", self._hotkey)

    def _register_modifier_only(self):
        """Register a hook that watches for all required modifiers being held."""
        parts = [p.strip().lower() for p in self._hotkey.split("+")]
        self._required_mods = {_normalize_modifier(p) for p in parts}
        self._mod_fired = False
        self._hook_handle = keyboard.hook(self._on_key_event, suppress=False)
        logger.debug(
            "Modifier-only hotkey registered, watching for: %s",
            self._required_mods,
        )

    def _unregister_modifier_only(self):
        if self._hook_handle is not None:
            keyboard.unhook(self._hook_handle)
            self._hook_handle = None
            self._required_mods = set()

    def _get_held_modifiers(self) -> set[str]:
        """Get the set of normalized modifier names currently held down."""
        mods = set()
        for scan_code, event in keyboard._pressed_events.items():
            name = event.name if hasattr(event, "name") and event.name else ""
            normalized = _normalize_modifier(name)
            if normalized:
                mods.add(normalized)
        return mods

    def _on_key_event(self, event: keyboard.KeyboardEvent):
        """Low-level hook for modifier-only hotkeys."""
        if self._capturing:
            return

        if event.event_type == "down":
            held = self._get_held_modifiers()
            if self._required_mods and self._required_mods <= held:
                if not self._mod_fired:
                    self._mod_fired = True
                    threading.Thread(
                        target=self._on_hotkey, daemon=True
                    ).start()
        elif event.event_type == "up":
            if self._mod_fired:
                held = self._get_held_modifiers()
                if not (self._required_mods <= held):
                    self._mod_fired = False

    def unregister(self):
        if self._registered:
            if self._hook_handle is not None:
                self._unregister_modifier_only()
            else:
                try:
                    keyboard.remove_hotkey(self._hotkey)
                except (KeyError, ValueError):
                    pass
            self._registered = False
            logger.debug("Unregistered global hotkey: %s", self._hotkey)

    def rebind(self, new_hotkey: str):
        """Unregister old hotkey and register a new one."""
        logger.info("Rebinding hotkey: %s -> %s", self._hotkey, new_hotkey)
        self.unregister()
        self._hotkey = new_hotkey
        self.register()

    def capture_new_hotkey(self, on_captured):
        """Capture the next key combination the user presses.

        Runs in a background thread. Calls on_captured(hotkey_str) when done,
        or on_captured(None) if the combination is invalid.
        """
        self._capturing = True
        thread = threading.Thread(
            target=self._do_capture, args=(on_captured,), daemon=True
        )
        thread.start()

    def _do_capture(self, on_captured):
        """Block until user presses a key combo, then validate it."""
        try:
            # Temporarily unregister so the current hotkey doesn't fire
            self.unregister()

            logger.debug("Waiting for user to press a key combination...")
            combo = keyboard.read_hotkey(suppress=False)
            logger.info("Captured key combination: %s", combo)

            # Normalize: keyboard lib returns e.g. "ctrl+shift+s"
            parts = [p.strip().lower() for p in combo.split("+")]

            # Must have at least 2 keys to avoid accidental single-key triggers
            if len(parts) >= 2:
                on_captured(combo)
            else:
                logger.warning(
                    "Invalid hotkey '%s': must be at least a 2-key combination",
                    combo,
                )
                on_captured(None)
        except Exception as e:
            logger.error("Error capturing hotkey: %s", e)
            on_captured(None)
        finally:
            self._capturing = False
            # Re-register (caller should rebind if a valid combo was captured)
            if not self._registered:
                self.register()

    def _on_hotkey(self):
        """Called in keyboard listener thread when hotkey is pressed."""
        if self._capturing:
            return
        text = self._capture_selected_text()
        if text and text.strip():
            logger.info("Captured %d characters of text", len(text))
            self._callback(text.strip())
        else:
            logger.debug("No text captured from clipboard")

    def _capture_selected_text(self) -> str:
        """Simulate Ctrl+C and read clipboard."""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""

        try:
            pyperclip.copy("")
        except Exception:
            pass

        # Wait for all keys to be released before sending Ctrl+C.
        # For modifier-only hotkeys the user may still be holding keys,
        # and sending ctrl+c while other modifiers are held results in
        # alt+shift+ctrl+c (etc.) which doesn't copy.
        deadline = time.monotonic() + 1.0  # 1 second timeout
        while keyboard._pressed_events and time.monotonic() < deadline:
            time.sleep(0.02)
        time.sleep(0.05)
        keyboard.send("ctrl+c")
        time.sleep(0.15)

        try:
            text = pyperclip.paste()
        except Exception:
            text = ""

        # Restore the user's original clipboard content
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            logger.debug("Failed to restore clipboard contents")

        return text

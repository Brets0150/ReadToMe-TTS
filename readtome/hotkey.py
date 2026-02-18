import logging
import threading
import time

import keyboard
import pyperclip

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self, hotkey: str, callback):
        self._hotkey = hotkey
        self._callback = callback
        self._registered = False
        self._capturing = False

    @property
    def current_hotkey(self) -> str:
        return self._hotkey

    def register(self):
        keyboard.add_hotkey(self._hotkey, self._on_hotkey, suppress=True)
        self._registered = True
        logger.info("Registered global hotkey: %s", self._hotkey)

    def unregister(self):
        if self._registered:
            keyboard.remove_hotkey(self._hotkey)
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

            # Validate: must include ctrl+shift at minimum
            has_ctrl = "ctrl" in parts or "control" in parts
            has_shift = "shift" in parts
            # Must have at least one non-modifier key
            modifiers = {"ctrl", "control", "shift", "alt", "windows", "win"}
            non_mod_keys = [p for p in parts if p not in modifiers]

            if has_ctrl and has_shift and non_mod_keys:
                on_captured(combo)
            else:
                logger.warning(
                    "Invalid hotkey '%s': must include Ctrl+Shift + another key",
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

        # Brief delay so hotkey keys are released before sending Ctrl+C
        time.sleep(0.05)
        keyboard.send("ctrl+c")
        time.sleep(0.15)

        try:
            text = pyperclip.paste()
        except Exception:
            text = ""

        return text

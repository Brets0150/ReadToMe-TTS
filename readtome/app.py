import logging
import threading
import time

from readtome.audio_player import AudioPlayer
from readtome.config import Config
from readtome.hotkey import HotkeyManager
from readtome.tray import TrayIcon
from readtome.tts_engine import TTSEngine

logger = logging.getLogger(__name__)


class ReadToMeApp:
    def __init__(self):
        self._config = Config.load()
        self._config.resolve_model_paths(Config.get_base_dir())

        self._tts = TTSEngine(self._config)
        self._player = AudioPlayer()
        self._hotkey = HotkeyManager(self._config.hotkey, self._on_text_captured)
        self._tray = TrayIcon(
            on_quit=self._quit,
            on_toggle_pause=self._toggle_pause,
            on_configure_shortcut=self._configure_shortcut,
            on_change_voice=self._change_voice,
            on_change_speed=self._change_speed,
            on_change_pitch=self._change_pitch,
            on_toggle_startup=self._toggle_startup,
            is_paused=lambda: self._paused,
            get_status=self._get_status_text,
            get_voices=Config.list_available_voices,
            get_current_voice=lambda: self._config.model_path,
            get_current_speed=lambda: self._config.speed,
            get_current_pitch=lambda: self._config.pitch,
        )

        self._paused = False
        self._speaking = False
        self._worker_thread: threading.Thread | None = None

    def run(self):
        """Main entry point."""
        model_thread = threading.Thread(target=self._load_model, daemon=True)
        model_thread.start()

        self._hotkey.register()
        self._tray.run()  # Blocks main thread

    def _load_model(self, model_path: str | None = None):
        self._tray.update_tooltip("ReadToMe - Loading voice...")
        try:
            self._tts.load_model(model_path)
            self._update_ready_tooltip()
            logger.info("Model loaded, ready to use")
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            self._tray.update_tooltip(f"ReadToMe - ERROR: {e}")

    def _update_ready_tooltip(self):
        hotkey_display = self._hotkey.current_hotkey.replace("+", "+").title()
        voice_name = self._config.get_voice_display_name()
        self._tray.update_tooltip(f"ReadToMe - {voice_name} ({hotkey_display})")

    def _on_text_captured(self, text: str):
        """Called from hotkey thread when text is captured."""
        if self._paused:
            logger.debug("Hotkey pressed but app is paused, ignoring")
            return
        if not self._tts.is_loaded:
            logger.warning("Model not loaded yet, ignoring hotkey")
            return

        # If already speaking, stop current and start new
        if self._speaking:
            logger.debug("Interrupting current speech")
            self._player.stop()
            if self._worker_thread:
                self._worker_thread.join(timeout=2.0)

        self._worker_thread = threading.Thread(
            target=self._speak_text, args=(text,), daemon=True
        )
        self._worker_thread.start()

    def _speak_text(self, text: str):
        """Runs in worker thread. Synthesizes and plays audio."""
        self._speaking = True
        self._tray.update_tooltip("ReadToMe - Speaking...")
        text_preview = text[:80] + ("..." if len(text) > 80 else "")
        logger.debug("Speaking text (%d chars): %s", len(text), text_preview)
        try:
            self._speak_streaming(text)
        except Exception as e:
            logger.error("TTS error: %s", e, exc_info=True)
        finally:
            self._speaking = False
            if self._tts.is_loaded:
                self._update_ready_tooltip()

    def _speak_streaming(self, text: str):
        """Stream synthesis: play each sentence chunk as it's generated."""
        chunk_num = 0
        t_start = time.perf_counter()
        t_first_chunk = None

        for samples, sr in self._tts.synthesize_stream(text):
            chunk_num += 1
            if t_first_chunk is None:
                t_first_chunk = time.perf_counter() - t_start
                logger.debug(
                    "First chunk in %.2fs (%d samples, %.1fs audio @ %dHz)",
                    t_first_chunk, len(samples), len(samples) / sr, sr,
                )
            else:
                logger.debug(
                    "Chunk %d: %d samples (%.1fs audio)",
                    chunk_num, len(samples), len(samples) / sr,
                )

            if self._player._stop_event.is_set():
                logger.debug("Stop requested, breaking at chunk %d", chunk_num)
                break

            self._player.play(samples, sr)

        t_total = time.perf_counter() - t_start
        logger.debug("Streaming complete: %d chunks in %.2fs", chunk_num, t_total)

    # ── Voice / Speed / Pitch handlers ───────────────────────────────────

    def _change_voice(self, model_path: str):
        """Switch to a different voice model. Reloads in background."""
        if model_path == self._config.model_path:
            return
        logger.info("Switching voice to: %s", model_path)
        # Stop any current speech
        if self._speaking:
            self._player.stop()
        # Reload model in background
        thread = threading.Thread(
            target=self._do_change_voice, args=(model_path,), daemon=True
        )
        thread.start()

    def _do_change_voice(self, model_path: str):
        self._load_model(model_path)
        self._config.save()

    def _change_speed(self, speed: float):
        logger.info("Speed changed to %.2f", speed)
        self._config.speed = speed
        self._config.save()

    def _change_pitch(self, pitch: float):
        logger.info("Pitch changed to %.2f", pitch)
        self._config.pitch = pitch
        self._config.save()

    # ── Other handlers ───────────────────────────────────────────────────

    def _toggle_startup(self, icon, item):
        """Toggle Start on Login."""
        enabled = Config.get_startup_enabled()
        Config.set_startup_enabled(not enabled)
        logger.info("Start on Login: %s", "enabled" if not enabled else "disabled")

    def _configure_shortcut(self, icon, item):
        """Called from tray menu. Starts hotkey capture mode."""
        logger.info("Configure Shortcut clicked — waiting for key combination...")
        self._tray.update_tooltip("ReadToMe - Press shortcut now (Ctrl+Shift+?)")
        self._hotkey.capture_new_hotkey(self._on_hotkey_captured)

    def _on_hotkey_captured(self, new_hotkey: str | None):
        """Called from capture thread when user presses a key combo."""
        if new_hotkey is None:
            logger.warning("Invalid shortcut — must include Ctrl+Shift + another key")
            self._tray.update_tooltip("ReadToMe - Invalid shortcut, keeping old one")
            time.sleep(2)
            self._update_ready_tooltip()
            return

        self._hotkey.rebind(new_hotkey)
        self._config.hotkey = new_hotkey
        self._config.save()
        logger.info("Shortcut changed to: %s (saved to config)", new_hotkey)
        self._update_ready_tooltip()

    def _toggle_pause(self, icon, item):
        self._paused = not self._paused
        if self._paused:
            self._player.stop()
            self._tray.update_tooltip("ReadToMe - Paused")
        else:
            self._update_ready_tooltip()

    def _get_status_text(self):
        if not self._tts.is_loaded:
            return "Loading model..."
        if self._paused:
            return "Paused"
        if self._speaking:
            return "Speaking..."
        return "Ready"

    def _quit(self, icon, item):
        self._player.stop()
        self._hotkey.unregister()
        self._tray.stop()

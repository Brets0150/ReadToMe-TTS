import logging
import threading

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioPlayer:
    def __init__(self, sample_rate: int = 24000):
        self._sample_rate = sample_rate
        self._lock = threading.Lock()
        self._playing = False
        self._stop_event = threading.Event()

    def play(self, samples: np.ndarray, sample_rate: int | None = None):
        """Play audio. Blocks until done or stopped."""
        sr = sample_rate or self._sample_rate
        duration = len(samples) / sr
        logger.debug("Playing %.1fs of audio (%d samples @ %dHz)", duration, len(samples), sr)
        with self._lock:
            self._playing = True
            self._stop_event.clear()
        try:
            sd.play(samples, sr)
            while sd.get_stream().active:
                if self._stop_event.is_set():
                    sd.stop()
                    logger.debug("Playback interrupted by stop event")
                    break
                sd.sleep(50)
        except Exception as e:
            logger.error("Playback error: %s", e, exc_info=True)
        finally:
            with self._lock:
                self._playing = False

    def play_chunks(self, chunk_iterator):
        """Play streaming chunks sequentially. Supports interruption."""
        for samples, sample_rate in chunk_iterator:
            if self._stop_event.is_set():
                break
            self.play(samples, sample_rate)

    def stop(self):
        """Interrupt current playback. Thread-safe."""
        logger.debug("Stop requested")
        self._stop_event.set()
        sd.stop()

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._playing

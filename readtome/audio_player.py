import logging
import threading

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

# Frames per blocking write. Small slices keep stop() responsive
# (~90ms at 22.05kHz) without adding measurable overhead.
_WRITE_SLICE_FRAMES = 2048


class AudioPlayer:
    def __init__(self, sample_rate: int = 24000):
        self._sample_rate = sample_rate
        self._lock = threading.Lock()
        self._playing = False
        self._stop_event = threading.Event()

    def play(self, samples: np.ndarray, sample_rate: int | None = None):
        """Play a single buffer of audio. Blocks until done or stopped."""
        self.play_chunks(iter([(samples, sample_rate)]))

    def play_chunks(self, chunk_iterator):
        """Play chunks back-to-back over one persistent output stream.

        Opening an audio device takes 100ms+ on Windows, so the stream is
        opened once and kept open for the whole sequence — chunks play
        gapless instead of paying a device open/close between sentences.
        Blocks until the iterator is exhausted or stop() is called.
        """
        stream = None
        stream_sr = None
        with self._lock:
            self._playing = True
        try:
            for samples, sample_rate in chunk_iterator:
                if self._stop_event.is_set():
                    break
                sr = sample_rate or self._sample_rate
                if stream is None or sr != stream_sr:
                    if stream is not None:
                        stream.stop()
                        stream.close()
                    stream = sd.OutputStream(
                        samplerate=sr, channels=1, dtype="int16", latency="low",
                    )
                    stream.start()
                    stream_sr = sr
                    logger.debug("Opened output stream @ %dHz", sr)

                samples = np.ascontiguousarray(samples, dtype=np.int16)
                logger.debug(
                    "Playing %.1fs of audio (%d samples @ %dHz)",
                    len(samples) / sr, len(samples), sr,
                )
                for i in range(0, len(samples), _WRITE_SLICE_FRAMES):
                    if self._stop_event.is_set():
                        break
                    stream.write(samples[i:i + _WRITE_SLICE_FRAMES])
        except Exception as e:
            logger.error("Playback error: %s", e, exc_info=True)
        finally:
            if stream is not None:
                try:
                    if self._stop_event.is_set():
                        stream.abort()  # drop buffered audio immediately
                        logger.debug("Playback interrupted by stop event")
                    else:
                        stream.stop()  # drain remaining buffered audio
                    stream.close()
                except Exception:
                    logger.debug("Error closing output stream", exc_info=True)
            with self._lock:
                self._playing = False

    def stop(self):
        """Interrupt current playback. Thread-safe."""
        logger.debug("Stop requested")
        self._stop_event.set()

    def reset(self):
        """Clear the stop flag so new playback can proceed."""
        self._stop_event.clear()

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._playing

    @property
    def is_stopped(self) -> bool:
        """Check if a stop has been requested."""
        return self._stop_event.is_set()

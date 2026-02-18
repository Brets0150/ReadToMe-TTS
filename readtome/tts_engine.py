import logging
import time

import numpy as np

from readtome.config import Config

logger = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self, config: Config):
        self._config = config
        self._voice = None
        self._loaded = False

    def load_model(self, model_path: str | None = None):
        from piper.voice import PiperVoice

        path = model_path or self._config.model_path
        logger.info("Loading Piper voice from %s", path)
        t0 = time.perf_counter()
        self._voice = PiperVoice.load(path)
        t_load = time.perf_counter() - t0
        self._loaded = True
        if model_path:
            self._config.model_path = model_path
        logger.info(
            "Voice loaded in %.2fs (sample_rate=%d)",
            t_load, self._voice.config.sample_rate,
        )

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def sample_rate(self) -> int:
        if self._voice:
            return self._voice.config.sample_rate
        return 22050

    def _get_playback_rate(self) -> int:
        """Apply pitch adjustment to the sample rate for playback."""
        base_sr = self.sample_rate
        return int(base_sr * self._config.pitch)

    def _make_syn_config(self):
        """Create a SynthesisConfig with speed applied."""
        from piper.config import SynthesisConfig

        return SynthesisConfig(
            length_scale=1.0 / self._config.speed,
        )

    def synthesize(self, text: str) -> tuple:
        """Synchronous synthesis. Returns (samples_ndarray, sample_rate)."""
        if not self._voice:
            raise RuntimeError("Model not loaded")
        logger.debug("Synthesizing %d chars with speed=%.1f", len(text), self._config.speed)
        t0 = time.perf_counter()

        syn_config = self._make_syn_config()
        chunks = []
        for audio_chunk in self._voice.synthesize(text, syn_config=syn_config):
            chunks.append(audio_chunk.audio_int16_array)

        if not chunks:
            logger.warning("No audio generated for text")
            return np.array([], dtype=np.int16), self._get_playback_rate()

        samples = np.concatenate(chunks)
        sr = self._get_playback_rate()
        t_synth = time.perf_counter() - t0
        duration = len(samples) / sr
        logger.debug(
            "Synthesized %d samples in %.2fs (%.1fx realtime, pitch=%.2f)",
            len(samples), t_synth, duration / t_synth if t_synth > 0 else 0,
            self._config.pitch,
        )
        return samples, sr

    def synthesize_stream(self, text: str):
        """Generator yielding (samples_ndarray, sample_rate) per sentence."""
        if not self._voice:
            raise RuntimeError("Model not loaded")
        logger.debug("Starting streaming synthesis for %d chars", len(text))

        syn_config = self._make_syn_config()
        sr = self._get_playback_rate()
        for audio_chunk in self._voice.synthesize(text, syn_config=syn_config):
            yield audio_chunk.audio_int16_array, sr

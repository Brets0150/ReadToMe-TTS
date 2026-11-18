import logging
import time

import numpy as np

from readtome.config import Config

logger = logging.getLogger(__name__)

# Amplitude below which an int16 sample counts as silence (~1% of full scale).
# Piper's generated pauses are near-zero, so this is well clear of speech.
_SILENCE_THRESHOLD = 330


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

    def warmup(self):
        """Run a tiny throwaway synthesis right after load.

        ONNX Runtime does lazy allocation/graph optimization on the first
        inference, which otherwise lands on the user's first hotkey press.
        """
        if not self._voice:
            return
        t0 = time.perf_counter()
        try:
            for _ in self._voice.synthesize("Hi.", syn_config=self._make_syn_config()):
                pass
            logger.debug("Warmup synthesis done in %.2fs", time.perf_counter() - t0)
        except Exception as e:
            logger.warning("Warmup synthesis failed: %s", e)

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

    def _condense_silence(self, samples: np.ndarray, sr: int) -> np.ndarray:
        """Shorten the long silences the model generates around punctuation.

        Internal silent runs (commas, dashes, etc.) longer than
        comma_pause_ms are compressed down to that length. Leading and
        trailing silence of each sentence chunk is capped at
        sentence_pause_ms, which sets the gap heard between sentences.
        Silences already shorter than the caps are left untouched.
        """
        if len(samples) == 0:
            return samples
        max_internal = max(0, int(sr * self._config.comma_pause_ms / 1000))
        max_edge = max(0, int(sr * self._config.sentence_pause_ms / 1000))

        quiet = np.abs(samples) < _SILENCE_THRESHOLD
        padded = np.concatenate(([False], quiet, [False]))
        edges = np.flatnonzero(np.diff(padded.astype(np.int8)))
        if len(edges) == 0:
            return samples
        run_starts = edges[0::2]
        run_ends = edges[1::2]

        keep = np.ones(len(samples), dtype=bool)
        for start, end in zip(run_starts, run_ends):
            is_edge_run = start == 0 or end == len(samples)
            limit = max_edge if is_edge_run else max_internal
            if end - start > limit:
                keep[start + limit:end] = False

        return samples[keep]

    def synthesize(self, text: str) -> tuple:
        """Synchronous synthesis. Returns (samples_ndarray, sample_rate)."""
        if not self._voice:
            raise RuntimeError("Model not loaded")
        logger.debug("Synthesizing %d chars with speed=%.1f", len(text), self._config.speed)
        t0 = time.perf_counter()

        sr = self._get_playback_rate()
        chunks = [samples for samples, _ in self.synthesize_stream(text)]

        if not chunks:
            logger.warning("No audio generated for text")
            return np.array([], dtype=np.int16), sr

        samples = np.concatenate(chunks)
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
        # Feed the text line by line so phonemization (which Piper runs on
        # the whole input before yielding any audio) only has to process one
        # block before the first chunk can play.
        blocks = [line.strip() for line in text.splitlines()]
        blocks = [b for b in blocks if b]
        for block in blocks:
            for audio_chunk in self._voice.synthesize(block, syn_config=syn_config):
                samples = self._condense_silence(audio_chunk.audio_int16_array, sr)
                if len(samples):
                    yield samples, sr

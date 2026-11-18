"""Tests for TTSEngine._condense_silence (pause capping).

Long silences the voice model generates are shortened: leading/trailing
silence of a chunk is capped at sentence_pause_ms, internal silences
(commas etc.) at comma_pause_ms. Shorter silences are left untouched.
"""
import numpy as np

from readtome.config import Config
from readtome.tts_engine import TTSEngine, _SILENCE_THRESHOLD

SR = 22050


def ms(n: int) -> int:
    return int(SR * n / 1000)


def speech(n_ms: int) -> np.ndarray:
    rng = np.random.default_rng(42)
    samples = rng.integers(5000, 15000, ms(n_ms))
    signs = rng.choice([-1, 1], ms(n_ms))
    return (samples * signs).astype(np.int16)


def silence(n_ms: int) -> np.ndarray:
    return np.zeros(ms(n_ms), dtype=np.int16)


def make_engine(sentence_pause_ms=150, comma_pause_ms=100) -> TTSEngine:
    cfg = Config(
        sentence_pause_ms=sentence_pause_ms, comma_pause_ms=comma_pause_ms
    )
    return TTSEngine(cfg)


def test_trailing_silence_capped():
    eng = make_engine()
    chunk = np.concatenate([speech(500), silence(400)])
    out = eng._condense_silence(chunk, SR)
    assert abs(len(out) - (ms(500) + ms(150))) <= 2


def test_internal_silence_capped():
    eng = make_engine()
    chunk = np.concatenate([speech(300), silence(300), speech(300)])
    out = eng._condense_silence(chunk, SR)
    assert abs(len(out) - (ms(600) + ms(100))) <= 2


def test_short_internal_silence_untouched():
    eng = make_engine()
    chunk = np.concatenate([speech(300), silence(60), speech(300)])
    out = eng._condense_silence(chunk, SR)
    assert len(out) == len(chunk)


def test_leading_silence_capped():
    eng = make_engine()
    chunk = np.concatenate([silence(500), speech(300)])
    out = eng._condense_silence(chunk, SR)
    assert abs(len(out) - (ms(150) + ms(300))) <= 2


def test_fully_silent_chunk_capped():
    eng = make_engine()
    out = eng._condense_silence(silence(1000), SR)
    assert abs(len(out) - ms(150)) <= 2


def test_pure_speech_untouched():
    eng = make_engine()
    chunk = speech(500)
    out = eng._condense_silence(chunk, SR)
    assert len(out) == len(chunk)


def test_empty_input():
    eng = make_engine()
    out = eng._condense_silence(np.array([], dtype=np.int16), SR)
    assert len(out) == 0


def test_speech_order_preserved():
    eng = make_engine()
    a = np.full(ms(100), 1000, dtype=np.int16)
    b = np.full(ms(100), 2000, dtype=np.int16)
    chunk = np.concatenate([a, silence(300), b])
    out = eng._condense_silence(chunk, SR)
    loud = out[np.abs(out) >= _SILENCE_THRESHOLD]
    assert np.all(loud[: ms(100)] == 1000)
    assert np.all(loud[ms(100):] == 2000)


def test_zero_caps_remove_silence_entirely():
    eng = make_engine(sentence_pause_ms=0, comma_pause_ms=0)
    chunk = np.concatenate([silence(100), speech(200), silence(100)])
    out = eng._condense_silence(chunk, SR)
    assert abs(len(out) - ms(200)) <= 2

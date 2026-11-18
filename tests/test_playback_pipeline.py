"""Tests for the pipelined synthesis/playback in ReadToMeApp._speak_streaming.

Uses a fake TTS engine and player so no model or audio device is needed:
chunks must play in order, interruption must stop promptly, and edge cases
must not deadlock the producer/consumer queue.
"""
import threading
import time

import numpy as np

from readtome.app import ReadToMeApp


class FakeTTS:
    def __init__(self, n_chunks=5, synth_delay=0.05):
        self.n_chunks = n_chunks
        self.synth_delay = synth_delay

    def synthesize_stream(self, text):
        for i in range(self.n_chunks):
            time.sleep(self.synth_delay)  # simulate inference time
            yield np.full(1000, i + 1, dtype=np.int16), 22050


class FakePlayer:
    """Mimics AudioPlayer's interface; 'plays' by sleeping per chunk."""

    def __init__(self, play_delay=0.05):
        self._stop = threading.Event()
        self.play_delay = play_delay
        self.played = []

    def reset(self):
        self._stop.clear()

    def stop(self):
        self._stop.set()

    @property
    def is_stopped(self):
        return self._stop.is_set()

    def play_chunks(self, chunk_iterator):
        for samples, _sr in chunk_iterator:
            if self._stop.is_set():
                break
            time.sleep(self.play_delay)
            self.played.append(samples[0])


def make_app(tts, player) -> ReadToMeApp:
    app = ReadToMeApp.__new__(ReadToMeApp)  # skip __init__ (tray/hotkeys)
    app._tts = tts
    app._player = player
    return app


def test_all_chunks_play_in_order():
    app = make_app(FakeTTS(), FakePlayer())
    t0 = time.monotonic()
    app._speak_streaming("hello world")
    assert app._player.played == [1, 2, 3, 4, 5]
    assert time.monotonic() - t0 < 3  # no hang


def test_interruption_stops_promptly():
    app = make_app(FakeTTS(n_chunks=50, synth_delay=0.02), FakePlayer(play_delay=0.1))

    def interrupt():
        time.sleep(0.35)
        app._player.stop()

    threading.Thread(target=interrupt).start()
    t0 = time.monotonic()
    app._speak_streaming("long text")
    assert 0 < len(app._player.played) < 50
    assert time.monotonic() - t0 < 2


def test_empty_stream_terminates_cleanly():
    app = make_app(FakeTTS(n_chunks=0), FakePlayer())
    t0 = time.monotonic()
    app._speak_streaming("")
    assert app._player.played == []
    assert time.monotonic() - t0 < 1

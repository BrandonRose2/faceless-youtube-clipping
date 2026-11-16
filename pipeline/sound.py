"""Procedural sound library for the Corners Cut videos (numpy only, no samples).

Every generator returns a mono 44.1 kHz float array in [-1, 1] at a level that
is safe to mix: beds are quiet, effects peak around 0.4-0.8. Use write_wav() to
save one, and `python -m pipeline.sound` to write output/sound_demo.wav.

Generators: drone(seconds, mood), hit(), crack(), whoosh(), riser(seconds),
tick(), typewriter_tick(). The drone starts from audio_bed() in
tools/render_coldopen_test.py (55 Hz root, fifth above, slow LFO).
"""
import math
import os
import wave

import numpy as np

SR = 44100


def _t(seconds):
    return np.arange(int(SR * seconds)) / SR


def _fade(x, fade_in=0.0, fade_out=0.0):
    """Linear fades so cuts never click."""
    n = len(x)
    if fade_in > 0:
        k = min(n, int(SR * fade_in))
        x[:k] *= np.linspace(0, 1, k)
    if fade_out > 0:
        k = min(n, int(SR * fade_out))
        x[n - k:] *= np.linspace(1, 0, k)
    return x


def _soften(x, cutoff):
    """Cheap low-pass: moving average whose width matches the cutoff."""
    width = max(1, int(SR / cutoff))
    return np.convolve(x, np.ones(width) / width, mode="same")


def drone(seconds, mood="neutral", seed=1):
    """Low music bed. mood: 'neutral' (the cold-open bed), 'somber' (minor, slow),
    'tense' (dissonant, faster pulse). Fades in and out over 3 s (or a third of
    the length for very short beds)."""
    moods = {
        # root Hz, [(ratio, amplitude), ...], LFO Hz
        "neutral": (55.0, [(1.0, 1.0), (1.498, 0.6), (2.005, 0.3)], 0.07),
        "somber": (49.0, [(1.0, 1.0), (1.189, 0.55), (1.498, 0.4), (2.0, 0.2)], 0.05),
        "tense": (55.0, [(1.0, 1.0), (1.059, 0.5), (1.498, 0.45), (2.12, 0.25)], 0.16),
    }
    root, parts, lfo_hz = moods.get(mood, moods["neutral"])
    t = _t(seconds)
    lfo = 0.6 + 0.4 * np.sin(2 * math.pi * lfo_hz * t)
    x = sum(a * np.sin(2 * math.pi * root * r * t) for r, a in parts) * lfo * 0.05
    # a little slow-moving air so it does not sound like a test tone
    rng = np.random.default_rng(seed)
    x = x + _soften(rng.standard_normal(len(t)) * 0.02, 400)
    f = 3.0 if seconds > 9 else seconds / 3
    return _fade(x, f, f)


def hit(seconds=1.4):
    """Low impact for big numbers and facts: pitch-dropping thump plus a short click."""
    t = _t(seconds)
    f = 38 + 70 * np.exp(-t * 14)  # ~108 Hz falling to ~38 Hz
    body = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    click = np.random.default_rng(2).standard_normal(len(t)) * np.exp(-t * 90) * 0.35
    return np.clip(body * 0.75 + click, -1, 1) * 0.8


def crack(seconds=1.6):
    """The collapse: a sharp noise burst with a sub-bass rumble (from the cold open)."""
    n = int(SR * seconds)
    env = np.exp(-np.arange(n) / (0.25 * SR))
    rng = np.random.default_rng(1)
    x = rng.standard_normal(n) * env * 0.5 + np.sin(2 * math.pi * 40 * np.arange(n) / SR) * env * 0.6
    k = int(SR * 0.004)
    x[:k] *= np.linspace(0, 1, k)
    return np.clip(x, -1, 1) * 0.8


def whoosh(seconds=0.9):
    """Transition sweep: noise whose brightness rises then falls."""
    n = int(SR * seconds)
    t = np.linspace(0, 1, n)
    noise = np.random.default_rng(3).standard_normal(n)
    out = np.zeros(n)
    # three smoothed bands, dark to bright, each active in its own part of the sweep
    for width, lo, hi in ((256, 0.0, 0.35), (64, 0.2, 0.65), (12, 0.45, 1.0)):
        band = np.convolve(noise, np.ones(width) / width, mode="same")
        w = np.clip((t - lo) / (hi - lo), 0, 1) * np.clip((hi + 0.35 - t) / 0.35, 0, 1)
        out += band * w
    x = out * np.sin(math.pi * t) ** 1.5
    return x / (np.max(np.abs(x)) + 1e-9) * 0.5


def riser(seconds=3.0):
    """Tension before a reveal: a rising tone plus noise that swells, then stops."""
    n = int(SR * seconds)
    t = np.linspace(0, 1, n)
    tone = np.sin(2 * math.pi * np.cumsum(120 * (1 + 7 * t ** 2)) / SR)
    noise = np.random.default_rng(4).standard_normal(n) * t ** 3
    x = (tone * 0.35 + noise * 0.25) * t ** 2
    k = int(SR * 0.05)
    x[-k:] *= np.linspace(1, 0, k)
    return np.clip(x, -1, 1) * 0.6


def tick(seconds=0.18):
    """Clock tick for 'creep over time': a dry wooden click."""
    t = _t(seconds)
    x = np.sin(2 * math.pi * 1900 * t) * np.exp(-t * 60) + \
        np.random.default_rng(5).standard_normal(len(t)) * np.exp(-t * 140) * 0.4
    return np.clip(x, -1, 1) * 0.5


def typewriter_tick(seconds=0.07):
    """Short key click for text cards."""
    t = _t(seconds)
    x = np.sin(2 * math.pi * 3100 * t) * np.exp(-t * 110) + \
        np.random.default_rng(6).standard_normal(len(t)) * np.exp(-t * 220) * 0.5
    return np.clip(x, -1, 1) * 0.4


def write_wav(path, x):
    """Save a float array as 16-bit mono WAV. Clips instead of wrapping."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    pcm = np.int16(np.clip(x, -1, 1) * 32767)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _place(mix, x, at):
    i = int(SR * at)
    end = min(len(mix), i + len(x))
    mix[i:end] += x[: end - i]


def demo(path="output/sound_demo.wav"):
    """20 s demo: three beds (neutral, somber, tense) with each effect spaced out."""
    mix = np.zeros(int(SR * 20.0))
    for start, mood in ((0.0, "neutral"), (7.0, "somber"), (14.0, "tense")):
        _place(mix, drone(6.5, mood), start)
    _place(mix, whoosh(), 1.0)          # 1.0  whoosh
    _place(mix, hit(), 2.6)             # 2.6  hit
    _place(mix, crack(), 4.2)           # 4.2  crack
    _place(mix, riser(3.0), 8.0)        # 8.0  riser (3 s), then...
    _place(mix, hit(), 11.1)            # 11.1 ...the hit that lands the reveal
    for i in range(3):
        _place(mix, tick(), 12.6 + i * 0.5)          # 12.6  three ticks
    for i in range(4):
        _place(mix, typewriter_tick(), 15.0 + i * 0.18)  # 15.0 four key clicks
    _place(mix, whoosh(), 17.0)         # 17.0 closing whoosh
    peak = float(np.max(np.abs(mix)))
    if peak > 0.95:  # never clip the demo
        mix *= 0.95 / peak
    write_wav(path, mix)
    return path, float(np.max(np.abs(mix)))


if __name__ == "__main__":
    p, pk = demo()
    print(f"{p}  peak={pk:.2f}")

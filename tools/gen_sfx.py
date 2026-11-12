"""Synthesised sound effects (no AI generation): filtered noise, sines, bell partials and a creaking sawtooth.
Writes 44.1 kHz mono WAVs into assets/audio/sfx/ using the same file names scripts/game/audio.gd looks up.

  python gen_sfx.py            # all of them
  python gen_sfx.py page_turn  # just one
"""
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "audio" / "sfx"


# ------------------------------------------------------------------ building blocks
def tt(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def noise(d, seed=1):
    return np.random.default_rng(seed).uniform(-1, 1, int(SR * d))


def band(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def lowpass(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def expdecay(d, rate):
    return np.exp(-tt(d) * rate)


def bump(d, center, width):
    return np.exp(-(((tt(d) - center) / width) ** 2))


def place(canvas, x, start):
    i = int(start * SR)
    n = min(len(x), len(canvas) - i)
    if n > 0:
        canvas[i:i + n] += x[:n]


def finish(x, peak_db=-3.0, fade_out=0.03):
    x = x - np.mean(x)
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)
    n = int(fade_out * SR)
    x[-n:] *= np.linspace(1, 0, n)
    x[:64] *= np.linspace(0, 1, 64)
    return x


def thump(freq, d, level=1.0):
    t = tt(d)
    f = freq * (1 + 0.8 * np.exp(-t * 40))               # slight pitch drop on impact
    return level * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)


def click(d=0.008, seed=3, level=1.0):
    return level * highpass(noise(d, seed), 1500) * np.linspace(1, 0, int(SR * d))


def bell(freq, d):
    t = tt(d)
    out = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, 1.4), (2.01, 0.45, 1.9), (2.76, 0.3, 2.6), (4.07, 0.15, 3.6), (5.4, 0.08, 5.0)):
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * dec * 1.6)
    return out * np.minimum(1, t / 0.004)


# ------------------------------------------------------------------ the sounds
def page_turn():
    d = 0.45
    t = tt(d)
    flutter = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 17 * t))
    swish = band(noise(d, 11), 1800, 7500) * np.sin(np.pi * t / d) ** 1.5 * flutter
    body = band(noise(d, 12), 400, 1400) * np.sin(np.pi * t / d) ** 2 * 0.35
    out = swish + body
    place(out, click(0.01, 5, 0.6), d - 0.07)             # the page lands
    return finish(out)


def diary_open():
    d = 0.9
    out = np.zeros(int(SR * d))
    place(out, thump(80, 0.25, 0.9), 0.0)                  # cover thump
    creak = band(noise(0.35, 21), 250, 900) * bump(0.35, 0.15, 0.09) * 0.55
    place(out, creak, 0.04)
    place(out, band(noise(0.4, 22), 1800, 7000) * np.sin(np.pi * tt(0.4) / 0.4) ** 1.5 * 0.5, 0.36)
    return finish(out)


def diary_close():
    d = 0.6
    out = np.zeros(int(SR * d))
    place(out, band(noise(0.25, 31), 1800, 7000) * np.sin(np.pi * tt(0.25) / 0.25) ** 1.5 * 0.45, 0.0)
    place(out, thump(72, 0.28, 1.0), 0.26)
    place(out, band(noise(0.2, 32), 250, 800) * bump(0.2, 0.08, 0.06) * 0.35, 0.24)
    return finish(out)


def bed_rustle():
    d = 1.0
    t = tt(d)
    rng = np.random.default_rng(41)
    lump = lowpass(np.abs(rng.normal(size=len(t))), 9)     # slow random envelope: cloth being moved
    lump = lump / lump.max()
    cloth = band(noise(d, 42), 300, 2200) * lump ** 1.5
    soft = lowpass(noise(d, 43), 700) * lump * 0.8
    win = np.sin(np.pi * t / d) ** 0.7
    return finish((cloth + soft) * win)


def door_open():
    d = 1.0
    t = tt(d)
    f = 110 + 85 * np.sin(np.pi * t / d) ** 1.2 + 6 * np.sin(2 * np.pi * 7 * t)   # creak pitch glides up and back
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((phase / (2 * np.pi)) % 1) - 1
    creak = band(saw, 450, 1900, 2) * np.sin(np.pi * np.clip(t / 0.85, 0, 1)) ** 1.2
    creak *= 0.7 + 0.3 * np.sin(2 * np.pi * 11 * t + 1)
    air = band(noise(d, 51), 600, 2400) * np.sin(np.pi * t / d) * 0.15
    out = creak + air
    place(out, click(0.01, 52, 0.9), 0.0)                  # latch
    place(out, thump(95, 0.12, 0.35), 0.0)
    return finish(out)


def door_close():
    d = 0.6
    out = np.zeros(int(SR * d))
    place(out, thump(62, 0.35, 1.0), 0.0)
    place(out, lowpass(noise(0.12, 61), 500) * expdecay(0.12, 28), 0.0)
    place(out, click(0.012, 62, 0.7), 0.13)               # latch catches
    place(out, thump(120, 0.08, 0.25), 0.13)
    return finish(out)


def title_chime():
    d = 4.0
    out = np.zeros(int(SR * d))
    for freq, start, level in ((392.0, 0.0, 0.8), (587.33, 0.45, 0.7), (783.99, 0.9, 0.6), (987.77, 1.4, 0.35)):
        place(out, bell(freq, 2.4) * level, start)
    echo = np.zeros_like(out)
    for delay, g in ((0.19, 0.38), (0.41, 0.24), (0.7, 0.14)):
        place(echo, lowpass(out, 3500) * g, delay)
    return finish(out + echo, fade_out=0.25)


def wipe_whoosh():
    d = 0.8
    t = tt(d)
    n = noise(d, 71)
    low = band(n, 250, 900) * bump(d, 0.4, 0.17)
    mid = band(n, 900, 2800) * bump(d, 0.34, 0.14) * 0.8
    high = band(n, 2800, 8000) * bump(d, 0.28, 0.11) * 0.5
    return finish(low + mid + high, fade_out=0.08)


def _tink(freq, d, decay, partial=1.58):
    """A small damped ceramic 'tink': a sine plus one inharmonic partial."""
    t = tt(d)
    return (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * partial * t)) * np.exp(-t * decay)


def pot_break(seed=1):
    """Clay pot shattering: sharp crack, big pieces, a shower of small shards, then a settling rattle."""
    rng = np.random.default_rng(seed)
    d = 1.0
    out = np.zeros(int(SR * d))
    place(out, band(noise(0.03, seed * 3), 900, 6500) * expdecay(0.03, 80), 0.0)            # the crack
    place(out, thump(200 + rng.uniform(-25, 25), 0.09, 0.8), 0.0)                              # body of the hit
    place(out, lowpass(noise(0.12, seed * 5), 1400) * expdecay(0.12, 30) * 0.6, 0.0)          # clay crunch
    for _ in range(rng.integers(5, 8)):                                                         # big pieces landing
        place(out, _tink(rng.uniform(1100, 2600), 0.12, rng.uniform(35, 80)) * rng.uniform(0.35, 0.7), rng.uniform(0.03, 0.4))
    for _ in range(rng.integers(12, 20)):                                                       # small shards
        t0 = rng.uniform(0.06, 0.8)
        place(out, _tink(rng.uniform(3000, 7500), 0.06, rng.uniform(140, 320)) * 0.5 * np.exp(-t0 * 2.2), t0)
    n = int(SR * 0.85)
    gate = (lowpass(np.abs(rng.normal(size=n)), 25) > 0.45).astype(float)                      # shards settling
    rattle = band(noise(0.85, seed * 7), 2500, 9000) * expdecay(0.85, 5.5) * gate * 0.22
    place(out, rattle, 0.1)
    return finish(out, fade_out=0.05)


def chest_open():
    """Latch click, wooden lid creak, thump against the stop, then a rising sparkle for the treasure."""
    d = 2.4
    out = np.zeros(int(SR * d))
    place(out, click(0.007, 81, 0.9), 0.0)                                                      # latch
    place(out, _tink(2300, 0.05, 160, 2.1) * 0.7, 0.0)
    place(out, thump(140, 0.06, 0.35), 0.02)
    cd = 0.58
    t = tt(cd)
    f = 150 + 230 * (t / cd) ** 1.3 + 7 * np.sin(2 * np.pi * 9 * t)                             # creak pitch rises as the lid swings up
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((phase / (2 * np.pi)) % 1) - 1
    creak = band(saw, 500, 1900, 2) * np.sin(np.pi * np.clip(t / cd, 0, 1)) ** 1.1
    creak *= 0.72 + 0.28 * np.sin(2 * np.pi * 14 * t + 0.5)
    place(out, creak * 0.8, 0.07)
    place(out, thump(105, 0.16, 1.0), 0.66)                                                     # lid hits the back
    place(out, lowpass(noise(0.1, 82), 900) * expdecay(0.1, 35) * 0.7, 0.66)
    place(out, click(0.01, 83, 0.5), 0.67)
    rng = np.random.default_rng(84)
    for i, freq in enumerate((1046.5, 1318.5, 1568.0, 2093.0, 2637.0)):                         # rising chime
        place(out, bell(freq, 1.3) * (0.5 - i * 0.04), 0.78 + i * 0.085)
    for _ in range(22):                                                                         # glitter
        t0 = rng.uniform(0.8, 1.9)
        place(out, _tink(rng.uniform(4200, 9500), 0.08, rng.uniform(60, 160)) * 0.28 * np.exp(-(t0 - 0.8) * 1.4), t0)
    echo = np.zeros_like(out)
    for delay, g in ((0.13, 0.3), (0.29, 0.18)):
        place(echo, highpass(out, 900) * g, delay)
    return finish(out + echo, fade_out=0.2)


def _sweep_noise(d, f_of_t, q=0.55, seed=1, hop=256, win=1024):
    """Noise through a band-pass whose centre frequency follows f_of_t(t); overlap-added Hann windows keep it click-free."""
    n = int(SR * d)
    src = noise(d + win / SR, seed)
    out = np.zeros(n + win)
    hann = np.hanning(win)
    for start in range(0, n, hop):
        fc = float(np.clip(f_of_t(start / SR), 150, 12000))
        seg = band(src[start:start + win], fc * (1 - q * 0.6), min(fc * (1 + q * 1.1), 14000), 2) * hann
        out[start:start + win] += seg
    return out[:n]


def sword_swing(seed=1):
    """A blade cutting the air: the pitch of the swish climbs, peaks, then falls (Doppler), with a faint steel 'shing'."""
    rng = np.random.default_rng(seed)
    d = 0.34 + 0.03 * seed
    t = tt(d)
    peak = rng.uniform(0.42, 0.52)
    lo, hi = rng.uniform(500, 750), rng.uniform(4200, 5200)
    shape = lambda x: np.sin(np.pi * min(max(x / d, 0), 1) ** 0.8)
    whoosh = _sweep_noise(d, lambda x: lo + (hi - lo) * shape(x) ** 1.4, seed=seed * 11)
    env = np.exp(-(((t / d - peak) / 0.27) ** 2))
    low = lowpass(noise(d, seed * 13), 600) * env * 0.35                                     # air displaced by the blade
    out = whoosh * env * 1.6 + low
    for k, (freq, amp) in enumerate(((3100, 0.10), (4650, 0.07), (6200, 0.05))):              # steel ring
        glide = freq * (1 + 0.04 * np.sin(np.pi * t / d))
        out += amp * np.sin(2 * np.pi * np.cumsum(glide) / SR) * np.exp(-t * (10 + 4 * k)) * np.minimum(1, t / 0.02)
    return finish(out, fade_out=0.06)


def sword_hit(seed=1):
    """Blade connecting: low thump, crack, a short metallic ring and a wet-ish crunch."""
    rng = np.random.default_rng(seed + 40)
    d = 0.45
    out = np.zeros(int(SR * d))
    place(out, thump(rng.uniform(110, 150), 0.12, 1.0), 0.0)
    place(out, band(noise(0.05, seed * 17), 700, 5500) * expdecay(0.05, 70) * 1.1, 0.0)       # crack
    place(out, lowpass(noise(0.14, seed * 19), 1600) * expdecay(0.14, 24) * 0.7, 0.005)       # crunch
    base = rng.uniform(2300, 2900)
    for ratio, amp, dec in ((1.0, 0.45, 24), (1.51, 0.3, 30), (2.32, 0.18, 40)):               # blade ring
        place(out, np.sin(2 * np.pi * base * ratio * tt(0.3)) * np.exp(-tt(0.3) * dec) * amp, 0.004)
    place(out, click(0.006, seed * 23, 0.6), 0.0)
    return finish(out, fade_out=0.06)


def _tone(freq, d, decay, partials=((1, 1.0), (2, 0.35), (3, 0.12))):
    t = tt(d)
    out = sum(a * np.sin(2 * np.pi * freq * r * t) for r, a in partials) * np.exp(-t * decay)
    return out * np.minimum(1, t / 0.003)


def menu_move():
    d = 0.08
    t = tt(d)
    x = np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 75) + 0.3 * np.sin(2 * np.pi * 3000 * t) * np.exp(-t * 95)
    return finish(x, peak_db=-9.0, fade_out=0.01)


def menu_select():
    d = 0.6
    out = np.zeros(int(SR * d))
    for i, f in enumerate((784.0, 1174.7, 1568.0)):                  # a quick rising triad, warm and soft
        place(out, _tone(f, 0.45, 9.0) * (0.9 - i * 0.12), i * 0.07)
    return finish(lowpass(out, 6500), peak_db=-5.0, fade_out=0.08)


def menu_back():
    d = 0.18
    t = tt(d)
    f = 900 - 420 * (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
    return finish(x, peak_db=-9.0, fade_out=0.03)


def pause_in():
    d = 0.4
    x = _sweep_noise(d, lambda t: 4200 - 3600 * min(t / d, 1), q=0.8, seed=91) * np.exp(-tt(d) * 6)
    low = thump(95, 0.1, 0.6)
    x[: len(low)] += low
    chime = _tone(523.25, 0.35, 12.0) * 0.25
    x[: len(chime)] += chime
    return finish(x, peak_db=-6.0, fade_out=0.08)


def pause_out():
    d = 0.32
    x = _sweep_noise(d, lambda t: 500 + 3600 * min(t / d, 1), q=0.8, seed=92) * np.sin(np.pi * tt(d) / d) ** 0.7
    place(x, _tone(784.0, 0.25, 14.0) * 0.25, 0.04)
    return finish(x, peak_db=-6.0, fade_out=0.08)


SOUNDS = {"page_turn": page_turn, "diary_open": diary_open, "diary_close": diary_close, "bed_rustle": bed_rustle,
          "door_open": door_open, "door_close": door_close, "title_chime": title_chime, "wipe_whoosh": wipe_whoosh,
          "pot_break_1": lambda: pot_break(1), "pot_break_2": lambda: pot_break(2), "pot_break_3": lambda: pot_break(3),
          "chest_open": chest_open,
          "menu_move": menu_move, "menu_select": menu_select, "menu_back": menu_back, "pause_in": pause_in, "pause_out": pause_out,
          "sword_swing_1": lambda: sword_swing(1), "sword_swing_2": lambda: sword_swing(2), "sword_swing_3": lambda: sword_swing(3),
          "sword_hit_1": lambda: sword_hit(1), "sword_hit_2": lambda: sword_hit(2), "sword_hit_3": lambda: sword_hit(3)}


def save(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"  {name}.wav  {len(x) / SR:.2f}s  peak {20 * np.log10(np.abs(x).max()):.1f} dB")


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(SOUNDS)
    for n in wanted:
        save(n, SOUNDS[n]())

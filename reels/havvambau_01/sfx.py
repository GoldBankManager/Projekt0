#!/usr/bin/env python3
"""
SFX-Spur für HavvamBau Reel 01 – komplett synthetisch (numpy), auf die Beat-Map in timeline.json getaktet.

  python3 reels/havvambau_01/sfx.py                 → out/sfx.wav  (nur SFX, Musik legst du selbst drunter)
  python3 reels/havvambau_01/sfx.py --music x.mp3   → zusätzlich out/preview_mix.wav (SFX + Musik zum Sync-Check)
"""
import argparse
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
HERE = Path(__file__).parent
TL = json.loads((HERE / "timeline.json").read_text())
B, DROP, DIG, DUMP, ROLL = TL["beats"], TL["drop"], TL["dig_impact"], TL["dump"], TL["hat_roll"]
rng = np.random.default_rng(7)


# ───────── Bausteine ─────────
def t_(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def svf_sweep(x, f0, f1, q=1.2, curve=1.0):
    """Bandpass, dessen Mittenfrequenz exponentiell von f0 nach f1 läuft (State-Variable-Filter)."""
    n = len(x)
    k = (np.arange(n) / max(n - 1, 1)) ** curve
    fc = f0 * (f1 / f0) ** k
    g = 2 * np.sin(np.pi * np.minimum(fc, SR / 6) / SR)
    low = band = 0.0
    out = np.empty(n)
    damp = 1 / q
    for i in range(n):
        high = x[i] - low - damp * band
        band += g[i] * high
        low += g[i] * band
        out[i] = band
    return out


def env_ad(n, a, d, curve=3.0):
    """Attack (linear) + exponentieller Decay, Längen in Sekunden."""
    na = max(1, int(a * SR))
    e = np.zeros(n)
    e[:min(na, n)] = np.linspace(0, 1, na)[:n]
    if n > na:
        e[na:] = np.exp(-curve * np.arange(n - na) / max(1, d * SR))
    return e


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def stereo(x, pan=0.0):
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l * 1.414, x * r * 1.414], 1)


def pan_sweep(x, p0, p1):
    p = np.linspace(p0, p1, len(x))
    return np.stack([x * np.cos((p + 1) * np.pi / 4) * 1.414, x * np.sin((p + 1) * np.pi / 4) * 1.414], 1)


_IR = None


def reverb(x, wet=0.3, dur=1.2):
    global _IR
    if _IR is None:
        n = int(dur * SR)
        decay = np.exp(-6 * np.arange(n) / n)
        _IR = np.stack([lp(rng.standard_normal(n), 6000) * decay, lp(rng.standard_normal(n), 6000) * decay], 1)
        _IR /= np.sqrt(np.sum(_IR ** 2, 0))
    if x.ndim == 1:
        x = stereo(x)
    pad = np.vstack([x, np.zeros((len(_IR), 2))])
    w = np.stack([fftconvolve(pad[:, c], _IR[:, c])[:len(pad)] for c in range(2)], 1)
    return pad * (1 - wet) + w * wet


# ───────── Sounds ─────────
def impact(size=1.0, dur=None):
    dur = dur or 0.5 + 0.9 * size
    t = t_(dur)
    f = 38 + (95 - 38) * np.exp(-t * 9 / max(size, .3))
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2 / size)
    thump = bp(noise(dur), 60, 420) * np.exp(-t * 18)
    click = hp(noise(dur), 2500) * np.exp(-t * 160)
    crack = bp(noise(dur), 900, 5000) * np.exp(-t * 35) * 0.5
    x = sub * 1.0 + thump * 0.8 + click * 0.35 * size + crack * size
    return np.tanh(norm(x) * 1.6) * 0.9


def boom():
    x = impact(1.6, 2.4)
    t = t_(2.4)
    tail = lp(noise(2.4), 160, 4) * np.exp(-t * 1.6) * 0.8
    rumble = np.sin(2 * np.pi * 31 * t) * np.exp(-t * 1.2) * 0.6
    return reverb(norm(x + norm(tail) * 0.6 + rumble), 0.22, 1.6)


def whoosh(dur=0.35, f0=300, f1=3200, peak_at_end=True, pan=(-0.6, 0.6), q=1.0):
    n = noise(dur)
    x = svf_sweep(n, f0, f1, q)
    k = np.linspace(0, 1, len(x))
    e = (k ** 2.2) if peak_at_end else np.sin(np.pi * k) ** 1.5
    if peak_at_end:  # kurzer Ausklang nach dem Peak
        e = np.concatenate([e, np.exp(-np.arange(int(.06 * SR)) / (.015 * SR))])
        x = np.concatenate([x, svf_sweep(noise(.06), f1, f1 * .7, q)])
    return pan_sweep(norm(x * e), *pan)


def swish(dur=0.16, pan=(0.5, -0.5)):
    return whoosh(dur, 900, 5500, False, pan, q=1.6)


def riser(dur):
    t = t_(dur)
    k = t / dur
    f = 180 * (2400 / 180) ** (k ** 1.5)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * 0.12
    nz = svf_sweep(noise(dur), 400, 8000, 1.4, 1.5) * 0.9
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * np.cumsum(4 + 28 * k ** 2) / SR)
    return stereo(norm((tone + nz) * k ** 2.2 * trem))


def reverse_cymbal(dur):
    t = t_(dur)
    x = hp(noise(dur), 5000) * np.exp(-(dur - t) * 5)
    return reverb(norm(x), 0.2, .8)[:len(x)]


def suck(dur=0.12):
    x = svf_sweep(noise(dur), 4000, 400, 1.3)
    k = np.linspace(0, 1, len(x))
    return stereo(norm(x * k ** 1.5))


def tick(f=3200):
    t = t_(0.05)
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.13 * t)) * np.exp(-t * 140) + hp(noise(.05), 4000) * np.exp(-t * 400) * 0.6
    return norm(x)


def blip():
    f = rng.uniform(1600, 2600)
    t = t_(0.025)
    return norm(np.sin(2 * np.pi * f * t) * np.exp(-t * 220) + hp(noise(.025), 3000) * np.exp(-t * 500) * .4)


def clank(f0=420):
    t = t_(0.9)
    parts = [(1.0, 1.0, 6), (2.76, .6, 9), (5.4, .45, 13), (8.93, .3, 18), (13.3, .2, 25)]
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6)) * np.exp(-t * d) for r, a, d in parts)
    x += hp(noise(.9), 2000) * np.exp(-t * 90) * 0.8
    return reverb(norm(x), .25, .9)


def hiss(dur=0.45):
    t = t_(dur)
    x = bp(noise(dur), 2200, 7500) * (np.sin(np.pi * t / dur) ** .6)
    pump = np.sin(2 * np.pi * 110 * t) * 0.25 * np.sin(np.pi * t / dur)
    return stereo(norm(x + pump))


def debris(dur=0.8, density=90, low=True):
    out = np.zeros(int(dur * SR))
    for _ in range(int(density * dur)):
        s = int(rng.uniform(0, dur) ** 1.6 / dur ** .6 * SR)
        g = int(rng.uniform(.004, .02) * SR)
        if s + g >= len(out):
            continue
        grain = lp(rng.standard_normal(g), rng.uniform(1200, 5000)) * np.hanning(g)
        out[s:s + g] += grain * rng.uniform(.2, 1) * (1 - s / len(out))
    if low:
        t = t_(dur)
        out += lp(noise(dur), 250) * np.exp(-t * 6) * 1.5
    return norm(out)


def pour(dur=0.8):
    out = np.zeros(int(dur * SR))
    for _ in range(int(260 * dur)):
        s = int(rng.uniform(0, dur * .85) * SR)
        g = int(rng.uniform(.006, .03) * SR)
        out[s:s + g] += lp(rng.standard_normal(g), rng.uniform(600, 3500)) * np.hanning(g) * rng.uniform(.3, 1)
    t = t_(dur)
    out *= np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .2)
    return norm(out + lp(noise(dur), 300) * .6 * np.minimum(1, (dur - t) / .2))


def engine(dur, rate0=26, rate1=26, level=1.0):
    t = t_(dur)
    rate = np.linspace(rate0, rate1, len(t))
    ph = np.cumsum(rate) / SR
    pulses = (np.sin(2 * np.pi * ph) > 0.6).astype(float) * (0.7 + 0.3 * rng.random(len(t)))
    x = lp(pulses + 0.4 * np.sin(2 * np.pi * ph * 2), 320, 3) + lp(noise(dur), 200) * 0.3
    e = np.minimum(1, t / .15) * np.minimum(1, (dur - t) / .15)
    return norm(x * e) * level


def glitch(dur=0.14):
    out = np.zeros(int(dur * SR))
    pos = 0
    while pos < len(out):
        seg = int(rng.uniform(.008, .025) * SR)
        f = rng.choice([180, 400, 800, 1600, 3200])
        tt = np.arange(seg) / SR
        out[pos:pos + seg] = np.sign(np.sin(2 * np.pi * f * tt))[:len(out) - pos] * rng.uniform(.3, 1)
        pos += seg
    return stereo(norm(lp(out, 7000)) * 0.8, rng.uniform(-.3, .3))


def tape_stop(dur=0.22):
    t = t_(dur)
    f = 220 * (1 - t / dur) ** 2 + 20
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)
    x += svf_sweep(noise(dur), 2500, 120, 1.2) * 0.6
    return norm(x * (1 - t / dur) ** .5)


def shutter():
    a = tick(5200) * .8
    out = np.zeros(int(.12 * SR))
    out[:len(a)] += a
    out[int(.055 * SR):int(.055 * SR) + len(a)] += a * .7
    return out


def pop(f0=900, f1=260):
    t = t_(0.12)
    f = f1 + (f0 - f1) * np.exp(-t * 60)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30))


def thud():
    t = t_(0.3)
    f = 55 + 90 * np.exp(-t * 30)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) + bp(noise(.3), 80, 600) * np.exp(-t * 30) * .5)


def shimmer(dur=1.2):
    t = t_(dur)
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(5, 11) * t)) for f in [2093, 2637, 3136, 4186, 5274])
    return reverb(norm(x * np.exp(-t * 3.5) * np.minimum(1, t / .01)), .45, 1.5)


def flash_pop():
    t = t_(0.15)
    return norm(hp(noise(.15), 3500) * np.exp(-t * 45) + bp(noise(.15), 300, 1200) * np.exp(-t * 60) * .5)


def slowmo(dur):
    t = t_(dur)
    x = svf_sweep(noise(dur), 900, 140, 1.5) + lp(noise(dur), 120) * .8
    return reverb(norm(x * np.sin(np.pi * t / dur) ** .7), .3)[:len(t)]


# ───────── Mix ─────────
mix = np.zeros((int((TL["duration"] + 0.5) * SR), 2))


def put(t, x, db=0.0, align_end=False):
    x = stereo(x) if x.ndim == 1 else x
    g = 10 ** (db / 20)
    s = int(round(t * SR)) - (len(x) if align_end else 0)
    if s < 0:
        x, s = x[-s:], 0
    e = min(len(mix), s + len(x))
    mix[s:e] += x[:e - s] * g


# Hook: Motor + Tippen
put(0.0, engine(0.75, 24, 26, 1), -20)
txt = "Ihr Projekt."
for i in range(1, len(txt) + 1):
    if txt[i - 1] != " ":
        put(0.06 + 0.44 * (i - 0.5) / len(txt), blip(), -15)
# B0 – erster Schnitt
put(B[0] + 0.02, whoosh(0.32), -9, align_end=True)
put(B[0], impact(0.8), -5)
put(B[0], flash_pop(), -14)
# B1 – "Unser Handwerk."
put(B[1], swish(), -10)
put(B[1], thud(), -8)
txt = "Unser Handwerk."
for i in range(1, len(txt) + 1, 2):
    put(B[1] + .02 + .18 * (i - .5) / len(txt), blip(), -18)
# B2 – Kabine
put(B[2], swish(0.2, (-.5, .5)), -10)
put(B[2], clank(380), -12)
# B3 – Whip-Pan
put(B[3] + .03, whoosh(0.3, 250, 4500, True, (.8, -.8)), -6, align_end=True)
put(B[3], impact(0.7), -8)
put(B[3] + .05, engine(DIG - B[3] + .45, 26, 34, 1), -20)
# Graben
put(DIG - .12, whoosh(0.12, 200, 1200, True, (0, 0)), -12)
put(DIG, impact(1.1), -3)
put(DIG, debris(0.9), -8)
put(DIG + .02, clank(300), -16)
put(DIG + .15, hiss(0.38), -15)
put(B[5], swish(0.14), -12)
put(B[5] + .05, hiss(0.3), -17)
# Split-Screen
put(B[6], glitch(0.15), -11)
put(B[6], impact(0.6), -9)
put(B[7] - .05, whoosh(0.3, 150, 900, False, (-.4, .4)), -10)
put(B[7], thud(), -10)
# Rush auf die Kabine
put(B[8], whoosh(0.34, 200, 5000, False, (.6, -.2)), -6)
put(B[8], impact(0.6), -10)
put(3.95, tape_stop(0.22), -10)
# Break: Freeze
put(TL["break"], shutter(), -8)
put(TL["break"], thud(), -10)
# Hi-Hat-Roll: Uhr tickt
for i, r in enumerate(ROLL):
    put(r, tick(2600 + 140 * i), -11 + i * 0.4)
put(ROLL[0], whoosh(0.12, 600, 2000, False), -18)
# Spannung bis zum Drop
put(B[12], thud(), -7)
put(B[12], riser(DROP - .09 - B[12]), -7)
put(B[12] + .15, engine(DROP - B[12] - .25, 24, 60, 1), -17)
put(DROP - .09, reverse_cymbal(0.55), -9, align_end=True)
put(B[13], swish(0.1), -12)
put(B[13], tick(5000), -14)
put(DROP - .09, suck(0.14), -10, align_end=True)
# DROP
put(DROP, boom(), 0)
put(DROP, debris(1.4, 140), -6)
put(DROP, flash_pop(), -8)
put(DROP + .03, clank(260), -14)
put(DROP + .02, slowmo(B[15] - DROP + .1), -13)
put(DROP + .2, engine(B[21] - DROP - .1, 30, 28, 1), -22)
# nach dem Drop
put(B[15] + .03, whoosh(0.26, 220, 3800, True, (-.8, .8)), -7, align_end=True)
put(B[15], impact(0.8), -6)
put(B[16], clank(520), -9)
put(B[16], swish(0.18), -11)
put(B[16] + .05, shimmer(0.6), -20)
put(B[17], hiss(0.4), -11)
put(B[17], whoosh(0.32, 150, 800, False, (.3, -.3)), -11)
put(B[17], thud(), -9)
put(DUMP, swish(0.14), -12)
put(DUMP + .05, pour(0.8), -7)
put(B[19] + .03, whoosh(0.28, 250, 4500, True, (.8, -.8)), -6, align_end=True)
put(B[19], impact(0.9), -5)
put(B[19] + .05, thud(), -6)
put(B[20], impact(0.7), -6)
put(B[20], flash_pop(), -14)
# Logo
T0 = B[21]
put(T0, whoosh(0.22, 400, 6000, False, (0, 0)), -9)
put(T0, flash_pop(), -10)
put(T0 + .03 + .1, thud(), -8)
put(T0 + .11 + .1, thud(), -9)
put(T0 + .2, swish(0.12, (-.6, .6)), -13)
put(T0 + .28, swish(0.12, (.6, -.6)), -15)
w0 = TL["end_hits"][0]
for i in range(9):
    put(w0 + i * .022, pop(1300 + 60 * i, 600), -19)
put(w0, impact(0.5), -9)
put(TL["end_hits"][1], thud(), -9)
put(TL["end_hits"][1], shimmer(0.8), -17)
put(TL["end_hits"][2], impact(0.6), -8)
put(TL["end_hits"][2], shimmer(1.4), -14)

# Master: Hochpass gegen DC, Soft-Limiter, -1 dBFS, Fade-Out am Ende
mix = np.stack([hp(mix[:, c], 25) for c in range(2)], 1)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.1) / np.tanh(1.1)
mix *= 10 ** (-1 / 20)
n_end = int(TL["duration"] * SR)
mix = mix[:n_end]
mix[-int(.25 * SR):] *= np.linspace(1, 0, int(.25 * SR))[:, None]


def write_wav(path, x):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--music", type=Path, help="Musik nur für eine Sync-Vorschau dazumischen")
    a = ap.parse_args()
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    write_wav(out / "sfx.wav", mix)
    print("✓", out / "sfx.wav")
    if a.music:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out / "sfx.wav"), "-i", str(a.music), "-filter_complex",
                        "[1:a]aresample=48000,volume=0.8[m];[0:a][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[o]",
                        "-map", "[o]", "-t", str(TL["duration"]), str(out / "preview_mix.wav")], check=True)
        print("✓", out / "preview_mix.wav")

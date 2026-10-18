"""Soundtrack for video_v2.html: the supplied music + SFX synced to the animation.

usage: python3 sound_v2.py <music.mp3> <out.wav>
Timings use the same eighth-note grid as video_v2.html (166 BPM, eighth = 0.3615 s).
"""
import subprocess
import sys
import wave
import numpy as np

SR = 48000
DUR = 9.8
N = int(DUR * SR)
rng = np.random.default_rng(5)
B0, E8 = -0.04, 0.3615


def beat(k):
    return B0 + E8 * k


DROP = beat(16)


def load_music(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype='<i2').astype(float).reshape(-1, 2) / 32768
    out = np.zeros((N, 2))
    out[:min(N, len(x))] = x[:N]
    return out


L = np.zeros(N)
R = np.zeros(N)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def lowpass(x, fc):
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def band(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


# ---------- sound palette (like the reference SFX pack) ----------
def click():                       # typing / UI click
    n = int(.03 * SR)
    x = band(rng.normal(0, 1, n), 1500, 7000) * env(n, .0003, .004)
    return x + np.sin(2 * np.pi * 3200 * np.arange(n) / SR) * env(n, .0002, .003) * .3


def typing(t0, dur, count, gain=.35):
    for k in range(count):
        add(click(), t0 + rng.random() * dur, gain * (.6 + .4 * rng.random()), pan=rng.uniform(-.3, .3))


def shutter():                     # camera shutter: two mechanical clicks
    n = int(.12 * SR)
    x = np.zeros(n)
    for off, g in ((0, 1), (.045, .7)):
        i = int(off * SR); m = int(.02 * SR)
        x[i:i + m] += band(rng.normal(0, 1, m), 800, 6000) * env(m, .0003, .005) * g
    return x


def shine():                       # sparkle for the glow line
    n = int(1.1 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * a for f, a in ((2637, 1), (3520, .7), (4699, .5), (5274, .35)))
    shimmer = 1 + .35 * np.sin(2 * np.pi * 14 * t)
    return s * shimmer * env(n, .01, .28) * .22


def whoosh(d=.4):
    n = int(d * SR); k = np.arange(n) / n
    y = band(rng.normal(0, 1, n), 250, 400 + 6000 * np.sin(np.pi * k) ** 2)
    return y * np.sin(np.pi * k) ** 2 * 1.6


def rustle(d=.45):                 # paper
    n = int(d * SR); t = np.arange(n) / SR
    x = band(rng.normal(0, 1, n), 900, 5000)
    am = np.clip(lowpass(rng.normal(0, 1, n), 30) * 8, 0, None)
    return x * am * np.sin(np.pi * t / d) * .5


def scribble(d=.3):                # marker on paper
    n = int(d * SR); t = np.arange(n) / SR
    x = band(rng.normal(0, 1, n), 1200, 3500)
    am = .55 + .45 * np.sin(2 * np.pi * 11 * t + 2 * np.sin(2 * np.pi * 3 * t))
    return x * am * np.minimum(1, t / .02) * np.minimum(1, (d - t) / .04) * .6


def stones(d=.7, density=220):     # gravel
    n = int(d * SR); x = np.zeros(n)
    for _ in range(int(density * d)):
        i = int(rng.random() * (n - 600)); g = rng.random()
        x[i:i + 600] += rng.normal(0, 1, 600) * np.exp(-np.arange(600) / 70) * g
    x = band(x, 1500, 9000)
    t = np.arange(n) / SR
    return x * np.sin(np.pi * t / d) ** .7 * .3


def thud(d=.3, f0=90):             # stamp
    n = int(d * SR); t = np.arange(n) / SR
    f = 45 + f0 * np.exp(-t * 24)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .07) + band(rng.normal(0, 1, n), 200, 2500) * env(n, .0005, .02) * .6


def pop():
    n = int(.12 * SR); t = np.arange(n) / SR
    f = 1100 - 700 * t / .12
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .03) * .7


def riser(d):
    n = int(d * SR); k = np.arange(n) / n
    noise = band(rng.normal(0, 1, n), 400, 600 + 9000 * k ** 2) * k ** 2.5
    f = 200 + 1400 * k ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * k ** 3 * .25
    return (noise * 1.2 + tone) * np.clip((1 - k) / .015, 0, 1)


def impact(d=1.8):
    n = int(d * SR); t = np.arange(n) / SR
    f = 32 + 80 * np.exp(-t * 8)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .5)
    crack = band(rng.normal(0, 1, n), 300, 5000) * env(n, .0005, .06)
    return np.tanh((boom + crack) * 1.5) * .9


def main():
    # ---------- cue sheet (matches video_v2.html) ----------
    typing(0.0, .38, 12)                          # "Ihre Wärmepumpe"
    add(whoosh(.5), .05, .25, pan=.4)             # pump slides in
    typing(beat(2) - .06, .34, 10)                # "ist bestellt. Und das"
    add(shutter(), beat(5), .55)                  # viewfinder snaps
    typing(beat(5) + .05, .3, 9, .3)              # "Fundament?"
    add(shine(), beat(6), .8)                     # glow line
    add(pop(), beat(6) - .04, .5)                 # eye icon
    for i in range(3):
        add(pop(), beat(6) + .16 + i * .09, .4, pan=.2 * i)
    add(whoosh(.36), beat(8) - .2, .7, pan=-.2)   # whip to scene 2
    add(shutter(), beat(8), .5)                   # bracket + label box
    add(stones(.8), beat(8) + .05, .7, pan=.35)   # foundation rises
    typing(beat(9) - .08, .32, 7)                 # "Saubere"
    typing(beat(10) - .18, .3, 10, .3)            # "Grundlage."
    add(shine(), beat(10), .7)
    for i in range(3):
        add(pop(), beat(10) + .25 + i * .09, .25)
    add(rustle(.5), beat(12) - .35, .8, pan=.2)   # notepad slides in
    add(whoosh(.36), beat(12) - .2, .6, pan=.2)   # whip to scene 3
    typing(beat(12) - .12, .3, 8, .25)
    for b in (12, 13, 14):                        # stamps
        add(thud(), beat(b) - .03, .5)
    add(scribble(.18), beat(12) + .12, .45)       # check marks
    add(scribble(.18), beat(13) + .12, .45)
    add(scribble(.3), beat(14) + .08, .5)         # circle
    add(riser(DROP - (beat(15) - .1)), beat(15) - .1, .55)   # rush into the drop
    add(impact(), DROP, .75)
    add(shutter(), DROP, .5)
    typing(beat(17) - .12, .24, 8, .25)           # "Wir schaffen die"
    typing(beat(18) - .16, .26, 9, .25)           # "Grundlage."
    add(shine(), beat(18), .6)
    for i in range(6):                            # service badges
        add(pop(), beat(19) - .1 + i * .09, .3, pan=-.4 + i * .16)
    add(whoosh(.45), beat(20) - .1, .6, pan=-.3)  # whip to CTA
    add(pop(), beat(21) - .12, .4)
    add(shutter(), beat(21), .45)
    typing(beat(21) - .05, .25, 5, .25)           # "Jetzt"
    typing(beat(21) + .08, .26, 8, .25)           # "anfragen."
    typing(beat(22) - .16, .2, 10, .3)            # phone number
    add(scribble(.34), beat(22), .55)             # marker circle
    typing(beat(23) - .2, .25, 9, .22)            # website
    add(shine(), beat(23), .55)
    for i in range(3):
        add(pop(), beat(24) + i * .09, .35)

    music = load_music(sys.argv[1])
    sfx = np.stack([L, R], 1)
    mix = music * 1.0 + sfx * .55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= .9 / np.abs(mix).max()
    out = sys.argv[2]
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print('wrote', out)


if __name__ == '__main__':
    main()

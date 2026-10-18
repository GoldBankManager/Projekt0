"""Synthesised sound design for the HavvamBau reel (timings match video.html)."""
import sys
import wave
import numpy as np

SR = 48000
T = dict(proj=4.0, burst=12.0, punch=14.0, serv=17.0, steps=22.0, end=26.0, total=32.5)
N = int(T['total'] * SR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)
BEAT = 0.5  # 120 BPM


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def kick(d=0.45):
    n = int(d * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, .002, .16) + rng.normal(0, 1, n) * env(n, .0005, .004) * .25


def hat(d=0.08):
    n = int(d * SR)
    x = rng.normal(0, 1, n)
    x = x - lowpass(x, 7000)
    return x * env(n, .0005, .018)


def clap():
    n = int(.25 * SR)
    x = rng.normal(0, 1, n)
    x = x - lowpass(x, 1200)
    e = sum(env(n, .0005, .012) * (np.arange(n) >= int(k * SR)) for k in (0, .01, .02)) + env(n, .001, .07) * .6
    return x * e * .5


def impact(d=2.2):
    n = int(d * SR); t = np.arange(n) / SR
    f = 30 + 90 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .003, .55)
    noise = lowpass(rng.normal(0, 1, n), 900) * env(n, .001, .25) * 1.4
    return np.tanh((boom + noise) * 1.6) * .9


def whoosh(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    k = t / d
    fc = 300 + 6000 * k ** 2
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty(n); acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    hp = y - lowpass(y, 200)
    shape = k ** 2.2 * np.clip((1 - k) / .08, 0, 1)
    return hp * shape * 2.2


def tick():
    n = int(.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * .6 + np.sin(2 * np.pi * 1200 * t)) * env(n, .0003, .008) * .5


def pop():
    n = int(.18 * SR); t = np.arange(n) / SR
    f = 900 - 500 * t / .18
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .05) * .6


def chime():
    n = int(2.5 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((880, 1), (1318.5, .5), (1760, .25)))
    return s * env(n, .002, .6) * .25


def thud(d=.35, f0=95):
    n = int(d * SR); t = np.arange(n) / SR
    f = 40 + f0 * np.exp(-t * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .09)
    grit = lowpass(rng.normal(0, 1, n), 1500) * env(n, .001, .05)
    return body + grit * .8


def rattle(d=.8, density=260):
    n = int(d * SR); x = np.zeros(n)
    for _ in range(int(density * d)):
        i = int(rng.random() * (n - 800)); g = rng.random()
        x[i:i + 800] += rng.normal(0, 1, 800) * np.exp(-np.arange(800) / 90) * g
    x = x - lowpass(x, 1800)
    t = np.arange(n) / SR
    return x * np.sin(np.pi * t / d) * .35


def zip_(d=.6):
    n = int(d * SR); x = np.zeros(n)
    ts = np.cumsum(np.full(60, d / 60))
    for k, tk in enumerate(ts[:-1]):
        i = int(tk * SR); x[i:i + 300] += np.sin(2 * np.pi * (1800 + k * 25) * np.arange(300) / SR) * np.exp(-np.arange(300) / 50)
    return x * .35


# ---------- music bed ----------
CHORDS = [(55.0, [220, 261.63, 329.63]),    # Am
          (43.65, [174.61, 220, 261.63]),   # F
          (65.41, [196, 261.63, 329.63]),   # C
          (49.0, [196, 246.94, 293.66])]    # G
tt = np.arange(N) / SR
bass = np.zeros(N); pad = np.zeros(N)
for k in range(int(T['total'] / 4) + 1):
    root, notes = CHORDS[k % 4]
    a, b = int(k * 4 * SR), min(N, int((k + 1) * 4 * SR))
    if a >= N:
        break
    seg = tt[a:b] - k * 4
    bass[a:b] = np.sin(2 * np.pi * root * seg) + .3 * np.sin(2 * np.pi * root * 2 * seg)
    for f in notes:
        for det in (-.15, .15):
            ph = (f + det) * seg
            pad[a:b] += 2 * (ph - np.floor(ph + .5))  # saw
xf = np.clip(np.minimum(tt % 4, 4 - tt % 4) / .05, 0, 1)  # declick chord changes
bass *= xf; pad = lowpass(pad * xf, 1100) * .06

# sidechain from kick grid
duck = np.ones(N)
kick_times = []
for b in np.arange(T['proj'], T['end'] + 2.01, BEAT):
    if T['punch'] + .5 <= b < T['serv']:
        continue  # breakdown for the punchline
    kick_times.append(b)
for kt in kick_times:
    i = int(kt * SR); n = int(.35 * SR)
    seg = 1 - .65 * np.exp(-np.arange(min(n, N - i)) / SR / .09)
    duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg)

# arrangement envelopes
def ramp(t0, t1, v0, v1):
    return np.interp(tt, [t0, t1], [v0, v1])

bass_lvl = np.where(tt < T['proj'], ramp(1.6, T['proj'], 0, .12), .28)
bass_lvl = np.where((tt > T['punch'] + .5) & (tt < T['serv']), .16, bass_lvl)
pad_lvl = np.clip(ramp(0, 1.0, .5, 1), 0, 1)
master_fade = np.clip(np.interp(tt, [T['total'] - 2.6, T['total'] - .1], [1, 0]), 0, 1)
L += (bass * bass_lvl * duck + pad * pad_lvl * duck)
R += (bass * bass_lvl * duck + pad * pad_lvl * duck * .92)

# ---------- drums ----------
for kt in kick_times:
    add(kick(), kt, .85)
for b in np.arange(T['proj'] + .25, T['end'] + 2, BEAT):
    if T['punch'] + .5 <= b < T['serv']:
        continue
    add(hat(), b, .22, pan=.25)
for b in np.arange(T['burst'], T['punch'] + .01, .25):
    add(hat(.05), b, .12, pan=-.3)
for c in (T['proj'] + 1, T['proj'] + 3, T['proj'] + 5, T['proj'] + 7, T['burst'], T['burst'] + .5, T['burst'] + 1,
          T['steps'] + 1, T['steps'] + 3):
    add(clap(), c, .55)

# ---------- hook ----------
add(impact(), .06, .95)
add(impact(1.6), .52, .8)
add(whoosh(.9), T['proj'] - .9, .6)         # pump lifts off
add(tick(), 2.55, .7)                        # highlight bar
# ---------- transitions ----------
for k in range(1, 4):
    add(whoosh(.4), T['proj'] + k * 2 - .35, .25, pan=(-1) ** k * .3)
S0 = T['proj']
for s_ in (S0 + .3, S0 + .85, S0 + 1.4):           # excavator scoops + dirt landing on the pile
    add(thud(), s_, .8, pan=-.1)
    add(rattle(.35, 120), s_ + .55, .7, pan=.5)
add(zip_(.6), S0 + 2.15, .8)                         # measuring tape
add(pop(), S0 + 3.05, .9)                            # "passt"
add(rattle(.8), S0 + 4.12, .9)                       # gravel bed
add(thud(.5, 60), S0 + 4.95, .6)                     # slab pour
add(whoosh(.45), S0 + 5.0, .35, pan=.4)              # screed sweep
for i in range(10):                                  # pavers
    add(tick(), S0 + (6.1 + i * .07 if i < 5 else 6.45 + (i - 5) * .07), .45, pan=-.4 + i * .08)
add(whoosh(.7), S0 + 6.25, .4)                       # pump lowered
add(thud(.4, 80), S0 + 6.95, .9)                     # pump sets down
add(chime(), S0 + 7.15, .7)                          # check
add(whoosh(.5), T['punch'] - .45, .6)
add(impact(1.8), T['punch'] + 1.85, .75)     # "Wir."
add(whoosh(.45), T['serv'] - .4, .4)
for j in range(7):
    add(tick(), T['serv'] + .6 + j * .5, .8, pan=.15)
add(whoosh(.45), T['steps'] - .4, .4)
for i in range(3):
    add(pop(), T['steps'] + .5 + i * .62, .9)
add(whoosh(.6), T['end'] - .55, .7)
add(impact(2.4), T['end'] + .55, .8)          # logo
add(chime(), T['end'] + 2.05, .9)             # CTA lands

mix = np.stack([L, R], 1) * master_fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix *= .89 / np.abs(mix).max()
out = sys.argv[1] if len(sys.argv) > 1 else 'out/sound.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out)

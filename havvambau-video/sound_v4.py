"""Soundtrack for video_v4.html.

The supplied clip (9.8 s) is extended on its own bar grid so the video can breathe:
  intro + build-up (0 – 5.74 s) · drop bar (5.74 – 8.63 s) four times · original fade-out.
The clip is faded out from the drop onwards, so every drop copy gets a gain ramp that
undoes that decay; each splice sits on a downbeat with a short equal-power crossfade.

usage: python3 sound_v4.py <music.mp3> <out.wav>
"""
import subprocess
import sys
import wave
import numpy as np
import sound_v2 as base
from sound_v2 import SR, shutter, shine, whoosh, thud, pop, riser, impact
from sound_v3 import flutter, ticks, roll, boing

B0, E8 = -0.04, 0.3615
beat = lambda k: B0 + E8 * k
DROP_A, DROP_B = beat(16), beat(24)          # one drop bar in the source clip
REPEATS = 4
SRC_END = 9.8
DUR = DROP_A + REPEATS * (DROP_B - DROP_A) + (SRC_END - DROP_B)
N = int(DUR * SR)
XF = int(.150 * SR)                           # beat-matched crossfade length


def downbeat(src, guess, search=.04):
    """Sample index where the kick's click starts near `guess` (rise of high-band energy)."""
    a, b = int((guess - search) * SR), int((guess + search) * SR)
    hi = np.abs(np.diff(src[a:b].mean(1)))
    k = int(.002 * SR)
    env = np.convolve(hi, np.ones(k) / k, 'same')
    return a + int(np.argmax(env > .5 * env.max()))


def extend(src, repeats=REPEATS, n=N):
    # splice 30 ms before the kick click (measured, not the rounded grid). Both cut points sit at
    # the same spot relative to their downbeat, so the crossfade is beat-matched: the original
    # next kick plays while the repeated bar fades in underneath
    pre = int(.030 * SR)
    a = downbeat(src, DROP_A) - pre
    b = downbeat(src, DROP_B) - pre
    bar = src[a:b].copy()
    # undo the clip's fade across the drop bar: fit the RMS decay per eighth, flatten it
    e8 = int(E8 * SR)
    t = np.array([(k + .5) * E8 for k in range(8)])
    r = np.array([np.sqrt((bar[k * e8:(k + 1) * e8] ** 2).mean()) for k in range(8)])
    slope, icpt = np.polyfit(t, r, 1)
    comp = lambda sec: icpt / (icpt + slope * sec)
    bar *= comp(np.arange(len(bar)) / SR)[:, None]
    end_gain = comp((b - a) / SR)
    tail = src[b:int(SRC_END * SR)] * end_gain             # continue at the compensated level
    # each part carries the XF samples that follow it in the source, so crossfades overlap into
    # real continuation and the total length (and beat grid) is preserved exactly
    parts = [(src[:a], src[a:a + XF])] + [(bar, src[b:b + XF] * end_gain)] * repeats + [(tail, None)]
    fade_in = np.sin(np.linspace(0, np.pi / 2, XF))[:, None]
    fade_out = np.cos(np.linspace(0, np.pi / 2, XF))[:, None]
    chunks, ext = [parts[0][0]], parts[0][1]
    for body, nxt_ext in parts[1:]:
        chunks.append(ext * fade_out + body[:XF] * fade_in)
        chunks.append(body[XF:])
        ext = nxt_ext
    out = np.concatenate(chunks)
    res = np.zeros((n, 2))
    res[:min(n, len(out))] = out[:n]
    return res


def main():
    base.N = N
    base.L = np.zeros(N)
    base.R = np.zeros(N)
    add = base.add
    k = beat
    # ---- A: hook
    add(whoosh(.45), 0.0, .55, pan=-.4)
    flutter(.05, .4, 8, .22)
    add(shutter(), k(2), .5)
    add(whoosh(.3), k(4) - .1, .5, pan=.5)            # panel wipes off
    flutter(k(4) + .1, .3, 7, .2)
    add(whoosh(.35), k(5) - .25, .5)                   # heat pump drops in
    add(thud(.35, 80), k(5), .6)
    add(pop(), k(6), .4)                               # LED blink
    # ---- B: stack
    add(whoosh(.4), k(8) - .25, .6)
    add(thud(.3, 90), k(8), .45)
    add(pop(), k(9), .5)                               # "Und wer macht das"
    add(pop(), k(10), .8); add(shine(), k(10), .45)    # red a
    add(whoosh(.35), k(11), .3)
    # ---- C: Ohne Grundlage steht nichts.
    for b in (12, 13, 14):
        add(whoosh(.22), k(b) - .12, .45, pan=(-1) ** b * .4)
        add(thud(.28, 85), k(b), .45)
    add(base.stones(.6), k(14) + .05, .6)              # pump tips over, ground cracks
    add(thud(.4, 60), k(14) + .25, .6)
    add(pop(), k(15) + .02, .6)
    add(riser(DROP_A - k(15) - .05), k(15) + .05, .35)
    # ---- DROP 1: lens
    add(impact(), DROP_A, .8); add(shutter(), DROP_A, .45)
    for b in (17, 18, 20, 22):
        add(pop(), k(b), .4)
    flutter(k(18) - .1, .3, 6, .2)
    # ---- DROP 2/3: four services with illustrations
    for i in range(4):
        s = k(24 + 4 * i)
        add(whoosh(.35), s - .25, .55, pan=(-1) ** i * .5)
        add(shutter(), s, .35)
        flutter(s + .05, .3, 6, .18)
        add(pop(), s + .35, .35)
    for j in range(3):                                 # excavator scoops
        add(thud(.25, 70), k(25) + j * .36, .35)
    add(base.stones(.7), k(29) - .1, .5)               # gravel bed
    add(thud(.3, 80), k(30), .5)                       # heat pump lands on the slab
    ticks(k(32) + .25, .9, 18, .3)                     # pavers click in
    add(whoosh(.6), k(36) + .2, .35)                   # tree grows
    add(pop(), k(37), .5); add(pop(), k(37) + .12, .4)
    # ---- CTA
    add(whoosh(.4), k(40) - .2, .5)
    add(boing(), k(40), .7)
    add(roll(k(41) - k(40) - .05), k(40) + .04, .6)
    flutter(k(40) + .12, .3, 6, .2)
    add(pop(), k(42) - .1, .7)                         # phone icon
    add(whoosh(.5), k(42) - .28, .55, pan=.6)
    ticks(k(42) - .2, .35, 10, .22)
    add(whoosh(.3), k(44) - .22, .45, pan=.4)
    add(shine(), k(46) - .05, .55)

    music = extend(load_music_full(sys.argv[1]))
    mix = music + np.stack([base.L, base.R], 1) * .55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= .9 / np.abs(mix).max()
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print(f'wrote {sys.argv[2]}  ({DUR:.3f} s)')


def load_music_full(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<i2').astype(float).reshape(-1, 2) / 32768


if __name__ == '__main__':
    main()

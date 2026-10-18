"""Soundtrack for video_v6.html: the supplied music (six drop bars) up front, light SFX underneath.

usage: python3 sound_v6.py <music.mp3> <out.wav>
"""
import sys
import wave
import numpy as np
import sound_v2 as base
from sound_v2 import SR, shutter, shine, whoosh, thud, pop, riser, impact
from sound_v3 import roll, boing
from sound_v4 import beat as k, DROP_A, DROP_B, SRC_END, extend, load_music_full

REPEATS = 6
DUR = DROP_A + REPEATS * (DROP_B - DROP_A) + (SRC_END - DROP_B)
N = int(DUR * SR)
E8 = k(1) - k(0)
TIP = [k(16), k(24), k(32), k(40)]
BRAND, CTA = k(48), k(56)
SFX_GAIN = .3          # SFX sit well under the music


def main():
    base.N = N
    base.L = np.zeros(N)
    base.R = np.zeros(N)
    add = base.add
    # hook
    add(whoosh(.45), 0.0, .5, pan=-.4)
    add(whoosh(.3), k(4) - .1, .4, pan=.4)
    add(thud(.35, 80), k(5), .5)                       # heat pump lands
    # promise
    add(whoosh(.5), k(8) - .3, .5)
    add(thud(.4, 70), k(8), .5)
    # "Sie steht dort viele Jahre."
    for b in (12, 13, 14):
        add(whoosh(.22), k(b) - .12, .35, pan=(-1) ** b * .4)
    add(pop(), k(15) + .02, .5)
    add(riser(DROP_A - k(15) - .05), k(15) + .05, .3)
    add(impact(1.2), DROP_A, .45)
    # tips: one swoosh per card, one soft pop + shine for each check
    for i, s in enumerate(TIP):
        if i:
            add(whoosh(.35), s - .25, .45, pan=(-1) ** i * .5)
        add(pop(), s + 6 * E8, .55); add(shine(), s + 6 * E8, .35)
    add(thud(.3, 80), TIP[0] + .8, .4)                 # slab drops
    add(base.click(), TIP[1] + 1.25, .7)               # level settles
    for j in range(5):                                 # condensate drips
        add(pop(), TIP[2] + .9 + j * .3, .15, pan=.3 * np.sin(j))
    add(roll(.6), TIP[3] + .5, .3)                     # trench opens
    # brand
    add(whoosh(.4), BRAND - .3, .45)
    add(impact(1.0), BRAND, .35)
    # CTA
    add(whoosh(.4), CTA - .2, .4)
    add(boing(), CTA, .5)
    add(roll(k(57) - CTA + .05), CTA + .04, .4)
    add(pop(), k(58) - .1, .5)
    add(whoosh(.4), k(58) - .28, .35, pan=.6)
    add(shine(), k(62) - .05, .4)

    music = extend(load_music_full(sys.argv[1]), REPEATS, N)
    mix = music + np.stack([base.L, base.R], 1) * SFX_GAIN
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= .9 / np.abs(mix).max()
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print(f'wrote {sys.argv[2]}  ({DUR:.3f} s)')


if __name__ == '__main__':
    main()

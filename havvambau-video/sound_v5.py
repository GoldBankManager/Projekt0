"""Soundtrack for video_v5.html: the supplied music extended to six drop bars + SFX.

usage: python3 sound_v5.py <music.mp3> <out.wav>
"""
import sys
import wave
import numpy as np
import sound_v2 as base
from sound_v2 import SR, shutter, shine, whoosh, thud, pop, riser, impact
from sound_v3 import flutter, ticks, roll, boing
from sound_v4 import beat as k, DROP_A, DROP_B, SRC_END, extend, load_music_full

REPEATS = 6
DUR = DROP_A + REPEATS * (DROP_B - DROP_A) + (SRC_END - DROP_B)
N = int(DUR * SR)
E8 = k(1) - k(0)
TIP = [k(16), k(24), k(32), k(40)]
BRAND, CTA = k(48), k(56)


def main():
    base.N = N
    base.L = np.zeros(N)
    base.R = np.zeros(N)
    add = base.add
    # ---- A: hook
    add(whoosh(.45), 0.0, .55, pan=-.4)
    flutter(.05, .4, 8, .22)
    add(shutter(), k(2), .5)
    add(whoosh(.3), k(4) - .1, .5, pan=.5)
    flutter(k(4) + .1, .3, 7, .2)
    add(whoosh(.35), k(5) - .25, .5)
    add(thud(.35, 80), k(5), .6)
    # ---- B: the promise "4 Dinge …"
    add(whoosh(.5), k(8) - .3, .6)
    add(thud(.4, 70), k(8), .6)
    add(pop(), k(8) + .05, .5)
    for b in (8, 9, 9.7, 10):
        flutter(k(b) - .05, .3, 5, .18)
    # ---- C: "Sonst kippt sie oder sackt ab."
    for b in (12, 13, 14):
        add(whoosh(.22), k(b) - .12, .45, pan=(-1) ** b * .4)
        add(thud(.28, 85), k(b), .45)
    add(base.stones(.6), k(14) + .05, .6)
    add(thud(.4, 60), k(14) + .25, .6)
    add(pop(), k(15) + .02, .6)
    add(riser(DROP_A - k(15) - .05), k(15) + .05, .35)
    add(impact(), DROP_A, .8); add(shutter(), DROP_A, .45)
    # ---- tips
    for i, s in enumerate(TIP):
        if i:
            add(whoosh(.35), s - .25, .55, pan=(-1) ** i * .5)
        add(shutter(), s, .3)
        flutter(s + .05, .3, 6, .18)
        flutter(s + .3, .4, 6, .12)
        add(pop(), s + .2, .35)
        add(pop(), s + 6 * E8, .7); add(shine(), s + 6 * E8, .5)     # check stamp
    add(base.stones(.6), TIP[0] + .35, .5); add(thud(.3, 80), TIP[0] + .8, .5)   # gravel, slab
    add(thud(.25, 70), TIP[0] + 1.1, .35)                                         # load arrows
    add(base.click(), TIP[1] + 1.25, .9); add(pop(), TIP[1] + 1.3, .4)            # level settles
    for j in range(8):                                                            # condensate drips
        add(pop(), TIP[2] + .9 + j * .17, .18, pan=.3 * np.sin(j))
    add(roll(.6), TIP[3] + .5, .45)                                              # trench opens
    ticks(TIP[3] + 1.55, .45, 7, .35)                                            # paving closes it
    # ---- brand
    add(whoosh(.4), BRAND - .3, .55)
    add(impact(1.2), BRAND, .55); add(shutter(), BRAND, .4)
    for b in (50, 52, 54):
        add(pop(), k(b), .35)
    flutter(k(50) - .1, .3, 6, .2)
    # ---- CTA
    add(whoosh(.4), CTA - .2, .5)
    add(boing(), CTA, .7)
    add(roll(k(57) - CTA + .05), CTA + .04, .6)
    flutter(CTA + .12, .3, 6, .2)
    add(pop(), k(58) - .1, .7)
    add(whoosh(.5), k(58) - .28, .55, pan=.6)
    ticks(k(58) - .2, .35, 10, .22)
    add(whoosh(.3), k(60) - .22, .45, pan=.4)
    add(shine(), k(62) - .05, .55)

    music = extend(load_music_full(sys.argv[1]), REPEATS, N)
    mix = music + np.stack([base.L, base.R], 1) * .55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= .9 / np.abs(mix).max()
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print(f'wrote {sys.argv[2]}  ({DUR:.3f} s)')


if __name__ == '__main__':
    main()

"""Soundtrack for video_v3.html: the supplied music + SFX synced to the kinetic type.

usage: python3 sound_v3.py <music.mp3> <out.wav>
"""
import sys
import wave
import numpy as np
from sound_v2 import (SR, N, L, R, rng, add, env, band, beat, DROP, load_music, click, shutter, shine, whoosh,
                      thud, pop, riser, impact)


def flutter(t0, dur, count, gain=.3):        # many small letter swishes
    for _ in range(count):
        add(whoosh(.09 + rng.random() * .08), t0 + rng.random() * dur, gain * (.5 + .5 * rng.random()),
            pan=rng.uniform(-.7, .7))


def ticks(t0, dur, count, gain=.3):
    for _ in range(count):
        add(click(), t0 + rng.random() * dur, gain * (.6 + .4 * rng.random()), pan=rng.uniform(-.4, .4))


def roll(d):                                   # the red dot rolling over paper
    n = int(d * SR); t = np.arange(n) / SR
    x = band(rng.normal(0, 1, n), 80, 900)
    am = .7 + .3 * np.sin(2 * np.pi * (18 + 30 * t / d) * t)
    return x * am * np.minimum(1, t / .03) * np.minimum(1, (d - t) / .05) * .9


def boing():                                    # dot lands
    n = int(.35 * SR); t = np.arange(n) / SR
    f = 180 + 260 * np.exp(-t * 18) * (1 + .3 * np.sin(2 * np.pi * 22 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .09) * .8


def main():
    TB, TC, TD, TE, TG, TH = beat(4), beat(8), beat(12), beat(15), beat(19), beat(20)
    # A – "Ihre Wärmepumpe": panel sweep, letters fly in
    add(whoosh(.45), 0.0, .55, pan=-.4)
    flutter(.05, .4, 8, .22)
    add(shutter(), beat(2), .55)                         # panel fills the frame
    add(thud(.25, 70), beat(2), .35)
    add(whoosh(.4), beat(3) - .05, .35, pan=-.6)          # outline ghosts
    add(whoosh(.4), beat(3) - .02, .35, pan=.6)
    # B – "bestellt?" / stack
    add(whoosh(.3), TB - .1, .5, pan=.5)                  # panel wipes off
    flutter(TB + .14, .3, 7, .2)
    add(whoosh(.35), beat(5) - .2, .6)                    # stack slams in
    add(thud(.3, 90), beat(5), .45)
    add(pop(), beat(5) + .08, .5)                         # "Und das" box
    add(pop(), beat(6), .8)                               # red "a"
    add(shine(), beat(6), .45)
    add(whoosh(.35), beat(7), .3)                         # dissolve
    # C – scattered letters assemble
    flutter(TC, .55, 12, .25)
    ticks(TC + .2, .45, 9, .25)
    add(thud(.3, 100), beat(10), .5)                      # word complete
    add(whoosh(.5), beat(10), .35)                        # outline G grows
    add(riser(TD - beat(11)), beat(11), .35)              # zoom through the G
    # D – cumulative stack
    for b in (12, 13, 14):
        add(whoosh(.22), beat(b) - .12, .45, pan=(-1) ** b * .4)
        add(thud(.28, 85), beat(b), .45)
        add(shutter(), beat(b), .3)                       # panel jumps
    # E – silence, dot grows
    add(pop(), TE + .02, .6)
    add(riser(DROP - TE - .05), TE + .05, .35)
    # F – drop
    add(impact(), DROP, .8)
    add(shutter(), DROP, .45)
    for b in (17, 18):
        add(pop(), beat(b), .45)
    # G – lens falls, dot bounces and rolls
    add(whoosh(.4), TG - .05, .5, pan=.3)
    add(pop(), TG, .6)
    add(boing(), TH, .7)
    add(roll(beat(21) - TH - .05), TH + .04, .6)
    # H – CTA
    flutter(TH + .12, .3, 6, .2)
    add(whoosh(.5), beat(22) - .28, .55, pan=.6)          # phone number on the wave
    ticks(beat(22) - .2, .35, 10, .22)
    add(whoosh(.3), beat(23) - .22, .45, pan=.4)
    add(shine(), beat(24) - .05, .55)                     # logo

    music = load_music(sys.argv[1])
    mix = music + np.stack([L, R], 1) * .55
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= .9 / np.abs(mix).max()
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print('wrote', sys.argv[2])


if __name__ == '__main__':
    main()

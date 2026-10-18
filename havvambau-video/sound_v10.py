"""Soundtrack for video_v10.html – no loops.

The two supplied clips are parts of the same song (83 BPM):
  track.mp3  (9.8 s): intro + build-up + drop
  track2.mp3 (16.5 s): the drop groove, starting on a downbeat
Music = track.mp3 through its drop hit, then all of track2.mp3 placed on the same beat grid
(found by cross-correlating onset envelopes); short fade-out because track2 stops mid-bar.

usage: python3 sound_v10.py <track.mp3> <track2.mp3> <out.wav> [--sfx-only]
"""
import sys
import wave
import numpy as np
import sound_v2 as base
from sound_v2 import SR, whoosh, pop, shine, shutter, thud, riser, impact
from sound_v3 import roll
from sound_v4 import downbeat, load_music_full

XF = int(.040 * SR)           # short crossfade just after the drop hit
FADE_OUT = 1.2
OFFSET = 2.923                # old time − new time where the rhythms line up (onset cross-correlation)
BAR = 2.8928                  # bar length measured on the old clip


def compose(old, new):
    # track2 starts on a downbeat: place its first sample one bar after the matching position, i.e.
    # just behind the drop hit of track.mp3, so the beat grid runs straight through the join
    cut = int((OFFSET + BAR) * SR)
    fi = np.sin(np.linspace(0, np.pi / 2, XF))[:, None]
    fo = np.cos(np.linspace(0, np.pi / 2, XF))[:, None]
    # match loudness over the drop sections
    d = int(5.74 * SR)
    g = np.sqrt((old[d:d + int(2.8 * SR)] ** 2).mean() / (new[:int(2.8 * SR)] ** 2).mean())
    new = new * g
    out = np.concatenate([old[:cut], old[cut:cut + XF] * fo + new[:XF] * fi, new[XF:]])
    n = len(out)
    out[n - int(FADE_OUT * SR):] *= np.linspace(1, 0, int(FADE_OUT * SR))[:, None] ** 1.5
    return out, downbeat(old, 5.74) / SR     # music, drop time in the output


def main():
    old, new = load_music_full(sys.argv[1]), load_music_full(sys.argv[2])
    music, drop = compose(old, new)
    N = len(music)
    base.N = N
    base.L = np.zeros(N)
    base.R = np.zeros(N)
    add = base.add
    T = [0, 2.85, drop] + [drop + i * BAR for i in range(1, 5)]    # scene starts (see video_v10.html)
    # very light SFX: a soft swoosh into each scene, one pop + shine per info
    for s in T[1:]:
        add(whoosh(.35), s - .25, .3)
    add(riser(drop - 5.38), 5.38, .2)
    add(impact(1.0), drop, .3)
    for i in range(4):
        s = drop + i * BAR
        add(pop(), s + 1.6, .35)
    for j in range(3):
        add(shutter(), drop + .9 + j * .45, .35)                    # camera on info 1
    add(roll(1.4), drop + 3 * BAR + 1.0, .2)                       # excavator on info 4
    add(shine(), T[-1] + .6, .3)                                   # end card
    sfx = np.stack([base.L, base.R], 1) * .3
    mix = np.tanh((music + sfx) * 1.05) / np.tanh(1.05)
    norm = .9 / np.abs(mix).max()
    if '--sfx-only' in sys.argv:
        mix = sfx * norm          # same level the SFX have inside the full mix, no music
    else:
        mix *= norm
    with wave.open(sys.argv[3], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    print(f'wrote {sys.argv[3]}  ({N / SR:.3f} s, drop at {drop:.3f} s)')


if __name__ == '__main__':
    main()

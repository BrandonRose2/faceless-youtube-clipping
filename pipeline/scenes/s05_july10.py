"""Section 6 (7:45 July 10, 2006) of video #1, hand-directed shot by shot.

Respectful by design (script rule): no graphic depiction, no victim imagery, no car, no photos of the
family. Only text, an abstract drawing of the anchors, and silence.

Run:  .venv/bin/python -m pipeline.scenes.s05_july10
Out:  output/01-big-dig-ceiling-collapse/sections/7-45-July 10, 2006/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0-10.1  Stock 054: the same tunnel as the cold open (script cue), caption July 10, 2006 / about 11 p.m.
            "Around 11 p.m. on July 10, 2006, Milena and Angel Del Valle drove east..."   quiet bed
 10.1-27.8  Our drawing: 20 anchors along the roof turn red one after another, faster and faster
            (script cue: like a zipper); counter "Anchors failed: n of 20"; the panels sag a little
            "the anchors finally reached the point of failure... like a zipper"          soft ticks, one low hit
 27.8-37.9  Card: 10 panels / about 52,000 pounds / roughly 26 tons
            "Ten precast concrete panels... roughly 26 tons"                             low hit on "26 tons"
 37.9-39.9  Black. Bed and effects are cut completely (script cue: two seconds, no sound)
            "The panels fell onto the Del Valles' car."
 39.9-45.4  Card: Angel Del Valle survived with minor injuries / Milena Del Valle, 39, was killed
            "Angel escaped with minor injuries. Milena was killed."                      silence, bed returns softly
 45.4-55.0  Card: Milena Del Valle / a mother of three / who came to Boston from Costa Rica
            "She was a mother of three who had come to Boston from Costa Rica."          bed fades out
"""
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw

from pipeline import scene_kit as K
from pipeline import sound as S

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/7-45-July 10, 2006"
RED, WHITE, AMBER, GREY = (235, 70, 60), (240, 240, 240), (240, 176, 40), (150, 155, 165)
W, H, FPS = K.W, K.H, K.FPS
N_ANCHORS = 20


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def zipper(dur, out):
    """Side view of the roof (top band), 20 anchors, and 10 hanging panels. Anchors fail one after
    another, speeding up. Failed anchors turn red; their panels sag a little. Nothing falls."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    big = K._font(K._FONT_BOLD, 64)
    small = K._font(K._FONT_BOLD, 38)
    xs = [160 + i * (1600 / (N_ANCHORS - 1)) for i in range(N_ANCHORS)]
    fail_t = [1.5 + 11.5 * (1 - (1 - i / (N_ANCHORS - 1)) ** 2) for i in range(N_ANCHORS)]   # speeds up
    for f in range(n):
        t = f / FPS
        im = Image.new("RGB", (W, H), (16, 19, 24))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W, 330], fill=(98, 104, 114))                                  # concrete roof
        failed = sum(1 for ft in fail_t if t >= ft)
        for i, x in enumerate(xs):
            gone = t >= fail_t[i]
            col = RED if gone else (196, 202, 212)
            drop = min(46, (t - fail_t[i]) * 70) if gone else 0
            dr.rectangle([x - 6, 330 + drop, x + 6, 400 + drop], fill=col)                  # the anchor and rod top
            dr.line([(x, 400 + drop), (x, 520)], fill=(120, 126, 136), width=3)             # hanger rod
        for p in range(10):
            a, b = 2 * p, 2 * p + 1
            sag = (min(46, max(0, (t - fail_t[a]) * 70)) + min(46, max(0, (t - fail_t[b]) * 70))) / 2 * 0.9
            dr.rectangle([xs[a] - 28, 520 + sag, xs[b] + 28, 590 + sag], fill=(132, 138, 150))   # ceiling panel
        cap = "Anchors failed: %d of %d" % (failed, N_ANCHORS)
        w = dr.textlength(cap, font=big)
        dr.text(((W - w) / 2, 800), cap, font=big, fill=RED if failed else WHITE)
        sub = "Each failure shifts its load onto the neighbors"
        w2 = dr.textlength(sub, font=small)
        dr.text(((W - w2) / 2, 900), sub, font=small, fill=GREY)
        im.save(f"{d}/{f:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out, fail_t


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    C = lambda n: f"{BASE}/clips/clip_{n}_stock.mp4"
    total = 55.0
    cuts = [("a", 10.1), ("b", 27.8), ("c", 37.9), ("d", 39.9), ("e", 45.4), ("f", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    zip_path, fail_t = zipper(dur["b"], f"{out}/02.mp4")
    shots = [
        K.shot(C("054"), 1.0, dur["a"], f"{out}/01.mp4", grade="dark", fade_in=1.0),
        zip_path,
        K.text_card([("10 precast panels", 84, WHITE), ("about 52,000 pounds", 84, WHITE),
                     ("roughly 26 tons", 120, AMBER)], dur["c"], f"{out}/03.mp4"),
        K.text_card([(" ", 10, (0, 0, 0))], dur["d"], f"{out}/04.mp4", fade_in=0, fade_out=0, bg=(0, 0, 0)),
        K.text_card([("Angel Del Valle survived", 70, WHITE), ("with minor injuries", 70, WHITE),
                     ("Milena Del Valle, 39, was killed", 80, GREY)], dur["e"], f"{out}/05.mp4", fade_in=0.8),
        K.text_card([("Milena Del Valle", 100, WHITE), ("a mother of three", 64, GREY),
                     ("who came to Boston from Costa Rica", 64, GREY)], dur["f"], f"{out}/06.mp4", fade_out=1.2),
    ]
    video = K.concat(shots, f"{out}/video_raw.mp4")
    video = K.lower_third(video, "July 10, 2006", 1.0, 5.5, f"{out}/video.mp4", sub="About 11 p.m. · I-90 connector tunnel")

    bed = S.drone(total, "somber")
    # silence for the black screen (script: two seconds, no sound), with short fades so there is no click
    a, b = int(37.9 * K.SR), int(39.9 * K.SR)
    bed[a:b] = 0.0
    bed[a - 4410:a] *= np.linspace(1, 0, 4410)
    bed[b:b + 22050] *= np.linspace(0, 1, 22050)
    sfx = [(10.1 + ft, S.tick(), -17) for ft in fail_t] + [(10.1 + fail_t[-1] + 0.3, S.hit(), -9),
                                                          (35.2, S.hit(), -9)]
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", bed_db=-27.0, length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

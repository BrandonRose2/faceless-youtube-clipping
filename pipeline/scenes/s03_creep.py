"""Section 4 (4:00 The hidden enemy: creep) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s03_creep
Out:  output/01-big-dig-ceiling-collapse/sections/4-00-The hidden enemy: creep/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0- 5.6  Card: One engineering word: CREEP
            "you need one engineering word: creep"                                 bed fades in, key clicks
  5.6-15.6  Diagram 05: epoxy under constant load, clock, "7 years"
            "constant load for a long time... slowly stretches"                    whoosh
 15.6-23.2  Stock 062: watch gears turning
            "a tiny bit at a time... plastics and adhesives creep at room temp"    whoosh
 23.2-43.4  Our animation: a weight on a sticky label slowly peels off the wall, then falls
            "the mailing label... over weeks or months it peels... one day it's on the floor"
                                                                                   clock ticks, riser, hit on the fall
 43.4-56.7  Diagram 06: STANDARD SET vs FAST SET epoxy (script cue), played 0.75x
            "the epoxy supplier made two versions"                                 whoosh
 56.7-66.0  Card: Fast-set epoxy / "exceptionally poor" / creep resistance
            "very poor resistance to creep... exceptionally poor"                  whoosh, key clicks
 66.0-74.6  Card: National Transportation Safety Board / fast-set epoxy at the D Street portal
            "according to the NTSB, the fast-set formula... near the D Street portal"  key clicks
 74.6-83.6  Card: The supplier disputed this / it said it supplied standard-set epoxy
            "the supplier later insisted it had supplied standard-set epoxy"       key clicks
 83.6-91.1  Card: Blame was spread much more widely
            "the investigators spread the blame much more widely"                  low hit
Stock total 7.6 s of 91.1 s (8%).
"""
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

from pipeline import scene_kit as K
from pipeline import sound as S

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/4-00-The hidden enemy: creep"
RED, WHITE, AMBER, GREY = (235, 70, 60), (240, 240, 240), (240, 176, 40), (150, 155, 165)
W, H, FPS = K.W, K.H, K.FPS


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def label_animation(dur, out):
    """A sticky label on a wall with a weight hanging from it. Over 'weeks and months' the
    label slowly peels and slides down; near the end it lets go and drops to the floor."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    font_big = K._font(K._FONT_BOLD, 64)
    font_mid = K._font(K._FONT_BOLD, 44)
    floor_y = 900
    fall_at = 0.88
    for i in range(n):
        p = i / n
        im = Image.new("RGB", (W, H), (22, 26, 33))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, floor_y, W, H], fill=(14, 16, 20))                 # floor
        dr.rectangle([560, 80, 1360, floor_y], fill=(38, 44, 54))           # wall panel
        slide = 220 * ease(p / fall_at) ** 1.6                              # slow creep down
        top = 200 + slide
        if p < fall_at:
            peel = min(1.0, p / fall_at)
            dr.rectangle([860, top, 1060, top + 120], fill=(232, 224, 190))              # the label
            dr.polygon([(860, top + 120), (860 + 200 * (1 - 0.3 * peel), top + 120),
                        (860 + 200 * (1 - 0.3 * peel), top + 120 + 30 * peel)], fill=(190, 182, 150))
            dr.line([(960, top + 120), (960, top + 320)], fill=GREY, width=4)           # string
            wy = top + 320
            dr.rectangle([890, wy, 1030, wy + 160], fill=(95, 100, 112))                  # the weight
            dr.text((910, wy + 50), "LOAD", font=font_mid, fill=WHITE)
        else:
            q = (p - fall_at) / (1 - fall_at)
            g = q * q                                                                    # falling
            y = (top + 320) + g * (floor_y - 160 - (top + 320))
            y = min(y, floor_y - 160)
            dr.rectangle([890, y, 1030, y + 160], fill=(95, 100, 112))
            dr.text((910, y + 50), "LOAD", font=font_mid, fill=WHITE)
            lx = 960 + 160 * q
            ly = min(floor_y - 8, top + 120 + g * (floor_y - 8 - (top + 120)))
            dr.rectangle([lx - 100, ly - 14, lx + 100, ly], fill=(232, 224, 190))         # label on the floor
        if p < 0.25:
            cap = "Day 1: it holds"
        elif p < 0.5:
            cap = "Week 3: a little lower"
        elif p < fall_at:
            cap = "Month 6: still sliding"
        else:
            cap = "One day..."
        col = RED if p >= fall_at else WHITE
        w = dr.textlength(cap, font=font_big)
        dr.text(((W - w) / 2, 960), cap, font=font_big, fill=col)
        im.save(f"{d}/{i:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"
    C = lambda n: f"{BASE}/clips/clip_{n}_stock.mp4"
    total = 91.1
    cuts = [("a", 5.6), ("b", 15.6), ("c", 23.2), ("d", 43.4), ("e", 56.7), ("f", 66.0), ("g", 74.6),
            ("h", 83.6), ("i", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.text_card([("One engineering word:", 60, WHITE), ("CREEP", 170, AMBER)], dur["a"], f"{out}/01.mp4", fade_in=0.6),
        K.shot(D("05"), 0.0, dur["b"], f"{out}/02.mp4"),
        K.shot(C("062"), 0.0, dur["c"], f"{out}/03.mp4", grade="cold"),
        label_animation(dur["d"], f"{out}/04.mp4"),
        K.shot(D("06"), 0.0, dur["e"], f"{out}/05.mp4", speed=0.75),
        K.text_card([("Fast-set epoxy", 70, WHITE), ("\"exceptionally poor\"", 110, RED),
                     ("creep resistance", 70, WHITE)], dur["f"], f"{out}/06.mp4"),
        K.text_card([("National Transportation Safety Board", 56, GREY), ("The fast-set epoxy", 80, WHITE),
                     ("was used at the D Street portal", 80, AMBER)], dur["g"], f"{out}/07.mp4"),
        K.text_card([("The supplier disputed this", 90, WHITE),
                     ("It said it supplied standard-set epoxy", 56, GREY)], dur["h"], f"{out}/08.mp4"),
        K.text_card([("Blame was spread", 90, WHITE), ("much more widely", 110, AMBER)], dur["i"], f"{out}/09.mp4",
                    fade_out=0.8),
    ]
    video = K.concat(shots, f"{out}/video.mp4")

    bed = S.drone(total, "somber")
    ticks = [(0.9 + i * 0.16, S.typewriter_tick(seed=90 + i), -14) for i in range(4)]
    ticks += [(57.0 + i * 0.16, S.typewriter_tick(seed=100 + i), -14) for i in range(3)]
    ticks += [(66.3 + i * 0.16, S.typewriter_tick(seed=110 + i), -14) for i in range(3)]
    ticks += [(74.9 + i * 0.16, S.typewriter_tick(seed=120 + i), -14) for i in range(3)]
    clock = [(25.0 + k * 1.3, S.tick(), -18) for k in range(10)]
    sfx = [(5.4, S.whoosh(), -12), (15.4, S.whoosh(), -12), (23.0, S.whoosh(), -12), (43.2, S.whoosh(), -12),
           (56.5, S.whoosh(), -12), (38.6, S.riser(3.0), -14), (41.3, S.hit(), -8),
           (83.7, S.hit(), -10)] + ticks + clock
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

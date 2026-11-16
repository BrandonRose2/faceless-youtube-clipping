"""Section 3 (2:30 How the ceiling was held up) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s02_ceiling
Out:  output/01-big-dig-ceiling-collapse/sections/2-30-How the ceiling was held up/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0-12.5  Diagram 02: roof, space above (plenum), hanging ceiling panels, slowed to 0.8x
            "the roof had a hanging ceiling... an open space called a plenum"     bed fades in
 12.5-16.4  Stock 016: concrete frame
            "large precast concrete panels, hung from the roof by steel rods"     whoosh
 16.4-26.4  Diagram 03: bolt, rod, epoxy in the roof
            "rods connected to anchor bolts... an 8-inch stainless-steel bolt"    whoosh
 26.4-30.6  Stock 020: threaded bolts on black
            "each anchor was a threaded stainless-steel bolt"
 30.6-35.1  Card: EPOXY / a two-part adhesive / hardens like plastic rock
            "workers filled the hole with epoxy..."                               key clicks
 35.1-40.1  Stock 018: concrete pour on a building site
            "Epoxy anchors are common in construction"                            whoosh
 40.1-46.0  Card: Strong. Fast. Common. / ...for lighter loads
            "strong, fast to install... more often used for lighter loads"        key clicks
 46.0-53.2  Diagram 11: sustained load arrow on a bolt
            "hanging tons of concrete overhead from glued bolts, for decades"     whoosh, low hit
 53.2-63.2  Diagram 04: weight scale, one panel tips heavily (script cue)
            "heavier concrete ceiling panels to save money... epoxy anchors anyway"
 63.2-70.6  Card: Not for a day. / Every second of every day.
            "Not for a day. Every second of every day..."                         3 clock ticks, low hit
Stock total 12.8 s of 70.6 s (18%).
"""
import json
import os
import subprocess

from pipeline import scene_kit as K
from pipeline import sound as S

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/2-30-How the ceiling was held up"
RED, WHITE, AMBER = (235, 70, 60), (240, 240, 240), (240, 176, 40)


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"
    C = lambda n: f"{BASE}/clips/clip_{n}_stock.mp4"
    total = 70.6
    cuts = [("a", 12.5), ("b", 16.4), ("c", 26.4), ("d", 30.6), ("e", 35.1), ("f", 40.1),
            ("g", 46.0), ("h", 53.2), ("i", 63.2), ("j", 70.6)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end
    shots = [
        K.shot(D("02"), 0.0, dur["a"], f"{out}/01.mp4", speed=0.8, fade_in=0.8),
        K.shot(C("016"), 2.0, dur["b"], f"{out}/02.mp4", grade="cold"),
        K.shot(D("03"), 0.0, dur["c"], f"{out}/03.mp4"),
        K.shot(C("020"), 2.0, dur["d"], f"{out}/04.mp4", grade="dark"),
        K.text_card([("EPOXY", 130, AMBER), ("a two-part adhesive", 60, WHITE),
                     ("that hardens like plastic rock", 60, WHITE)], dur["e"], f"{out}/05.mp4"),
        K.shot(C("018"), 3.0, dur["f"], f"{out}/06.mp4", grade="cold"),
        K.text_card([("Strong. Fast. Common.", 100, WHITE), ("...for lighter loads", 70, AMBER)],
                    dur["g"], f"{out}/07.mp4"),
        K.shot(D("11"), 0.0, dur["h"], f"{out}/08.mp4", speed=1.0),
        K.shot(D("04"), 0.0, dur["i"], f"{out}/09.mp4"),
        K.text_card([("Not for a day.", 110, WHITE), ("Every second of every day.", 80, RED)],
                    dur["j"], f"{out}/10.mp4", fade_out=0.8),
    ]
    video = K.concat(shots, f"{out}/video.mp4")

    bed = S.drone(total, "neutral")
    ticks = [(30.9 + i * 0.16, S.typewriter_tick(seed=70 + i), -14) for i in range(4)]
    ticks += [(40.3 + i * 0.16, S.typewriter_tick(seed=80 + i), -14) for i in range(4)]
    ticks += [(63.6, S.tick(), -16), (64.6, S.tick(), -16), (65.6, S.tick(), -16)]
    sfx = [(12.3, S.whoosh(), -12), (16.2, S.whoosh(), -12), (34.9, S.whoosh(), -12),
           (45.8, S.whoosh(), -12), (50.0, S.hit(), -9), (53.0, S.whoosh(), -12),
           (63.0, S.hit(), -9)] + ticks
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

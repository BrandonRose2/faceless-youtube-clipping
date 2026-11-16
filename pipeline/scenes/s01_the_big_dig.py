"""Section 2 (1:00 The Big Dig) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s01_the_big_dig
Out:  output/01-big-dig-ceiling-collapse/sections/1-00-The Big Dig/section.mp4 (+ check/ frames)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0- 4.9  Title card: "To understand the collapse, you have to understand THE BIG DIG"
                                                                                bed fades in, key clicks
  4.9-14.0  Push-in, 1950s aerial of the elevated Central Artery (photo 008)
            "cut in half by an elevated six-lane highway... loud and jammed"     whoosh
 14.0-23.7  Push-in on the plan map of the tunnels and harbor (002)
            "bury the entire highway underground... a tunnel under the harbor"   whoosh
 23.7-33.7  Slow pan across the pre/post Big Dig map: old road, then the tunnels (001)
            "officially the Central Artery/Tunnel Project... the Big Dig"         whoosh
 33.7-42.2  Card: Two decades / $14.6 billion / costliest highway project in U.S. history
            "two decades... roughly $14.6 billion"                                key clicks, low hit
 42.2-50.2  Pan across the pre/post highway map with Logan Airport (003)
            "links the Massachusetts Turnpike to the Ted Williams Tunnel and the airport" whoosh
 50.2-57.8  Push-in on the blueprint-style tunnel plan (004), caption I-90 connector, opened 2003
            "opened in 2003... the tunnel the Del Valles were driving through"
No stock footage in this section. (Diagram 01 is an abstract placeholder and is not used.)
"""
import json
import os
import subprocess

from pipeline import scene_kit as K
from pipeline import sound as S

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/1-00-The Big Dig"
RED, WHITE, AMBER = (235, 70, 60), (240, 240, 240), (240, 176, 40)


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    P = lambda n: f"{BASE}/photos/photo_{n}.jpg"
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"
    total = 57.8
    cuts = [("a", 4.9), ("b", 14.0), ("c", 23.7), ("d", 33.7), ("e", 42.2), ("f", 50.2), ("g", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.text_card([("To understand the collapse,", 56, WHITE), ("you have to understand", 56, WHITE),
                     ("THE BIG DIG", 130, AMBER)], dur["a"], f"{out}/01.mp4", fade_in=0.6, fade_out=0.3),
        K.kenburns(P("008"), dur["b"], f"{out}/02.mp4", "in", amount=0.14),
        K.kenburns(P("002"), dur["c"], f"{out}/03.mp4", "in", amount=0.15),
        K.kenburns(P("001"), dur["d"], f"{out}/04.mp4", "right", amount=0.12),
        K.text_card([("Two decades", 72, WHITE), ("$14.6 billion", 140, RED),
                     ("the costliest highway project in U.S. history", 46, WHITE)], dur["e"], f"{out}/05.mp4"),
        K.kenburns(P("003"), dur["f"], f"{out}/06.mp4", "right", amount=0.14),
        K.kenburns(P("004"), dur["g"], f"{out}/07.mp4", "in", amount=0.12, fade_out=0.8),
    ]
    video = K.concat(shots, f"{out}/video_raw.mp4")
    video = K.lower_third(video, "Boston's Central Artery", 5.6, 4.5, f"{out}/video_a.mp4", sub="Elevated six-lane highway")
    video = K.lower_third(video, "I-90 connector tunnel", 51.0, 5.5, f"{out}/video.mp4", sub="Opened to traffic in 2003")

    bed = S.drone(total, "neutral")
    ticks = [(0.9 + i * 0.16, S.typewriter_tick(seed=60 + i), -14) for i in range(3)]
    ticks += [(34.0 + i * 0.16, S.typewriter_tick(seed=50 + i), -14) for i in range(4)]
    sfx = [(4.7, S.whoosh(), -12), (13.8, S.whoosh(), -12), (23.5, S.whoosh(), -12),
           (35.0, S.hit(), -9), (42.0, S.whoosh(), -12)] + ticks
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

"""Section 1 (0:00 Cold open) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s00_cold_open
Out:  output/01-big-dig-ceiling-collapse/sections/0-00-Cold open/section.mp4
      and check/ frames (one every 10 s) to look at before using it.

SHOT LIST (time in section seconds -> picture -> what the narrator says -> sound)
  0.0- 7.6  Dark tunnel interior (stock 054), caption "Boston, July 10, 2006"
            "just before eleven... driving east through a tunnel under Boston"   bed fades in
  7.6-15.9  Push-in on the real Big Dig map (photo 001, shows Logan Airport)
            "heading for Logan Airport... Angel is at the wheel"                 whoosh
 15.9-23.7  Push-in on the real Zakim Bridge photo (006)
            "barely three years old... most expensive highway project"          whoosh
 23.7-30.0  Diagram 02: tunnel roof, space above, hanging ceiling panels
            "heavy concrete ceiling panels held up by steel rods"                whoosh
 30.0-36.7  Diagram 03: bolt, rod, epoxy (played 1.25x so the epoxy label lands on "glue")
            "each bolt is held in place by one thing: glue"                      low hit on "glue"
 36.7-44.1  Diagram 05: epoxy under constant load, clock, "7 years" (played 1.35x)
            "slowly, silently letting go"                                        3 clock ticks, riser
 44.1-46.1  Hard cut to black (script direction)                                 CRACK, bed dips
 46.1-52.0  Text card "About 26 tons of concrete and steel"
            "26 tons of concrete and steel would fall onto the road"             low hit, key clicks
 52.0-56.5  Text card "A $14.6 billion tunnel"
 56.5-61.3  Text card "Warning signs came seven years too early"
            "...a fast-setting glue brought down a ceiling in a $14.6 billion
            tunnel, and of the warning signs that came seven years too early"    key clicks
 61.3-65.8  Title card THE GLUE THAT KILLED (after the narration ends)           whoosh, hit
Only the tunnel interior is stock footage (about 12% of the section).
"""
import json
import os
import subprocess

from pipeline import scene_kit as K
from pipeline import sound as S

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/0-00-Cold open"
RED, WHITE, AMBER = (235, 70, 60), (240, 240, 240), (240, 176, 40)


def fr(seconds):
    """Snap a duration to whole frames so the cuts add up exactly to the narration."""
    return round(seconds * K.FPS) / K.FPS


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    vo_len = t["duration_s"]
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    P = lambda n: f"{BASE}/photos/photo_{n}.jpg"
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"

    cuts = [  # (name, end time in section seconds)
        ("tunnel", 7.6), ("map", 15.9), ("zakim", 23.7), ("roof", 30.0), ("bolt", 36.7), ("creep", 44.1),
        ("black", 46.1), ("tons", 52.0), ("cost", 56.5), ("warn", 61.3), ("title", 65.8),
    ]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.shot(f"{BASE}/clips/clip_054_stock.mp4", 1.0, dur["tunnel"], f"{out}/01.mp4", grade="dark", fade_in=1.2),
        K.kenburns(P("001"), dur["map"], f"{out}/02.mp4", "in", amount=0.15),
        K.kenburns(P("006"), dur["zakim"], f"{out}/03.mp4", "in", amount=0.12, grade="cold"),
        K.shot(D("02"), 0.0, dur["roof"], f"{out}/04.mp4"),
        K.shot(D("03"), 0.0, dur["bolt"], f"{out}/05.mp4", speed=1.25),
        K.shot(D("05"), 0.0, dur["creep"], f"{out}/06.mp4", speed=1.35, fade_out=0.3),
        K.text_card([(" ", 10, (0, 0, 0))], dur["black"], f"{out}/07.mp4", fade_in=0, fade_out=0, bg=(0, 0, 0)),
        K.text_card([("About 26 tons", 120, RED), ("of concrete and steel", 70, WHITE)], dur["tons"], f"{out}/08.mp4", fade_in=0.15),
        K.text_card([("A $14.6 billion tunnel", 96, WHITE)], dur["cost"], f"{out}/09.mp4"),
        K.text_card([("Warning signs came", 80, WHITE), ("seven years too early", 96, AMBER)], dur["warn"], f"{out}/10.mp4"),
        K.text_card([("THE GLUE THAT KILLED", 120, AMBER), ("The Big Dig Ceiling Collapse", 64, WHITE)], dur["title"], f"{out}/11.mp4", fade_in=0.5, fade_out=0.8),
    ]
    video = K.concat(shots, f"{out}/video_raw.mp4")
    video = K.lower_third(video, "Boston, July 10, 2006", 1.4, 5.0, f"{out}/video.mp4", sub="Interstate 90 connector tunnel")

    total = 65.8
    bed = S.drone(total, "somber")
    bed[int(43.9 * K.SR):int(46.4 * K.SR)] *= 0.1      # the bed drops away so the crack lands
    ticks = [(46.35 + i * 0.16, S.typewriter_tick(seed=20 + i), -14) for i in range(4)]
    ticks += [(52.2 + i * 0.16, S.typewriter_tick(seed=30 + i), -14) for i in range(3)]
    ticks += [(56.7 + i * 0.16, S.typewriter_tick(seed=40 + i), -14) for i in range(3)]
    sfx = [
        (7.4, S.whoosh(), -12), (15.7, S.whoosh(), -12), (23.5, S.whoosh(), -12),
        (35.3, S.hit(), -9),
        (37.6, S.tick(), -16), (38.3, S.tick(), -16), (39.0, S.tick(), -16),
        (40.9, S.riser(3.0), -14),
        (44.12, S.crack(), -3),
        (46.2, S.hit(), -9),
        (61.1, S.whoosh(), -12), (61.4, S.hit(), -9),
    ] + ticks
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {vo_len:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

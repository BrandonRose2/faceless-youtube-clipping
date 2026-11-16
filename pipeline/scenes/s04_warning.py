"""Section 5 (6:00 The warning in 1999) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s04_warning
Out:  output/01-big-dig-ceiling-collapse/sections/6-00-The warning in 1999/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0- 5.9  Card: The part that should make every engineer uncomfortable
            "the part of the story that should make every engineer uncomfortable"  bed fades in, key clicks
  5.9-17.6  Our drawing: one anchor slowly pulling out of its epoxy hole, "1999: anchors found pulled partway out"
            "crews found ceiling anchors that had moved... pulled partway out"      whoosh, creak ticks
 17.6-27.3  Card: That was the warning. / Bolts don't slide out of cured epoxy for no reason
            "That was the warning. Bolts don't slide out of cured epoxy..."          whoosh, low hit
 27.3-53.0  Diagram 07: timeline, red flag at 1999, seven empty years (script cue), slowed to 0.38x
            "According to the NTSB, nobody identified that movement as creep..."     whoosh
            lower thirds: NTSB: nobody identified it as creep / Supplier's information:
            inadequate and misleading (investigators) / No follow-up monitoring or inspection
 53.0-62.0  Card: 1998 / State Inspector General's report / anchor bolts and glue flagged, Ted Williams Tunnel
            "Years earlier, in 1998..."                                              whoosh, key clicks
 62.0-71.2  Card: Weak design specifications / Anchors not installed or tested properly
            "weak design specifications... not installed or tested properly"        key clicks
 71.2-78.3  Card: The warnings were there. / They were never connected to the cause.
            "the warning signs were there... nobody kept checking"                   whoosh, riser
 78.3-84.6  Our drawing again: slow zoom on the anchor as a hairline gap opens (script cue)
            "for the next seven years the anchors kept carrying the load"            low hit
No stock footage in this section.
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
SEC = f"{BASE}/sections/6-00-The warning in 1999"
RED, WHITE, AMBER, GREY = (235, 70, 60), (240, 240, 240), (240, 176, 40), (150, 155, 165)
W, H, FPS = K.W, K.H, K.FPS


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def anchor_animation(dur, out, pull_px, zoom_end, caption, caption_color=WHITE):
    """Close-up of one anchor bolt in an epoxy-filled hole. The bolt slowly slides out of the
    hole (pull_px = how far, in pixels) while the camera optionally zooms in (zoom_end > 1)."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    cap_font = K._font(K._FONT_BOLD, 60)
    lab_font = K._font(K._FONT_BOLD, 34)
    cx, cy = 960, 420            # zoom centre
    for i in range(n):
        p = i / n
        z = 1 + (zoom_end - 1) * ease(p)
        dy = pull_px * ease(p)

        def X(x):
            return cx + (x - cx) * z

        def Y(y):
            return cy + (y - cy) * z

        im = Image.new("RGB", (W, H), (16, 19, 24))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W, Y(420)], fill=(98, 104, 114))                               # concrete roof
        dr.rectangle([X(880), Y(200), X(1040), Y(420)], fill=(8, 9, 12))                     # the hole
        dr.rectangle([X(880), Y(200), X(920), Y(420)], fill=(226, 168, 52))                  # epoxy, left
        dr.rectangle([X(1000), Y(200), X(1040), Y(420)], fill=(226, 168, 52))                # epoxy, right
        dr.rectangle([X(920), Y(200 + dy), X(1000), Y(800 + dy)], fill=(196, 202, 212))      # bolt + rod
        for k in range(0, 700, 28):                                                         # thread lines
            yy = 200 + dy + k
            if yy < 420:
                dr.line([(X(920), Y(yy)), (X(1000), Y(yy + 8))], fill=(150, 156, 166), width=2)
        if dy > 6:                                                                          # the gap that opens
            dr.text((X(1060), Y(205)), "gap", font=lab_font, fill=RED)
            dr.line([(X(1052), Y(215)), (X(1018), Y(200 + dy / 2))], fill=RED, width=3)
        dr.text((X(1090), Y(560)), "anchor bolt", font=lab_font, fill=GREY)
        dr.text((X(1090), Y(330)), "epoxy", font=lab_font, fill=(226, 168, 52))
        w = dr.textlength(caption, font=cap_font)
        dr.text(((W - w) / 2, 960), caption, font=cap_font, fill=caption_color)
        im.save(f"{d}/{i:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"
    total = 84.6
    cuts = [("a", 5.9), ("b", 17.6), ("c", 27.3), ("d", 53.0), ("e", 62.0), ("f", 71.2), ("g", 78.3), ("h", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.text_card([("The part that should make", 70, WHITE), ("every engineer", 100, AMBER),
                     ("uncomfortable", 100, AMBER)], dur["a"], f"{out}/01.mp4", fade_in=0.6),
        anchor_animation(dur["b"], f"{out}/02.mp4", pull_px=95, zoom_end=1.0,
                         caption="1999: anchors found pulled partway out"),
        K.text_card([("That was the warning.", 110, RED), ("Bolts don't slide out of cured epoxy", 56, WHITE),
                     ("for no reason", 56, WHITE)], dur["c"], f"{out}/03.mp4"),
        K.shot(D("07"), 0.0, dur["d"], f"{out}/04.mp4", speed=0.38),
        K.text_card([("1998", 150, AMBER), ("State Inspector General's report", 62, WHITE),
                     ("flagged anchor bolt and glue problems", 56, GREY),
                     ("in the Ted Williams Tunnel", 56, GREY)], dur["e"], f"{out}/05.mp4"),
        K.text_card([("Weak design specifications", 80, WHITE), ("Anchors not installed", 80, AMBER),
                     ("or tested properly", 80, AMBER)], dur["f"], f"{out}/06.mp4"),
        K.text_card([("The warnings were there.", 90, WHITE), ("They were never connected", 70, GREY),
                     ("to the cause.", 70, GREY)], dur["g"], f"{out}/07.mp4"),
        anchor_animation(dur["h"], f"{out}/08.mp4", pull_px=16, zoom_end=1.45,
                         caption="The epoxy kept creeping", caption_color=RED),
    ]
    video = K.concat(shots, f"{out}/video_raw.mp4")
    video = K.lower_third(video, "NTSB: nobody identified it as creep", 27.8, 5.8, f"{out}/va.mp4", sub="The 1999 anchor movement")
    video = K.lower_third(video, "Supplier's information", 34.3, 7.2, f"{out}/vb.mp4", sub="Called inadequate and misleading by investigators")
    video = K.lower_third(video, "No follow-up", 42.0, 10.0, f"{out}/video.mp4", sub="No monitoring, no inspection program after opening")

    bed = S.drone(total, "tense")
    ticks = [(0.9 + i * 0.16, S.typewriter_tick(seed=130 + i), -14) for i in range(4)]
    ticks += [(53.4 + i * 0.16, S.typewriter_tick(seed=140 + i), -14) for i in range(4)]
    ticks += [(62.4 + i * 0.16, S.typewriter_tick(seed=150 + i), -14) for i in range(3)]
    creak = [(7.0 + k * 1.6, S.tick(), -20) for k in range(6)]
    sfx = [(5.7, S.whoosh(), -12), (17.4, S.whoosh(), -12), (17.8, S.hit(), -9), (27.1, S.whoosh(), -12),
           (52.8, S.whoosh(), -12), (71.0, S.whoosh(), -12), (74.8, S.riser(3.3), -14),
           (78.3, S.hit(), -9)] + ticks + creak
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

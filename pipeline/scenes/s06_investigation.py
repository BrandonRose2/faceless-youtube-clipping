"""Section 7 (9:00 The investigation) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s06_investigation
Out:  output/01-big-dig-ceiling-collapse/sections/9-00-The investigation/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0- 6.5  Card: Parts of the Big Dig tunnel system were shut down
            "The reaction was immediate. Parts of the Big Dig tunnel system were shut down."   bed, key clicks
  6.5-16.5  Our drawing: 1,100 dots turn red one by one, counter "Epoxy anchors judged problematic"
            "Inspectors went through the ceilings bolt by bolt... more than 1,100 epoxy anchors"   ticks, low hit
 16.5-22.4  Card: Mechanical backup anchors installed / Some sections stayed closed for months
            "Crews installed mechanical anchors as a backup... closed for months"              whoosh
 22.4-31.9  Diagram 09: Federal investigation, 12 months, 171-page report (script cue)
            "The National Transportation Safety Board spent a year investigating"              whoosh
 31.9-41.7  Card: July 10, 2007 / exactly one year later / 171 pages, 20 findings, 20 recommendations
            "On July 10, 2007... adopted its final report"                                     low hit, key clicks
 41.7-49.1  Card: Probable cause: epoxy with poor creep resistance
            "The probable cause was the use of an epoxy anchor adhesive with poor creep resistance"   whoosh
 49.1-56.6  Anchor drawing (from section 5): "Deformed and fractured until the anchors pulled free"
            "Over time it deformed and fractured until the anchors pulled free"                creak ticks
 56.6-80.8  On-screen text, one line at a time (script cue): designers, managers and contractor did not
            treat creep as critical; no monitoring after 1999; industry-wide lack of understanding
            "the board didn't blame the glue alone..."                                         whoosh, key clicks, riser
 80.8-88.9  Card: NTSB highway safety director / didn't think they understood / creep at all
            "he didn't think they understood creep at all"                                     low hit
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
from pipeline.scenes.s04_warning import anchor_animation

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/9-00-The investigation"
RED, WHITE, AMBER, GREY = (235, 70, 60), (240, 240, 240), (240, 176, 40), (150, 155, 165)
BG = (14, 17, 22)
W, H, FPS = K.W, K.H, K.FPS


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def counter_animation(dur, out, total=1100):
    """A field of dots, one per problem anchor. They turn red in order while a counter climbs."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    big = K._font(K._FONT_BOLD, 110)
    mid = K._font(K._FONT_BOLD, 46)
    cols, rows = 55, 20
    gx, gy = 1800 / cols, 560 / rows
    for f in range(n):
        p = f / n
        count = int(total * ease(p / 0.9))
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        for i in range(total):
            r, c = divmod(i, cols)
            x, y = 60 + c * gx + gx / 2, 60 + r * gy + gy / 2
            col = RED if i < count else (52, 58, 70)
            dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col)
        label = f"{count:,}" + ("+" if count >= total else "")
        w = dr.textlength(label, font=big)
        dr.text(((W - w) / 2, 700), label, font=big, fill=RED)
        sub = "epoxy anchors judged problematic"
        w2 = dr.textlength(sub, font=mid)
        dr.text(((W - w2) / 2, 850), sub, font=mid, fill=WHITE)
        im.save(f"{d}/{f:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out


def lines_reveal(dur, out, items):
    """items: list of (start_seconds, [(text, size, color), ...]). Each group fades in at its time and stays."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    fonts = {}
    for f in range(n):
        t = f / FPS
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        y = 150
        for start, lines in items:
            a = max(0.0, min(1.0, (t - start) / 0.6))
            for txt, sz, col in lines:
                font = fonts.setdefault(sz, K._font(K._FONT_BOLD, sz))
                c = tuple(int(BG[k] + (col[k] - BG[k]) * a) for k in range(3))
                w = dr.textlength(txt, font=font)
                dr.text(((W - w) / 2, y), txt, font=font, fill=c)
                y += int(sz * 1.3)
            y += 70
        im.save(f"{d}/{f:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    D = lambda n: f"{BASE}/diagrams/diag_{n}.mp4"
    total = 88.9
    cuts = [("a", 6.5), ("b", 16.5), ("c", 22.4), ("d", 31.9), ("e", 41.7), ("f", 49.1), ("g", 56.6),
            ("h", 80.8), ("i", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.text_card([("Parts of the", 70, WHITE), ("Big Dig tunnel system", 100, AMBER),
                     ("were shut down", 70, WHITE)], dur["a"], f"{out}/01.mp4", fade_in=0.6),
        counter_animation(dur["b"], f"{out}/02.mp4"),
        K.text_card([("Mechanical backup anchors installed", 70, WHITE),
                     ("Some sections stayed closed for months", 56, GREY)], dur["c"], f"{out}/03.mp4"),
        K.shot(D("09"), 0.0, dur["d"], f"{out}/04.mp4"),
        K.text_card([("July 10, 2007", 110, AMBER), ("exactly one year after the collapse", 50, GREY),
                     ("171 pages · 20 findings · 20 safety recommendations", 56, WHITE)], dur["e"], f"{out}/05.mp4"),
        K.text_card([("Probable cause", 50, GREY), ("Epoxy adhesive with", 80, WHITE),
                     ("poor creep resistance", 100, RED)], dur["f"], f"{out}/06.mp4"),
        anchor_animation(dur["g"], f"{out}/07.mp4", pull_px=95, zoom_end=1.0,
                         caption="Deformed and fractured until the anchors pulled free"),
        lines_reveal(dur["h"], f"{out}/08.mp4", [
            (0.3, [("The designers, the project managers", 60, WHITE), ("and the contractor", 60, WHITE),
                   ("did not treat creep as a critical failure mode", 52, AMBER)]),
            (9.5, [("No monitoring after the 1999 warning", 60, WHITE)]),
            (14.0, [("An industry-wide lack of understanding", 60, WHITE),
                    ("of creep in adhesive anchors", 52, AMBER)]),
        ]),
        K.text_card([("NTSB highway safety director", 50, GREY), ("didn't think they understood", 80, WHITE),
                     ("creep at all", 130, AMBER)], dur["i"], f"{out}/09.mp4", fade_out=0.8),
    ]
    video = K.concat(shots, f"{out}/video.mp4")

    bed = S.drone(total, "somber")
    ticks = [(0.9 + i * 0.16, S.typewriter_tick(seed=160 + i), -14) for i in range(3)]
    ticks += [(32.2 + i * 0.16, S.typewriter_tick(seed=170 + i), -14) for i in range(4)]
    ticks += [(57.0 + i * 0.16, S.typewriter_tick(seed=180 + i), -14) for i in range(3)]
    ticks += [(66.0 + i * 0.16, S.typewriter_tick(seed=190 + i), -14) for i in range(3)]
    ticks += [(70.5 + i * 0.16, S.typewriter_tick(seed=200 + i), -14) for i in range(3)]
    counter = [(6.7 + k * 0.45, S.tick(), -19) for k in range(20)]
    creak = [(49.5 + k * 1.6, S.tick(), -20) for k in range(4)]
    sfx = [(16.3, S.hit(), -9), (16.3, S.whoosh(), -12), (22.2, S.whoosh(), -12), (31.8, S.hit(), -9),
           (41.5, S.whoosh(), -12), (56.4, S.whoosh(), -12), (77.0, S.riser(3.6), -14),
           (80.8, S.hit(), -9)] + ticks + counter + creak
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

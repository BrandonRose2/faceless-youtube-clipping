"""Section 8 (10:45 Who paid) of video #1, hand-directed shot by shot.

Run:  .venv/bin/python -m pipeline.scenes.s07_who_paid
Out:  output/01-big-dig-ceiling-collapse/sections/10-45-Who paid/section.mp4 (+ check/)

SHOT LIST (time in section seconds -> picture -> narration -> sound)
  0.0- 4.8  Card: The aftermath played out in courtrooms for more than two years
            "The aftermath played out in courtrooms for more than two years."          bed, key clicks
  4.8-31.8  Our ledger (script cue): amounts count up as each is named
            $458 million settlement (Bechtel/Parsons Brinckerhoff + about two dozen smaller firms),
            $407 million their share, "spared the consortium from criminal charges"
            "...a settlement of about $458 million... share was about $407 million"       whoosh, ticks, hits
 31.8-50.4  Text, line by line: Powers Fasteners, the only company criminally charged / indicted,
            pleaded not guilty / Dec 2008: charge dropped after paying $16 million
            "The epoxy supplier, Powers Fasteners, was the only company criminally charged..."   whoosh, key clicks
 50.4-59.3  Card: The Del Valle family settled their wrongful death lawsuit / 15 defendants / more than $28 million
            "The Del Valle family settled... for more than $28 million."                  whoosh, quiet
 59.3-62.8  Card: No individual engineer went to prison
            "No individual engineer went to prison."                                      whoosh, low hit
 62.8-68.5  Stock 013: night highway traffic flowing (script's quiet beat)
            "Many of the people involved would say, with some truth..."                   quiet
 68.5-72.7  Card: Many would say the industry didn't understand the risk. That's why this case matters.
            "That's exactly what makes this case so important."                           bed fades out
Stock total 5.7 s of 72.7 s (8%).
"""
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

from pipeline import scene_kit as K
from pipeline import sound as S
from pipeline.scenes.s06_investigation import lines_reveal

BASE = "output/01-big-dig-ceiling-collapse"
SEC = f"{BASE}/sections/10-45-Who paid"
RED, WHITE, AMBER, GREY = (235, 70, 60), (240, 240, 240), (240, 176, 40), (150, 155, 165)
BG = (14, 17, 22)
W, H, FPS = K.W, K.H, K.FPS


def fr(seconds):
    return round(seconds * K.FPS) / K.FPS


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ledger(dur, out):
    """Three groups fade in as the narrator names them; the two dollar amounts count up."""
    n = int(dur * FPS)
    d = tempfile.mkdtemp()
    F = {sz: K._font(K._FONT_BOLD, sz) for sz in (36, 44, 52, 64, 90, 130)}
    mix = lambda col, a: tuple(int(BG[k] + (col[k] - BG[k]) * a) for k in range(3))

    def centered(dr, text, y, sz, col, a):
        w = dr.textlength(text, font=F[sz])
        dr.text(((W - w) / 2, y), text, font=F[sz], fill=mix(col, a))

    for f in range(n):
        t = f / FPS
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        centered(dr, "Settlement · January 2008", 90, 52, GREY, 1.0)
        a1 = min(1.0, max(0.0, (t - 1.5) / 0.6))
        centered(dr, "Bechtel/Parsons Brinckerhoff", 230, 64, WHITE, a1)
        centered(dr, "the joint venture that managed the Big Dig", 320, 36, GREY, a1)
        centered(dr, "and about two dozen smaller firms", 380, 44, WHITE, a1)
        v1 = int(458 * ease((t - 9.0) / 2.5))
        a1b = min(1.0, max(0.0, (t - 9.0) / 0.4))
        centered(dr, f"${v1} million", 470, 130, AMBER, a1b)
        a2 = min(1.0, max(0.0, (t - 14.0) / 0.6))
        centered(dr, "Bechtel/Parsons Brinckerhoff's share", 680, 52, WHITE, a2)
        v2 = int(407 * ease((t - 14.8) / 2.0))
        centered(dr, f"${v2} million" if t >= 14.8 else " ", 750, 90, AMBER, a2)
        a3 = min(1.0, max(0.0, (t - 19.5) / 0.6))
        centered(dr, "The deal spared the consortium from criminal charges", 900, 52, GREY, a3)
        im.save(f"{d}/{f:05d}.png")
    K.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{d}/%05d.png"] + K._ENC + [out])
    shutil.rmtree(d, ignore_errors=True)
    return out


def main():
    t = json.load(open(f"{SEC}/timing.json"))
    out = f"{SEC}/work"
    os.makedirs(out, exist_ok=True)
    C = lambda n: f"{BASE}/clips/clip_{n}_stock.mp4"
    total = 72.7
    cuts = [("a", 4.8), ("b", 31.8), ("c", 50.4), ("d", 59.3), ("e", 62.8), ("f", 68.5), ("g", total)]
    dur, prev = {}, 0.0
    for name, end in cuts:
        dur[name] = fr(end - prev)
        prev = end

    shots = [
        K.text_card([("The aftermath played out", 70, WHITE), ("in courtrooms for more than", 70, WHITE),
                     ("two years", 100, AMBER)], dur["a"], f"{out}/01.mp4", fade_in=0.6),
        ledger(dur["b"], f"{out}/02.mp4"),
        lines_reveal(dur["c"], f"{out}/03.mp4", [
            (0.3, [("The epoxy supplier, Powers Fasteners", 60, WHITE),
                   ("was the only company criminally charged", 52, AMBER)]),
            (6.0, [("Indicted for involuntary manslaughter", 56, WHITE), ("It pleaded not guilty", 46, GREY)]),
            (12.2, [("December 2008: the charge was dropped", 56, WHITE),
                    ("after the company agreed to pay $16 million", 52, AMBER)]),
        ]),
        K.text_card([("The Del Valle family settled", 64, WHITE), ("their wrongful death lawsuit", 64, WHITE),
                     ("against 15 defendants", 52, GREY), ("more than $28 million", 100, AMBER)],
                    dur["d"], f"{out}/04.mp4"),
        K.text_card([("No individual engineer", 90, WHITE), ("went to prison", 120, AMBER)], dur["e"], f"{out}/05.mp4"),
        K.shot(C("013"), 0.0, dur["f"], f"{out}/06.mp4", speed=0.85, grade="cold", fade_in=0.6),
        K.text_card([("Many would say the industry", 64, WHITE), ("didn't understand the risk", 64, WHITE),
                     ("That's why this case matters", 80, AMBER)], dur["g"], f"{out}/07.mp4", fade_out=1.0),
    ]
    video = K.concat(shots, f"{out}/video.mp4")

    bed = S.drone(total, "somber")
    ticks = [(0.9 + i * 0.16, S.typewriter_tick(seed=210 + i), -14) for i in range(3)]
    counts = [(4.8 + 9.0 + k * 0.2, S.tick(), -19) for k in range(12)] + \
             [(4.8 + 14.8 + k * 0.2, S.tick(), -19) for k in range(10)]
    ticks += [(31.8 + 0.5 + i * 0.16, S.typewriter_tick(seed=220 + i), -14) for i in range(3)]
    ticks += [(31.8 + 6.2 + i * 0.16, S.typewriter_tick(seed=230 + i), -14) for i in range(3)]
    ticks += [(31.8 + 12.4 + i * 0.16, S.typewriter_tick(seed=240 + i), -14) for i in range(3)]
    sfx = [(4.6, S.whoosh(), -12), (4.8 + 9.0, S.hit(), -9), (4.8 + 14.8, S.hit(), -9), (31.6, S.whoosh(), -12),
           (50.2, S.whoosh(), -12), (59.1, S.whoosh(), -12), (59.4, S.hit(), -9)] + ticks + counts
    audio = K.mix(f"{SEC}/vo.wav", bed, sfx, f"{out}/audio.wav", length=total)
    final = K.mux(video, audio, f"{SEC}/section.mp4")

    os.makedirs(f"{SEC}/check", exist_ok=True)
    for sec in range(0, int(total) + 1, 10):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sec), "-i", final, "-frames:v", "1",
                        "-vf", "scale=960:-1", f"{SEC}/check/{sec:03d}s.jpg"], check=True)
    print(final, f"(narration {t['duration_s']:.1f}s, video {total}s)")


if __name__ == "__main__":
    main()

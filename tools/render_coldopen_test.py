"""Render the 60s cold-open test for video #1 (Big Dig) with free tools only:
PIL-drawn diagram, numpy drone + crack, ffmpeg assembly."""
import math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = "/home/claude/coldopen"
M = f"{D}/media"
W, H, FPS = 1280, 720, 30
VO_LEN = 59.56
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def font(p, s):
    return ImageFont.truetype(p, s)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------- 1. diagram animation (narration 23.24s -> 44.42s) ----------
def diagram(dur=21.2):
    os.makedirs(f"{D}/frames", exist_ok=True)
    n = int(dur * FPS)
    BG, CONC, STEEL, GLUE, TXT = (14, 17, 22), (120, 122, 126), (190, 196, 205), (240, 176, 40), (235, 235, 235)
    RED = (225, 60, 50)
    f1, f2, f3 = font(FB, 34), font(FR, 26), font(FB, 54)
    for i in range(n):
        t = i / FPS
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        z = ease((t - 3.5) / 2.5)          # 0 = wide view, 1 = zoomed on one anchor
        s = 1 + 0.6 * z
        cx, cy = W / 2, 260

        def P(x, y):
            return (cx + (x - cx) * s, cy + (y - cy) * s)

        def rect(x0, y0, x1, y1, **kw):
            a, b = P(x0, y0), P(x1, y1)
            d.rectangle([a[0], a[1], b[0], b[1]], **kw)

        creep = ease((t - 13.5) / 7.0) * 26
        rect(-400, 60, W + 400, 210, fill=CONC)                      # roof slab
        for ax in range(160, W - 100, 160):                          # anchors, rods
            dx = creep if ax == int(cx) else creep * 0.6
            rect(ax - 9, 120, ax + 9, 210, fill=(60, 60, 64))        # drilled hole
            rect(ax - 9, 120 + dx * 0.9, ax + 9, 210, fill=GLUE)     # epoxy
            rect(ax - 4, 130 + dx, ax + 4, 270 + dx, fill=STEEL)     # bolt
            rect(ax - 3, 270 + dx, ax + 3, 440 + dx, fill=STEEL)     # hanger rod
        rect(60, 440 + creep, W - 60, 480 + creep, fill=(150, 150, 150))  # ceiling panel
        if z < 0.9:                                                  # road + car in wide view
            a = 1 - z
            car = tuple(int(c * a + b) for c, b in zip((60, 90, 140), BG))
            rect(W / 2 - 90, 600, W / 2 + 90, 650, fill=car)
            rect(W / 2 - 55, 570, W / 2 + 55, 602, fill=car)
            rect(-400, 660, W + 400, 675, fill=(40, 40, 44))
        if t < 4:
            d.text((40, 650), "I-90 connector tunnel ceiling (simplified)", font=f2, fill=TXT)
        if 6 <= t < 13.5:
            a = P(cx + 14, 160)
            d.line([a, (a[0] + 150, a[1] - 40)], fill=GLUE, width=3)
            d.text((a[0] + 160, a[1] - 64), "EPOXY (glue)", font=f1, fill=GLUE)
            b = P(cx + 6, 300)
            d.line([b, (b[0] + 150, b[1] + 30)], fill=STEEL, width=3)
            d.text((b[0] + 160, b[1] + 14), "anchor bolt + hanger rod", font=f2, fill=STEEL)
            if t >= 9:
                d.text((40, 590), "Each bolt held in place by one thing:", font=f2, fill=TXT)
                d.text((40, 626), "GLUE", font=f3, fill=GLUE)
        if t >= 13.5:
            d.text((40, 586), "EPOXY CREEP", font=f3, fill=RED)
            d.text((40, 652), "slow deformation under a load that never goes away", font=f2, fill=TXT)
            yrs = 1999 + int(ease((t - 13.5) / 7.0) * 7)
            d.text((W - 230, 600), str(yrs), font=font(FB, 64), fill=TXT)
        if t > dur - 0.7:
            k = (t - (dur - 0.7)) / 0.7
            im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), min(1, k))
        im.save(f"{D}/frames/{i:05d}.png")
    run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{D}/frames/%05d.png", "-c:v", "libx264",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{D}/diagram.mp4"])


# ---------- 2. text cards (transparent PNG overlays) ----------
def card(name, lines, sizes, colors):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = H / 2 - sum(sizes) * 0.65
    for txt, sz, col in zip(lines, sizes, colors):
        f = font(FS if sz > 50 else FB, sz)
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=col, stroke_width=3, stroke_fill=(0, 0, 0))
        y += sz * 1.3
    im.save(f"{D}/{name}.png")


# ---------- 3. audio bed: low drone + crack at 44.4s ----------
def audio_bed():
    sr = 44100
    t = np.arange(int(sr * VO_LEN)) / sr
    lfo = 0.6 + 0.4 * np.sin(2 * math.pi * 0.07 * t)
    x = (np.sin(2 * math.pi * 55 * t) + 0.6 * np.sin(2 * math.pi * 82.4 * t)
         + 0.3 * np.sin(2 * math.pi * 110.3 * t)) * lfo * 0.05
    x *= np.clip(t / 3, 0, 1) * np.clip((VO_LEN - t) / 3, 0, 1)
    x[(t > 44.4) & (t < 46.4)] *= 0.15
    rng = np.random.default_rng(1)
    c0, L = int(44.42 * sr), int(1.6 * sr)
    env = np.exp(-np.arange(L) / (0.25 * sr))
    crack = rng.standard_normal(L) * env * 0.5 + np.sin(2 * math.pi * 40 * np.arange(L) / sr) * env * 0.6
    x[c0:c0 + L] += crack[: len(x) - c0]
    pcm = np.int16(np.clip(x, -1, 1) * 32767)
    with wave.open(f"{D}/bed.wav", "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


# ---------- 4. assemble ----------
def seg(out, src, start, dur, speed=1.0, vf_extra=""):
    vf = (f"setpts={1 / speed}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps={FPS}")
    if vf_extra:
        vf += "," + vf_extra
    run(["ffmpeg", "-y", "-ss", str(start), "-i", src, "-t", str(dur), "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])


def main():
    diagram()
    card("card_tons", ["About 26 tons of concrete"], [60], [(235, 70, 60)])
    card("card_title", ["THE GLUE THAT KILLED", "The Big Dig Ceiling Collapse"], [72, 34],
         [(240, 240, 240), (240, 176, 40)])
    audio_bed()
    S = f"{D}/seg"
    os.makedirs(S, exist_ok=True)
    # scene lengths line up with pauses in the narration
    seg(f"{S}/a.mp4", f"{M}/t4.mp4", 0, 6.0, speed=0.5, vf_extra="fade=in:0:20")   # clip you liked, slowed
    seg(f"{S}/b.mp4", f"{M}/t1.mp4", 0, 4.6, speed=0.87)
    seg(f"{S}/c.mp4", f"{M}/t2.mp4", 2, 12.64)
    run(["ffmpeg", "-y", "-i", f"{D}/diagram.mp4", "-t", "21.18", "-c", "copy", f"{S}/d.mp4"])
    seg(f"{S}/e.mp4", f"{M}/t3.mp4", 3, 5.62, vf_extra="eq=saturation=0.25:brightness=-0.12,fade=in:0:15")
    seg(f"{S}/f.mp4", f"{M}/t4.mp4", 0, 9.6, speed=0.32, vf_extra="fade=out:st=8.6:d=1")
    with open(f"{S}/list.txt", "w") as fh:
        for x in "abcdef":
            fh.write(f"file '{S}/{x}.mp4'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{S}/list.txt", "-c", "copy", f"{S}/joined.mp4"])
    out = f"{D}/coldopen_test.mp4"
    run(["ffmpeg", "-y", "-i", f"{S}/joined.mp4", "-i", f"{D}/card_tons.png", "-i", f"{D}/card_title.png",
         "-i", f"{M}/vo.mp3", "-i", f"{D}/bed.wav", "-filter_complex",
         "[0:v][1:v]overlay=enable='between(t,45.2,50.0)'[v1];"
         "[v1][2:v]overlay=enable='between(t,52.5,58.9)'[v];"
         "[3:a]volume=1.0[vo];[4:a]volume=0.9[bed];[vo][bed]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-t", str(VO_LEN), out])
    print(out)


if __name__ == "__main__":
    main()

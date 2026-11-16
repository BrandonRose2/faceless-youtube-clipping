"""Scene toolkit for hand-built video sections (Step 3 of docs/NEXT-TASK.md).

Modeled on tools/render_coldopen_test.py. Everything renders 1920x1080, 30 fps,
H.264, so clips from any helper can be joined with concat() without re-encoding.

  shot(src, start, dur, out, speed=1.0, grade=None)   trim a video clip
  kenburns(photo, dur, out, direction="in")           slow push-in / pull-out / pan on a photo
  text_card(lines, dur, out)                          title or fact card on a dark background
  lower_third(video, text, start, dur, out)           caption bar over a video
  concat(shots, out)                                  join clips made by the helpers above
  mix(vo, bed, sfx_list, out)                         voice + bed (ducked) + effects, -14 LUFS
  mux(video, audio, out)                              put the mixed audio on a video

`python -m pipeline.scene_kit` renders a 15 s test scene to output/scene_kit_test.mp4.
Durations are OUTPUT seconds. Look at a frame of every clip before using it.
"""
import glob
import os
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
SR = 44100

_FONT_BOLD = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
_FONT_SERIF = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
               "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]

GRADES = {
    None: "",
    "cold": "eq=saturation=0.7:brightness=-0.05,colorbalance=bs=0.08:bm=0.04",
    "warm": "eq=saturation=1.05,colorbalance=rs=0.06:bs=-0.05",
    "desat": "eq=saturation=0.25:brightness=-0.12",
    "dark": "eq=brightness=-0.15:contrast=1.1",
}


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise RuntimeError("ffmpeg failed: " + " ".join(cmd[:6]) + " ...\n" + r.stderr[-800:])


def _font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


_ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]


def _fades(dur, fade_in, fade_out):
    f = []
    if fade_in:
        f.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out:
        f.append(f"fade=t=out:st={max(0, dur - fade_out):.3f}:d={fade_out}")
    return ",".join(f)


def _chain(*parts):
    return ",".join(p for p in parts if p)


def shot(src, start, dur, out, speed=1.0, grade=None, fade_in=0.0, fade_out=0.0):
    """Trim `dur` output seconds of a clip starting at `start` (source seconds).
    speed 0.5 = half-speed slow motion. grade: None, 'cold', 'warm', 'desat' or 'dark'."""
    vf = _chain(f"setpts={1 / speed:.4f}*PTS",
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                GRADES[grade], _fades(dur, fade_in, fade_out))
    run(["ffmpeg", "-y", "-ss", str(start), "-i", src, "-vf", vf, "-t", f"{dur:.3f}"] + _ENC + [out])
    return out


def kenburns(photo, dur, out, direction="in", amount=0.18, grade=None, fade_in=0.0, fade_out=0.0):
    """Slow camera move on a still photo. direction: 'in', 'out', 'left', 'right'."""
    n = max(2, int(dur * FPS))
    c = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    moves = {
        "in": f"z='1+{amount}*on/{n}':{c}",
        "out": f"z='{1 + amount}-{amount}*on/{n}':{c}",
        "left": f"z={1 + amount}:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'",
        "right": f"z={1 + amount}:x='(iw-iw/zoom)*(on/{n})':y='ih/2-(ih/zoom/2)'",
    }
    vf = _chain("scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160",
                f"zoompan={moves[direction]}:d={n}:s={W}x{H}:fps={FPS}",
                GRADES[grade], _fades(dur, fade_in, fade_out))
    run(["ffmpeg", "-y", "-loop", "1", "-i", photo, "-frames:v", str(n), "-vf", vf] + _ENC + [out])
    return out


def _card_png(lines, path, bg=(14, 17, 22)):
    """lines: list of (text, size, (r,g,b)). Draws centered text with an outline."""
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    total = sum(sz * 1.35 for _, sz, _ in lines)
    y = (H - total) / 2
    for txt, sz, col in lines:
        f = _font(_FONT_SERIF if sz >= 80 else _FONT_BOLD, sz)
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=col, stroke_width=3, stroke_fill=(0, 0, 0))
        y += sz * 1.35
    im.save(path)


def text_card(lines, dur, out, fade_in=0.4, fade_out=0.4, bg=(14, 17, 22)):
    """lines: list of (text, font_size, (r,g,b)), e.g. [("About 26 tons of concrete", 96, (235,70,60))]."""
    png = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    _card_png(lines, png, bg)
    n = int(dur * FPS)
    run(["ffmpeg", "-y", "-loop", "1", "-i", png, "-frames:v", str(n), "-vf",
         _fades(dur, fade_in, fade_out) or "null"] + _ENC + [out])
    os.unlink(png)
    return out


def lower_third(video, text, start, dur, out, sub=None):
    """Caption bar at the bottom-left, visible from `start` for `dur` seconds."""
    png = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f1, f2 = _font(_FONT_BOLD, 54), _font(_FONT_BOLD, 34)
    w = max(d.textlength(text, font=f1), d.textlength(sub or "", font=f2)) + 70
    h = 100 + (46 if sub else 0)
    x0, y0 = 90, H - 170 - (46 if sub else 0)
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(0, 0, 0, 170))
    d.rectangle([x0, y0, x0 + 8, y0 + h], fill=(240, 176, 40, 255))
    d.text((x0 + 36, y0 + 18), text, font=f1, fill=(255, 255, 255, 255))
    if sub:
        d.text((x0 + 36, y0 + 92), sub, font=f2, fill=(240, 176, 40, 255))
    im.save(png)
    end = start + dur
    run(["ffmpeg", "-y", "-i", video, "-i", png, "-filter_complex",
         f"[0:v][1:v]overlay=0:0:enable='between(t,{start},{end})'", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-pix_fmt", "yuv420p", "-an", out])
    os.unlink(png)
    return out


def concat(shots, out):
    """Join clips made by shot/kenburns/text_card (same encoding, so no re-encode)."""
    lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for s in shots:
        lst.write(f"file '{os.path.abspath(s)}'\n")
    lst.close()
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, "-c", "copy", out])
    os.unlink(lst.name)
    return out


# ---------------- audio ----------------
def _read_mono(path):
    """Any audio file -> float array at 44.1 kHz mono (via ffmpeg)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    run(["ffmpeg", "-y", "-i", path, "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", tmp])
    with wave.open(tmp) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32767
    os.unlink(tmp)
    return x


def _write_wav(path, x):
    pcm = np.int16(np.clip(x, -1, 1) * 32767)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _db(db):
    return 10 ** (db / 20)


def mix(vo, bed, sfx_list, out, vo_db=-16.0, bed_db=-24.0, duck_db=-6.0, sfx_db=-8.0, length=None):
    """Voice at about -16 dBFS RMS, bed at about -24 dBFS RMS (lowered a further
    `duck_db` while the voice is speaking), effects at `sfx_db`, then normalized
    to -14 LUFS. vo: path to an audio file or None. bed: a float array (from
    pipeline.sound.drone) or None. sfx_list: [(seconds, float_array), ...].
    `length` (seconds) cuts or pads everything to that length. Returns `out` (a .wav)."""
    v = _read_mono(vo) if vo else np.zeros(0)
    n = int(length * SR) if length else max(len(v), len(bed) if bed is not None else 0, 1)
    mixed = np.zeros(n)
    active = np.zeros(n)
    if len(v):
        v = v[:n]
        loud = np.abs(v) > 0.01
        rms = np.sqrt(np.mean(v[loud] ** 2)) if np.any(loud) else 1.0
        v = v * (_db(vo_db) / (rms + 1e-9))
        mixed[:len(v)] += v
        k = int(SR * 0.3)
        env = np.convolve(np.abs(v), np.ones(k) / k, mode="same")
        active[:len(v)] = np.clip(env / 0.02, 0, 1)
    if bed is not None:
        b = np.resize(bed, n)  # repeat if the bed is shorter
        b = b * (_db(bed_db) / (np.sqrt(np.mean(b ** 2)) + 1e-9)) * (1 - (1 - _db(duck_db)) * active)
        mixed += b
    for item in sfx_list:  # (seconds, array) or (seconds, array, peak_db) to make one effect louder or quieter
        at, s = item[0], item[1]
        db = item[2] if len(item) > 2 else sfx_db
        i = int(at * SR)
        if 0 <= i < n:
            j = min(n, i + len(s))
            mixed[i:j] += s[: j - i] * _db(db) / max(np.max(np.abs(s)), 1e-9)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    _write_wav(tmp, mixed)
    run(["ffmpeg", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1",
         "-sample_fmt", "s16", out])
    os.unlink(tmp)
    return out


def mux(video, audio, out):
    """Video (no sound) + mixed audio -> MP4 (H.264 + AAC 192k, faststart)."""
    run(["ffmpeg", "-y", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", out])
    return out


# ---------------- 15 s test scene ----------------
def test_scene(out_dir="output"):
    from pipeline import sound as S
    base = "output/01-big-dig-ceiling-collapse"
    photo = sorted(glob.glob(f"{base}/photos/*.jpg"))[0]
    clip = sorted(glob.glob(f"{base}/clips/*.mp4"))[0]
    vo = sorted(glob.glob(f"{base}/sections/*/vo.wav"))[0]
    os.makedirs(out_dir, exist_ok=True)
    t = tempfile.mkdtemp()
    parts = [
        kenburns(photo, 6.0, f"{t}/a.mp4", "in", grade="cold", fade_in=0.5),
        text_card([("About 26 tons", 110, (235, 70, 60)), ("of concrete", 80, (240, 240, 240))], 3.5, f"{t}/b.mp4"),
        shot(clip, 1.0, 5.5, f"{t}/c.mp4", grade="dark", fade_out=0.6),
    ]
    video = concat(parts, f"{t}/v.mp4")
    video = lower_third(video, "Boston, 2006", 1.0, 4.0, f"{t}/v2.mp4", sub="I-90 connector tunnel")
    total = 6.0 + 3.5 + 5.5
    sfx = [(5.6, S.whoosh()), (6.0, S.typewriter_tick(seed=1)), (6.25, S.typewriter_tick(seed=2)),
           (6.5, S.typewriter_tick(seed=3)), (9.45, S.whoosh())]
    audio = mix(vo, S.drone(total, "neutral"), sfx, f"{t}/a.wav", length=total)
    return mux(video, audio, f"{out_dir}/scene_kit_test.mp4")


if __name__ == "__main__":
    print(test_scene())

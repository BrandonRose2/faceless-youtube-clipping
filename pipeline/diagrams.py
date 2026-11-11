"""Step 4: Render animated diagram clips from visual cues in a script.

Usage:
  python3 pipeline/diagrams.py --script scripts/01-big-dig-ceiling-collapse.md

Reads *[visual cues]* from the script and renders matching diagram animations
(1920x1080 at 30fps) into `output/<slug>/diagrams/diag_01.mp4`, `diag_02.mp4`,
etc., plus `manifest.json`. Uses PIL + ffmpeg piping (no temp frame files).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1920, 1080, 30

BG_COLOR = (15, 18, 24)
CONCRETE = (100, 105, 115)
STEEL = (180, 185, 195)
EPOXY_ORANGE = (240, 176, 40)
RED_ALERT = (225, 60, 50)
GREEN_OK = (40, 180, 100)
BLUE_MAP = (50, 130, 220)
WHITE_TEXT = (240, 240, 240)
DIM_TEXT = (160, 165, 175)


TEXT_SCALE = 1.35  # all labels render ~35% larger so they read on a phone


def load_font(size, bold=False):
    from PIL import ImageFont
    candidates = []
    if bold:
        candidates.extend([
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ])
    else:
        candidates.extend([
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ])
    for fp in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, int(size * TEXT_SCALE))
    return ImageFont.load_default()


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def draw_text_centered(draw, text, y, size, color, bold=False, cx=None):
    font = load_font(size, bold=bold)
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W if cx is None else 2 * cx) // 2 - (bbox[2] - bbox[0]) // 2
    draw.text((x, y), text, font=font, fill=color)


def pipe_diagram(generator, output_path, fps=FPS):
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{W}x{H}',
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-pix_fmt', 'yuv420p',
        '-loglevel', 'error',
        str(output_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    count = 0
    try:
        for frame_bytes in generator:
            proc.stdin.write(frame_bytes)
            count += 1
    finally:
        proc.stdin.close()
        proc.wait()
    print(f'  -> {output_path.name} ({count} frames, ~{count/fps:.1f}s)')


# --- Dedicated Drawing Functions for Big Dig Cues ---

def draw_map_animation(d, t, dur):
    for i in range(0, W, 120):
        d.line([(i, 0), (i, H)], fill=(30, 35, 45), width=2)
    for j in range(0, H, 120):
        d.line([(0, j), (W, j)], fill=(30, 35, 45), width=2)
    fade = 1.0 - ease(min(1.0, t / 3.0))
    d.line([(200, 400), (400, 380), (600, 420), (800, 380), (1000, 420),
            (1200, 380), (1400, 420), (1600, 380)],
           fill=(int(225*fade), int(60*fade), int(50*fade)), width=5)
    tunnel_progress = ease(min(1.0, max(0.0, (t - 2.0) / 4.0)))
    segments = [(200, 500), (400, 480), (600, 520), (800, 480), (1000, 520),
                (1200, 480), (1400, 520), (1600, 480)]
    current_end = int(len(segments) * tunnel_progress)
    if current_end > 1:
        pts = segments[:current_end + 1]
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=BLUE_MAP, width=8)
    if t > 3.0:
        a = min(1.0, (t - 3.0) / 1.5)
        draw_text_centered(d, "I-90 CONNECTOR TUNNEL", 150, 48,
                           tuple(int(c * a) for c in WHITE_TEXT), bold=True)
    if t > 5.0:
        a = min(1.0, (t - 5.0) / 1.5)
        draw_text_centered(d, "Boston • Ted Williams Tunnel • Logan Airport", 600, 32,
                           tuple(int(c * a) for c in DIM_TEXT))


def draw_cutaway_animation(d, t, dur):
    d.rectangle([(100, 170), (1820, 320)], fill=CONCRETE)          # roof
    d.rectangle([(100, 320), (1820, 620)], fill=(40, 45, 55))      # space above ceiling
    for x in range(150, 1800, 280):                                # hanging ceiling panels
        d.rectangle([(x, 620), (x + 200, 760)], fill=(130, 135, 145))
        d.line([(x + 100, 320), (x + 100, 620)], fill=STEEL, width=4)  # hanger rods
    d.rectangle([(100, 760), (1820, 1000)], fill=(30, 32, 38))     # roadway space
    labels = [
        (215, "CONCRETE TUNNEL ROOF", WHITE_TEXT),
        (450, "SPACE ABOVE THE CEILING (AIR DUCT)", WHITE_TEXT),
        (800, "HANGING CEILING PANELS", EPOXY_ORANGE),
        (930, "TRAFFIC LANES", DIM_TEXT),
    ]
    shown = int(len(labels) * ease(min(1.0, t / 4.0)) + 0.999)
    for y, text, col in labels[:shown]:
        draw_text_centered(d, text, y, 30, col, bold=True)
    if t > 2.0:
        a = min(1.0, (t - 2.0) / 1.0)
        draw_text_centered(d, "TUNNEL CROSS-SECTION: D STREET PORTAL", 70, 36,
                           tuple(int(c * a) for c in WHITE_TEXT), bold=True)


def draw_hanger_zoom(d, t, dur):
    d.rectangle([(150, 80), (1820, 380)], fill=CONCRETE)             # concrete roof
    hole_x, top, bottom = 760, 150, 380
    d.rectangle([(hole_x - 22, top), (hole_x + 22, bottom)], fill=(50, 52, 58))
    fill = ease(min(1.0, max(0.0, (t - 1.0) / 3.0)))
    d.rectangle([(hole_x - 20, bottom - (bottom - top) * fill), (hole_x + 20, bottom)], fill=EPOXY_ORANGE)
    bolt = ease(min(1.0, max(0.0, (t - 2.0) / 2.0)))
    if bolt > 0:
        d.rectangle([(hole_x - 7, bottom - (bottom - top - 10) * bolt), (hole_x + 7, bottom + 10)], fill=STEEL)
    d.rectangle([(hole_x - 5, bottom + 10), (hole_x + 5, 800)], fill=STEEL)     # hanger rod
    d.polygon([(hole_x - 90, 800), (hole_x + 90, 800), (hole_x + 70, 840), (hole_x - 70, 840)], fill=STEEL)
    d.rectangle([(150, 840), (1820, 910)], fill=(130, 135, 145))                 # ceiling panel
    draw_text_centered(d, "CONCRETE TUNNEL ROOF", 100, 28, WHITE_TEXT, bold=True, cx=1350)
    labels = [
        ((hole_x + 10, 200), "8-INCH STAINLESS-STEEL BOLT", 2.5),
        ((hole_x + 22, 320), "EPOXY HOLDS THE BOLT IN THE HOLE", 3.5),
        ((hole_x + 5, 600), "STEEL HANGER ROD", 4.5),
        ((hole_x + 90, 820), "CEILING PANEL", 5.5),
    ]
    font = load_font(28)
    for (px, py), text, show_at in labels:
        if t >= show_at:
            d.line([(px, py), (1000, py)], fill=EPOXY_ORANGE, width=3)
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=EPOXY_ORANGE)
            d.text((1015, py - 22), text, font=font, fill=WHITE_TEXT)


def draw_weight_scale(d, t, dur):
    px, py, half = 960, 520, 440  # pivot and beam half-length
    d.polygon([(px - 70, 900), (px + 70, 900), (px, py)], fill=CONCRETE)
    tilt = math.radians(18 * ease(min(1.0, t / 3.0)))
    lx, ly = px - half * math.cos(tilt), py - half * math.sin(tilt)
    rx, ry = px + half * math.cos(tilt), py + half * math.sin(tilt)
    d.line([(lx, ly), (rx, ry)], fill=STEEL, width=14)
    for x, y, col in ((lx, ly, DIM_TEXT), (rx, ry, RED_ALERT)):
        d.line([(x - 70, y + 90), (x, y)], fill=col, width=3)
        d.line([(x + 70, y + 90), (x, y)], fill=col, width=3)
        d.arc([(x - 90, y + 50), (x + 90, y + 130)], 0, 180, fill=col, width=6)
    grow = ease(min(1.0, t / 2.0))
    w = 80 * grow
    d.rectangle([(rx - w, ry + 130 - 110 * grow), (rx + w, ry + 130)], fill=RED_ALERT)
    if t > 1.5:
        draw_text_centered(d, "NORMAL LOAD", ly - 90, 30, DIM_TEXT, cx=lx)
    if t > 2.5:
        draw_text_centered(d, "26 TONS OF CEILING PANELS", ry + 160, 30, RED_ALERT, bold=True, cx=min(rx, W - 330))


def draw_creep_label(d, t, dur):
    d.rectangle([(100, 100), (1820, 1000)], fill=(25, 28, 35))
    slide = ease(min(1.0, max(0.0, (t - 2.0) / 5.0))) * 200
    top = 300 + slide
    d.rectangle([(700, top), (1220, top + 180)], fill=(240, 200, 80), outline=EPOXY_ORANGE, width=3)
    draw_text_centered(d, "EPOXY", top + 60, 36, BG_COLOR, bold=True)
    wy = top + 240
    d.line([(960, top + 180), (960, wy)], fill=DIM_TEXT, width=4)
    d.rectangle([(860, wy), (1060, wy + 90)], fill=RED_ALERT)
    draw_text_centered(d, "CONSTANT LOAD", wy + 25, 24, WHITE_TEXT, bold=True)
    cx, cy = 1550, 230
    d.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=(40, 45, 55), outline=WHITE_TEXT, width=4)
    ang = t * math.pi * 2
    d.line([(cx, cy), (cx + int(60 * math.sin(ang)), cy - int(60 * math.cos(ang)))], fill=WHITE_TEXT, width=4)
    years = int(slide / 200 * 7)
    if years > 0:
        draw_text_centered(d, f"{years} YEAR{'S' if years > 1 else ''}", cy + 110, 30, DIM_TEXT, bold=True, cx=cx)
    if slide > 150:
        draw_text_centered(d, "CREEP: SLOW STRETCHING UNDER CONSTANT LOAD", 915, 34, RED_ALERT, bold=True)


def draw_epoxy_comparison(d, t, dur):
    mid = W // 2
    sides = [
        (480, (20, 30, 50), BLUE_MAP, (100, 150, 200), "STANDARD SET",
         ["Hardens more slowly", "Better creep resistance"], GREEN_OK),
        (1440, (50, 20, 20), RED_ALERT, (200, 100, 100), "FAST SET",
         ["Hardens quickly", "Very poor creep resistance"], RED_ALERT),
    ]
    for cx, bg, edge, tube, title, points, col in sides:
        d.rectangle([(cx - 430, 120), (cx + 430, 960)], fill=bg, outline=edge, width=4)
        draw_text_centered(d, title, 190, 40, edge, bold=True, cx=cx)
        d.rectangle([(cx - 70, 320), (cx + 70, 600)], fill=tube, outline=edge, width=3)
        d.rectangle([(cx - 70, 320), (cx + 70, 360)], fill=edge)
        for i, p in enumerate(points):
            if t > 1.0 + i * 0.8:
                draw_text_centered(d, p, 690 + i * 75, 30, col if i else WHITE_TEXT, bold=bool(i), cx=cx)
    draw_text_centered(d, "VS", 470, 56, WHITE_TEXT, bold=True, cx=mid)


def draw_timeline_warning(d, t, dur):
    timeline_y = 500
    d.rectangle([(200, timeline_y), (1720, timeline_y + 20)], fill=DIM_TEXT)
    years = list(range(1995, 2008))
    marker_positions = {}
    for i, year in enumerate(years):
        x = 200 + int((i / (len(years) - 1)) * 1520)
        marker_positions[year] = x
        d.line([(x, timeline_y - 30), (x, timeline_y + 50)], fill=WHITE_TEXT, width=3)
        d.text((x - 20, timeline_y + 70), str(year), font=load_font(28), fill=DIM_TEXT)
    flag_x = marker_positions.get(1999, 500)
    flag_pop = ease(min(1.0, max(0.0, (t - 1.5) / 1.0)))
    if flag_pop > 0:
        flag_y = timeline_y - int(150 * flag_pop)
        d.line([(flag_x, timeline_y), (flag_x, flag_y)], fill=WHITE_TEXT, width=4)
        d.rectangle([(flag_x, flag_y), (flag_x + int(120 * flag_pop), flag_y + 60)], fill=RED_ALERT)
        if t > 3.0:
            draw_text_centered(d, "1999: ANCHOR BOLTS DETECTED SLIPPING", flag_y - 40, 28, RED_ALERT, bold=True)
    if t > 4.5:
        gap_cx = (marker_positions.get(1999, 500) + marker_positions.get(2006, 1500)) // 2 - 40
        draw_text_centered(d, "7 YEARS — NO CREEP MONITORING", timeline_y - 75, 30, DIM_TEXT, cx=gap_cx)
    collapse_x = marker_positions.get(2006, 1500)
    if t > 6.0:
        d.ellipse([collapse_x - 30, timeline_y - 40, collapse_x + 30, timeline_y + 20], fill=RED_ALERT)
        draw_text_centered(d, "JULY 10, 2006: CEILING COLLAPSE", timeline_y + 120, 32, RED_ALERT, bold=True)


def draw_zipper_failure(d, t, dur):
    d.rectangle([(0, 0), (W, 400)], fill=CONCRETE)
    num_anchors = 20
    spacing = 1720 // (num_anchors - 1)
    failed_count = int(ease(min(1.0, t / 4.0)) * num_anchors)
    for i in range(num_anchors):
        ax = 100 + i * spacing
        if i >= failed_count:
            d.rectangle([(ax - 6, 370), (ax + 6, 400)], fill=STEEL)
        else:
            d.rectangle([(ax - 6, 450), (ax + 6, 480)], fill=RED_ALERT)
    for i in range(5):
        d.rectangle([(200 + i * 350, 400), (500 + i * 350, 600)], fill=(130, 135, 145), outline=STEEL, width=2)
    if t > 3.0:
        draw_text_centered(d, "PROGRESSIVE ZIPPER FAILURE (20 ANCHORS)", 750, 36, RED_ALERT, bold=True)


def draw_federal_investigation(d, t, dur):
    d.rectangle([(50, 150), (W - 50, 950)], fill=(20, 22, 28), outline=EPOXY_ORANGE, width=3)
    if t > 0.5:
        draw_text_centered(d, "FEDERAL INVESTIGATION", 250, 56, WHITE_TEXT, bold=True)
    if t > 1.5:
        draw_text_centered(d, "12 MONTHS • 171-PAGE REPORT", 330, 32, EPOXY_ORANGE)
    findings = [
        "1. Fast-Set Epoxy Creep Failure",
        "2. Lack of Long-Term Monitoring",
        "3. Industry-Wide Misunderstanding of Creep",
    ]
    for i, f_text in enumerate(findings):
        if t > 2.5 + i * 1.0:
            draw_text_centered(d, f_text, 500 + i * 70, 32, DIM_TEXT)


def draw_financial_ledger(d, t, dur):
    d.rectangle([(100, 100), (W - 100, 200)], fill=(25, 28, 35))
    draw_text_centered(d, "SETTLEMENTS & PENALTIES", 130, 40, WHITE_TEXT, bold=True)
    entries = [
        ("Bechtel/Parsons Brinckerhoff Consortium", 407000000, "management/joint venture share"),
        ("Total Management Settlement", 458000000, "including 24+ smaller firms"),
        ("Powers Fasteners (Epoxy Supplier)", 16000000, "criminal charge dismissed"),
        ("Del Valle Family Wrongful Death", 28000000, "settlement against 15 defendants"),
    ]
    for i, (entity, amount, note) in enumerate(entries):
        row_y = 280 + i * 120
        d.rectangle([(100, row_y), (W - 100, row_y + 100)], fill=(20, 22, 28))
        d.text((150, row_y + 20), entity, font=load_font(32), fill=WHITE_TEXT)
        if t > 1.0 + i * 0.8:
            prog = min(1.0, (t - 1.0 - i * 0.8) / 1.5)
            curr = int(amount * ease(prog))
            d.text((1300, row_y + 25), f"${curr:,}", font=load_font(36), fill=EPOXY_ORANGE)
        d.text((150, row_y + 65), note, font=load_font(24), fill=DIM_TEXT)


def draw_sustained_load(d, t, dur):
    for y in range(H):
        b = int(15 + (y / H) * 10)
        d.line([(0, y), (W, y)], fill=(b, b + 3, b + 8))
    bolt_x = W // 2
    d.rectangle([(bolt_x - 100, 200), (bolt_x + 100, 300)], fill=CONCRETE)
    d.rectangle([(bolt_x - 10, 300), (bolt_x + 10, 600)], fill=STEEL)
    d.rectangle([(bolt_x - 15, 280), (bolt_x + 15, 300)], fill=EPOXY_ORANGE)
    pulse = 0.8 + 0.2 * math.sin(t * 3)
    arrow_len = int(200 * pulse)
    d.rectangle([(bolt_x - 15, 150), (bolt_x + 15, 150 + arrow_len)], fill=RED_ALERT)
    d.polygon([(bolt_x - 40, 150 + arrow_len), (bolt_x, 150 + arrow_len + 60), (bolt_x + 40, 150 + arrow_len)], fill=RED_ALERT)
    if t > 1.0:
        draw_text_centered(d, "SUSTAINED LOAD", 70, 36, RED_ALERT, bold=True)
    if t > 2.0:
        draw_text_centered(d, "Load that never goes away — 24/7 for life", 700, 28, DIM_TEXT)


def draw_redundant_hangers(d, t, dur):
    d.rectangle([(200, 150), (W - 200, 300)], fill=CONCRETE)
    d.rectangle([(400, 700), (1520, 900)], fill=(130, 135, 145), outline=STEEL, width=3)
    hx_list = [550, 800, 1100, 1350]
    failed_idx = 1 if t > 3.0 else None
    for i, hx in enumerate(hx_list):
        col = RED_ALERT if (failed_idx is not None and i == failed_idx) else STEEL
        d.line([(hx, 300), (hx, 700)], fill=col, width=8)
    if failed_idx is not None:
        for lx in [550, 1100, 1350]:
            if lx != 800:
                d.line([(800, 650), (lx, 650)], fill=GREEN_OK, width=4)
    if t > 1.0:
        draw_text_centered(d, "REDUNDANT HANGERS: Shared Load Distribution", 100, 40, WHITE_TEXT, bold=True)
    if t > 4.0:
        draw_text_centered(d, "If one fails, remaining hangers share the weight", 930, 40, GREEN_OK, bold=True)


def render_title_card(title_lines, subtitle_lines, output_path, duration=6.0):
    def generator():
        from PIL import Image, ImageDraw
        n = int(duration * FPS)
        for i in range(n):
            t = i / FPS
            im = Image.new('RGB', (W, H), BG_COLOR)
            d = ImageDraw.Draw(im)
            cx, cy = W // 2, H // 2 - 50
            y_pos = cy - 80
            for line in title_lines:
                d.text((cx - d.textlength(line, font=load_font(48, bold=True)) // 2, y_pos),
                       line, font=load_font(48, bold=True), fill=EPOXY_ORANGE)
                y_pos += 60
            for line in subtitle_lines:
                d.text((cx - d.textlength(line, font=load_font(28)) // 2, y_pos),
                       line, font=load_font(28), fill=WHITE_TEXT)
                y_pos += 40
            yield im.tobytes()
    pipe_diagram(generator(), output_path, FPS)


CUE_RENDERERS = {
    "animated map": draw_map_animation,
    "map:": draw_map_animation,
    "3d cutaway": draw_cutaway_animation,
    "cutaway": draw_cutaway_animation,
    "zoom into a single hanger": draw_hanger_zoom,
    "single hanger": draw_hanger_zoom,
    "weight scale": draw_weight_scale,
    "graphic: a weight scale": draw_weight_scale,
    "sticky label": draw_creep_label,
    "split screen": draw_epoxy_comparison,
    "two epoxy tubes": draw_epoxy_comparison,
    "red flag": draw_timeline_warning,
    "timeline at 1999": draw_timeline_warning,
    "zipper": draw_zipper_failure,
    "anchors pop out": draw_zipper_failure,
    "federal investigation": draw_federal_investigation,
    "ledger": draw_financial_ledger,
    "sustained load": draw_sustained_load,
    "redundant hangers": draw_redundant_hangers,
    "overhead load carried": draw_redundant_hangers,
}


def extract_cues(script_path):
    text = script_path.read_text()
    return re.findall(r'\[(.*?)\]\*', text)


def get_cue_type(cue):
    low = cue.lower()
    for key in CUE_RENDERERS:
        if key in low:
            return key
    return None


def render_generic_diagram(cue_text, output_path, duration=8.0):
    words = cue_text.split()
    title = ' '.join(words[:15]) + '...' if len(words) > 15 else cue_text
    def generator():
        from PIL import Image, ImageDraw
        n = int(duration * FPS)
        for i in range(n):
            t = i / FPS
            im = Image.new('RGB', (W, H), BG_COLOR)
            d = ImageDraw.Draw(im)
            draw_text_centered(d, title, 450, 36, WHITE_TEXT, bold=True)
            yield im.tobytes()
    pipe_diagram(generator(), output_path, FPS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--script', required=True)
    args = ap.parse_args()

    script_path = Path(args.script)
    slug = script_path.stem
    diagrams_dir = ROOT / 'output' / slug / 'diagrams'
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    cues = extract_cues(script_path)
    print(f"Found {len(cues)} visual cues in {slug}")

    diagram_cues = []
    for cue in cues:
        low = cue.lower()
        if any(kw in low for kw in ['animated', 'map', 'cutaway', '3d', 'graphic', 'diagram',
                                    'label', 'title card', 'timeline', 'split screen',
                                    'ledger', 'reconstruction', 'zoom into']):
            # Skip the main video title card (handled separately as card_title.mp4)
            if 'title card' in low and 'federal investigation' not in low:
                continue
            diagram_cues.append(cue)

    print(f"Rendering {len(diagram_cues)} diagrams...")
    manifest = []
    diag_num = 1

    for cue in diagram_cues:
        cue_key = get_cue_type(cue)
        output_path = diagrams_dir / f'diag_{diag_num:02d}.mp4'
        duration = 10.0

        if cue_key and cue_key in CUE_RENDERERS:
            print(f"  [{diag_num:02d}] {cue[:50]}...")
            renderer = CUE_RENDERERS[cue_key]
            def make_gen(r=renderer, dur=duration):
                from PIL import Image, ImageDraw
                n = int(dur * FPS)
                for i in range(n):
                    t = i / FPS
                    im = Image.new('RGB', (W, H), BG_COLOR)
                    d = ImageDraw.Draw(im)
                    r(d, t, dur)
                    yield im.tobytes()
            pipe_diagram(make_gen(), output_path, FPS)
        else:
            print(f"  [{diag_num:02d}] (generic) {cue[:50]}...")
            render_generic_diagram(cue, output_path, duration)

        manifest.append({"file": output_path.name, "cue": cue})
        diag_num += 1

    title_cues = [c for c in cues if 'title card' in c.lower()]
    for cue in title_cues:
        if 'THE GLUE THAT KILLED' in cue:
            out_card = diagrams_dir / 'card_title.mp4'
            print("  Rendering title card...")
            render_title_card(['THE GLUE THAT KILLED'], ['The Big Dig Ceiling Collapse'], out_card, 8.0)
            manifest.append({"file": out_card.name, "cue": cue})

    manifest_path = diagrams_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n✅ Done! Manifest: {manifest_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

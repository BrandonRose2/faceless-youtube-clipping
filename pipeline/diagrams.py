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
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def draw_text_centered(draw, text, y, size, color, bold=False):
    font = load_font(size, bold=bold)
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
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
    d.rectangle([(100, 200), (1820, 350)], fill=CONCRETE)
    d.rectangle([(100, 350), (1820, 650)], fill=(40, 45, 55))
    for x in range(150, 1800, 280):
        d.rectangle([(x, 650), (x + 200, 800)], fill=(130, 135, 145))
    d.rectangle([(100, 800), (1820, 1000)], fill=(30, 32, 38))
    d.rectangle([(900, 780), (1020, 830)], fill=(60, 65, 75))
    callouts = [
        ((950, 275), (600, 100), "CONCRETE ROOF"),
        ((950, 500), (1300, 100), "PLENUM (AIR VENTILATION)"),
        ((950, 725), (1300, 200), "PRECAST CONCRETE CEILING PANELS"),
    ]
    progress = ease(min(1.0, t / 4.0))
    shown = int(len(callouts) * progress)
    for i in range(shown):
        pt, label_pos, text = callouts[i]
        d.line([pt, label_pos], fill=EPOXY_ORANGE, width=3)
        d.ellipse([pt[0] - 8, pt[1] - 8, pt[0] + 8, pt[1] + 8], fill=EPOXY_ORANGE)
        draw_text_centered(d, text, label_pos[1], 28, WHITE_TEXT)
    if t > 2.0:
        a = min(1.0, (t - 2.0) / 1.0)
        draw_text_centered(d, "TUNNEL CROSS-SECTION: D STREET PORTAL", 50, 36,
                           tuple(int(c * a) for c in WHITE_TEXT), bold=True)


def draw_hanger_zoom(d, t, dur):
    d.rectangle([(200, 100), (1820, 400)], fill=CONCRETE)
    hole_x, hole_y = 850, 220
    d.rectangle([(hole_x - 20, hole_y - 80), (hole_x + 20, hole_y + 20)], fill=(50, 52, 58))
    epoxy_fill = ease(min(1.0, max(0.0, (t - 1.0) / 3.0)))
    d.rectangle([(hole_x - 18, hole_y - 78 * epoxy_fill), (hole_x + 18, hole_y + 18)], fill=EPOXY_ORANGE)
    bolt_visible = ease(min(1.0, max(0.0, (t - 2.0) / 2.0)))
    if bolt_visible > 0:
        d.rectangle([(hole_x - 6, hole_y - 75 * bolt_visible), (hole_x + 6, hole_y)], fill=STEEL)
    rod_start_y = hole_y + 20
    d.rectangle([(hole_x - 4, rod_start_y), (hole_x + 4, 900)], fill=STEEL)
    bracket_y = 750
    d.polygon([(hole_x - 80, bracket_y), (hole_x + 80, bracket_y),
               (hole_x + 60, bracket_y + 40), (hole_x - 60, bracket_y + 40)], fill=STEEL)
    d.rectangle([(200, 790), (1820, 850)], fill=(130, 135, 145))
    labels = [
        ((hole_x + 50, hole_y - 40), "8-INCH STAINLESS STEEL BOLT", 2.5),
        ((hole_x + 50, hole_y + 30), "TWO-PART EPOXY ADHESIVE", 3.5),
        ((hole_x + 50, rod_start_y + 100), "STEEL BRACKET & HANGER ROD", 4.5),
        ((hole_x + 50, rod_start_y + 200), "CONCRETE TUNNEL ROOF", 5.5),
    ]
    for label_pt, text, show_at in labels:
        if t >= show_at:
            d.line([label_pt, (label_pt[0] - 40, label_pt[1])], fill=EPOXY_ORANGE, width=2)
            draw_text_centered(d, text, label_pt[1] - 15, 28, WHITE_TEXT)


def draw_weight_scale(d, t, dur):
    d.rectangle([(900, 750), (1120, 850)], fill=(80, 85, 95))
    d.polygon([(1010, 850), (1050, 850), (1030, 750)], fill=STEEL)
    beam_angle = -30 * ease(min(1.0, t / 3.0))
    rad = math.radians(beam_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    left_x, left_y = 1030 - 400 * cos_a, 800 + 400 * sin_a
    right_x, right_y = 1030 + 400 * cos_a, 800 - 400 * sin_a
    d.line([(left_x, left_y), (right_x, right_y)], fill=STEEL, width=12)
    d.arc([(left_x - 60, left_y), (left_x + 60, left_y + 80)], 0, 180, fill=DIM_TEXT, width=4)
    d.line([(left_x - 50, left_y), (left_x - 50, left_y + 80)], fill=DIM_TEXT, width=2)
    d.line([(left_x + 50, left_y), (left_x + 50, left_y + 80)], fill=DIM_TEXT, width=2)
    d.arc([(right_x - 60, right_y), (right_x + 60, right_y + 80)], 0, 180, fill=RED_ALERT, width=4)
    d.line([(right_x - 50, right_y), (right_x - 50, right_y + 80)], fill=RED_ALERT, width=2)
    d.line([(right_x + 50, right_y), (right_x + 50, right_y + 80)], fill=RED_ALERT, width=2)
    weight_size = 60 * ease(min(1.0, t / 2.0))
    d.rectangle([(right_x - weight_size, right_y + 80), (right_x + weight_size, right_y + 160)], fill=RED_ALERT)
    if t > 1.5:
        draw_text_centered(d, "STANDARD ANCHOR LOAD", left_y + 100, 24, DIM_TEXT)
    if t > 2.5:
        draw_text_centered(d, "26-TON OVERHEAD CEILING PANEL", right_y + 180, 24, RED_ALERT, bold=True)


def draw_creep_label(d, t, dur):
    d.rectangle([(100, 100), (1920, 980)], fill=(25, 28, 35))
    label_y_base = 400
    slide_amount = ease(min(1.0, max(0.0, (t - 2.0) / 5.0))) * 200
    label_rect = [(700, label_y_base + slide_amount), (1220, label_y_base + 200 + slide_amount)]
    d.rectangle(label_rect, fill=(240, 200, 80), outline=EPOXY_ORANGE, width=3)
    draw_text_centered(d, "EPOXY ADHESIVE", 440 + slide_amount, 32, BG_COLOR)
    weight_y = label_rect[1][1] + 10
    d.rectangle([(850, weight_y), (1070, weight_y + 100)], fill=RED_ALERT)
    d.line([(850, weight_y), (850, weight_y - 50)], fill=DIM_TEXT, width=3)
    d.line([(1070, weight_y), (1070, weight_y - 50)], fill=DIM_TEXT, width=3)
    d.line([(960, weight_y - 50), (960, label_rect[0][1])], fill=DIM_TEXT, width=3)
    clock_cx, clock_cy = 1500, 200
    d.ellipse([clock_cx - 80, clock_cy - 80, clock_cx + 80, clock_cy + 80],
              fill=(40, 45, 55), outline=WHITE_TEXT, width=4)
    minute_hand_angle = t * math.pi * 2
    mx = clock_cx + int(60 * math.sin(minute_hand_angle))
    my = clock_cy - int(60 * math.cos(minute_hand_angle))
    d.line([(clock_cx, clock_cy), (mx, my)], fill=WHITE_TEXT, width=4)
    years_passed = int(slide_amount / 200 * 7)
    if years_passed > 0:
        draw_text_centered(d, f"{years_passed} YEARS OF CREEP", 100, 32, DIM_TEXT)
    if slide_amount > 150:
        draw_text_centered(d, "EPOXY CREEP: Slow deformation under constant load", 850, 36, RED_ALERT, bold=True)


def draw_epoxy_comparison(d, t, dur):
    split_x = W // 2
    d.rectangle([(50, 150), (split_x - 50, 950)], fill=(20, 30, 50), outline=BLUE_MAP, width=4)
    tube_y = 400
    d.rectangle([(200, tube_y), (400, tube_y + 250)], fill=(100, 150, 200), outline=BLUE_MAP, width=3)
    d.rectangle([(200, tube_y), (400, tube_y + 40)], fill=BLUE_MAP)
    draw_text_centered(d, "STANDARD SET", 250, 36, BLUE_MAP, bold=True)
    benefits = ["Slower Cure Time", "High Creep Resistance", "Approved for Overhead"]
    for i, b in enumerate(benefits):
        if t > 1.0 + i * 0.8:
            draw_text_centered(d, f"✓ {b}", 550 + i * 60, 28, GREEN_OK)

    d.rectangle([(split_x + 50, 150), (W - 50, 950)], fill=(50, 20, 20), outline=RED_ALERT, width=4)
    d.rectangle([(1520, tube_y), (1720, tube_y + 250)], fill=(200, 100, 100), outline=RED_ALERT, width=3)
    d.rectangle([(1520, tube_y), (1720, tube_y + 40)], fill=RED_ALERT)
    draw_text_centered(d, "FAST SET", 250, 36, RED_ALERT, bold=True)
    warnings = ["Fast Curing Speed", "POOR CREEP RESISTANCE", "NOT for Heavy Overhead"]
    for i, w in enumerate(warnings):
        if t > 1.0 + i * 0.8:
            col = RED_ALERT if "NOT" in w else DIM_TEXT
            draw_text_centered(d, f"⚠ {w}", 550 + i * 60, 28, col)
    draw_text_centered(d, "VS", split_x - 20, 480, WHITE_TEXT, bold=True)


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
        draw_text_centered(d, "7 YEARS - NO CREEP MONITORING / NO INSPECTIONS", timeline_y - 80, 32, DIM_TEXT)
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

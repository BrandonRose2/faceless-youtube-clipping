"""Step 1: split script into timed sections, generate per-section voiceover + timing JSON.

Usage:
  python3 pipeline/sections.py --script scripts/01-big-dig-ceiling-collapse.md \
      [--voice bm_george] [--output-dir output]

Produces one folder per section under output/<slug>/sections/NN-name/:
  - vo.wav (mono 24 kHz, paragraphs joined with 0.35 s silence)
  - timing.json (paragraph timings + visual cues)
"""
import argparse
import json
import re
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


# ---------------------------------------------------------------------------
# Parsing helpers (reused logic from voice.py where appropriate)
# ---------------------------------------------------------------------------

def strip_visual_cues(text: str) -> str:
    """Remove *[italics]* visual cues so TTS only reads narration."""
    return re.sub(r"\*\[.*?\]\*", "", text, flags=re.DOTALL)


def extract_narration(script_path: Path) -> str:
    """Read script markdown and return plain narration text (no visual cues)."""
    raw = script_path.read_text()
    narration = strip_visual_cues(raw)
    lines = [line.strip() for line in narration.splitlines()]
    skip_prefixes = ("DRAFT", "**Target", "*Italic", "> ", "---")
    clean = []
    for line in lines:
        if not line:
            clean.append("")
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            clean.append("")  # blank out skipped lines so we don't merge paragraphs accidentally
            continue
        clean.append(line)
    return "\n".join(clean).strip()


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(r"^##\s+(\d{1,2}:\d{2})\s+(.+)$", re.MULTILINE)


def parse_sections(script_path: Path) -> list[dict]:
    """Return list of {name, start_mmss, raw_text} for each video section heading."""
    raw = script_path.read_text()
    # Find all ## HH:MM Title lines
    matches = list(SECTION_RE.finditer(raw))
    if not matches:
        raise SystemExit(f"No section headings found in {script_path}")

    sections = []
    for i, m in enumerate(matches):
        start = m.group(1)  # "0:00" etc.
        name = m.group(2).strip()
        # Text runs from end of this match to end of file or start of next match
        text_start = m.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        section_raw = raw[text_start:text_end]
        sections.append({"name": name, "start_mmss": start, "raw": section_raw})

    return sections


def split_paragraphs(text: str) -> list[str]:
    """Split on double-newline, discard empty blocks."""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts


# ---------------------------------------------------------------------------
# Visual-cue extraction
# ---------------------------------------------------------------------------

CUE_RE = re.compile(r"\*\[(.*?)\]\*")


def extract_cues(text: str) -> list[tuple[float, str]]:
    """Return [(offset_seconds_approx, cue_text)] for every *[...]* block.
    
    offset is a rough estimate based on character position relative to total length.
    We'll refine with actual audio timing after synthesis.
    """
    cues = []
    for m in CUE_RE.finditer(text):
        cues.append((m.start(), m.group(1)))
    return cues


# ---------------------------------------------------------------------------
# Audio synthesis
# ---------------------------------------------------------------------------

SILENCE_GAP_S = 0.35  # seconds between paragraphs
SAMPLE_RATE = 24000


_PIPE = None


def synthesize_paragraph(para: str, voice: str) -> np.ndarray:
    """Generate one paragraph via Kokoro, return mono float32 at SAMPLE_RATE."""
    from kokoro import KPipeline

    global _PIPE
    if _PIPE is None:
        _PIPE = KPipeline(lang_code=voice[0] if voice[:1] in ("a", "b") else "a")
    gen = _PIPE(para, voice=voice)
    chunks = []
    for result in gen:
        chunks.append(result.audio.cpu().numpy())
    if not chunks:
        return np.zeros(SAMPLE_RATE, dtype=np.float32)
    return np.concatenate(chunks)


def make_silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)


def join_with_gaps(paragraph_audios: list[np.ndarray]) -> tuple[np.ndarray, list[dict]]:
    """Concatenate with SILENCE_GAP_S silence between paragraphs.
    Returns (full_audio, paragraphs_info) where paragraphs_info has
    [{'start': t, 'end': t+dur, 'text': ...}, ...].
    """
    sil_len = int(SILENCE_GAP_S * SAMPLE_RATE)
    parts = []
    paragraphs_info = []
    t = 0.0
    for i, aud in enumerate(paragraph_audios):
        dur = len(aud) / SAMPLE_RATE
        if i > 0:
            # add silence before this paragraph
            parts.append(make_silence(SILENCE_GAP_S))
            t += SILENCE_GAP_S
        parts.append(aud)
        paragraphs_info.append({"start": round(t, 2), "end": round(t + dur, 2), "text": None})
        t += dur
    full = np.concatenate(parts)
    return full, paragraphs_info


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Per-section voiceover + timing generation.")
    ap.add_argument("--script", required=True)
    ap.add_argument("--voice", default="bm_george")
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        raise SystemExit(f"Script not found: {script_path}")

    root = Path(__file__).resolve().parent.parent
    out_root = Path(args.output_dir) if args.output_dir else root / "output"

    slug = script_path.stem
    sections = parse_sections(script_path)

    print(f"Script: {slug}")
    print(f"Sections: {len(sections)}")
    total_words = 0

    for sec in sections:
        name = sec["name"]
        start = sec["start_mmss"]
        # Visual cues are NOT spoken. A cue's time is the start of the narration paragraph after it.
        para_texts, cue_pairs, pending = [], [], []
        for blk in split_paragraphs(sec["raw"]):
            pending += CUE_RE.findall(blk)
            narr = re.sub(r"[*_`]", "", strip_visual_cues(blk)).strip()
            if narr:
                cue_pairs += [(len(para_texts), c) for c in pending]
                pending = []
                para_texts.append(narr)
        cue_pairs += [(None, c) for c in pending]   # cues after the last paragraph land at its end
        n_paras = len(para_texts)
        total_words += sum(len(p.split()) for p in para_texts)

        # Sanitize folder name
        folder_name = f"{start.replace(':', '-')}-{name}"
        # Shorten long names
        if len(folder_name) > 60:
            folder_name = folder_name[:60]
        sec_dir = out_root / slug / "sections" / folder_name
        sec_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Section: [{start}] {name} ({n_paras} paragraphs)")

        # Synthesize each paragraph
        paras_audios = []
        for pi, pt in enumerate(para_texts):
            print(f"  Paragraph {pi+1}/{n_paras}: {len(pt.split())} words")
            aud = synthesize_paragraph(pt, args.voice)
            paras_audios.append(aud)

        # Join
        full, para_info = join_with_gaps(paras_audios)

        # Write WAV
        out_wav = sec_dir / "vo.wav"
        import soundfile as sf
        sf.write(str(out_wav), full, SAMPLE_RATE)
        dur_total = len(full) / SAMPLE_RATE

        # Build timing.json
        for pi, pt in enumerate(para_texts):
            para_info[pi]["text"] = pt
        cues_json = []
        for pi, cue_txt in cue_pairs:
            at_time = para_info[pi]["start"] if pi is not None else para_info[-1]["end"]
            cues_json.append({"at": at_time, "cue": cue_txt})

        timing = {
            "section": name,
            "start_mmss": start,
            "duration_s": round(dur_total, 2),
            "paragraphs": para_info,
            "cues": cues_json,
        }
        out_timing = sec_dir / "timing.json"
        out_timing.write_text(json.dumps(timing, indent=2))

        print(f"  → {out_wav.relative_to(root)}  ({dur_total:.1f}s)")
        print(f"  → {out_timing.relative_to(root)}")

    mins = int(total_words // 60 * 4.5)  # rough estimate
    secs_rem = int(total_words % 60 * 4.5 / 60)
    print(f"\n✅ Done. Total ~{total_words} words across {len(sections)} sections.")
    print("Next: sound.py (music beds + effects) → scene_kit.py → per-section scenes")


if __name__ == "__main__":
    main()

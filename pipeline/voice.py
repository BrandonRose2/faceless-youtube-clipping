"""Step 2: generate narration voiceover via Kokoro (local, free TTS).

Usage:
  python3 pipeline/voice.py --script scripts/02-hyatt-regency-walkway-collapse-1981.md \
      --voice am_michael [--output-dir output]

Available voices: af_heart, af_bella, am_michael, bf_emma, bm_george, etc.
Write out/wav (mono 24 kHz, compatible with ffmpeg assembly).
Kokoro runs locally on your Mac after initial model download (~150 MB).
See docs/PIPELINE.md for full pipeline overview.
"""
import argparse
import re
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


def strip_visual_cues(text: str) -> str:
    """Remove *[italics]* visual cues so TTS only reads narration."""
    return re.sub(r"\*\\[.*?\\]\*", "", text, flags=re.DOTALL)


def extract_narration(script_path: Path) -> str:
    """Read script markdown and return plain narration text (no visual cues)."""
    raw = script_path.read_text()
    narration = strip_visual_cues(raw)
    # Collapse whitespace but keep paragraph breaks for natural pacing
    lines = [line.strip() for line in narration.splitlines()]
    # Skip metadata header lines (DRAFT note, title, target length)
    skip_prefixes = ("DRAFT", "**Target", "*Italic", "> ", "---")
    clean = []
    for line in lines:
        if not line:
            clean.append("")
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        clean.append(line)
    return "\n".join(clean).strip()


def synthesize(narration: str, voice: str, output_wav: Path) -> None:
    """Generate audio via Kokoro and save as mono WAV (24 kHz)."""
    from kokoro import KPipeline
    import soundfile as sf
    import torch

    pipeline = KPipeline(lang_code='a')  # 'a' = American English
    generator = pipeline(narration, voice=voice)

    all_audio = []
    sample_rate = 24000

    for result in generator:
        audio_np = result.audio.cpu().numpy()
        all_audio.append(audio_np)

    if all_audio:
        full_audio = np.concatenate(all_audio)
        sf.write(str(output_wav), full_audio, sample_rate)


def main():
    ap = argparse.ArgumentParser(description="Generate voiceover from a script draft.")
    ap.add_argument("--script", required=True, help="Path to script markdown")
    ap.add_argument("--voice", default="en-US-GuyNeural", help="edge-tts voice name")
    ap.add_argument("--output-dir", default=None, help="Output root (default: repo root / output)")
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        raise SystemExit(f"Script not found: {script_path}")

    root = Path(__file__).resolve().parent.parent
    out_root = Path(args.output_dir) if args.output_dir else root / "output"

    # Derive slug from filename (first two segments before .md)
    stem = script_path.stem  # e.g. "02-hyatt-regency-walkway-collapse-1981"
    num = stem.split("-")[0]  # "02"
    slug = stem
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    narration = extract_narration(script_path)
    out_wav = out_dir / "voice.wav"

    print(f"Generating voiceover for {slug} ...")
    print(f"  Voice: {args.voice}")
    print(f"  Words: {len(narration.split())}")
    print(f"  Output: {out_wav.relative_to(root)}")

    synthesize(narration, args.voice, out_wav)

    duration_info = ""
    try:
        import subprocess
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(out_wav)],
            capture_output=True, text=True, check=True
        )
        secs = float(r.stdout.strip())
        mins = int(secs // 60)
        secs_rem = int(secs % 60)
        duration_info = f"  Duration: ~{mins}:{secs_rem:02d}"
    except Exception:
        pass

    print(f"✅ Done.{duration_info}")
    print(f"Next: footage.py (pull clips) → assemble.py (combine)")


if __name__ == "__main__":
    main()

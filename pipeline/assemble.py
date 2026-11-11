"""Step 5: assemble a video from narration, footage, diagrams, and music in script order.

Usage:
  python3 pipeline/assemble.py \
      --script scripts/01-big-dig-ceiling-collapse.md \
      --voice output/01-big-dig-ceiling-collapse/voice.wav \
      --clips-dir output/01-big-dig-ceiling-collapse/clips \
      --diagrams-dir output/01-big-dig-ceiling-collapse/diagrams \
      --output output/01-big-dig-ceiling-collapse/draft.mp4
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_audio_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())


def find_pause_points(wav_path: Path, min_pause_ms: int = 400) -> list[float]:
    cmd = [
        "ffmpeg", "-i", str(wav_path),
        "-af", f"silencedetect=noise=-30dB:d={min_pause_ms/1000}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    pauses = []
    for line in result.stderr.splitlines():
        match = re.search(r"silence_end: (\d+\.\d+)", line)
        if match:
            pauses.append(float(match.group(1)))
    return pauses


def parse_script_cues(script_path: Path):
    text = script_path.read_text()
    total_words = len(text.split())
    cues = []
    for match in re.finditer(r'\*\[(.*?)\]\*', text):
        pos = match.start()
        fraction = len(text[:pos].split()) / max(1, total_words)
        cues.append((fraction, match.group(1)))
    return cues


def assemble_video(
    script: Path,
    voice: Path,
    clips_dir: Path,
    diagrams_dir: Path | None,
    music: Path | None,
    output: Path,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> Path:
    voice_dur = get_audio_duration(voice)
    print(f"Voiceover duration: {voice_dur:.1f}s")

    script_cues = parse_script_cues(script)
    print(f"Parsed {len(script_cues)} script cues with timeline positions.")

    manifest_map = {}
    if diagrams_dir and diagrams_dir.exists():
        manifest_path = diagrams_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest_data = json.loads(manifest_path.read_text())
                for item in manifest_data:
                    manifest_map[item["cue"]] = diagrams_dir / item["file"]
            except Exception as e:
                print(f"  ⚠️ Could not load manifest.json: {e}")

    diagram_files = sorted(diagrams_dir.glob("diag_*.mp4")) if diagrams_dir and diagrams_dir.exists() else []
    title_card = diagrams_dir / "card_title.mp4" if diagrams_dir and diagrams_dir.exists() else None
    photo_clips = sorted(clips_dir.glob("*_photo.mp4")) if clips_dir.exists() else []
    stock_clips = sorted(clips_dir.glob("*_stock.mp4")) if clips_dir.exists() else []
    all_clips = photo_clips + stock_clips + diagram_files
    if title_card and title_card.exists():
        all_clips.insert(0, title_card)

    print(f"Available assets: {len(diagram_files)} diagrams, {len(photo_clips)} photos, {len(stock_clips)} stock clips.")

    pauses = find_pause_points(voice, min_pause_ms=500)
    cut_points = [0.0] + [p for p in pauses if 0.5 < p < voice_dur - 0.5] + [voice_dur]
    cut_points = sorted(list(set(cut_points)))

    seg_files = []
    clip_pool = all_clips if all_clips else [None]
    pool_idx = 0

    for i in range(len(cut_points) - 1):
        seg_start = cut_points[i]
        seg_end = cut_points[i + 1]
        seg_dur = seg_end - seg_start

        if seg_dur < 0.5:
            continue

        mid_fraction = (seg_start + seg_dur / 2.0) / voice_dur
        chosen_clip = None

        best_cue = min(script_cues, key=lambda c: abs(c[0] - mid_fraction), default=(0, "")) if script_cues else None
        if best_cue and abs(best_cue[0] - mid_fraction) < 0.15:
            cue_text = best_cue[1]
            if cue_text in manifest_map:
                chosen_clip = manifest_map[cue_text]
            else:
                low = cue_text.lower()
                if any(w in low for w in ["map", "cutaway", "hanger", "scale", "sticky", "epoxy", "timeline", "zipper", "ledger", "sustained", "redundant"]):
                    if diagram_files:
                        chosen_clip = diagram_files[pool_idx % len(diagram_files)]
                elif any(w in low for w in ["archival", "photo", "newspaper"]):
                    if photo_clips:
                        chosen_clip = photo_clips[pool_idx % len(photo_clips)]

        if not chosen_clip:
            if clip_pool:
                chosen_clip = clip_pool[pool_idx % len(clip_pool)]
                pool_idx += 1

        seg_file = output.parent / f"_seg_{i:03d}.mp4"
        
        if chosen_clip and chosen_clip.exists():
            clip_dur = get_audio_duration(chosen_clip)
            if clip_dur >= seg_dur:
                cmd = [
                    "ffmpeg", "-y", "-i", str(chosen_clip),
                    "-t", str(seg_dur),
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-an", str(seg_file)
                ]
            else:
                loops = int(seg_dur / clip_dur) + 1
                cmd = [
                    "ffmpeg", "-y", "-stream_loop", str(loops), "-i", str(chosen_clip),
                    "-t", str(seg_dur),
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-an", str(seg_file)
                ]
        else:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=151824:s={width}x{height}:d={seg_dur}:r={fps}",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-an", str(seg_file)
            ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        seg_files.append(seg_file)

    main_concat = output.parent / "_main_concat.mp4"
    list_file = output.parent / "_concat_list.txt"
    with open(list_file, "w") as f:
        for sf in seg_files:
            f.write(f"file '{sf.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy", str(main_concat)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    list_file.unlink(missing_ok=True)

    audio_parts = [str(voice)]
    if music and music.exists():
        music_dur = get_audio_duration(music)
        if music_dur >= voice_dur:
            music_trimmed = output.parent / "_music_trimmed.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(music), "-t", str(voice_dur),
                "-c:a", "copy", str(music_trimmed)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_parts.append(str(music_trimmed))

    if len(audio_parts) == 1:
        final_audio = str(voice)
    else:
        final_audio = output.parent / "_final_audio.aac"
        filter_complex = "[" + ":".join(f"[{i}:a]" for i in range(len(audio_parts))) + f"]amix=inputs={len(audio_parts)}:duration=first[outa]"
        subprocess.run([
            "ffmpeg", "-y",
            *[[item, "-i", item] for item in audio_parts][0::2],
            "-filter_complex", filter_complex,
            "-map", "[outa]", "-c:a", "aac", "-b:a", "192k", str(final_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(main_concat),
        "-i", str(final_audio),
        "-c:v", "copy", "-c:a", "copy",
        str(output)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for tmp in output.parent.glob("_*"):
        tmp.unlink(missing_ok=True)

    print(f"✅ Final video assembled at 1920x1080: {output}")
    return output


def main():
    ap = argparse.ArgumentParser(description="Assemble video in script order at 1080p.")
    ap.add_argument("--script", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--diagrams-dir", default=None)
    ap.add_argument("--music", default=None)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    assemble_video(
        script=Path(args.script),
        voice=Path(args.voice),
        clips_dir=Path(args.clips_dir),
        diagrams_dir=Path(args.diagrams_dir) if args.diagrams_dir else None,
        music=Path(args.music) if args.music else None,
        output=Path(args.output),
    )


if __name__ == "__main__":
    main()

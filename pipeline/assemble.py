"""Step 5: assemble a video from narration, footage, diagrams, and music.

Usage:
  python3 pipeline/assemble.py \
      --script scripts/02-hyatt-regency-walkway-collapse-1981.md \
      --voice output/02-hyatt-regency-walkway-collapse-1981/voice.wav \
      --clips-dir output/02-hyatt-regency-walkway-collapse-1981/clips \
      [--diagrams-dir output/02-hyatt-regency-walkway-collapse-1981/diagrams] \
      [--music output/background.mp3] \
      [--output output/02-hyatt-regency-walkway-collapse-1981/final.mp4]

Uses ffmpeg to combine audio and video tracks. Cuts footage on narration pauses
(where there are long silences in the audio).
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def get_audio_duration(path: Path) -> float:
    """Get duration of an audio/video file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())


def find_pause_points(wav_path: Path, min_pause_ms: int = 300) -> list[float]:
    """Find pause points in audio where we can cut scenes."""
    # Use ffmpeg to detect silence
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


def concat_clips(clips: list[Path], output: Path, target_dur: float = 0) -> Path:
    """Concatenate multiple video clips into one."""
    list_file = output.parent / "_concat_list.txt"
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy", str(output)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    list_file.unlink(missing_ok=True)
    return output


def assemble_video(
    voice: Path,
    clips_dir: Path,
    diagrams_dir: Path | None,
    music: Path | None,
    output: Path,
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
) -> Path:
    """Combine all assets into final video."""

    voice_dur = get_audio_duration(voice)
    print(f"Voiceover duration: {voice_dur:.1f}s")

    # Find pause points for scene cuts
    pauses = find_pause_points(voice, min_pause_ms=400)
    print(f"Found {len(pauses)} pause points")

    # Collect available clips
    mp4_files = sorted(clips_dir.glob("*.mp4")) if clips_dir.exists() else []
    print(f"Available clips: {len(mp4_files)}")

    # Build video segments
    seg_num = 0
    seg_files = []
    clip_idx = 0
    prev_time = 0.0

    for pause_t in pauses[:len(mp4_files) * 2]:  # limit to avoid too many segments
        seg_start = prev_time
        seg_end = min(pause_t, voice_dur)
        seg_dur = seg_end - seg_start

        if seg_dur > 0.5:  # skip very short segments
            seg_file = output.parent / f"_seg_{seg_num:03d}.mp4"
            if clip_idx < len(mp4_files):
                # Use a clip
                clip = mp4_files[clip_idx]
                clip_dur = get_audio_duration(clip)
                # Loop or trim clip to fit segment
                if clip_dur >= seg_dur:
                    cmd = [
                        "ffmpeg", "-y", "-i", str(clip),
                        "-t", str(seg_dur),
                        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-an", str(seg_file)
                    ]
                else:
                    # Loop clip to fill segment
                    loops = int(seg_dur / clip_dur) + 1
                    cmd = [
                        "ffmpeg", "-y", "-stream_loop", str(loops), "-i", str(clip),
                        "-t", str(seg_dur),
                        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-an", str(seg_file)
                    ]
                clip_idx += 1
            else:
                # Create black placeholder
                cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={seg_dur}:r={fps}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-an", str(seg_file)
                ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            seg_files.append(seg_file)
            seg_num += 1

        prev_time = seg_end

    # Concatenate all segments
    if seg_files:
        main_concat = output.parent / "_main_concat.mp4"
        concat_clips(seg_files, main_concat)
        final_video = main_concat
    else:
        # No pauses found, just use a single clip or black
        final_video = output.parent / "_fallback.mp4"
        if mp4_files:
            clip = mp4_files[0]
            subprocess.run([
                "ffmpeg", "-y", "-i", str(clip),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-an", str(final_video)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={voice_dur}:r={fps}",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-an", str(final_video)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Add audio (voiceover ± music)
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

    # Mix audio
    if len(audio_parts) == 1:
        final_audio = str(voice)
    else:
        final_audio = output.parent / "_final_audio.aac"
        filter_complex = "[" + ":".join(f"[{i}:a]" for i in range(len(audio_parts))) + f"]amix=inputs={len(audio_parts)}:duration=first[outa]"
        subprocess.run([
            "ffmpeg", "-y",
            *[[item, "-i", item] for item in audio_parts][0::2] if len(audio_parts) > 1 else [],
            "-filter_complex", filter_complex,
            "-map", "[outa]", "-c:a", "aac", "-b:a", "192k", str(final_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Final assembly
    cmd = [
        "ffmpeg", "-y",
        "-i", str(final_video),
        "-i", str(final_audio),
        "-c:v", "copy", "-c:a", "copy",
        str(output)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cleanup temp files
    for tmp in output.parent.glob("_*"):
        tmp.unlink(missing_ok=True)

    print(f"✅ Final video: {output.relative_to(Path('.').resolve())}")
    return output


def main():
    ap = argparse.ArgumentParser(description="Assemble video from assets.")
    ap.add_argument("--script", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--diagrams-dir", default=None)
    ap.add_argument("--music", default=None)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    voice = Path(args.voice)
    clips_dir = Path(args.clips_dir)
    diagrams_dir = Path(args.diagrams_dir) if args.diagrams_dir else None
    music = Path(args.music) if args.music else None
    output = Path(args.output)

    output.parent.mkdir(parents=True, exist_ok=True)

    assemble_video(
        voice=voice,
        clips_dir=clips_dir,
        diagrams_dir=diagrams_dir,
        music=music,
        output=output,
    )


if __name__ == "__main__":
    main()

"""Step 3: pull Pexels footage clips based on visual cues in a script.

Usage:
  python3 pipeline/footage.py --script scripts/02-hyatt-regency-walkway-collapse-1981.md \
      --api-key $PEXELS_API_KEY [--output-dir output]

Reads [visual cues] from the script (e.g. *[Archival photos: Liberty Memorial]*),
searches Pexels for matching clips, downloads them, and writes credits.txt.

Outputs: output/NN-slug/clips/*.mp4 + output/NN-slug/credits.txt
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import quote
import urllib.request
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))


def extract_cues(script_path: Path) -> list[str]:
    """Extract visual cue text from *[text]* patterns."""
    raw = script_path.read_text()
    return re.findall(r"\*\[(.*?)\]\*", raw)


def search_pexels(query: str, api_key: str, per_page: int = 5) -> list[dict]:
    """Search Pexels video library. Returns list of download URLs."""
    url = f"https://api.pexels.com/videos/search?query={quote(query)}&per_page={per_page}"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        results = []
        for item in data.get("videos", [])[:per_page]:
            # Get the best HD version
            videos = item.get("video_files", [])
            hd = next((v for v in videos if v.get("quality") == "HD"), None)
            sd = next((v for v in videos if v.get("quality") == "SD"), None)
            chosen = hd or sd
            if chosen and "link" in chosen:
                results.append({
                    "url": chosen["link"],
                    "width": chosen.get("width"),
                    "height": chosen.get("height"),
                    "duration": item.get("duration", 0),
                    "user": item.get("user", {}).get("name", "Unknown"),
                })
        return results
    except Exception as e:
        print(f"  ⚠️  Search failed for '{query}': {e}")
        return []


def download_clip(url: str, dest: Path) -> bool:
    """Download a video clip from URL to dest path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FacelessYouTubePipeline/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  ⚠️  Download failed: {e}")
        return False


async def main():
    ap = argparse.ArgumentParser(description="Pull Pexels footage for a script.")
    ap.add_argument("--script", required=True)
    ap.add_argument("--api-key", default=None, help="Pexels API key (or set PEXELS_API_KEY env)")
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    api_key = args.api_key or os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        raise SystemExit("No Pexels API key provided. Get one at pexels.com/api and add to .env")

    script_path = Path(args.script)
    root = Path(__file__).resolve().parent.parent
    out_root = Path(args.output_dir) if args.output_dir else root / "output"

    slug = script_path.stem
    clips_dir = out_root / slug / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    cues = extract_cues(script_path)
    print(f"Found {len(cues)} visual cues in {slug}")

    # Keywords to search for each cue type
    keyword_map = {
        "archival": ["historical", "vintage", "old footage"],
        "photo": ["photography", "camera", "static"],
        "diagram": ["blueprint", "technical drawing", "animation"],
        "dark": ["night", "shadow", "dusk"],
        "city": ["urban", "skyline", "building"],
        "construction": ["construction site", "building", "crane"],
        "metal": ["steel", "metal", "industrial"],
        "water": ["dam", "river", "ocean", "wave"],
        "fire": ["fire", "flame", "explosion"],
        "bridge": ["bridge", "highway", "road"],
        "crowd": ["crowd", "people", "gathering"],
        "ballroom": ["party", "event", "dance"],
        "hospital": ["medical", "doctor", "emergency"],
        "tunnel": ["tunnel", "underground", "subway"],
    }

    all_results = []
    processed = set()

    for cue in cues:
        cue_lower = cue.lower()
        # Skip if it's just a label/caption, not a scene description
        if any(word in cue_lower for word in ["label", "callout", "graphic", "overlay", "text", "title card"]):
            continue

        keywords = []
        for key, vals in keyword_map.items():
            if key in cue_lower:
                keywords.extend(vals[:2])  # max 2 variants per keyword

        if not keywords:
            # Use cue text directly if no mapping matched
            keywords = [cue[:50]]

        for kw in keywords[:3]:  # max 3 searches per cue
            if kw in processed:
                continue
            processed.add(kw)
            print(f"  Searching: {kw}")
            results = await asyncio.to_thread(search_pexels, kw, api_key, per_page=3)
            all_results.extend(results)
            # Small delay to respect API rate limits
            await asyncio.sleep(0.5)

    # Deduplicate by URL
    seen_urls = set()
    unique_clips = []
    for clip in all_results:
        if clip["url"] not in seen_urls:
            seen_urls.add(clip["url"])
            unique_clips.append(clip)

    print(f"\nDownloading {len(unique_clips)} clips...")
    credits = []
    for i, clip in enumerate(unique_clips):
        filename = f"clip_{i+1:03d}.mp4"
        dest = clips_dir / filename
        print(f"  [{i+1}/{len(unique_clips)}] {clip['url'][:60]}...")
        if download_clip(clip["url"], dest):
            credits.append(f"- Clip {i+1}: {clip['user']} via Pexels ({dest.name})")
            print(f"    ✅ Saved: {dest.name} ({clip['width']}x{clip['height']}, {clip['duration']:.1f}s)")

    # Write credits file
    credits_file = out_root / slug / "credits.txt"
    credits_file.write_text("\n".join(credits) + "\n" if credits else "No clips downloaded.\n")
    print(f"\n✅ Done. Credits written to {credits_file.relative_to(root)}")
    print(f"Next: diagrams → assemble")


if __name__ == "__main__":
    import os
    asyncio.run(main())

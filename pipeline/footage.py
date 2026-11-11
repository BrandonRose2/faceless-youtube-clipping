"""Step 3: pull footage for a script from Pixabay (stock video) and Wikimedia Commons (real photos).

Usage:
  python3 pipeline/footage.py --script scripts/01-big-dig-ceiling-collapse.md \
      [--topic "Big Dig tunnel"] [--output-dir output]

Reads *[visual cues]* from the script.
- Archival / photo cues -> real photos from Wikimedia Commons (no key needed).
  Each photo becomes a short slow-zoom .mp4 so assemble.py can use it.
- Scene cues (tunnel, traffic, construction...) -> stock clips from Pixabay.
  Needs PIXABAY_API_KEY in .env (free at pixabay.com/api/docs).
- Diagram, map, label and title cues are skipped; step 4 (diagrams) draws those.

Outputs: output/<slug>/clips/*.mp4 + output/<slug>/credits.txt
Wikimedia photos need the credit lines in credits.txt pasted into the video description.
"""
import argparse
import html
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "FacelessYouTubePipeline/1.0 (https://github.com/BrandonRose2/faceless-youtube-clipping)"

SKIP_WORDS = ["label", "callout", "graphic", "overlay", "text", "title card", "diagram",
              "animated", "animation", "map", "cutaway", "3d", "zoom into", "hard cut",
              "cut to black", "chart", "timeline"]
PHOTO_WORDS = ["archival", "photo", "newspaper", "headline", "news footage"]
STOCK_KEYWORDS = {
    "tunnel": "highway tunnel", "traffic": "traffic", "highway": "highway",
    "construction": "construction site", "crane": "crane", "concrete": "concrete",
    "steel": "steel beams", "bolt": "bolts", "city": "city skyline", "boston": "city skyline",
    "night": "night road", "water": "river", "bridge": "bridge", "crowd": "crowd",
    "ballroom": "ballroom", "hotel": "hotel lobby", "hospital": "ambulance",
    "court": "courthouse", "office": "office", "rain": "rain",
}
STOPWORDS = {"Archival", "Photos", "Photo", "Footage", "Slow", "Close", "Wide", "The", "A", "An", "Of"}


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  ⚠️  Download failed: {e}")
        return False


def extract_cues(script_path: Path) -> list[str]:
    return re.findall(r"\*\[(.*?)\]\*", script_path.read_text())


def default_topic(slug: str) -> str:
    words = re.sub(r"^\d+-", "", slug).split("-")
    generic = {"ceiling", "collapse", "walkway", "failure", "disaster"}
    kept = [w for w in words if w not in generic and not w.isdigit()]
    return " ".join(kept or words)


# ---------- Wikimedia Commons ----------

def search_wikimedia(query: str, limit: int = 4) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1920,
    }
    try:
        data = get_json("https://commons.wikimedia.org/w/api.php?" + urlencode(params))
    except Exception as e:
        print(f"  ⚠️  Wikimedia search failed for '{query}': {e}")
        return []
    out = []
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        if info.get("width", 0) < 800:
            continue
        strip = lambda s: re.sub(r"<[^>]+>", "", html.unescape(s or "")).strip()
        out.append({
            "url": info.get("thumburl") or info.get("url"),
            "title": page.get("title", ""),
            "artist": strip(meta.get("Artist", {}).get("value")) or "Unknown",
            "license": strip(meta.get("LicenseShortName", {}).get("value")) or "see source",
            "source": info.get("descriptionurl", ""),
        })
    return out


def photo_to_clip(img: Path, mp4: Path, seconds: int = 6) -> bool:
    """Turn a still photo into a slow push-in 1920x1080 clip."""
    frames = seconds * 30
    vf = (f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
          f"zoompan=z='min(zoom+0.0007,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s=1920x1080:fps=30,format=yuv420p")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(img), "-vf", vf,
                        "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", str(mp4)])
    return r.returncode == 0


def cue_to_photo_query(cue: str) -> str | None:
    """Proper names in the cue (e.g. 'Boston Central Artery'), or None if it has none.
    The first word of each sentence is ignored, so 'Quiet beat.' or 'Date stamp' never become searches."""
    names = []
    for sentence in re.split(r"[.!?]\s+", cue):
        words = sentence.split()[1:]
        names += [w.strip(".,:;").removesuffix("'s").removesuffix("’s") for w in words if w[:1].isupper()]
    names = [n for n in names if n and n not in STOPWORDS]
    return " ".join(names[:4]) or None


# ---------- Pixabay ----------

def search_pixabay(query: str, key: str, per_page: int = 3) -> list[dict]:
    params = {"key": key, "q": query, "per_page": max(3, per_page), "safesearch": "true"}
    try:
        data = get_json("https://pixabay.com/api/videos/?" + urlencode(params))
    except Exception as e:
        print(f"  ⚠️  Pixabay search failed for '{query}': {e}")
        return []
    out = []
    for hit in data.get("hits", [])[:per_page]:
        vids = hit.get("videos", {})
        chosen = next((vids[s] for s in ("large", "medium", "small") if vids.get(s, {}).get("url")), None)
        if chosen:
            out.append({"url": chosen["url"], "user": hit.get("user", "Unknown"),
                        "source": hit.get("pageURL", ""), "duration": hit.get("duration", 0)})
    return out


def cue_to_stock_query(cue: str) -> str | None:
    low = cue.lower()
    for word, query in STOCK_KEYWORDS.items():
        if word in low:
            return query
    return None


def main():
    ap = argparse.ArgumentParser(description="Pull Pixabay clips and Wikimedia photos for a script.")
    ap.add_argument("--script", required=True)
    ap.add_argument("--topic", default=None, help="Subject for photo searches, e.g. 'Big Dig tunnel'")
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--extra", default="", help="Comma-separated extra Pixabay queries")
    args = ap.parse_args()

    load_env()
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "")

    script_path = Path(args.script)
    slug = script_path.stem
    topic = args.topic or default_topic(slug)
    out_root = Path(args.output_dir) if args.output_dir else ROOT / "output"
    clips_dir = out_root / slug / "clips"
    photos_dir = out_root / slug / "photos"
    clips_dir.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    cues = extract_cues(script_path)
    print(f"Found {len(cues)} visual cues in {slug} (photo topic: '{topic}')")
    if not pixabay_key:
        print("⚠️  No PIXABAY_API_KEY in .env: skipping stock clips, pulling photos only.")

    photo_queries, stock_queries = [topic], []
    for cue in cues:
        low = cue.lower()
        if any(w in low for w in PHOTO_WORDS):
            q = cue_to_photo_query(cue)
            if q:
                photo_queries.append(q)
        elif any(w in low for w in SKIP_WORDS):
            continue
        else:
            q = cue_to_stock_query(cue)
            if q:
                stock_queries.append(q)
    photo_queries = list(dict.fromkeys(photo_queries))
    stock_queries.extend([q.strip() for q in args.extra.split(",") if q.strip()])
    stock_queries = list(dict.fromkeys(stock_queries))

    credits_photos, credits_clips, seen = [], [], set()
    n = 0

    for q in photo_queries:
        print(f"  Wikimedia: {q}")
        for p in search_wikimedia(q, limit=10 if q == topic else 4):
            if p["url"] in seen:
                continue
            seen.add(p["url"])
            n += 1
            img = photos_dir / f"photo_{n:03d}.jpg"
            mp4 = clips_dir / f"clip_{n:03d}_photo.mp4"
            if download(p["url"], img) and photo_to_clip(img, mp4):
                credits_photos.append(f"- {p['title'].removeprefix('File:')} by {p['artist']}, "
                                      f"{p['license']}, via Wikimedia Commons: {p['source']}")
                print(f"    ✅ {mp4.name}")
        time.sleep(0.5)

    if pixabay_key:
        for q in stock_queries:
            print(f"  Pixabay: {q}")
            for c in search_pixabay(q, pixabay_key, per_page=5):
                if c["url"] in seen:
                    continue
                seen.add(c["url"])
                n += 1
                mp4 = clips_dir / f"clip_{n:03d}_stock.mp4"
                if download(c["url"], mp4):
                    if c["duration"] < 4:
                        print(f"    ⚠️  Skipping {mp4.name}: too short ({c['duration']}s)")
                        mp4.unlink(missing_ok=True)
                        continue
                    credits_clips.append(f"- {mp4.name}: {c['user']} via Pixabay {c['source']}")
                    print(f"    ✅ {mp4.name} ({c['duration']}s)")
            time.sleep(0.5)

    credits = ["PHOTOS (paste into the video description; credit is required):", *credits_photos,
               "", "STOCK CLIPS (Pixabay, credit optional):", *credits_clips]
    credits_file = out_root / slug / "credits.txt"
    credits_file.write_text("\n".join(credits) + "\n")
    print(f"\n✅ Done: {len(credits_photos)} photos, {len(credits_clips)} clips. Credits: {credits_file}")
    print("Check every photo actually shows this disaster before using it.")


if __name__ == "__main__":
    main()

"""Step 1: draft a video script through FreeLLMAPI.

Usage:
  python3 pipeline/write_script.py --num 2 --topic "Hyatt Regency walkway collapse, 1981" \
      --angle "One rod change killed 114 people"

Writes scripts/NN-slug.md, marked DRAFT, ending with a "Claims to verify" list for the fact check.
Uses scripts/01-big-dig-ceiling-collapse.md as the style example.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import complete  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "scripts" / "01-big-dig-ceiling-collapse.md"

SYSTEM = (
    "You write narration scripts for a faceless YouTube documentary channel about engineering disasters. "
    "Tone: calm, precise, respectful of victims, no sensationalism. You explain WHY things failed in plain "
    "language a curious non-engineer understands. You never invent facts: if you are unsure of a number, "
    "name or date, say so in the 'Claims to verify' list instead of guessing."
)

PROMPT = """Write a complete script for this video, in exactly the same structure and markdown format as the example.

TOPIC: {topic}
ANGLE / HOOK: {angle}
TARGET: about {minutes} minutes of narration (~{words} words of narration, not counting visual cues).

Requirements:
- Start with "# Video #{num} Script — <short title>", then a "## Title, thumbnail and description" section with 3 title options using the formula: specific detail, then hidden cause, then human cost.
- Timestamped sections ("## 0:00 Cold open", "## 1:00 ...") in this order: cold open, background, how the structure worked, the hidden flaw (explain the engineering simply), the warnings, the day it failed, the investigation, who paid, what engineers learned (3 lessons), and a closing with a tease for the next video.
- Visual cues go on their own line in italics and square brackets, e.g. *[Diagram: ...]*. Prefer diagrams and animations over footage. Never call for footage from other YouTube channels or graphic depictions of death.
- End with "## Production notes" (sources to check, visuals, tone, 3 Shorts ideas), then "## Claims to verify": a numbered list of EVERY specific fact in the script (each number, date, name, quote and cause) with the source you believe supports it. Mark any you are unsure of with (UNSURE).

EXAMPLE SCRIPT (match this format and quality; do not reuse its content):
---
{example}
---
"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--num", type=int, required=True, help="video number, e.g. 2")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--angle", default="")
    ap.add_argument("--minutes", type=int, default=15)
    args = ap.parse_args()

    prompt = PROMPT.format(topic=args.topic, angle=args.angle, minutes=args.minutes,
                           words=args.minutes * 150, num=args.num, example=EXAMPLE.read_text())
    text = complete(prompt, system=SYSTEM, max_tokens=12000).strip()
    if not text:
        raise SystemExit("FreeLLMAPI returned an empty reply. Try again or change FREELLMAPI_MODEL.")

    header = ("> **DRAFT** written by a free model through FreeLLMAPI. "
              "Fact-check every item in \"Claims to verify\" before recording.\n\n")
    out = ROOT / "scripts" / f"{args.num:02d}-{slugify(args.topic)}.md"
    if out.exists():
        raise SystemExit(f"{out.relative_to(ROOT)} already exists; not overwriting it.")
    out.write_text(header + text + "\n")
    n_words = len(re.sub(r"\*\[.*?\]\*", "", text).split())
    print(f"Wrote {out.relative_to(ROOT)} (~{n_words} words). Next: fact-check, then add it to the README table.")


if __name__ == "__main__":
    main()

# Next task: diagrams, more footage, and a real assembly (video #1 Big Dig)

**Written:** 2026-11-11. **Deadline:** Big Dig visuals ready by Sun Nov 15; edit done by Tue Nov 17; video goes live Fri Nov 20.

Read `HANDOFF.md` (rules) and `docs/PIPELINE.md` (steps) first. Then do the three parts below **in order**, one commit and push per part. Test every part on `scripts/01-big-dig-ceiling-collapse.md`.

## Where things stand

- Voiceover is done: `output/01-big-dig-ceiling-collapse/voice.wav` (17:31, Kokoro `bm_george`).
- Footage step works (`pipeline/footage.py`): 11 Wikimedia photos (as slow-zoom clips) + 9 Pixabay clips in `output/01-big-dig-ceiling-collapse/clips/`. That is only ~3 minutes of visuals for 17.5 minutes of narration.
- `pipeline/assemble.py` has three problems: it **ignores `--diagrams-dir`**, it uses clips in **file order, not script order**, and it fills leftover time with **black**. It also renders at 1280x720.
- Keys live in `.env` (`PIXABAY_API_KEY`, `FREELLMAPI_*`). `.env` is gitignored. Never print, log or commit a key.

## Part 1: diagrams (`pipeline/diagrams.py`)

Build one script that renders each diagram cue as a short animated 1920x1080 `.mp4` (30 fps, 6 to 15 s each) into `output/<slug>/diagrams/`, named in script order: `diag_01.mp4`, `diag_02.mp4`, ...

- Start from `tools/render_coldopen_test.py`: it already has `diagram()`, `card()`, `ease()` and font helpers using PIL frames + ffmpeg. Reuse that style (dark background, clean lines, one accent color, big readable labels).
- Pure Python + PIL + ffmpeg. No paid tools, no AI image generation.
- Also write `output/<slug>/diagrams/manifest.json`: a list of `{"file": "diag_01.mp4", "cue": "<exact cue text>"}` in script order.
- Each diagram must be simple and accurate. When unsure of an engineering detail, keep it generic rather than invent specifics.

The Big Dig script's diagram cues (all 12 must be covered):

1. Animated map: the old elevated road fades out; tunnels draw in underneath the city.
2. 3D cutaway of the tunnel near the D Street portal. Label the roof, the hanging ceiling and the space above it. (A clean 2D cross-section is fine.)
3. Zoom into a single hanger: rod, steel bracket, anchor bolt going up into the concrete roof.
4. Graphic: a weight scale. One panel tips heavily.
5. Simple animation: a weight hanging from a sticky label on a wall. Time-lapse clock spins. The label slowly slides.
6. Split screen: two epoxy tubes labeled STANDARD SET and FAST SET.
7. Graphic: a red flag pops up on a timeline at 1999. Seven empty years stretch out to 2006.
8. Animated reconstruction, no graphic detail. Anchors pop out one by one along a line, like a zipper.
9. Title card: "Federal investigation: 12 months." (No NTSB logo.)
10. Simple animated ledger. Amounts tick up as each is named. (Take the amounts from the script text.)
11. Clean diagram: a sustained load arrow pointing down on a bolt, labeled "Load that never goes away."
12. Diagram: overhead load carried by redundant hangers. If one fails, the others share the weight.

Also handle the script's title card cue ("THE GLUE THAT KILLED — The Big Dig Ceiling Collapse") with `card()`.

**Done when:** `python3 pipeline/diagrams.py --script scripts/01-big-dig-ceiling-collapse.md` produces all files plus `manifest.json`, and a frame grab from each looks clean (text readable, nothing cut off).

## Part 2: more footage (`pipeline/footage.py`)

Goal: at least 8 minutes of distinct photos + clips for Big Dig, so assembly rarely repeats.

- Add a `--extra` option: comma-separated extra Pixabay queries, e.g. `--extra "boston traffic,tunnel lights,city at night,courtroom,news camera,hard hat worker,glue tube,clock"`.
- Raise Pixabay results to up to 5 per query and skip clips shorter than 4 s.
- Keep the credits format in `credits.txt` exactly as it is (PHOTOS section needs credit; STOCK section optional).
- Keep the Wikimedia search as is. Every photo must show this disaster or Boston's highways; never add unrelated images.

**Done when:** a rerun gives 8+ minutes total (sum durations with ffprobe and print the total).

## Part 3: assembly in script order (`pipeline/assemble.py`)

- Render at **1920x1080**.
- Walk the script's cues in order. For each cue, pick the matching visual: a diagram from `manifest.json` for diagram cues, a Wikimedia photo clip for archival/photo cues, a Pixabay clip for scene cues. Spread them over the narration in the same order the cues appear (the cue's position in the script text, as a fraction of total words, gives a good estimate of when it is spoken).
- Never show black. If a gap needs filling, reuse a relevant clip (not the one just shown).
- Keep the existing pause-point cutting, music option, and output path behavior.

**Done when:** `python3 pipeline/assemble.py --script scripts/01-big-dig-ceiling-collapse.md --voice output/01-big-dig-ceiling-collapse/voice.wav --clips-dir output/01-big-dig-ceiling-collapse/clips --diagrams-dir output/01-big-dig-ceiling-collapse/diagrams --output output/01-big-dig-ceiling-collapse/draft.mp4` makes a 17:31 1080p video with no black stretches, and diagrams appear near the lines that describe them.

## Rules (short version)

- `git pull` before editing. Put your chat name in the Status cell of the step in `docs/PIPELINE.md` and push before starting.
- Media files (`.mp4`, `.wav`, `.jpg`) never go in the repo; `output/` is gitignored. When a part is done, copy results to Brandon's iCloud folder: `~/Library/Mobile Documents/com~apple~CloudDocs/Faceless Youtube - Claude w: VidIQ/01 Big Dig/` (`footage/` for clips and diagrams, `renders/` for `draft.mp4`).
- Small commits with clear messages. Update `docs/PIPELINE.md` status when a part is done.
- Don't delete Brandon's files. Ask before anything you can't undo.
- When finished, tell Brandon: what was built, the draft video path, and anything that looked wrong.

# Automated video pipeline

Goal: each Friday's video is produced with free tools, so Brandon only reviews and publishes. It feeds the deadlines in `plan/schedule.json`.

## Where it runs
On **Brandon's Mac**, on a schedule (`launchd`). It has to run there because FreeLLMAPI only listens on `localhost:31415`, and the free voice engine runs locally too.

## Steps

```
next video in plan/schedule.json
   │
   ▼
1. write_script.py ── FreeLLMAPI ──► scripts/NN-slug.md   (DRAFT + "Claims to verify")
   │                                  └─ fact check by a Claude chat or Brandon
   ▼
2. voice.py ── Kokoro (local, free) ──► output/slug/voice.wav
3. footage.py ── Pexels API (free) ──► output/slug/clips/ + credits.txt
4. diagrams ── code templates (free) ──► output/slug/diagrams/
   │
   ▼
5. assemble.py ── ffmpeg (free) ──► output/slug/final.mp4
   │
   ▼
6. upload.py ── YouTube Data API (free) ──► uploaded as PRIVATE, then Brandon is notified
   │
   ▼
Brandon watches it and schedules or publishes it
```

## Build status

| Step | File | Status |
|---|---|---|
| 1. Script draft | `pipeline/write_script.py` + `pipeline/llm.py` | Built; first live run on the Mac pending |
| 2. Voice | `pipeline/voice.py` | To build: Kokoro on the Mac, 1–2 documentary voices for Brandon to choose from |
| 3. Footage | `pipeline/footage.py` | To build: reads `[visual cues]`, pulls Pexels clips, writes photographer credits |
| 4. Diagrams | templates | To build: anchor/bolt, bridge, dam, pressure vessel. Start from `tools/render_coldopen_test.py` |
| 5. Assembly | `pipeline/assemble.py` | Prototype in `tools/render_coldopen_test.py` (cuts on narration pauses) |
| 6. Upload | `pipeline/upload.py` | To build: needs a Google Cloud OAuth client from Brandon; always uploads as private |
| Scheduler | `launchd` job | To build: runs the steps for the next video in `plan/schedule.json` |

Helpers: claim a step by putting your chat's name in its Status cell and pushing before you start.

## Run step 1 on the Mac

```bash
git clone https://github.com/BrandonRose2/faceless-youtube-clipping
cd faceless-youtube-clipping
cp .env.example .env        # paste your FreeLLMAPI key into .env (never commit it)
python3 pipeline/write_script.py --num 2 --topic "Hyatt Regency walkway collapse, 1981" --angle "One rod change killed 114 people"
```

FreeLLMAPI must be open. Step 1 uses only Python's standard library, so there's nothing to install.

## Rules for this pipeline
- A free-model script is a **draft** until every item in its "Claims to verify" list is checked against a source.
- Use only our own diagrams, free stock footage (credit the photographer), and public-domain or licensed images. Never reuse other channels' videos.
- Every upload is **private**. Brandon publishes.
- Prompts sent through FreeLLMAPI are visible to the free providers behind it. Send nothing private.
- Rendered media goes in `output/` (gitignored), not in the repo.

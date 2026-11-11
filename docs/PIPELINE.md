# Automated video pipeline

Goal: each Friday's video is produced with free tools, so Brandon only reviews and publishes. It feeds the deadlines in `plan/schedule.json`.

## Where it runs
On **Brandon's Mac**, on a schedule (`launchd`). It has to run there because FreeLLMAPI only listens on `localhost:31415`, and the free voice engine runs locally too.

**Voice engine:** Kokoro (local, free TTS). Installed in `.venv` — activate with `source .venv/bin/activate` then run pipeline scripts. Model downloaded automatically (~150 MB on first run). Voices: `af_heart`, `am_michael`, `bf_emma`, `bm_george`, etc. Edge-tts fallback also available if needed.

## Steps

```
next video in plan/schedule.json
   │
   ▼
1. write_script.py ── FreeLLMAPI ──► scripts/NN-slug.md   (DRAFT + "Claims to verify")
   │                                  └─ fact check by a Claude chat or Brandon
   ▼
2. voice.py ── edge-tts (Microsoft Azure Neural, free, no API key) ──► output/slug/voice.wav
3. footage.py ── Wikimedia photos + Pixabay clips (free) ──► output/slug/clips/ + credits.txt
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
| 1. Script draft | `pipeline/write_script.py` + `pipeline/llm.py` | ✅ Built; live run completed (see `scripts/02-hyatt-regency-walkway-collapse-1981.md`) |
| 2. Voice | `pipeline/voice.py` | ✅ Built — uses Kokoro (local, free). Default voice `bm_george`; accent follows the voice prefix (`a` American, `b` British). Full output: `output/<slug>/voice.wav`; copy to the iCloud video folder |
| 3. Footage | `pipeline/footage.py` | ✅ Built — updated for --extra queries, 5 results/query, 4s min duration. (Codex) |
| 4. Diagrams | `pipeline/diagrams.py` | ✅ Built (Codex) — renders 1920x1080 animated diagram clips + manifest.json. Needs visual polish (sizes, label overlap) |
| 5. Assembly | `pipeline/assemble.py` | ✅ Built — 1920x1080, places diagrams/photos/clips in script-cue order, no black gaps; voice + optional music. Audio is PCM (convert to AAC before upload) |
| 6. Upload | `pipeline/upload.py` | ❌ To build: needs Google Cloud OAuth client from Brandon |
| Scheduler | `launchd` job | ❌ To build |

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

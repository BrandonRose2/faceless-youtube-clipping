# Automated video pipeline

Goal: each Friday's video is produced with free tools, so Brandon only reviews and publishes. It feeds the deadlines in `plan/schedule.json`.

## Where it runs
On **Brandon's Mac**, on a schedule (`launchd`). It has to run there because FreeLLMAPI only listens on `localhost:31415`, and the free voice engine runs locally too.

**Voice engine:** edge-tts (Microsoft Azure Neural voices). Installed via `pip3 install --break-system-packages edge-tts`. No API key needed. Choose a voice from the list at `docs/PIPELINE.md` or run `python3 -c "import asyncio, edge_tts; asyncio.run(edge_tts.list_voices())"`.

## Steps

```
next video in plan/schedule.json
   │
   ▼
1. write_script.py ── FreeLLMAPI ──► scripts/NN-slug.md   (DRAFT + "Claims to verify")
   │                                  └─ fact check by a Claude chat or Brandon
   ▼
2. voice.py ── edge-tts (Microsoft Azure Neural, free, no API key) ──► output/slug/voice.wav
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
| 1. Script draft | `pipeline/write_script.py` + `pipeline/llm.py` | ✅ Built; live run completed (see `scripts/02-hyatt-regency-walkway-collapse-1981.md`) |
| 2. Voice | `pipeline/voice.py` | ✅ Built — uses edge-tts (Microsoft Azure Neural voices). No API key needed. Samples at `output/en-*-Neural.mp3`. Full output: `output/<slug>/voice.wav` |
| 3. Footage | `pipeline/footage.py` | ⚠️  Built but needs PEXELS_API_KEY (free at pexels.com/api) |
| 4. Diagrams | `pipeline/diagrams/*.py` | ❌ To build — use `tools/render_coldopen_test.py` as starting template |
| 5. Assembly | `pipeline/assemble.py` | ✅ Built — combines voice + clips + music via ffmpeg |
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

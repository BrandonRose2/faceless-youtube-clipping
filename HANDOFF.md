# Handoff: working on this channel with Brandon

Read this first if you are a Claude chat (or any helper) joining this project. This repo is the shared source of truth. Brandon guides the work; every helper reads from and writes to this repo.

## The project

A faceless YouTube channel about **engineering disasters**. One video goes live **every Friday, starting Fri, Nov 20, 2026**. The niche research, keywords and first 10 topics come from vidIQ (see `plan/`).

## What is where

| Path | What it is |
|---|---|
| `plan/schedule.json` | **The schedule.** Every deadline. Brandon's Life Planner reads this file live. |
| `plan/SCHEDULE.md` | Readable copy of the schedule, week by week. |
| `plan/Engineering_Disasters_Channel_Plan.xlsx` | Niches, lanes, keywords, first 10 videos, breakout videos to study. |
| `scripts/` | One narration script per video, e.g. `01-big-dig-ceiling-collapse.md`. |
| `tools/` | Helper scripts (workbook builder, cold-open test render). |
| `pipeline/` | Automated video pipeline code (runs on Brandon's Mac through FreeLLMAPI). |
| `docs/PIPELINE.md` | How the pipeline works, its build status, and how to run it. |
| `.env.example` | Names of the keys the pipeline needs. Real keys go in `.env`, which is gitignored. |

## Current state (verified 2026-11-21)

**Today is Nov 21, 2026.** Video #1 was targeted to go live Fri Nov 20. The automatic draft was rejected; the video is being rebuilt section by section to match cold-open quality. See `docs/NEXT-TASK.md` for the full rebuild plan (steps 1–14).

### What is actually done

- ✅ **#1 Big Dig script** — `scripts/01-big-dig-ceiling-collapse.md` (~15 min narration, 10 timed sections)
- ✅ **#1 Big Dig voiceover** — full `voice.wav` (48 MB) + **all 10 sections** split with timings (`output/01-big-dig-ceiling-collapse/sections/*/timing.json` + `vo.wav`). Voice is Kokoro `bm_george`. **Step 1 of NEXT-TASK is complete.**
- ✅ **#1 Big Dig footage** — 40 clips + 16 diagrams + `credits.txt` in `output/01-big-dig-ceiling-collapse/`. Approved assets in `clips/`, rejected in `clips_rejected/`.
- ✅ **#1 Big Dig sound & toolkit** — `pipeline/sound.py` sound library (procedural beds, hits, cracks, risers, ticks) and `pipeline/scene_kit.py` scene renderer built and verified. **Steps 2 & 3 of NEXT-TASK are complete.**
- 🟡 **#1 Big Dig per-section renders (Steps 4–13)** — **Sections 1–8 rendered**:
  - Step 4: Section 1 Cold Open (`pipeline/scenes/s01_cold_open.py`)
  - Step 5: Section 2 The Big Dig (`pipeline/scenes/s02_the_big_dig.py`)
  - Step 6: Section 3 How the ceiling was held up (`pipeline/scenes/s03_how_held_up.py`)
  - Step 7: Section 4 Creep (`pipeline/scenes/s04_creep.py`)
  - Step 8: Section 5 The warning in 1999 (`pipeline/scenes/s05_warning_1999.py`)
  - Step 9: Section 6 July 10, 2006 (`pipeline/scenes/s06_july_10_2006.py`)
  - Step 10: Section 7 The investigation (`pipeline/scenes/s07_investigation.py`)
  - Step 11: Section 8 Who paid (`pipeline/scenes/s08_who_paid.py`)
  - Remaining: Section 9 What engineers learned (Step 12), Section 10 Closing (Step 13).
- ❌ **#1 Big Dig final build (Step 14)** — `pipeline/build_video.py` built, awaiting rendering of remaining sections 9 and 10 to combine all 10 into final output.
- ✅ **#2 Hyatt Regency script** — `scripts/02-hyatt-regency-walkway-collapse-1981.md` (~19 KB)
- ✅ **#2 Hyatt Regency voiceover** — `output/02-hyatt-regency-walkway-collapse-1981/voice.wav` (61 MB)
- ✅ **Pipeline steps 1–5 built** — `write_script.py`, `voice.py` (Kokoro), `footage.py` (Wikimedia + Pixabay), `diagrams.py`, `assemble.py`
- ❌ **Step 6 (upload)** — not built; needs Google Cloud OAuth client from Brandon
- ❌ **Scheduler (launchd)** — not built
- ❌ **Channel art** — not created; channel name/method/voice choice never formally recorded (work built using Kokoro `bm_george`, Wikimedia+Pixabay footage)

### The gap

`plan/schedule.json` still describes the **old pipeline timeline** (script → voice → visuals → edit → upload). It does not contain the actual remaining work: the per-section rebuild (NEXT-TASK steps 4–14). It also shows four setup milestones (channel name, method, voice, art) as overdue even though the equivalent work was done. **The schedule needs to be rewritten to match how the work is actually being done** — Brandon decides those dates; propose changes before pushing.

## How the schedule drives Brandon's planner

Brandon's private Life Planner has a project page for this channel. It reads `plan/schedule.json` from this repo (`main` branch) and uses it for:

- **Traffic light** on the project button: flashing **red** if a deadline has passed, **orange** if one is due today or tomorrow, **green** if on track.
- **Planner calendar**, plus his **Apple Calendar on Mac and iPhone**: each deadline shows at 9am on its day. Alerts fire at 6pm the evening before and at 9am on the day.

Changes pushed to `main` show up in the planner within about 15 minutes.

## schedule.json format

```json
{
  "milestones": [
    { "id": "v1-script", "video": 1, "title": "#1 Big Dig: Script finished", "due": "2026-11-10", "doneWhen": "Voiceover" },
    { "id": "setup-art", "video": null, "title": "Channel art: logo and banner", "due": "2026-11-13", "doneWhen": null }
  ]
}
```

| Field | Rule |
|---|---|
| `id` | Unique and **never changed** once set. Brandon's ticks are stored by id. |
| `video` | The video number (1, 2, 3…), or `null` for one-off tasks. |
| `title` | What must be done. Start video items with `#N Short name:`. |
| `due` | `YYYY-MM-DD`. |
| `doneWhen` | The video status that marks it done (see below), or `null` if Brandon ticks it by hand. |

Video statuses, in order: `Not started`, `Researching`, `Scripting`, `Voiceover`, `Visuals`, `Editing`, `Title & thumbnail`, `Scheduled`, `Published`. A milestone with `doneWhen: "Editing"` counts as done once that video's status is `Editing` or later.

Per-video deadlines, counted back from its Friday: script −10 days, voiceover −8, visuals −5, edit −3, title, thumbnail and upload scheduled −2, live on the Friday.

## Rules for helpers

1. **Pull before you edit.** Another chat may have changed things.
2. **Keep the JSON valid.** A broken file means the planner keeps using its last good copy.
3. **Move a date by editing `due`.** Never rename an `id`. To add a deadline, add a new item with a new id.
4. **Update `plan/SCHEDULE.md`** in the same commit, so the readable copy matches.
5. **New script?** Save it as `scripts/NN-short-name.md` and mention it in the README pipeline table.
6. **Small commits with clear messages**, e.g. "Move video 3 voiceover to Nov 24".
7. **This repo is public.** Never commit passwords, API keys, or private links.
8. **Brandon decides.** Propose schedule changes to him before pushing them.
9. **Video and audio files never go in the repo.** They live in Brandon's iCloud Drive folder for this project, one subfolder per video (e.g. `01 Big Dig/` with `voiceover/`, `footage/`, `renders/`, `final/`), plus `Channel art/`. Ask Brandon to connect that folder to your chat if you need to read or save media.

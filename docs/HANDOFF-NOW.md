# Handoff: faceless-youtube-clipping — Brandon's Engineering Disasters Channel

**Repo:** https://github.com/BrandonRose2/faceless-youtube-clipping  
**Working copy:** `/Users/brandonrose/faceless-youtube-clipping`  
**Date written:** 2026-11-10  

Read `HANDOFF.md` before anything else — it contains all the rules Brandon expects helpers to follow. This file adds the current state and where work can pick up.

---

## Project in one line

Faceless YouTube channel about **engineering disasters**. One video goes live every Friday, starting **Fri Nov 20, 2026**. Niche research, keywords and the first 10 topics came from vidIQ.

---

## What today looks like against the plan

**Today is Nov 10.** In the schedule that is:
- ✅ **#1 Big Dig: Script finished** — due today (it exists at `scripts/01-big-dig-ceiling-collapse.md`, ~2200 words)
- ✅ **#2 Hyatt Regency: Script finished** — drafted via FreeLLMAPI (~2937 words, ~21:23 narration)
- 🔴 **Video #1 Voiceover recorded** — due Thu Nov 12 (2 days away)
- ✅ **Pipeline step 2 (voice)** — built and tested with edge-tts; full voiceover for #2 generated at `output/02-hyatt-regency-walkway-collapse-1981/voice.wav`

Steps 1, 2, and 5 are built and functional. Steps 3 (footage — needs PEXELS_API_KEY), 4 (diagrams), and 6 (upload — needs Google OAuth) still need work, as does the launchd scheduler.

---

## Current file inventory (what actually exists)

| Path | Status |
|---|---|
| `plan/schedule.json` + `plan/SCHEDULE.md` | ✅ Maintained by Brandon's Life Planner; edit dates here, update both files together |
| `plan/Engineering_Disasters_Channel_Plan.xlsx` | ✅ Master workbook (5 tabs: Top 20 Niches, Lane Comparison, Keywords, First 10 Videos tracker, Breakout References). Built with `tools/combine.py` |
| `scripts/01-big-dig-ceiling-collapse.md` | ✅ Full ~15-min narration script with visual cues; also used as the style example for step 1 |
| `pipeline/write_script.py` + `pipeline/llm.py` | ✅ Step 1 — drafts scripts through FreeLLMAPI (runs on Brandon's Mac, uses localhost:31415) |
| `pipeline/voice.py` | ❌ To build — uses Kokoro (local, free) for documentary-style voices |
| `pipeline/footage.py` | ❌ To build — reads `[visual cues]` from scripts, pulls Pexels clips, writes photographer credits |
| `pipeline/diagrams/*` (templates) | ❌ To build — anchor/bolt, bridge, dam, pressure vessel diagrams; start from `tools/render_coldopen_test.py` |
| `pipeline/assemble.py` | ❌ To build — prototype lives inside `tools/render_coldopen_test.py` (cuts on narration pauses with ffmpeg) |
| `pipeline/upload.py` | ❌ To build — needs Google Cloud OAuth client from Brandon; always uploads private |
| `launchd` job | ❌ To build — runs the next-video pipeline on schedule |
| `.env` | ⚠️ Exists and gitignored (good). Contains real keys — never commit it |

README table lists videos #1–#10; only #1 has a script drafted.

---

## How to run what exists

```bash
cd /Users/brandonrose/faceless-youtube-clipping
git pull                # ALWAYS before editing (plan rule #1)
python3 pipeline/write_script.py \
    --num 2 \
    --topic "Hyatt Regency walkway collapse, 1981" \
    --angle "One rod change killed 114 people"
```

Step 1 uses only Python standard library — nothing to install. FreeLLMAPI must be running on localhost:31415.

Output lands at `scripts/02-hyatt-regency-walkway-collapse.md` marked **DRAFT** with a "Claims to verify" list. A Claude chat or Brandon fact-checks every claim before recording.

---

## Pipeline build order recommendations

If the next helper wants to unblock the schedule, these are the practical priorities:

1. **Step 2 (voice)** — Kokoro on the Mac. Two documentary voices for Brandon to choose from. Without this, no video after script can ship.
2. **Step 5 (assemble)** — The cold-open test (`tools/render_coldopen_test.py`) already proves the concept: PIL diagram animation + ffmpeg concat + overlay text cards. Generalize it into `pipeline/assemble.py`.
3. **Step 3 (footage)** — Reads `[visual cues]`, hits Pexels API, saves clips + `credits.txt`.
4. **Step 4 (diagrams)** — Template-driven SVG/PIL drawings for common disaster types.
5. **Step 6 (upload)** — Needs a Google Cloud OAuth client from Brandon. Always private upload.
6. **launchd scheduler** — Runs the full chain for whichever video is next in `schedule.json`.

Helpers should claim a step by writing their name into its Status cell in `docs/PIPELINE.md` and pushing before they start.

---

## Rules that matter most (re-stated from HANDOFF.md)

1. **Pull before you edit.** Another chat may have changed `main`.
2. **Keep `schedule.json` valid JSON.** A broken file breaks the planner.
3. **Move dates by editing `due` only. Never rename an `id`.** Brandon's ticks are stored by id.
4. **Update `plan/SCHEDULE.md` in the same commit** as any `schedule.json` edit.
5. **New script → `scripts/NN-short-name.md` + README pipeline table row.**
6. **Small commits with clear messages.** Example: `"Move video 3 voiceover to Nov 24"`.
7. **This repo is public.** Never commit secrets (`.env` is already gitignored — keep it that way).
8. **Brandon decides.** Propose schedule changes to him before pushing.
9. **Media files live in iCloud Drive**, one subfolder per video (`01 Big Dig/voiceover/`, `renders/`, etc.). Ask Brandon to connect that folder if a helper needs media.

---

## Suggested skills for the next agent

| Skill | When to use it |
|---|---|
| `/handoff` | Anytime another helper joins mid-project |
| `/careful` | Before touching `plan/schedule.json` or pushing |
| `/review` | After drafting a new script or pipeline step |
| `/ship` | Ready to land a complete pipeline step to main |
| `/learn` | If the next helper needs to understand Kokoro, ffmpeg pipelines, or YouTube Data API OAuth |

---

## Open questions / things Brandon should confirm

- Is the FreeLLMAPI instance running and reachable on localhost:31415 right now?
- Has Brandon chosen a channel name and created the YouTube channel yet? (Due Wed Nov 11.)
- Has he picked the narration voice (AI vs. his own)? (Due Thu Nov 12.)
- Does he want to proceed with the pipeline build order above, or shift priorities?

---

*Written by the current Claude session. Repo was clean on `main` with zero uncommitted changes.*

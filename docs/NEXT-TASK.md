# Next task: rebuild video #1 (Big Dig) section by section, cold-open quality

**Written:** 2026-11-11. **Goal:** the full 17.5-minute video at the quality of the cold open. **Video goes live Fri Nov 20; final cut needed by Tue Nov 17.**

The automatic draft (`pipeline/assemble.py`) was rejected: random footage, irrelevant photos, no music, no sound effects. The cold open (`tools/render_coldopen_test.py`, result in iCloud `01 Big Dig/renders/coldopen_test.mp4`) is the quality bar. It works because every shot is chosen by hand for what the narrator is saying at that moment, cuts land on narration pauses, and there is a sound bed (low drone) plus sound effects (the crack).

We rebuild the video that way: **one script section at a time, each hand-directed.**

## How to work (read this, the models doing this are on a free tier)

- **One step per Codex session.** Do the step, check it, commit and push, then stop and report. Don't start the next step.
- **Small edits.** Never rewrite a whole existing file in one reply. New files: write them in parts if they are long.
- Read `HANDOFF.md` rules first. Use `.venv/bin/python` (has Kokoro, numpy, Pillow). Media never goes in the repo; `output/` is gitignored.
- Mark the step you're on in the table at the bottom (`🟡 <your name>`) and push before starting; mark `✅` when done.

## Footage rules (the main thing that went wrong)

1. **Every shot must show what the narrator is talking about right then.** If nothing fits, use a diagram, a title/text card, or a slow push-in on a relevant real photo. Never a random clip.
2. Priority: real photos of the Big Dig / Boston (Wikimedia) > our diagrams > text cards > stock video. Stock video only for generic shots that truly match (night traffic in a tunnel, a courtroom gavel, a news camera), at most ~20% of a section.
3. Never use: animations/neon/cartoons, beaches, nature, non-Boston cities shown as Boston, anything in `plan/footage_blocklist.txt`.
4. Shots 3–7 s each, cut on narration pauses. No shot repeats within a section.
5. Look at a frame of every clip/photo before using it (`ffmpeg -ss 1 -i clip.mp4 -frames:v 1 check.jpg`). Approved assets are in `output/01-big-dig-ceiling-collapse/clips/` (rejected ones moved to `clips_rejected/`) and `diagrams/`.

## Sound rules

- Every section has a **music bed** under the voice, ducked so the voice stays clear (bed around -24 dB, voice around -16 dB; final mix normalized to -14 LUFS).
- Music: if Brandon has put tracks in iCloud `Faceless Youtube - Claude w: VidIQ/Music/` (YouTube Audio Library, safe for monetization), use those. Otherwise use the procedural beds from `pipeline/sound.py`.
- **Sound effects** on key moments: whooshes on transitions, a low hit on big facts and numbers, a crack/rumble for the collapse, clock ticks for "creep over time", a typewriter tick for text cards, a riser before reveals. Keep them subtle.

## Steps

### Step 1. Per-section voiceover with timings (`pipeline/sections.py`)
Split `scripts/01-big-dig-ceiling-collapse.md` into its 10 timed sections (the `## 0:00 Cold open` … `## 13:45 Closing` headings; skip "Title, thumbnail…" and "Production notes"). For each section, generate voice with Kokoro `bm_george` **one paragraph at a time** (reuse the narration-cleaning in `pipeline/voice.py`), join with 0.35 s gaps, and write to `output/<slug>/sections/NN-name/`:
- `vo.wav`
- `timing.json`: `{"paragraphs": [{"start": 0.0, "end": 7.4, "text": "..."}], "cues": [{"at": 7.4, "cue": "<visual cue text>"}]}`. A cue's `at` = start of the paragraph that follows it.
Done when all 10 folders exist and the sum of section lengths is ~17–18 min.

### Step 2. Sound library (`pipeline/sound.py`)
numpy-only generators, each returning a mono 44.1 kHz float array, plus a `write_wav()` helper: `drone(seconds, mood)` (moods: tense, somber, neutral; reuse `audio_bed()` from the cold-open script as the starting point), `hit()`, `crack()`, `whoosh()`, `riser(seconds)`, `tick()`, `typewriter_tick()`. Write a 20 s demo `output/sound_demo.wav` with each effect, spaced out. Done when the demo plays cleanly with no clipping.

### Step 3. Scene toolkit (`pipeline/scene_kit.py`)
Reusable helpers modeled on `tools/render_coldopen_test.py`: `shot(src, start, dur, speed=1.0, grade=None)` (trim, scale/crop to 1920x1080, optional slow-mo and color grade), `kenburns(photo, dur, direction)`, `text_card(lines, dur)`, `lower_third(text)`, `concat(shots)`, and `mix(vo, bed, sfx_list, out)` (sfx_list = `[(time, wav)]`; ducks the bed under the voice; normalizes to -14 LUFS with ffmpeg `loudnorm`). Done when a 15 s test scene renders with a photo push-in, a text card, a stock shot, a bed and two effects.

### Steps 4–13. One section per step (`pipeline/scenes/sNN_<name>.py`)
For each section in order: read its `timing.json`, then **write a shot list as a comment at the top of the file first** (time range → visual → why it matches the narration → sound effect). Then render it with `scene_kit` to `output/<slug>/sections/NN-name/section.mp4`. Grab a frame every 10 s into `sections/NN-name/check/` and look at every frame against the footage rules before committing. One section per step:
4 = 0:00 Cold open (port `tools/render_coldopen_test.py`; keep its look), 5 = 1:00 The Big Dig, 6 = 2:30 How the ceiling was held up, 7 = 4:00 Creep, 8 = 6:00 The warning in 1999, 9 = 7:45 July 10, 2006 (keep it respectful: no graphic depiction, no victim imagery), 10 = 9:00 The investigation, 11 = 10:45 Who paid, 12 = 12:00 What engineers learned, 13 = 13:45 Closing.

### Step 14. Final build (`pipeline/build_video.py`)
Join all `section.mp4` files with a short crossfade, check total length matches the voiceover, render `output/<slug>/final.mp4` (1080p, H.264, AAC 192k, -14 LUFS, `+faststart`). Copy it to iCloud `01 Big Dig/renders/final_v1.mp4` if your sandbox allows; otherwise tell Brandon it's ready to copy.

## Status

| Step | Status |
|---|---|
| 1. Per-section voiceover + timings | ⬜ |
| 2. Sound library | ⬜ |
| 3. Scene toolkit | ⬜ |
| 4. Cold open | ⬜ |
| 5. The Big Dig | ⬜ |
| 6. How the ceiling was held up | ⬜ |
| 7. Creep | ⬜ |
| 8. The warning in 1999 | ⬜ |
| 9. July 10, 2006 | ⬜ |
| 10. The investigation | ⬜ |
| 11. Who paid | ⬜ |
| 12. What engineers learned | ⬜ |
| 13. Closing | ⬜ |
| 14. Final build | ⬜ |

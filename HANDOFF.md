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

## How the schedule drives Brandon's planner

Brandon's private Life Planner has a project page for this channel. It reads `plan/schedule.json` from this repo (`main` branch) and uses it for:

- **Traffic light** on the project button: flashing **red** if a deadline has passed, **orange** if one is due within 2 days, **green** if on track.
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

import sys, copy
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

src, out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src)

NAVY = "1F2A44"
title_font = Font(name="Arial", size=14, bold=True, color=NAVY)
note_font = Font(name="Arial", size=9, color="555555")
head_font = Font(name="Arial", bold=True, color="FFFFFF")
head_fill = PatternFill("solid", fgColor=NAVY)
body_font = Font(name="Arial", size=10)
yellow = PatternFill("solid", fgColor="FFF2CC")
wrap = Alignment(vertical="top", wrap_text=True)

# 1) First 10 Videos: add a fill-in Views column (H), matching the yellow input columns
v = wb["First 10 Videos"]
v["H4"].value = "Views"
v["H4"]._style = copy.copy(v["G4"]._style)
for r in range(5, 15):
    v.cell(r, 8)._style = copy.copy(v.cell(r, 6)._style)
v.column_dimensions["H"].width = 12
v["A2"].value = ("Yellow columns are yours to fill in (Status, Publish date, Notes, Views). "
                 "Target 15-35 min. Title formula: specific detail + hidden cause + human cost.")

# 2) New Top 20 Niches tab, styled like the others
n = [
    ("Kitchen hacks / budget cooking", "inventor Kitchen: 31.6K subs, ~$33.6K/mo, 149K avg views", "Evergreen, high ad rates, lots of search traffic"),
    ("DIY / home repair / upcycling", "Inventor Master ~$18.2K/mo; Creative DIY Tips ~$16.3K/mo", "Ideas never run out; home-improvement ads pay well"),
    ("Woodworking tips", "Top Wood Tips: 16.2K subs, ~$15.8K/mo", "Hobby buyers who click affiliate tool links"),
    ("Extreme weather / disasters explained", "Disasters Explained: 28.8K subs, ~$21.4K/mo", "New news events keep feeding the topic"),
    ("WW2 / military history documentaries", "Events Untold: 404K avg views; WW2 Exposed views up 460% in 30 days", "Older viewers who watch long videos to the end"),
    ("Ancient history / human origins", "The Helix Report: 18.2K subs, ~$12.5K/mo, 31-min videos", "Long watch time, little competition"),
    ("History ASMR / sleep stories", "Istorium: views up 392% in 30 days", "Nightly rewatching, very long sessions"),
    ("Police bodycam analysis", "Patrol Pro: 21.2K subs, 533K avg views, ~$18.9K/mo", "New public footage keeps coming"),
    ("Dashcam / road incidents", "DashCam Files: 168K subs, 1.39M avg views", "Endless supply of viewer submissions"),
    ("Narrated moral / inspirational stories", "Seeds of Hope: 35K subs, 483K avg views, ~$13K/mo", "Story script plus voiceover is easy to scale"),
    ("Manhwa / webnovel recaps", "Comeback King Studios: 95K subs, ~$16.4K/mo, 105-min videos", "Huge watch time from loyal fans"),
    ("Movie recaps & explainers", "Go Movie ~$16.9K/mo; Ultimate Movie Recap ~$12K/mo", "Strong demand (needs real commentary to avoid copyright claims)"),
    ("Original AI sci-fi / dark fantasy films", "Cine Drop: 151K subs, 1.96M avg views, ~$28.3K/mo", "Fast-growing new format (has to be original, not mass-produced)"),
    ("Engineering / how things work (YOUR PICK)", "CAD COMPANY: 1.75M avg views, ~$20.6K/mo; ENGINOR PLUS views up 383%", "Educational content earns higher ad rates"),
    ("Quizzes & trivia", "Quiz Lamby ~$16.6K/mo; Quiz Stumble ~$9.6K/mo", "Cheap to make from templates, high engagement"),
    ("Miniature cooking", "Clover Mini Kitchen ~$34.7K/mo; Monkey Xuka subs up 154% in 30 days", "Appeals worldwide, no language barrier"),
    ("Satisfying ASMR (slime, candy, textures)", "Trephor ASMR ~$10.2K/mo; Zup ASMR subs up 481% in 30 days", "Gets rewatched over and over"),
    ("Simulation / tycoon / idle gameplay", "Azrilich: 81K subs, ~$14K/mo; mcveety 47-min videos", "Long sessions, little talking needed"),
    ("Sports analysis (pickleball, football tactics)", "Pickleballtv ~$11.7K/mo; GOALATO ~$8.7K/mo", "Pickleball is a growing sport with high-income viewers"),
    ("English-learning podcasts", "Enjoy English Talks: 242K subs, ~$10.9K/mo", "Global audience, evergreen, binge-listening"),
]
ws = wb.create_sheet("Top 20 Niches", 0)
ws["A1"] = "Top 20 Faceless YouTube Niches"
ws["A1"].font = title_font
ws["A2"] = ("Source: vidIQ scan of ~150 faceless English channels started 2024-2026, Nov 2026. "
            "Earnings are vidIQ monthly estimates, not confirmed revenue. Highlighted row = your niche.")
ws["A2"].font = note_font
for i, hdr in enumerate(["#", "Niche", "Example channel (vidIQ data)", "Why it should last"], 1):
    c = ws.cell(4, i, hdr)
    c.font, c.fill, c.alignment = head_font, head_fill, Alignment(vertical="center", wrap_text=True)
thin = Side(style="thin", color="DDDDDD")
for i, row in enumerate(n, 1):
    for j, val in enumerate((i,) + row, 1):
        c = ws.cell(4 + i, j, val)
        c.font, c.alignment, c.border = body_font, wrap, Border(bottom=thin)
        if i == 14:
            c.fill = yellow
            c.font = Font(name="Arial", size=10, bold=True)
r = 4 + len(n) + 2
ws.cell(r, 1, ("Left off for long-term risk: reuploaded short dramas; celebrity/anime/football fan edits; "
               "Roblox and kids' toy channels; meme compilations.")).font = note_font
for col, w in zip("ABCD", [5, 42, 62, 52]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A5"

wb.save(out)
print([s.title for s in wb])

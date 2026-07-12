---
name: bikefit
description: Run the full guided bike-fit analysis for the user, start to finish — from filming advice to a plain-English verdict. Use this WHENEVER the user wants to analyze, grade, or check their bike fit / cycling position / saddle height / riding posture from a video, OR types /bikefit. Designed for complete beginners who know nothing about the tool.
---

# Bike Fit — guided end-to-end protocol

You are guiding a possibly non-technical cyclist through a complete bike-fit
analysis. Assume they know nothing about this repo, Python, or the terminal. Do
everything for them, one step at a time, in plain language. **Match the user's
language (French or English).** Keep the repo's playful, encouraging tone (see
CLAUDE.md) but stay genuinely helpful — a nervous beginner comes first.

Follow these phases IN ORDER. Do not skip ahead. Stop and wait for the user
whenever you need something from them.

## Phase 0 — Setup (do it silently, don't lecture)
1. Make sure dependencies are installed: run `uv sync` (or pip per the README).
   Install ffmpeg if missing (see setup.ps1 / setup.sh). Only surface this to the
   user if something needs their approval or fails.

## Phase 1 — How to film (BEFORE they record)
2. Read `files/filming-guide.md`. Give the user the SHORT version, emphasizing the
   3 geometry rules that decide everything:
   - **Landscape** (turn the phone sideways), never portrait.
   - **Dead side-on**, camera square to the bike — a good check: both wheels look
     like two circles of the same size. If you see the front of the bike, you're at
     an angle (this makes the tool measure the wrong leg).
   - **Camera at hip/crank height** (~60–80 cm), on a tripod/chair/box, dead level.
   - Plus: 2.5–4 m away, good light (not backlit by a window), pedal 20–30 s,
     ride your normal hand position, and **don't send the clip through WhatsApp**
     (it wrecks the quality) — transfer the original file.
3. Tell them exactly where to put the video: drop it in the `videos/` folder. If
   they don't know how to get a phone video onto the computer, walk them through it
   (USB cable, AirDrop, Google Drive "original quality", email as attachment).
   Reassure them their video stays local and is never uploaded anywhere.

## Phase 2 — Collect their specs (ask, then fill the file yourself)
4. Ask, ONE QUESTION AT A TIME (don't dump a form), for each of these. If they don't
   know a value, say "no worries, we'll skip it" and leave it blank — but tell them
   what they lose (below), because a blank scale/reach input downgrades the cm
   numbers to "indicative" (the tool says so; it never guesses silently):
   - height (cm)
   - inseam (cm) — barefoot, back to a wall, a book pulled up snug between the legs,
     measure floor to top of the book.
   - arm length (cm) — shoulder tip (acromion) to wrist, arm straight, no hand.
     (Feeds the cm reach estimate.)
   - torso length (cm) — acromion to hip joint (the bony bump on the side of the
     hip), sitting up straight. (Feeds the cm reach estimate.)
   - bike model
   - frame size (cm)
   - current stem length (mm) — often printed on the stem.
   - saddle height (mm), if they know it.
   - **tyre width (mm)** — on the tyre sidewall, e.g. `700x28C` -> 28. IMPORTANT: this
     sets the pixels->cm scale (wheel outer Ø = 622mm rim + 2x tyre). It VARIES per
     bike, so always ask; if skipped the tool assumes 28mm and flags cm as indicative.
   - crank length (mm) — engraved on the inside of the crank arm (170/172.5/175).
   - frame reach (mm) and frame stack (mm) — look up THEIR exact model+size on
     geometrygeeks.bike or the maker's geometry chart. (You, Claude, can web-search
     these for them.) Needed for the cm cockpit-reach estimate.
   - roughly how far the camera was (m)
   - road bike or TT/tri bike?
5. Write their answers into a `rider.yaml` file YOURSELF, using `rider.example.yaml`
   as the template. The user must not edit any file. `rider.yaml` is git-ignored, so
   their personal specs never get pushed anywhere. NOTHING rider- or bike-specific is
   ever hard-coded in the code — it all comes from `rider.yaml`, so the repo works for
   any person and any bike.

## Phase 3 — Run the analysis
6. Once the video is in `videos/`, run:
   `uv run python analyze_bikefit.py --input videos/<their-file> --out out_fit --rider rider.yaml`
   Note the video filename may contain spaces — quote it.
7. This takes a few minutes on a CPU (no GPU here). Let them know, don't leave them
   wondering. Run it in the background and check back.

## Phase 4 — Explain the results like a human
8. Read `files/fit-rules.md` so your advice matches the tool's logic. Read
   `out_fit/report.md` and open the bottom-of-stroke still (`out_fit/stills/*_BDC.jpg`)
   to sanity-check that the skeleton is on the NEAR (camera-side) leg.
9. **If the report shows the camera-angle warning** (near/far leg indistinguishable),
   or the skeleton is clearly on the far/hidden leg, tell the user the clip needs a
   re-shoot per Phase 1, and don't over-trust the numbers.
10. Explain in plain language: overall verdict, then what's dialed (green) and what
    to change. Give them ONE priority change first (saddle height OR reach, not both),
    with the concrete action (e.g. "raise the saddle ~8 mm" or "shorter stem +
    raise the bars"). Then: change one thing, re-film, re-run, compare.
11. Be honest about limits: a 2D side video is a great starting point, not a 3D pro
    fit or medical advice. For persistent pain or a suspected frame-size mismatch,
    recommend a professional fitter.

## Key correctness notes (so you don't repeat old mistakes)
- Knee angle: the report's `knee_flexion_bdc` is FLEXION (180 − interior). A HIGH
  number = knee still BENT at the bottom = saddle too LOW = RAISE it. (Not "too
  straight".) The report also prints the interior angle now.
- Never claim the fit is validated by a clip that triggered the camera-angle warning.
- Change ONE thing per session; the whole point of the before/after is isolating it.

# Fit rules — the formulas behind the personalized advice

`analyze_bikefit.py` uses these when a `rider.yaml` is provided (`--rider`). They
turn raw joint angles + body/bike specs into concrete, personalized guidance. All
are **starting-point heuristics from the bike-fit literature**, not a substitute
for a professional 3D fit. Sources for the angle ranges are in
[`bikefit-research-ranges.md`](bikefit-research-ranges.md).

## Inputs (rider.yaml)

| Field | Unit | Used for |
|---|---|---|
| `height_cm` | cm | Frame-size sanity check |
| `inseam_cm` | cm | Theoretical saddle height (LeMond), frame-size check |
| `bike` | text | Displayed in report; flags tri/TT vs road profile |
| `frame_size_cm` | cm | Frame-size sanity check vs height/inseam |
| `stem_length_mm` | mm | Reach advice (how much shorter to go) |
| `saddle_height_mm` | mm | Compare measured setup to LeMond target |
| `camera_distance_m` | m | (Reserved) pixels→mm scale |

Every field is **optional** — each rule only fires if its inputs are present.

## Rules

### 1. Saddle height — LeMond method
Theoretical saddle height (center of BB to top of saddle, along the seat tube) ≈
**inseam_cm × 0.883**, in cm. This is the classic LeMond number.

- If `saddle_height_mm` is given, compare it to the LeMond target and report the
  delta in mm.
- Cross-check with the **dynamic knee angle at BDC** (the video measurement):
  interior knee angle target ≈ **140–148°** (equivalently, `knee_flexion_bdc`
  30–40, since flexion = 180 − interior).
  - Interior **< 140°** (flexion **> 40**) → knee too bent → **saddle too LOW → raise**.
  - Interior **> 150°** (flexion **< 30**) → knee too straight → **saddle too HIGH → lower**.
- When both disagree, trust the **video** for the direction (it's your actual
  pedaling position) and use LeMond as a plausibility bound.

### 2. Degrees → millimeters (saddle)
Rough rule near the target: **~1° of knee angle ≈ ~3–4 mm of saddle height** for a
typical adult leg. Report a *range*, cap the suggestion at ~15 mm per change, and
always say "change one thing, then re-film."

### 3. Frame size vs body
Road-bike rough guide (endurance/race geometry):

| Height | Typical frame (cm) |
|---|---|
| 1.70–1.75 m | 52–54 |
| 1.75–1.80 m | 54–56 |
| 1.80–1.85 m | 56–58 |

- These overlap a lot; brand geometry (reach/stack) matters more than the label.
- If `frame_size_cm` is at or above the **top** of the rider's band **and** the
  video shows a **long/low front** (torso < 40° from horizontal, shoulder < 80°,
  elbow forced), flag: *"frame may be on the large side — reach likely too long."*
- Be honest about the limit: a too-big frame can be *mitigated* with a shorter
  stem and higher bars but not fully fixed. Recommend a pro fit if pain persists.

### 4. Reach / cockpit (the front end)
Read torso + shoulder + elbow together — they share one cause:

- **Torso < 40° from horizontal** = too stretched/low.
- **Shoulder < 80°** = closed, scrunched cockpit (weight on hands).
- **Elbow > 30° or forced-straight** = arms reaching for the bars.
- If two or more fire → **front end too long/low**. Fix order (one at a time):
  1. **Raise the bars** (move spacers under→over the stem, or a +angle stem) —
     biggest win for hand/neck/back pain.
  2. **Shorter stem** (e.g. 100 → 90 → 80 mm) — the main lever against "too stretched".
  3. Only then touch saddle height (raising the saddle *lengthens* effective reach).

### 5. Discipline profile
If `bike` mentions tri / TT / time-trial, the road ranges don't apply (TT runs a
lower torso and different hip/knee). Say so; don't grade a TT setup against road
numbers.

## Reporting honesty
- Always restate the specs used, so the advice is auditable.
- Every fix is a *starting point*; recommend a professional fitter for persistent
  pain, numbness, or a suspected frame-size mismatch.
- Not medical advice. Change one thing per session and re-film.

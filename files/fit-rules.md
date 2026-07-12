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

### 6. Extra side-on metrics (report-only — context, never gate the verdict)
These come from `bike_calib.py` (a px→mm scale + bottom-bracket from the ankle orbit)
and `fit_metrics.py`. All are **report-only**: they inform, they never turn the fit
red. Every cm/mm number is gated by `calibration.quality_flag` (ok | indicative |
suppress) — if the wheel scale and the crank-orbit scale disagree >10–15% the camera
isn't square, and cm outputs are downgraded or hidden. Angles are scale-free and
unaffected.

- **KOPS / saddle setback.** Knee-vs-pedal-spindle horizontal offset at the 3 o'clock
  crank position (found via the ankle's crank angle). Positive = knee ahead of the
  spindle (sign is bike-direction-independent). Band ~ −40…+10 mm neutral, but wide
  (±10–15 mm real resolution) and **report-only** — KOPS is a coincidental proxy, not
  biomechanics (Sheldon Brown; The Rider Project). **Do not chase KOPS to fix knee
  pain:** force studies show fore/aft saddle barely changes patellofemoral load (1–4%;
  Bini & Hume 2012, Menard 2018), and a *rearward* saddle raises knee shear/compression
  more. So if moving the saddle **forward** relieved anterior knee pain, that's most
  likely **reach-driven** (shorter effective reach), not a setback-load effect — keep
  what stopped the pain, treat KOPS as informational.
- **Knee ROM (BDC↔TDC).** Interior knee angle at top of stroke + the sweep. Very
  closed at TDC (<58°) hints saddle too low or crank too long. Corroborates BDC (which
  owns the saddle-height verdict); the sweep is derived so it carries ±4–5°.
- **Pelvic rock (vertical).** Hip vertical oscillation over the stroke, as % of femur
  (size-free) + mm. >~4% suggests saddle too high. ⚠️ Only vertical is visible
  side-on; **true lateral rock needs a rear-view clip**. Sub-~12 mm is below the noise
  floor — treat as zero.
- **Effective bar drop.** Saddle-region (hip proxy) to hoods (wrist) vertical drop.
  Proxy-biased, so trust it as a **relative** number between reshoots and **defer to
  the torso angle** for the real front-end verdict.
- **Cockpit reach.** Two reads: a scale-free **arm/torso pixel ratio** (always
  available, comparable between clips) and an optional **cm estimate** = bike front run
  (from `frame_reach_mm` + stem) vs the rider's comfortable reach (from `arm_length_cm`
  + `torso_length_cm`). The cm read needs those specs; if absent, only the ratio shows.
- **Ankle / foot angle: not computed.** COCO-17 has no toe/foot keypoint, so a true
  ankle angle is impossible from this clip — the report says so rather than faking it.

## Reporting honesty
- Always restate the specs used, so the advice is auditable.
- Every fix is a *starting point*; recommend a professional fitter for persistent
  pain, numbness, or a suspected frame-size mismatch.
- Not medical advice. Change one thing per session and re-film.

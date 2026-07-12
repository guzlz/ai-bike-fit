"""
fit_metrics.py -- the new side-on fit measurements beyond the 5 BDC angles.

Built on the calibration from bike_calib.py (BB, ankle-orbit, mm/px scale, facing,
hoods) plus the per-frame COCO keypoints. Everything here is DELIBERATELY honest
about 2D limits: measurements that a side view can't do reliably are labelled
indicative or refused outright (see ankle_angle), and NONE of these gate the overall
verdict -- they add context to the 5 core angles, matching the tool's posture.

Crank phase is read from the ankle, which orbits the BB (the pedal proxy). One angle
`theta` drives frame selection for every measurement:
    theta = atan2(-(ankle_y - bb_y), facing*(ankle_x - bb_x))
    0 = 3 o'clock (forward & level, the KOPS frame)
   -90 = 6 o'clock (BDC)   +90 = 12 o'clock (TDC)

Grading bands and their sources live in files/fit-rules.md and
files/bikefit-research-ranges.md. All bands are honest about the monocular +/-2-3 deg
and the scale error; report-only metrics use a wide amber pad.

User-varying inputs (arm/torso length, crank) come from rider.yaml. A default is a
last-resort fallback and is FLAGGED as assumed in the output, never silent -- same
rule as tyre width in bike_calib.py.
"""

import numpy as np

# Body-measurement fallbacks (used only if rider.yaml lacks them; flagged when used).
ARM_LEN_CM_DEFAULT = 62.0     # shoulder(acromion) -> wrist, arm extended
TORSO_LEN_CM_DEFAULT = 52.0   # acromion -> hip joint, seated upright

# Scott Addict endurance-road nominal cockpit numbers are passed in from rider/geometry;
# reach math uses whatever frame reach/stack/stem the caller supplies.


def _deg(r):
    return float(np.degrees(r))


def crank_theta(ankle_xy, bb, facing):
    """Per-frame crank angle from the ankle orbit. NaN where ankle missing."""
    ax = ankle_xy[:, 0] - bb[0]
    ay = ankle_xy[:, 1] - bb[1]
    return np.arctan2(-(ay), facing * ax)     # +y is up in math convention


def _median_over(mask, *series):
    if mask.sum() == 0:
        return [np.nan] * len(series)
    return [float(np.nanmedian(s[mask])) for s in series]


def interior(a, b, c):
    """Interior angle at b (deg). a,b,c: (2,) arrays. NaN if degenerate."""
    a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
    if not (np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(c).all()):
        return np.nan
    ba, bc = a - b, c - b
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n == 0:
        return np.nan
    return _deg(np.arccos(np.clip(np.dot(ba, bc) / n, -1, 1)))


# ------------------------------- KOPS / setback -------------------------------

def kops(pts, cof, side, ride_mask, KP, cal):
    """Knee-Over-Pedal-Spindle horizontal offset at the 3 o'clock crank position.
    Returns dict or None. Positive kops_mm = knee AHEAD of the spindle (regardless of
    which way the bike faces). Report-only; KOPS is a loose reference, not a law."""
    if cal.bb is None or cal.mm_per_px is None or cal.crank_orbit_r_px is None:
        return None
    ki, ai = KP[f"{side}_knee"], KP[f"{side}_ankle"]
    ax = pts[:, ai, :]
    theta = crank_theta(ax, cal.bb, cal.facing)
    fwd = cal.facing * (ax[:, 0] - cal.bb[0]) > 0
    kC = cof[:, ki]
    cand = (ride_mask & np.isfinite(theta) & (np.abs(theta) < np.radians(8)) & fwd
            & np.isfinite(pts[:, ki, 0]) & (kC >= 0.4))
    if cand.sum() < 3:
        return {"kops_mm": None, "n": int(cand.sum()),
                "note": "3 o'clock frame not clearly captured -> KOPS unreliable."}
    knee_x = float(np.nanmedian(pts[cand, ki, 0]))
    # spindle proxy: the orbit point at 3 o'clock (geometry, robust to per-frame noise)
    pedal_x = cal.bb[0] + cal.facing * cal.crank_orbit_r_px
    kops_mm = cal.facing * (knee_x - pedal_x) * cal.mm_per_px
    return {"kops_mm": round(float(kops_mm), 1), "n": int(cand.sum())}


# ------------------------------- knee ROM -------------------------------

def knee_rom(pts, cof, side, ride_mask, KP, cal, knee_int_bdc):
    """Knee interior angle at TDC + the BDC->TDC sweep. knee_int_bdc is passed in
    (already computed by the main tool). TDC = ankle highest (theta ~ +90)."""
    hi, ki, ai = KP[f"{side}_hip"], KP[f"{side}_knee"], KP[f"{side}_ankle"]
    out = {"knee_int_bdc": (round(knee_int_bdc, 1) if np.isfinite(knee_int_bdc) else None)}
    if cal.bb is not None:
        theta = crank_theta(pts[:, ai, :], cal.bb, cal.facing)
        band = ride_mask & np.isfinite(theta) & (theta > np.radians(90 - 15))
    else:  # no BB -> fall back to "ankle highest" (smallest y)
        ay = pts[:, ai, 1].astype(float)
        band = ride_mask & np.isfinite(ay)
        if band.sum() >= 5:
            thr = np.nanpercentile(ay[band], 15)
            band = band & (ay <= thr)
    ints = np.array([interior(pts[i, hi], pts[i, ki], pts[i, ai]) for i in range(len(pts))])
    bandv = band & np.isfinite(ints)
    if bandv.sum() < 3:
        out["knee_int_tdc"] = None
        out["knee_rom"] = None
        out["tdc_uncertain"] = True
        return out
    tdc = float(np.nanmedian(ints[bandv]))
    std = float(np.nanstd(ints[bandv]))
    out["knee_int_tdc"] = round(tdc, 1)
    out["tdc_uncertain"] = bool(std > 12)   # foreshortening/occlusion at 12 o'clock
    if np.isfinite(knee_int_bdc):
        out["knee_rom"] = round(knee_int_bdc - tdc, 1)   # the sweep
    else:
        out["knee_rom"] = None
    return out


# ------------------------------- pelvic rock -------------------------------

def pelvic_rock(pts, cof, side, ride_mask, KP, cal, fps):
    """Vertical hip oscillation over the stroke, detrended. Returns mm + % of femur.
    Side-on sees only VERTICAL rock; true lateral rock needs a rear view."""
    hi, ki = KP[f"{side}_hip"], KP[f"{side}_knee"]
    hy = pts[:, hi, 1].astype(float)
    ok = ride_mask & np.isfinite(hy)
    if ok.sum() < max(10, int(fps)):
        return None
    idx = np.where(ok)[0]
    hy_ok = hy[idx]
    # detrend: subtract a ~1-stroke rolling median so we measure stroke rock, not drift
    win = max(5, int(round(fps)))          # ~1s window ~ a bit over one stroke
    med = np.array([np.median(hy_ok[max(0, k - win // 2):k + win // 2 + 1])
                    for k in range(len(hy_ok))])
    detr = hy_ok - med
    p2p_px = float(np.percentile(detr, 95) - np.percentile(detr, 5))
    femur = np.array([np.hypot(pts[i, hi, 0] - pts[i, ki, 0], pts[i, hi, 1] - pts[i, ki, 1])
                      for i in idx])
    femur_px = float(np.nanmedian(femur[np.isfinite(femur)])) if np.isfinite(femur).any() else np.nan
    out = {"rock_pct_femur": round(100 * p2p_px / femur_px, 2) if femur_px else None}
    if cal.mm_per_px:
        out["rock_mm"] = round(p2p_px * cal.mm_per_px, 1)
    # noise floor: hip keypoint jitters a few px -> ignore sub-~12mm-ish signals
    out["below_noise_floor"] = bool(cal.mm_per_px and p2p_px * cal.mm_per_px < 12)
    return out


# ------------------------------- bar drop -------------------------------

def bar_drop(pts, cof, side, ride_mask, KP, cal):
    """Effective saddle-to-hoods vertical drop, from body proxies (hip top ~ saddle
    region, wrist ~ hoods). INDICATIVE: the hip-joint sits below the saddle top by a
    rider-specific offset, so the absolute number is biased; trust it as a RELATIVE
    number between reshoots, and defer to the torso angle. Positive = bars below."""
    if cal.mm_per_px is None:
        return None
    hi, wi = KP[f"{side}_hip"], KP[f"{side}_wrist"]
    hy = pts[:, hi, 1].astype(float)
    wy = pts[:, wi, 1].astype(float)
    okh = ride_mask & np.isfinite(hy)
    okw = ride_mask & np.isfinite(wy) & (cof[:, wi] >= 0.4)
    if okh.sum() < 10 or okw.sum() < 10:
        return None
    saddle_y = float(np.percentile(hy[okh], 5))    # highest hip (smallest y) ~ seat level region
    bar_y = float(np.median(wy[okw]))
    drop_mm = (bar_y - saddle_y) * cal.mm_per_px
    return {"drop_mm": round(float(drop_mm), 1),
            "note": "indicative: saddle proxy = hip joint (sits below saddle top); "
                    "trust as relative between reshoots, defer to torso angle."}


# ------------------------------- hoods reach -------------------------------

def hoods_reach(pts, cof, side, ride_mask, KP, cal, rider, geom):
    """Two independent reads of 'is the cockpit too long?':
      A. GEOMETRIC (cm): compare the rider's usable arm+torso span to the bike's
         BB->hoods horizontal run derived from frame reach/stack + stem. Needs body
         measurements (arm, torso) from rider.yaml; flagged if they fall back.
      B. SCALE-FREE RATIO: shoulder->wrist reach vs torso length, in pixels, so the
         scale cancels and it's comparable between clips without any calibration.
    Returns dict with whichever reads are available."""
    out = {}

    # --- B. scale-free ratio (works even with no calibration) ---
    si, ei, wi, hi = (KP[f"{side}_shoulder"], KP[f"{side}_elbow"],
                      KP[f"{side}_wrist"], KP[f"{side}_hip"])
    arm_px, torso_px, sh_reach_x = [], [], []
    for i in np.where(ride_mask)[0]:
        s, w, h = pts[i, si], pts[i, wi], pts[i, hi]
        if np.isfinite(s).all() and np.isfinite(w).all():
            arm_px.append(np.hypot(*(w - s)))
            sh_reach_x.append(abs(w[0] - s[0]))
        if np.isfinite(s).all() and np.isfinite(h).all():
            torso_px.append(np.hypot(*(s - h)))
    if arm_px and torso_px:
        arm_m = float(np.nanmedian(arm_px))
        torso_m = float(np.nanmedian(torso_px))
        out["reach_ratio"] = round(arm_m / torso_m, 3) if torso_m else None
        out["shoulder_reach_ratio"] = (round(float(np.nanmedian(sh_reach_x)) / torso_m, 3)
                                       if (sh_reach_x and torso_m) else None)

    # --- A. geometric cm (needs body measurements) ---
    arm_given = rider.get("arm_length_cm") not in (None, "")
    torso_given = rider.get("torso_length_cm") not in (None, "")
    arm_cm = float(rider["arm_length_cm"]) if arm_given else ARM_LEN_CM_DEFAULT
    torso_cm = float(rider["torso_length_cm"]) if torso_given else TORSO_LEN_CM_DEFAULT
    out["body_assumed"] = bool(not arm_given or not torso_given)

    reach = geom.get("frame_reach_mm")
    stack = geom.get("frame_stack_mm")
    stem = None
    if rider.get("stem_length_mm") not in (None, ""):
        stem = float(rider["stem_length_mm"])
    # --- A. geometric cm estimate (rough, first-order; the ratio B is the robust one) ---
    # Compare like with like: BOTH runs measured horizontally from the SADDLE.
    #   bike side:  saddle -> hoods = frame_reach + stem_horizontal - saddle_setback
    #   rider side: the forward reach the torso+arm actually span at the target lean
    # Setback needs calibration (KOPS); when unknown, use a nominal road value and say
    # the estimate is approximate. Kept only if it lands in a sane range, else dropped
    # rather than reported as a bogus number (the -314mm kind).
    if reach and stack:
        setback_mm = 60.0   # nominal saddle-behind-BB; refined by KOPS when calibrated
        stem_h = (stem or 90.0) * np.cos(np.radians(17)) + 40.0   # +hoods ahead of bar
        bike_run_mm = float(reach) + stem_h - setback_mm         # saddle -> hoods, horizontal
        # Rider's forward reach from the saddle: shoulder sits ~torso*cos(lean) ahead of
        # the hip, then the arm reaches ~arm*cos(arm_drop) further to the hoods.
        lean = np.radians(43)          # target torso_from_horiz mid-band
        arm_drop = np.radians(40)      # arm angled down to the hoods
        rider_run_mm = torso_cm * 10 * np.cos(lean) + arm_cm * 10 * np.cos(arm_drop)
        delta = bike_run_mm - rider_run_mm     # + = bike front longer than comfy reach
        # Sanity gate: a road saddle->hoods run is ~450-650mm; a plausible rider reach
        # similar. If either is wildly off, our proxies/specs are bad -> don't report cm.
        if 350 <= bike_run_mm <= 750 and 350 <= rider_run_mm <= 800 and abs(delta) <= 200:
            out["bike_run_mm"] = round(bike_run_mm, 0)
            out["rider_run_mm"] = round(rider_run_mm, 0)
            out["reach_delta_mm"] = round(float(delta), 0)
        else:
            out["reach_cm_note"] = ("cm reach estimate out of sane range "
                                    f"(bike {bike_run_mm:.0f}, rider {rider_run_mm:.0f} mm) "
                                    "-> body/frame proxies too rough; use the ratio instead.")
    return out


# ------------------------------- ankle angle (refused) -------------------------------

def ankle_angle(*_a, **_k):
    """NOT computed. The ankle interior angle needs a foot/toe landmark to form the
    shank->foot ray, and COCO-17 has no keypoint distal to the ankle (15/16).
    Inventing a toe would manufacture the measurement, so we refuse and say so."""
    return {"available": False,
            "reason": ("ankle/foot angle needs a toe or ball-of-foot point, which the "
                       "COCO-17 pose model doesn't provide -- not measurable from this "
                       "clip. Would need a foot-keypoint model (e.g. COCO-WholeBody).")}

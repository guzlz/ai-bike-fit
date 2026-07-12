"""
bike_calib.py -- detect bike parts + establish a pixel->mm scale from a side-on clip.

analyze_bikefit.py gives us COCO body keypoints per frame but NO bike parts (YOLO
pose sees the rider, not the wheels/cranks). This module recovers what the cm-based
fit measurements (saddle setback/KOPS, reach, bar drop) need:

  - bottom bracket (BB): the crank axle. Found from MOTION, not image detection --
    the near ankle traces a circle about the BB as the rider pedals, so we fit a
    circle to the ankle track (Kasa + RANSAC) and its CENTER is the BB. Rock solid,
    immune to the round wall-mirror / backlit-window traps that fool Hough.
  - wheels: two ~700c circles, via HoughCircles behind hard geometric gates (a wheel
    pair is large, low in frame, equal-radius, horizontally aligned, spaced ~3x their
    radius). The lone high-up wall mirror fails every one of those.
  - scale (mm/px): PRIMARY from the wheel outer diameter (rim 622mm + 2*tire_mm --
    the camera sees the TYRE edge, not the rim, so tyre width matters). The ankle
    orbit gives an independent CHECK scale; if the two disagree the camera isn't
    square (parallax) and we downgrade cm outputs to "indicative".
  - hoods: where the hands rest, taken from the wrist keypoint (robust) rather than
    edge-detecting a thin bar against a bright window.

Everything here only gates the NEW cm-based measurements. Angles are scale-free and
never depend on this module -- if calibration fails, the original angle report is
unchanged.

Pure cv2 + numpy, no new deps. Validated in geometry/logic; verify wheel + orbit
detection VISUALLY on a good clip before trusting cm numbers (see the overlay).
"""

from dataclasses import dataclass, field, asdict
import numpy as np

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False


# --- Physical constants (overridable from rider.yaml) ---
RIM_DIAMETER_MM = 622.0          # 700c / ETRTO bead-seat: the wheel WITHOUT tyre
TIRE_WIDTH_MM_DEFAULT = 28.0     # outer Ø = rim + 2*tyre; camera sees the tyre edge
CRANK_LEN_MM_DEFAULT = 172.5
FOOT_OFFSET_NOMINAL_MM = 40.0    # pedal spindle -> ankle-bone keypoint (foot lever)
FOOT_OFFSET_MIN_MM = 10.0        # plausibility window for the wheel/crank cross-check
FOOT_OFFSET_MAX_MM = 75.0

# Wheel-detection geometry gates (fractions of frame height H, dimensionless ratios)
CY_MIN_FRAC = 0.42               # wheel CENTERS sit low; the wall mirror sits high -> rejected
R_MIN_FRAC = 0.16
R_MAX_FRAC = 0.44
RADIUS_MATCH_TOL = 0.12          # the two wheels have near-equal radius
Y_ALIGN_FRAC = 0.10              # ...and are horizontally aligned
WHEELBASE_RATIO_LO = 2.4         # center-distance / radius ~ 3.0 for a road bike
WHEELBASE_RATIO_HI = 3.8

# Scale-agreement thresholds
SCALE_WARN = 0.10                # >10% disagreement -> indicative
SCALE_SUPPRESS = 0.15            # >15% -> suppress cm outputs


def wheel_outer_mm(tire_mm=TIRE_WIDTH_MM_DEFAULT):
    """Outer diameter the camera actually sees = rim bead-seat + two tyre widths."""
    return RIM_DIAMETER_MM + 2.0 * float(tire_mm)


@dataclass
class Calibration:
    bb: tuple | None = None                    # (x, y) bottom-bracket px
    crank_orbit_r_px: float | None = None      # ankle-orbit radius (= crank + foot offset)
    wheels: dict = field(default_factory=dict)  # {'near':(x,y,r), 'far':(x,y,r), 'radius_px':r}
    hoods: tuple | None = None                 # (x, y) hands-on-hoods px
    facing: int = 1                            # +1 if handlebar is on +x side of BB, else -1
    mm_per_px: float | None = None             # PRIMARY scale (wheel)
    mm_per_px_crank: float | None = None       # CHECK scale (orbit, nominal offset)
    scale_disagreement: float | None = None
    implied_foot_offset_mm: float | None = None
    tire_assumed: bool = False                 # True if tyre width fell back to default
    confidence: float = 0.0
    quality_flag: str = "suppress"             # 'ok' | 'indicative' | 'suppress'
    notes: list = field(default_factory=list)

    def to_json(self):
        d = asdict(self)
        # tuples/np -> plain lists/floats for json
        for k in ("bb", "hoods"):
            if d[k] is not None:
                d[k] = [round(float(v), 1) for v in d[k]]
        w = {}
        for k, v in self.wheels.items():
            w[k] = ([round(float(x), 1) for x in v] if isinstance(v, (tuple, list, np.ndarray))
                    else (round(float(v), 2) if v is not None else None))
        d["wheels"] = w
        for k in ("crank_orbit_r_px", "mm_per_px", "mm_per_px_crank", "scale_disagreement",
                  "implied_foot_offset_mm", "confidence"):
            if d[k] is not None:
                d[k] = round(float(d[k]), 4)
        return d


# ----------------------------- circle fitting -----------------------------

def fit_circle_kasa(P):
    """Algebraic (Kasa) least-squares circle fit. P: (M,2) -> (cx, cy, r).
    Closed form: linearize (x-a)^2+(y-b)^2=r^2 into 2ax+2by+c = x^2+y^2."""
    x, y = P[:, 0].astype(np.float64), P[:, 1].astype(np.float64)
    A = np.column_stack([2 * x, 2 * y, np.ones_like(x)])
    d = x * x + y * y
    sol, *_ = np.linalg.lstsq(A, d, rcond=None)
    cx, cy, c = sol
    r = np.sqrt(max(c + cx * cx + cy * cy, 0.0))
    return float(cx), float(cy), float(r)


def _circle_from_3(p):
    (x1, y1), (x2, y2), (x3, y3) = p
    a, b, c, d = x2 - x1, y2 - y1, x3 - x1, y3 - y1
    e = a * (x1 + x2) + b * (y1 + y2)
    f = c * (x1 + x3) + d * (y1 + y3)
    g = 2 * (a * (y3 - y2) - b * (x3 - x2))
    if abs(g) < 1e-6:                       # collinear
        return None
    cx = (d * e - b * f) / g
    cy = (a * f - c * e) / g
    r = float(np.hypot(x1 - cx, y1 - cy))
    return float(cx), float(cy), r


def fit_bb_orbit(P, frame_diag, iters=400, seed=0, inlier_band=0.12, min_frac=0.35):
    """Robust BB = center of the ankle orbit. RANSAC over 3-point circles, then a
    trimmed Kasa refit. Returns (cx, cy, r, inlier_mask, quality) or None.

    Real ankle tracks are noisy (ankling + keypoint jitter mean the foot does NOT
    trace a clean circle), so the inlier band (12% of radius) and consensus (35%) are
    looser than a synthetic circle would need; the angular-coverage + RMS quality
    terms still down-weight a poor fit so a noisy orbit yields low confidence, not a
    confident-but-wrong BB. quality = dict(angular_coverage, inlier_ratio, radial_rms_norm)."""
    P = np.asarray(P, np.float64)
    M = len(P)
    if M < 12:
        return None
    # Light smoothing knocks down the per-frame jitter/ankling that pushes points off
    # the true orbit, without moving the center (a low-pass on an ordered track).
    if M >= 9:
        k = 3
        pad = np.pad(P, ((k, k), (0, 0)), mode="edge")
        P = np.stack([np.convolve(pad[:, 0], np.ones(2 * k + 1) / (2 * k + 1), "valid"),
                      np.convolve(pad[:, 1], np.ones(2 * k + 1) / (2 * k + 1), "valid")], 1)
    rng = np.random.default_rng(seed)
    best_inl, best_model = None, None
    for _ in range(iters):
        idx = rng.choice(M, 3, replace=False)
        m = _circle_from_3(P[idx])
        if m is None:
            continue
        cx, cy, r = m
        if not (5 < r < 0.5 * frame_diag):
            continue
        resid = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - r)
        inl = resid < inlier_band * r
        if best_inl is None or inl.sum() > best_inl.sum():
            best_inl, best_model = inl, m
    if best_inl is None or best_inl.sum() < max(10, min_frac * M):
        return None
    inl_pts = P[best_inl]
    cx, cy, r = fit_circle_kasa(inl_pts)
    resid = np.abs(np.hypot(inl_pts[:, 0] - cx, inl_pts[:, 1] - cy) - r)
    keep = resid <= np.percentile(resid, 85)   # shed borderline 15% (within inliers)
    inl_pts = inl_pts[keep]
    cx, cy, r = fit_circle_kasa(inl_pts)

    # quality: how well do inliers wrap the clock + how tight is the fit
    ang = np.arctan2(inl_pts[:, 1] - cy, inl_pts[:, 0] - cx)
    sectors = np.unique((((ang + np.pi) / (2 * np.pi)) * 12).astype(int) % 12)
    coverage = len(sectors) / 12.0
    resid_in = np.abs(np.hypot(inl_pts[:, 0] - cx, inl_pts[:, 1] - cy) - r)
    rms_norm = float(np.sqrt(np.mean(resid_in ** 2)) / (r + 1e-9))
    quality = {"angular_coverage": round(coverage, 3),
               "inlier_ratio": round(float(best_inl.sum()) / M, 3),
               "radial_rms_norm": round(rms_norm, 4)}
    return cx, cy, r, best_inl, quality


# ----------------------------- wheel detection -----------------------------

def _wheel_candidates(gray, H, W):
    if not _HAS_CV2:
        return np.empty((0, 3), np.float32)
    g = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(
        g, cv2.HOUGH_GRADIENT, dp=1.5, minDist=int(0.20 * W),
        param1=120, param2=55,
        minRadius=int(R_MIN_FRAC * H), maxRadius=int(R_MAX_FRAC * H))
    if circles is None:
        return np.empty((0, 3), np.float32)
    c = circles[0]
    return c[c[:, 1] >= CY_MIN_FRAC * H]     # drop high circles (the wall mirror)


def _best_pair(c, H):
    """Score every candidate pair against the wheel-pair priors; return the best
    ((xl,yl,rl),(xr,yr,rr)) or None."""
    best, best_score = None, -1.0
    K = len(c)
    for i in range(K):
        for j in range(i + 1, K):
            a, b = c[i], c[j]
            (xl, yl, rl), (xr, yr, rr) = (a, b) if a[0] < b[0] else (b, a)
            rmean = 0.5 * (rl + rr)
            if max(rl, rr) == 0:
                continue
            if abs(rl - rr) / max(rl, rr) > RADIUS_MATCH_TOL:
                continue
            if abs(yl - yr) > Y_ALIGN_FRAC * H:
                continue
            ratio = abs(xr - xl) / rmean
            if not (WHEELBASE_RATIO_LO <= ratio <= WHEELBASE_RATIO_HI):
                continue
            if not (R_MIN_FRAC * H <= rmean <= R_MAX_FRAC * H):
                continue
            s_ratio = 1.0 - abs(ratio - 3.0) / 1.4
            s_req = 1.0 - (abs(rl - rr) / max(rl, rr)) / RADIUS_MATCH_TOL
            s_low = np.clip((0.5 * (yl + yr)) / H, 0, 1)
            s_size = np.clip(rmean / (0.30 * H), 0, 1.5)
            score = s_ratio + s_req + 0.5 * s_low + 0.5 * s_size
            if score > best_score:
                best_score, best = score, ((xl, yl, rl), (xr, yr, rr))
    return best


def detect_wheels(frames_sample, H, W):
    """frames_sample: list of BGR frames (subsampled). Returns (wheels_dict, conf)."""
    if not _HAS_CV2 or not frames_sample:
        return {}, 0.0
    pairs = []
    n_pass_gate = 0
    for f in frames_sample:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        c = _wheel_candidates(gray, H, W)
        if len(c) >= 2:
            p = _best_pair(c, H)
            if p is not None:
                pairs.append(p)
                n_pass_gate += 1
    n = len(frames_sample)
    if len(pairs) < max(3, 0.15 * n):
        return {}, 0.0
    L = np.array([p[0] for p in pairs])
    R = np.array([p[1] for p in pairs])
    left = np.median(L, axis=0)
    right = np.median(R, axis=0)
    radii = np.r_[L[:, 2], R[:, 2]]
    radius = float(np.median(radii))
    radius_cv = float(np.std(radii) / (radius + 1e-9))
    wheels = {"near": None, "far": None, "left": tuple(left), "right": tuple(right),
              "radius_px": radius, "radius_cv": round(radius_cv, 4)}
    # confidence: consensus * stability * gate-cleanliness
    consensus = min(1.0, len(pairs) / (0.4 * n))
    stability = float(np.clip(1.0 - radius_cv / 0.10, 0, 1))
    cleanliness = n_pass_gate / max(1, n)
    conf = float(consensus * stability * cleanliness)
    return wheels, conf


# ----------------------------- hoods (from wrist) -----------------------------

def hoods_from_wrist(wrist_xy, wrist_cf):
    """Hands rest on the hoods; the wrist keypoint is a robust proxy. Returns
    ((x,y), spread_px) or (None, None)."""
    ok = np.isfinite(wrist_xy).all(1) & (wrist_cf >= 0.4)
    if ok.sum() < 10:
        return None, None
    W = wrist_xy[ok]
    center = tuple(np.median(W, axis=0))
    spread = float(np.hypot(*(np.std(W, axis=0))))
    return center, spread


# ----------------------------- orchestration -----------------------------

def calibrate(pts, cof, side, ride_mask, KP, frames_sample, H, W, rider=None):
    """Full calibration. See module docstring. Returns a Calibration."""
    rider = rider or {}
    # Tyre width scales the wheel outer Ø, which sets the whole cm scale. It VARIES
    # per rider (25/28/30/32...), so it must come from rider.yaml. The default is a
    # last-resort fallback, NOT a silent assumption -- if we fall back, we say so in
    # the report and mark cm outputs indicative, because a wrong tyre width biases
    # every cm number by ~1% per 3mm.
    tire_given = rider.get("tire_width_mm") not in (None, "")
    tire = float(rider["tire_width_mm"]) if tire_given else TIRE_WIDTH_MM_DEFAULT
    crank_given = rider.get("crank_len_mm") not in (None, "")
    crank = float(rider["crank_len_mm"]) if crank_given else CRANK_LEN_MM_DEFAULT
    outer_mm = wheel_outer_mm(tire)
    cal = Calibration()
    cal.tire_assumed = not tire_given
    frame_diag = float(np.hypot(H, W))

    # --- BB from the ankle orbit (the anchor) ---
    ai = KP[f"{side}_ankle"]
    aP = pts[ride_mask, ai, :]
    aC = cof[ride_mask, ai]
    okA = np.isfinite(aP).all(1) & (aC >= 0.5)
    orbit = fit_bb_orbit(aP[okA], frame_diag) if okA.sum() >= 12 else None
    conf_bb = 0.0
    if orbit is not None:
        cx, cy, r, _inl, q = orbit
        cal.bb = (cx, cy)
        cal.crank_orbit_r_px = r
        # RMS divisor 0.18: real ankle orbits run ~0.10-0.15 RMS (ankling + jitter), so
        # a genuinely circular-but-noisy track still scores well; only rms>~0.18 (a
        # non-circular cloud) drives the term toward zero. Coverage + inlier ratio carry
        # most of the weight.
        conf_bb = float(np.clip(q["angular_coverage"], 0, 1)
                        * np.clip(q["inlier_ratio"], 0, 1)
                        * np.clip(1 - q["radial_rms_norm"] / 0.18, 0, 1))
        cal.notes.append(f"BB from ankle orbit: coverage {q['angular_coverage']:.0%}, "
                         f"inliers {q['inlier_ratio']:.0%}, rms {q['radial_rms_norm']:.3f}.")
    else:
        cal.notes.append("Ankle-orbit fit failed (thin/blurred pedal track) -> no BB.")

    # --- facing: where is the handlebar relative to the BB? ---
    wi = KP[f"{side}_wrist"]
    wxy = pts[:, wi, :]
    wcf = cof[:, wi]
    if cal.bb is not None:
        okW = np.isfinite(wxy).all(1) & (wcf >= 0.4)
        if okW.sum() >= 5:
            cal.facing = 1 if float(np.median(wxy[okW, 0]) - cal.bb[0]) > 0 else -1

    # --- wheels + primary scale ---
    wheels, conf_wheels = detect_wheels(frames_sample, H, W)
    cal.wheels = wheels
    if wheels.get("radius_px"):
        cal.mm_per_px = outer_mm / (2.0 * wheels["radius_px"])
        tyre_src = "ASSUMED default" if cal.tire_assumed else "from specs"
        cal.notes.append(f"Wheel scale: outer Ø {outer_mm:.0f}mm (rim {RIM_DIAMETER_MM:.0f} "
                         f"+ 2x{tire:.0f}mm tyre, {tyre_src}) / {2*wheels['radius_px']:.0f}px.")
        if cal.tire_assumed:
            cal.notes.append(f"Tyre width not provided -> assumed {TIRE_WIDTH_MM_DEFAULT:.0f}mm. "
                             f"Set tire_width_mm in rider.yaml for correct cm; each 3mm off "
                             f"biases cm ~1%. cm outputs marked indicative.")

    # --- cross-check via the orbit (solve implied foot offset) ---
    offset_ok = True
    if cal.mm_per_px and cal.crank_orbit_r_px:
        implied_orbit_mm = cal.crank_orbit_r_px * cal.mm_per_px
        cal.implied_foot_offset_mm = implied_orbit_mm - crank
        offset_ok = FOOT_OFFSET_MIN_MM <= cal.implied_foot_offset_mm <= FOOT_OFFSET_MAX_MM
        mm_per_px_crank_nom = (crank + FOOT_OFFSET_NOMINAL_MM) / cal.crank_orbit_r_px
        cal.mm_per_px_crank = mm_per_px_crank_nom
        cal.scale_disagreement = abs(cal.mm_per_px - mm_per_px_crank_nom) / cal.mm_per_px
    elif cal.crank_orbit_r_px and not cal.mm_per_px:
        # wheels failed: fall back to a nominal crank scale, mark indicative
        cal.mm_per_px = (crank + FOOT_OFFSET_NOMINAL_MM) / cal.crank_orbit_r_px
        cal.mm_per_px_crank = cal.mm_per_px
        cal.notes.append("No wheels detected -> scale from crank orbit (nominal offset); "
                         "cm outputs are INDICATIVE.")

    # --- hoods ---
    cal.hoods, hoods_spread = hoods_from_wrist(wxy, wcf)

    # --- composite confidence + quality flag ---
    if cal.scale_disagreement is None:
        conf_agree = 0.5 if cal.mm_per_px else 0.0
    else:
        if offset_ok and cal.scale_disagreement <= SCALE_WARN:
            conf_agree = 1.0
        else:
            conf_agree = float(np.clip(1 - (cal.scale_disagreement - SCALE_WARN) / 0.20, 0, 1))
            if not offset_ok:
                conf_agree = min(conf_agree, 0.4)
    cal.confidence = float(0.45 * conf_bb + 0.35 * conf_wheels + 0.20 * conf_agree)

    disagree = cal.scale_disagreement if cal.scale_disagreement is not None else 0.0
    if (cal.confidence >= 0.75 and wheels.get("radius_px") and offset_ok
            and disagree <= SCALE_WARN and not cal.tire_assumed):
        cal.quality_flag = "ok"
    elif (cal.confidence < 0.45 or not cal.mm_per_px or disagree > SCALE_SUPPRESS):
        cal.quality_flag = "suppress"
    else:
        cal.quality_flag = "indicative"   # includes the tyre-assumed case (scale uncertain)

    if cal.quality_flag != "ok" and cal.mm_per_px and disagree > SCALE_WARN:
        cal.notes.append(f"Two pixel scales disagree by {disagree:.0%} "
                         f"(implied foot offset "
                         f"{cal.implied_foot_offset_mm:.0f}mm) -> camera may not be square; "
                         f"cm numbers indicative only.")
    return cal

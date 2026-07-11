"""
analyze_bikefit.py -- AI bike-fit analyzer (skeleton overlay, colored by research)

A fork of analyze_swing.py for cycling fit. Same stack: YOLO11 pose (joints) +
OpenCV/supervision (drawing). Point a SIDE-ON trainer clip at it and it:

  1. Tracks the near-side leg/arm/torso every frame.
  2. Finds bottom-dead-center (BDC = crank at 6 o'clock = knee most extended)
     and measures the fit angles there (knee, torso, elbow, shoulder, hip).
  3. Colors each measured joint GREEN / AMBER / RED against research-backed
     ranges (see ANGLE_TARGETS), so a bad fit lights up red and a dialed fit
     goes green across the board.
  4. Renders the colored-skeleton overlay for the whole clip, saves the BDC
     still (+ a few frames) for the edit, and writes findings + the exact
     adjustment ("knee 47deg -> saddle too low, raise ~10mm").

Run it on BOTH clips (film bad first, apply the fix, film good):
  python analyze_bikefit.py --input bad.mov  --out out_bad
  python analyze_bikefit.py --input good.mov --out out_good

Ranges are DYNAMIC (measured while pedaling on video), which run ~8deg higher
than the old static Holmes numbers -- sources in the repo notes.
"""

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

try:
    import supervision as sv
    _HAS_SV = True
except Exception:  # supervision only needed for streaming frames; fall back to cv2
    _HAS_SV = False

KP = {
    "nose": 0, "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7,
    "right_elbow": 8, "left_wrist": 9, "right_wrist": 10, "left_hip": 11,
    "right_hip": 12, "left_knee": 13, "right_knee": 14, "left_ankle": 15,
    "right_ankle": 16,
}

# Research-backed DYNAMIC road ranges. (green_lo, green_hi, amber_pad).
# Outside green +/- amber_pad = RED. See repo notes for citations.
ANGLE_TARGETS = {
    "knee_flexion_bdc": (30.0, 40.0, 5.0),   # >40 saddle low, <30 saddle high
    "torso_from_horiz": (40.0, 50.0, 6.0),   # >56 too upright, <34 too aggressive
    "elbow_flexion":    (15.0, 30.0, 8.0),   # ~0 = locked out
    "shoulder_angle":   (80.0, 95.0, 10.0),
    "hip_angle_top":    (85.0, 110.0, 999.0),  # report only (amber_pad huge = never red)
}

# BGR
GREEN = (90, 210, 90)
AMBER = (40, 190, 245)
RED = (60, 60, 240)
NEUTRAL = (210, 210, 210)
HUD = (240, 240, 240)


def preprocess(src, dst, maxdim, start=None, end=None):
    vf = (f"scale=w=min({maxdim}\\,iw):h=min({maxdim}\\,ih):"
          f"force_original_aspect_ratio=decrease:force_divisible_by=2")
    cmd = ["ffmpeg", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]          # trim to just the pedaling window
    cmd += ["-i", src]
    if end is not None:
        cmd += ["-t", str(end - (start or 0))]
    cmd += ["-vf", vf, "-an", dst]
    subprocess.run(cmd, check=True, capture_output=True)
    return dst


def frames(path):
    if _HAS_SV:
        yield from sv.get_video_frames_generator(path)
        return
    cap = cv2.VideoCapture(path)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield f
    cap.release()


def interior_angle(a, b, c):
    """Angle at b (deg) formed by a-b-c. NaN if any point missing."""
    a, b, c = np.asarray(a), np.asarray(b), np.asarray(c)
    if not (np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(c).all()):
        return np.nan
    ba, bc = a - b, c - b
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n == 0:
        return np.nan
    cosv = np.clip(np.dot(ba, bc) / n, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosv)))


def angle_from_horizontal(p_top, p_bot):
    """Angle of the line p_top->p_bot vs the horizontal, 0-90."""
    v = np.asarray(p_bot) - np.asarray(p_top)
    if not np.isfinite(v).all() or np.allclose(v, 0):
        return np.nan
    return float(abs(np.degrees(np.arctan2(abs(v[1]), abs(v[0])))))


# Monocular pose on a phone clip resolves joint angles to ~+/-2-3 deg, so a hard
# band edge is false precision: 78 and 80 are the same measurement. Treat readings
# within this tolerance of the green band as in-range (applied to EVERY angle, and
# far too small to rescue anything genuinely off -- a red is red by many degrees).
GREEN_TOL = 2.5


def verdict(name, val):
    """green | amber | red | na for an angle vs its target band."""
    if val is None or not np.isfinite(val):
        return "na"
    lo, hi, pad = ANGLE_TARGETS[name]
    if lo - GREEN_TOL <= val <= hi + GREEN_TOL:
        return "green"
    if lo - pad <= val <= hi + pad:
        return "amber"
    return "red"


COLOR = {"green": GREEN, "amber": AMBER, "red": RED, "na": NEUTRAL}


def pick_side(pts, cof):
    """Choose the near (camera-facing) side = the one with higher mean joint
    confidence across the clip. Returns 'left' or 'right'."""
    def m(side):
        idx = [KP[f"{side}_{j}"] for j in ("shoulder", "hip", "knee", "ankle", "elbow", "wrist")]
        return np.nanmean(cof[:, idx])
    return "left" if m("left") >= m("right") else "right"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="out_bike")
    # x-pose (largest) by default: the nano model can't localize the knee/ankle
    # under pedaling motion blur, which wrecks the BDC knee angle. x is accurate and
    # fast on GPU (auto-downloads on first run, ~113MB). Pass --model yolo11n-pose.pt
    # to trade accuracy for speed on a CPU-only machine.
    ap.add_argument("--model", default="yolo11x-pose.pt")
    ap.add_argument("--maxdim", type=int, default=1280)
    ap.add_argument("--conf", type=float, default=0.30)
    ap.add_argument("--device", default=None)
    ap.add_argument("--start", type=float, default=None, help="trim: seconds to start (skip mount)")
    ap.add_argument("--end", type=float, default=None, help="trim: seconds to end (skip dismount)")
    ap.add_argument("--override", default="", help=(
        "force a joint's color, e.g. 'knee_flexion_bdc=amber'. Use when the clip was "
        "reshot after a known change so it reflects the rider's real prior setup. "
        "Recorded in the report as a manual override, not a measurement."))
    args = ap.parse_args()

    out = Path(args.out)
    (out / "stills").mkdir(parents=True, exist_ok=True)
    work = str(out / "_work.mp4")
    preprocess(args.input, work, args.maxdim, args.start, args.end)

    pose = YOLO(args.model)

    # ---- Pass 1: joints per frame ----
    xy_list, cf_list = [], []
    for frame in frames(work):
        r = pose(frame, conf=args.conf, verbose=False, device=args.device)[0]
        fxy = np.full((17, 2), np.nan, np.float32)
        fcf = np.zeros(17, np.float32)
        if r.keypoints is not None and r.keypoints.xy is not None and len(r.keypoints) > 0:
            conf = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else None
            xy = r.keypoints.xy.cpu().numpy()
            b = 0 if conf is None else int(np.argmax(conf.mean(axis=1)))  # main rider
            fxy = xy[b]
            if conf is not None:
                fcf = conf[b]
        xy_list.append(fxy)
        cf_list.append(fcf)
    pts = np.stack(xy_list)
    cof = np.stack(cf_list)
    N = len(pts)
    side = pick_side(pts, cof)

    def P(joint, i):
        return pts[i, KP[f"{side}_{joint}"]]

    # ---- Locate the actual pedal stroke, then bottom-dead-center ----
    # Naively taking the single max-knee-extension frame breaks on real clips:
    # while mounting/standing over the bike the leg goes dead straight (~180deg
    # interior), beating every genuine pedal stroke. So first mask to frames where
    # the rider is truly in a side-on riding pose and pedaling, then find BDC there
    # and report the MEDIAN across the bottom band (robust to one bad frame).
    near = ("shoulder", "hip", "knee", "ankle")
    conf_min = np.array([min(cof[i, KP[f"{side}_{j}"]] for j in near) for i in range(N)])
    knee_int = np.array([interior_angle(P("hip", i), P("knee", i), P("ankle", i))
                         for i in range(N)])
    torso_h = np.array([angle_from_horizontal(P("shoulder", i), P("hip", i)) for i in range(N)])
    ankle_y = np.array([P("ankle", i)[1] for i in range(N)])  # y grows downward on screen

    riding = (
        (conf_min >= 0.5)
        & np.isfinite(knee_int) & (knee_int >= 80) & (knee_int <= 168)  # exclude dead-straight standing leg
        & np.isfinite(torso_h) & (torso_h >= 15) & (torso_h <= 70)      # real riding lean, not bent over the bars
    )
    if riding.sum() < 10:  # clip too short/odd -> fall back to any finite leg frame
        riding = np.isfinite(knee_int)
        if not riding.any():
            raise SystemExit("No rider/leg detected. Need a clean side-on clip.")

    # Pedaling vs standing: while pedaling the foot oscillates up/down every stroke;
    # standing next to the bike (or mount/dismount) has almost no oscillation. Crucial
    # because a foot on the FLOOR sits lower than it ever does at BDC, so a standing
    # frame otherwise wins the "lowest foot" test and gets measured as a "dialed fit".
    fps_guess = float(sv.VideoInfo.from_video_path(work).fps) if _HAS_SV else 30.0
    win = max(15, int(round(fps_guess)))  # ~1s window
    ay = ankle_y.astype(float).copy()
    fin = np.isfinite(ay)
    if fin.sum() >= 2:  # interpolate gaps so the rolling window is continuous
        ay = np.interp(np.arange(N), np.where(fin)[0], ay[fin])
    roll_std = np.array([ay[max(0, i - win // 2):min(N, i + win // 2 + 1)].std() for i in range(N)])
    ref = np.percentile(roll_std, 90) if roll_std.size else 0.0  # p90, robust to a dismount spike
    pedaling = roll_std >= 0.30 * ref if ref > 0 else np.ones(N, bool)

    ride = riding & pedaling
    if ride.sum() < 10:  # oscillation gate too aggressive (very short clip) -> relax it
        ride = riding

    # Drop the first/last ~1s: transitions and settling blur live at the edges.
    base = ride.copy()
    if base.sum() > 4 * win:
        base[:win] = False
        base[-win:] = False

    # True BDC = foot lowest AND leg most extended AT ONCE, with confident keypoints.
    # Either signal alone is fooled by motion blur (a blurred mid-stroke foot can read
    # low; a mistracked leg can read straight), but they only coincide at the real
    # bottom of the stroke. Intersect the top bands of both, require good confidence.
    ay_v = np.where(base, ankle_y, np.nan)
    ki_v = np.where(base, knee_int, np.nan)
    foot_low = base & (ankle_y >= np.nanpercentile(ay_v, 70))
    leg_ext = base & (knee_int >= np.nanpercentile(ki_v, 70))
    bottom = foot_low & leg_ext & (conf_min >= 0.6)
    if bottom.sum() < 3:  # relax step by step for short/low-conf clips
        bottom = (foot_low & leg_ext) if (foot_low & leg_ext).sum() >= 3 else leg_ext
    if bottom.sum() < 3:
        bottom = base & np.isfinite(knee_int)
    cand = np.where(bottom)[0]
    # Representative BDC frame (for the still + chips) = closest to the band median,
    # NOT an extreme, so one blurred outlier can't become the hero still.
    med_ki = float(np.nanmedian(knee_int[cand]))
    bdc = int(cand[np.argmin(np.abs(knee_int[cand] - med_ki))])
    n_riding, n_bottom = int(ride.sum()), int(len(cand))

    # ---- Measure the fit angles (knee, torso, elbow, shoulder, hip) ----
    def measure(i):
        knee = interior_angle(P("hip", i), P("knee", i), P("ankle", i))
        elbow_int = interior_angle(P("shoulder", i), P("elbow", i), P("wrist", i))
        return {
            # knee flexion = how bent the knee still is at the bottom (180 - interior)
            "knee_flexion_bdc": (180.0 - knee) if np.isfinite(knee) else np.nan,
            "torso_from_horiz": angle_from_horizontal(P("shoulder", i), P("hip", i)),
            "elbow_flexion": (180.0 - elbow_int) if np.isfinite(elbow_int) else np.nan,
            "shoulder_angle": interior_angle(P("hip", i), P("shoulder", i), P("elbow", i)),
            "hip_angle_top": interior_angle(P("shoulder", i), P("hip", i), P("knee", i)),
        }

    # Median across the bottom band so a single mistracked frame can't skew the fit.
    _per = [measure(i) for i in cand]
    ang = {k: float(np.nanmedian([p[k] for p in _per])) if np.any(np.isfinite([p[k] for p in _per]))
           else np.nan for k in _per[0]}
    verdicts = {k: verdict(k, v) for k, v in ang.items()}

    # Manual color override (--override knee_flexion_bdc=amber). For when a clip was
    # reshot after a known adjustment and should show the rider's real prior state.
    # Tracked separately so the report is transparent about what was measured vs set.
    overrides = {}
    for tok in args.override.split(","):
        tok = tok.strip()
        if "=" in tok:
            k, val = (x.strip().lower() for x in tok.split("=", 1))
            if k in verdicts and val in COLOR:
                overrides[k] = val
                verdicts[k] = val

    # Adjustment logic for the money angles.
    fixes = []
    kf = ang["knee_flexion_bdc"]
    if np.isfinite(kf):
        if kf > 42:
            fixes.append(f"Knee {kf:.0f}deg at bottom (target 30-40) -> saddle TOO LOW. Raise saddle ~{min(20, (kf-40)*2):.0f}mm.")
        elif kf < 28:
            fixes.append(f"Knee {kf:.0f}deg at bottom (target 30-40) -> saddle TOO HIGH. Lower saddle ~{min(20,(30-kf)*2):.0f}mm.")
    tz = ang["torso_from_horiz"]
    if np.isfinite(tz):
        if tz > 56:
            fixes.append(f"Torso {tz:.0f}deg from horizontal (target 40-50) -> too upright. Longer/lower reach.")
        elif tz < 34:
            fixes.append(f"Torso {tz:.0f}deg (target 40-50) -> very aggressive. Shorten reach or raise bars if uncomfortable.")
    eb = ang["elbow_flexion"]
    if np.isfinite(eb) and eb < 8:
        fixes.append(f"Elbows locked ({eb:.0f}deg bend) -> soften elbows / reach may be too long.")
    if not fixes:
        fixes.append("All key angles in range. Dialed fit.")

    # Hip angle is report-only (flexibility-dependent, huge amber_pad), so it doesn't
    # gate the overall verdict -- only the true fit angles do.
    graded = {k: v for k, v in verdicts.items() if ANGLE_TARGETS[k][2] < 900}
    overall = "GREEN - dialed" if all(v in ("green", "na") for v in graded.values()) \
        else ("RED - fix needed" if "red" in graded.values() else "AMBER - close")

    # ---- Pass 2: colored-skeleton overlay for the whole clip ----
    # Segments defining each measured angle, colored by that joint's verdict.
    def seg_color(name):
        return COLOR[verdicts.get(name, "na")]

    def worst(*names):  # red beats amber beats green -> the arm is only as good as its worst joint
        rank = {"red": 3, "amber": 2, "green": 1, "na": 0}
        return max((verdicts.get(n, "na") for n in names), key=lambda v: rank[v])

    def draw_frame(frame, i):
        s = frame.copy()
        def pt(j):
            p = P(j, i)
            return None if not np.isfinite(p).all() else tuple(p.astype(int))
        # Color the whole arm by the WORST of shoulder + elbow so a closed cockpit
        # (bad shoulder angle) actually lights the arm red, not just a small dot.
        arm_c = COLOR[worst("shoulder_angle", "elbow_flexion")]
        segs = [
            (pt("hip"), pt("knee"), seg_color("knee_flexion_bdc")),
            (pt("knee"), pt("ankle"), seg_color("knee_flexion_bdc")),
            (pt("shoulder"), pt("hip"), seg_color("torso_from_horiz")),
            (pt("shoulder"), pt("elbow"), arm_c),
            (pt("elbow"), pt("wrist"), arm_c),
        ]
        for a, b, c in segs:
            if a and b:
                cv2.line(s, a, b, (0, 0, 0), 8, cv2.LINE_AA)
                cv2.line(s, a, b, c, 4, cv2.LINE_AA)
        # joint dots
        for j, name in (("knee", "knee_flexion_bdc"), ("shoulder", "shoulder_angle"),
                        ("elbow", "elbow_flexion"), ("hip", "torso_from_horiz")):
            p = pt(j)
            if p:
                cv2.circle(s, p, 7, (0, 0, 0), -1, cv2.LINE_AA)
                cv2.circle(s, p, 5, COLOR[verdicts.get(name, "na")], -1, cv2.LINE_AA)
        # HUD
        h, w = s.shape[:2]
        bar = s.copy()
        cv2.rectangle(bar, (0, 0), (w, 34), (0, 0, 0), -1)
        cv2.addWeighted(bar, 0.5, s, 0.5, 0, s)
        cv2.putText(s, "ATHLETE AI  BIKE FIT", (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD, 1, cv2.LINE_AA)
        # angle chips at BDC (and near it) so numbers are readable in the edit
        if abs(i - bdc) < max(2, N // 40):
            lines = [
                (f"KNEE {ang['knee_flexion_bdc']:.0f}", verdicts['knee_flexion_bdc']),
                (f"TORSO {ang['torso_from_horiz']:.0f}", verdicts['torso_from_horiz']),
                (f"SHOULDER {ang['shoulder_angle']:.0f}", verdicts['shoulder_angle']),
                (f"ELBOW {ang['elbow_flexion']:.0f}", verdicts['elbow_flexion']),
            ]
            y = 60
            for txt, v in lines:
                cv2.putText(s, txt, (10, y), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(s, txt, (10, y), cv2.FONT_HERSHEY_DUPLEX, 0.7, COLOR[v], 2, cv2.LINE_AA)
                y += 30
        return s

    overlay_path = str(out / "overlay.mp4")
    info = sv.VideoInfo.from_video_path(work) if _HAS_SV else None
    writer = None
    for i, frame in enumerate(frames(work)):
        s = draw_frame(frame, i)
        if writer is None:
            fps = info.fps if info else 30
            writer = cv2.VideoWriter(overlay_path, cv2.VideoWriter_fourcc(*"mp4v"),
                                     fps, (s.shape[1], s.shape[0]))
        writer.write(s)
        if i == bdc or i in (0, N // 2, N - 1):
            cv2.imwrite(str(out / "stills" / f"frame_{i:04d}{'_BDC' if i == bdc else ''}.jpg"), s)
    if writer:
        writer.release()

    # OpenCV writes mp4v, which Windows Photos / QuickTime often won't play.
    # Re-encode to H.264 + yuv420p so the overlay plays everywhere.
    playable = str(out / "overlay_h264.mp4")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", overlay_path, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        "-preset", "veryfast", playable],
                       check=True, capture_output=True)
    except Exception as e:
        playable = overlay_path  # ffmpeg missing -> fall back to the mp4v file
        print(f"[warn] H.264 re-encode failed ({e}); play {overlay_path}")

    report = {
        "input": args.input, "side_measured": side, "bdc_frame": bdc,
        "riding_frames": n_riding, "bottom_band_frames": n_bottom,
        "overall": overall, "angles": {k: (round(v, 1) if np.isfinite(v) else None) for k, v in ang.items()},
        "verdicts": verdicts, "fixes": fixes,
        "manual_overrides": overrides,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2))
    md = ["# Bike fit report", f"- Input: `{args.input}` (measured {side} side, BDC frame {bdc})",
          f"- Overall: **{overall}**", "", "## Angles (deg) vs target"]
    for k, v in ang.items():
        lo, hi, _ = ANGLE_TARGETS[k]
        val = f"{v:.0f}" if np.isfinite(v) else "n/a"
        md.append(f"- {k}: **{val}** (target {lo:.0f}-{hi:.0f}) -> {verdicts[k].upper()}")
    md += ["", "## Do this"] + [f"- {f}" for f in fixes]
    (out / "report.md").write_text("\n".join(md))
    print("\n".join(md))
    print(f"\n[done] overlay (play this): {playable}  |  stills: {out/'stills'}")


if __name__ == "__main__":
    main()

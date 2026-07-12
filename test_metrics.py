"""
test_metrics.py -- fast, dependency-light checks for the geometry in bike_calib.py
and fit_metrics.py. Pure math on synthetic data (no video, no YOLO), so it runs in
under a second: `uv run python test_metrics.py`.

These guard the parts most likely to break silently: the circle fit, the crank-phase
clock, and the KOPS sign convention (which must be independent of which way the bike
faces). Run before committing changes to either module.
"""
import numpy as np
import bike_calib as bc
import fit_metrics as fm


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    assert cond, f"FAILED: {name}"


def test_circle_fit():
    print("circle fit:")
    cx0, cy0, r0 = 500.0, 800.0, 210.0
    th = np.linspace(0, 2 * np.pi, 60)
    P = np.column_stack([cx0 + r0 * np.cos(th), cy0 + r0 * np.sin(th)])
    cx, cy, r = bc.fit_circle_kasa(P)
    check("Kasa recovers a clean circle", abs(cx - cx0) < 1 and abs(cy - cy0) < 1 and abs(r - r0) < 1)

    noisy = P + np.random.default_rng(0).normal(0, 1.5, P.shape)
    noisy = np.vstack([noisy, [[100, 100], [900, 200], [500, 50]]])  # 3 wild outliers
    res = bc.fit_bb_orbit(noisy, frame_diag=2000.0)
    check("RANSAC BB survives outliers", res is not None and abs(res[0] - cx0) < 6 and abs(res[1] - cy0) < 6)

    # A noisy, non-circular cloud must NOT yield a confident fit (coverage/rms guard).
    blob = np.random.default_rng(1).normal(500, 40, (80, 2))
    res2 = bc.fit_bb_orbit(blob, frame_diag=2000.0)
    ok = res2 is None or res2[4]["radial_rms_norm"] > 0.15
    check("random blob is refused or flagged high-rms", ok)


def test_tyre_scale():
    print("tyre-aware scale:")
    check("25mm -> 672", bc.wheel_outer_mm(25) == 672)
    check("28mm -> 678", bc.wheel_outer_mm(28) == 678)
    check("32mm -> 686", bc.wheel_outer_mm(32) == 686)


def test_crank_theta():
    print("crank phase clock:")
    bb = (500.0, 800.0)
    ank = np.array([[500 + 210, 800], [500, 800 + 210], [500, 800 - 210]])  # 3 o'clock, BDC, TDC
    th = np.degrees(fm.crank_theta(ank, bb, 1))
    check("3 o'clock ~ 0deg", abs(th[0]) < 1)
    check("BDC ~ -90deg", abs(th[1] + 90) < 1)
    check("TDC ~ +90deg", abs(th[2] - 90) < 1)


def _kops_case(facing):
    """Knee 30px AHEAD of the spindle at 3 o'clock -> KOPS must be positive, for
    EITHER facing direction."""
    class C:
        pass
    cal = C()
    cal.bb = (500.0, 800.0)
    cal.mm_per_px = 0.5
    cal.crank_orbit_r_px = 210.0
    cal.facing = facing
    N = 20
    pts = np.full((N, 17, 2), np.nan, np.float32)
    cof = np.zeros((N, 17), np.float32)
    spindle_x = 500 + facing * 210
    for i in range(N):
        pts[i, 16] = [spindle_x, 800]              # ankle at 3 o'clock (front, level)
        pts[i, 14] = [spindle_x + facing * 30, 780]  # knee 30px further forward = ahead
        cof[i, 14] = 0.9
        cof[i, 16] = 0.9
    ride = np.ones(N, bool)
    return fm.kops(pts, cof, "right", ride, {"right_knee": 14, "right_ankle": 16}, cal)


def test_kops_sign():
    print("KOPS sign (facing-independent):")
    a = _kops_case(+1)
    b = _kops_case(-1)
    check("facing +1: knee ahead -> +15mm", a["kops_mm"] is not None and 10 < a["kops_mm"] < 20)
    check("facing -1: knee ahead -> +15mm (same sign)", b["kops_mm"] is not None and 10 < b["kops_mm"] < 20)


def test_ankle_refused():
    print("ankle angle honesty:")
    a = fm.ankle_angle()
    check("ankle angle is refused, not faked", a.get("available") is False and "reason" in a)


if __name__ == "__main__":
    test_circle_fit()
    test_tyre_scale()
    test_crank_theta()
    test_kops_sign()
    test_ankle_refused()
    print("\nALL TESTS PASSED")

# Bike-fit angle ranges (the research behind the colors)

These are the DYNAMIC road-cycling ranges `analyze_bikefit.py` colors against
(green = in range, amber = borderline, red = out). Dynamic = measured while
pedaling on video, which runs ~8deg higher than the old static Holmes numbers.

| Angle (side-on) | Green zone | Red means -> fix |
|---|---|---|
| Knee flexion at BDC | 30-40 deg (33-43 easy / 30-40 hard) | >42 saddle too low (raise); <28 too high (lower) |
| Torso from horizontal | 40-50 deg | >56 too upright (longer/lower reach); <34 too aggressive |
| Elbow flexion | 15-30 deg (avg 19+/-8) | ~0 = locked out (soften / shorten reach) |
| Shoulder angle | ~80-95 deg (90 on hoods) | reach too long/short |
| Hip angle (top) | ~85-110 deg (report only, softer) | flexibility / reach |

## Sources
- Knee 30-40 deg dynamic at BDC + static-vs-dynamic ~8deg gap: methodology/validity study, https://pubmed.ncbi.nlm.nih.gov/24499342/
- Holmes 25-35 deg static + joint kinematic averages (knee 36+/-7, elbow 19+/-8): https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
- Full joint-angle set (torso 45-50, shoulder ~90, hip, elbow) + TDC knee ~65deg / crank-too-long tell: https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles

## Extra metrics (report-only) — sources
These back the KOPS / knee-ROM / pelvic-rock / bar-drop numbers in `fit_metrics.py`.
They're report-only for a reason: the evidence base is weaker/looser than the core
angles, so the tool informs rather than grades on them.
- **KOPS is a coincidental proxy, not biomechanics:** https://www.sheldonbrown.com/kops.html · https://theriderproject.co.uk/2017/11/02/the-myth-of-the-myth-of-kops/ · https://www.stt-systems.com/blog/kops-bike-fitting-performance-comfort-injury-prevention/
- **Saddle fore/aft barely changes patellofemoral load (the anterior-knee-pain tension):** Bini & Hume 2012, PF compression 1-4%, TF shear +19-26% *backward* — https://pubmed.ncbi.nlm.nih.gov/23312729/ · Menard et al. 2018, TF compression 14-15% higher *backward*, forward NOT associated with higher PF force — https://pubmed.ncbi.nlm.nih.gov/29920153/
- **High saddle → pelvic rock; true (lateral) rock needs a rear view:** https://bikedynamics.co.uk/saddlepain.htm · https://www.meld3d.com/blog/A-Tale-of-Pelvic-Asymmetry-in-Cycling · trochanteric-height comfort window 97-103%: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10790431/
- **Handlebar drop norms (endurance ~2.5-5 cm; population spread 5-17 cm, weak height correlation):** https://www.roadbikerider.com/whats-the-correct-handlebar-saddle-relationship-d1/ · https://www.cyclingweekly.com/fitness/bike-fit/just-how-important-is-saddle-setback-plus-how-to-tell-if-yours-is-too-far-forwards-or-backwards

_Note: full-text force magnitudes (Newtons) from Bini/Menard would need library/DOI
access; the above are the open PubMed abstracts + fitting literature. All bands stay
honest about the monocular ±2-3 deg and the px→mm scale error._

## Measurement tolerance
Monocular pose on a phone clip resolves joint angles to roughly +/-2-3 deg, so the
tool treats a reading within 2.5 deg of the green band as in-range (green). This is
honest precision, not goalpost-moving: it applies to every angle and is far too
small to change a genuine fault (a red is red by many degrees). The soft bike-fit
literature bands (e.g. shoulder ~80-95 with a "~") already imply this.

## On-camera note
Demo the research with Claude Research ("I made Claude read the actual bike-fit
literature"), but the tool ships with these numbers hard-coded so the colors are
identical + defensible every run. Say "great starting point, not a replacement
for a pro fit" -- a 2D side photo is population ranges, not a 3D mocap fit.

## Note: these are ROAD ranges
Tri/TT setups run a lower, more aggressive torso and slightly different hip/knee.
If the first post is on a road/trainer setup, these apply. Add a TT profile later
if needed.

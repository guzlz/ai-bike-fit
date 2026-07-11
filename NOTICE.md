# Third-party notices

AI Bike Fit is licensed under **AGPL-3.0** (see [`LICENSE`](LICENSE)).

This repository contains only its own source code, documentation, and
configuration. It does **not** redistribute any third-party library or any model
weights — those are downloaded to the end user's machine at install/run time by
`pip` / `uv` and by the Ultralytics API. The licenses below apply to those
components as obtained from their official sources.

| Component | Role | License | Source |
|---|---|---|---|
| Ultralytics YOLO11 (`ultralytics`) + `yolo11x-pose.pt` weights | Pose estimation model | **AGPL-3.0** | https://github.com/ultralytics/ultralytics · https://www.ultralytics.com/license |
| supervision (Roboflow) | Frame streaming + annotation | MIT | https://github.com/roboflow/supervision |
| OpenCV (`opencv-python`) | Image handling | Apache-2.0 (library) / MIT (wheel scripts) | https://github.com/opencv/opencv-python |
| NumPy | Array math | BSD-3-Clause | https://github.com/numpy/numpy |
| PyTorch (`torch`, `torchvision`) | Model runtime | BSD-3-Clause | https://github.com/pytorch/pytorch |
| FFmpeg | Video decode/re-encode (called as an external binary via `subprocess`) | LGPL/GPL depending on build | https://ffmpeg.org |

## Why this project is AGPL-3.0

`analyze_bikefit.py` imports the Ultralytics library directly
(`from ultralytics import YOLO`). Under the GPL/AGPL, a direct import forms a
*combined work*, so the AGPL-3.0 copyleft of Ultralytics reaches this project's
source. AGPL-3.0 is therefore the correct and required license here. Running the
tool yourself is free; embedding it in a proprietary or closed-source product
requires a commercial [Ultralytics Enterprise License](https://www.ultralytics.com/license).

FFmpeg is invoked only as a separate external process (`subprocess.run(["ffmpeg", ...])`),
which is *mere aggregation* — no linking, no bundling — so its license imposes no
obligation on this project, and this project imposes none on it.

## Research references

The angle-grading ranges in [`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md)
are factual findings drawn from published sport-science literature, restated in our
own words with links to the sources. Facts and numeric ranges are not copyrightable;
no third-party text, tables, or figures are reproduced.

*Not medical advice.* A 2D side-view analysis gives population-range guidance, not a
clinical or 3D professional fit.

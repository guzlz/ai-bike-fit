# 🚲 AI Bike Fit

**🌍 Language / Langue : 🇬🇧 English (this page) · [🇫🇷 Français](README.fr.md)**

**Grade your own road bike fit with AI — for free.**

Film yourself pedaling on a trainer, and this tool grades your bike fit like a
fitter would. It tracks your joints, measures the angles at the bottom of your
pedal stroke, and draws a colored skeleton on the video:

- 🟢 **green** = dialed
- 🟠 **orange** = borderline
- 🔴 **red** = fix it

Then it tells you the exact change, e.g. *"knee too straight, drop your saddle
about 8 mm."*

It reads the same body angles a paid fitter looks at (saddle height off your
knee, reach off your shoulder and elbow), grades them against published research
ranges, and hands you a before/after you can actually see.

---

## Two ways to use it

### 🟢 The easy way — let Claude Code do everything

You don't download anything, make folders, or write code. [Claude Code](https://claude.com/claude-code)
(the free coding agent in your terminal) does all of it.

1. Install Claude Code.
2. Clone this repo and open Claude Code inside the folder:
   `git clone https://github.com/guzlz/ai-bike-fit.git` then `cd ai-bike-fit`.
3. Just tell it, in your own words: **"analyze my bike fit"** (or "check my
   position", "j'ai mal au dos à vélo, aide-moi"…).

That's it. It **automatically** starts the guided protocol: it tells you how to
film, asks for your bike + body specs, sets everything up, runs the analysis, and
explains your results in plain language — one step at a time. You never need to
know any commands. **This is the recommended path if you're not technical.**

*(Advanced: you can type `/bikefit` to launch the same protocol explicitly, or
paste the prompt from [`PROMPT.md`](PROMPT.md) — but you don't have to.)*

### 🔧 The manual way — run it yourself

For those comfortable with a terminal.

**One-command setup** (installs uv, all dependencies, and ffmpeg for you):

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit
# Windows:
powershell -ExecutionPolicy Bypass -File setup.ps1
# macOS / Linux:
bash setup.sh
```

**Then — where do I put my video?** Drop your clip into the **`videos/` folder** in
the project, give it a simple name (e.g. `my-ride.mp4`), and point `--input` at it:

```bash
uv run python analyze_bikefit.py --input videos/my-ride.mp4 --out out_fit
```

Your videos stay on your machine — the `videos/` folder is git-ignored, so nothing
you drop there is ever pushed. Results appear in `out_fit/`. See
[`videos/README.md`](videos/README.md) for a step-by-step.

> 📐 **Film it right first.** Landscape, dead side-on, camera at hip height, 2.5–4 m
> away. A bad clip gives *wrong numbers*, not a bad fit — read
> [`files/filming-guide.md`](files/filming-guide.md) before recording. The tool now
> warns you if it can't tell your near leg from your far leg.

**Personalized advice (optional):** for saddle-height, frame-size and reach tips
tailored to you, copy [`rider.example.yaml`](rider.example.yaml) to `rider.yaml`,
fill in your height/inseam/bike, and add `--rider rider.yaml` to the command. Your
specs stay local (git-ignored). In Claude Code, just answer its questions — it fills
the file for you.

**Or set it up by hand** — two options:

**With [uv](https://docs.astral.sh/uv/) (recommended — handles Python for you):**

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit
uv sync
uv run python analyze_bikefit.py --input videos/my-ride.mp4 --out out_fit
```

**With pip:**

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit

# Install PyTorch (pick one):
pip install torch torchvision                                              # CPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128  # NVIDIA GPU

pip install -r requirements.txt
python analyze_bikefit.py --input videos/my-ride.mp4 --out out_fit
```

> **You also need [ffmpeg](https://ffmpeg.org/) on your PATH:**
> `winget install Gyan.FFmpeg` (Windows) · `brew install ffmpeg` (Mac) ·
> `apt install ffmpeg` (Linux).

The **first run downloads the pose model** (`yolo11x-pose.pt`, ~113 MB) once.
On a CPU-only machine it's slower — add `--model yolo11n-pose.pt` to trade some
accuracy for speed.

If your clip has getting-on / getting-off at the ends, trim to the pedaling window:

```bash
python analyze_bikefit.py --input videos/my-ride.mp4 --out out_fit --start 5 --end 35
```

---

## 🎥 Film it right (this is 90% of the result)

A fit tool is only as good as the clip. Ninety seconds of setup here saves you a
reshoot:

- **Side-on.** Camera directly to the side of the bike, lens straight at you,
  square to the bike. Not in front, behind, or at an angle.
- **Hip height.** Rest the phone at the height of your hip or the crank, on
  something stable. Not looking down from standing height.
- **Nothing blocking your near leg and arm.** Move the fan, water bottles,
  anything between the camera and your body.
- **A trainer is ideal** (you stay in one spot). Outside works if someone films
  you riding straight past, square to the side.
- **Pedal steady for 20–30 seconds** at an easy effort and normal cadence.
- **Good light.** Bright room or daylight → less motion blur → more accurate read.
- **Hands where you normally ride** (on the hoods for most people), the whole clip.
- **Road bike / road position.** These ranges are for a road or trainer setup.
  Tri/TT bikes sit lower and more aggressive and need different numbers.

**One tip that prevents a reshoot:** trim the clip to just the pedaling part
(cut the getting-on and getting-off), or use `--start` / `--end`.

---

## 📊 What you get

```text
out_fit/
  overlay_h264.mp4     # your whole clip with the colored skeleton (plays anywhere)
  stills/              # the bottom-of-stroke frame + a few others
  report.md            # plain-English verdict + the exact fix
  report.json          # the same, structured
```

`report.md` looks like this:

```text
# Bike fit report
- Overall: RED - fix needed

## Angles (deg) vs target
- knee_flexion_bdc: 45 (target 30-40) -> RED
- torso_from_horiz: 44 (target 40-50) -> GREEN
- elbow_flexion: 22 (target 15-30) -> GREEN
- shoulder_angle: 88 (target 80-95) -> GREEN

## Do this
- Knee 45deg at bottom (target 30-40) -> saddle TOO LOW. Raise saddle ~10mm.
```

Screenshot the before, make the change, film again, and watch the joints go green.

---

## 🎨 What the colors mean

| Angle (side-on) | Green zone | Red means |
|---|---|---|
| Knee at the bottom | 30–40° | over 42 saddle too low (raise); under 28 too high (lower) |
| Torso from horizontal | 40–50° | over 56 too upright; under 34 very aggressive |
| Elbow bend | 15–30° | near 0 locked out (soften / shorten reach) |
| Shoulder (torso to arm) | ~80–95° | closed/scrunched cockpit, weight on the hands |
| Hip at the top | ~85–110° | flexibility / reach (report only) |

Full sources and the research behind these numbers are in
[`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md).

---

## 🧠 How it works (the open-source pieces)

- **[Ultralytics YOLO11](https://github.com/ultralytics/ultralytics)** — the vision
  model. It looks at each frame and returns **17 body keypoints** (shoulders,
  elbows, wrists, hips, knees, ankles…), each with a pixel position and confidence.
  We use the **pose** variant `yolo11x-pose` (large model, for accuracy through
  pedaling blur; the weights are downloaded from Ultralytics on first run, not
  shipped in this repo). Everything after — finding the bottom of your stroke,
  turning joints into fit angles — is plain geometry. *AGPL-3.0.*
- **[supervision](https://github.com/roboflow/supervision)** by Roboflow — reading
  video frames and drawing annotations. *MIT.*
- **OpenCV** + **NumPy** for image handling and angle math, **PyTorch** to run the
  model (on your GPU if you have one), **ffmpeg** to make the overlay play anywhere.

The fit angles are graded against published sport-science ranges (Holmes method +
a dynamic-vs-static validity study). Sources in
[`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md).

---

## ⚠️ Notes and limits

- A 2D side-view video gives you **population ranges and a great starting point,
  not a 3D pro fit**. For persistent pain, numbness, or a big position change, see
  a real fitter.
- **Road ranges.** Tri/TT setups run lower and more aggressive — different profile.
- **Not medical advice.** If something hurts, change one thing at a time and stop
  if it gets worse.
- Keep the large model (`yolo11x-pose`) unless you're on a slow CPU and just want a
  rough look — the small one can't pin your knee/ankle through pedaling blur.
- **Change one thing per session** (saddle height OR reach, not both) and re-film,
  so you know what each change did.

---

## 📄 License

This project is licensed under **AGPL-3.0** — see [`LICENSE`](LICENSE). It **depends
on** Ultralytics YOLO11 (AGPL-3.0), which our code imports directly; that
combined-work relationship is why this project is AGPL-3.0. Running it yourself is
free; embedding it in a proprietary/closed product requires an
[Ultralytics Enterprise License](https://www.ultralytics.com/license). supervision
(MIT), OpenCV (Apache-2.0/MIT), NumPy and PyTorch (BSD) are permissively licensed
and installed by the user — this repo does not redistribute them or the model
weights. See [`NOTICE.md`](NOTICE.md) for the full third-party license list.

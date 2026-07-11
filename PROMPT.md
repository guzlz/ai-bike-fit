# The Claude Code prompt (the easy way)

> **Paste this into Claude Code, not a regular Claude chat.** This guide installs
> software and runs commands on your computer, which a normal chat window cannot
> do. Claude Code is the free coding agent that runs in your terminal and can
> actually do these steps for you.

You do not download anything, make any folders, or write any code. Claude Code
does all of it. Open Claude Code, paste the prompt below, send it, and it walks
you through the whole thing one step at a time. The only thing you provide is your
video.

---

```text
I want to grade my own road bike fit from a phone video, and I'm starting from
scratch. I don't want to download anything, create folders, or write code myself.
You do all of it. Walk me through it one step at a time in plain English, and stop
and wait for me whenever you need something.

The goal: I'll give you a short SIDE-ON video of me pedaling on my bike (on a
trainer). You measure my body angles at the bottom of the pedal stroke, tell me
what's dialed and what to change (mainly saddle height and reach), and draw a
colored skeleton on the video so I can see it: green = good, orange = borderline,
red = fix.

Here is everything I need you to do, end to end. Do it all yourself:

1. Make a folder (something like "bike-fit") and work inside it. I shouldn't have
   to create it myself.
2. Check whether I already have Python; if not, help me install it. Then install
   the exact open-source libraries this is built on, and read their current docs
   before you write code so you use the right API:
   - ultralytics (the YOLO11 pose model that finds my body joints) -
     https://github.com/ultralytics/ultralytics, docs at https://docs.ultralytics.com.
     Note it is AGPL-3.0 licensed. Install with: pip install ultralytics
   - supervision by Roboflow (helper for reading video frames and drawing) -
     https://github.com/roboflow/supervision. MIT licensed. pip install supervision
   - opencv-python and numpy for the image handling and math.
   Install PyTorch too: if I have an NVIDIA GPU use the CUDA build, otherwise the
   normal CPU build is fine (a short clip runs on CPU, just slower). Make sure
   ffmpeg is available.
3. Build a bike-fit analyzer script. It should:
   - Read a SIDE-ON video and run YOLO11x-pose on each frame (load it with
     YOLO('yolo11x-pose.pt') from ultralytics - use the large 'x' model, because
     the small one can't find the joints accurately through pedaling motion blur).
     For each frame it returns 17 body keypoints per person in COCO order
     (shoulders, elbows, wrists, hips, knees, ankles, etc.), each with an x,y
     pixel position and a confidence. Pick the highest-confidence person, take my
     near-side (camera-side) shoulder, elbow, wrist, hip, knee and ankle, and
     ignore low-confidence points. Angles are just geometry on those points (the
     knee angle is the angle between the hip->knee and ankle->knee lines).
   - Find bottom-dead-center (BDC = the bottom of the pedal stroke, where the
     knee is most extended), but ONLY during real pedaling - ignore me mounting,
     standing next to the bike, or coasting. Measure the median across several
     strokes so one blurry frame can't skew the result.
   - Measure these angles at BDC and grade each green / amber / red against these
     research-backed dynamic road ranges (allow a ~2.5 degree tolerance at the
     edges, since a phone video only resolves to a few degrees):
       - Knee flexion at the bottom: green 30-40 deg. Over ~42 = saddle too low
         (raise it); under ~28 = saddle too high (lower it).
       - Torso from horizontal: green 40-50 deg.
       - Elbow bend: green 15-30 deg.
       - Shoulder angle (torso to upper arm): green ~80-95 deg. Much lower means
         a closed, scrunched cockpit (reach too short or too much weight on the
         hands).
       - Hip angle at the top: ~85-110 deg (report only, flexibility dependent).
   - These ranges are grounded in the bike-fit literature, not made up. Ground your
     grading in these sources, and read them if you can so the numbers are current:
       - The Holmes method (the clinical standard for the knee angle at the bottom
         of the stroke), and joint-angle averages (knee 36 +/- 7 deg, elbow 19 +/- 8
         deg): https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
       - A dynamic-vs-static validity study showing angles measured while pedaling
         on video run ~8 deg higher than static goniometer numbers (this is why the
         knee zone is a dynamic 30-40, not the static 25-35):
         https://pubmed.ncbi.nlm.nih.gov/24499342/
       - Practitioner cross-check for the full joint set (torso, shoulder, hip):
         https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
   - Draw the colored skeleton on the whole clip, coloring the arm by the worse
     of shoulder/elbow so a closed cockpit actually shows. Save the BDC still.
   - Write a short report with the exact fix, e.g. "knee 45 deg at the bottom ->
     saddle too low, raise ~10mm."
   - Re-encode the overlay to H.264 so it plays on any phone or computer.
4. Ask me for my video file when you're ready. Run it, show me the overlay and the
   report, and explain my results in plain English - what's dialed and what to
   change first.

Go one step at a time. Don't dump everything at once, and don't make me touch any
files or code myself. When you need me to approve a command, just ask and I'll say
yes.
```

---

## Already cloned this repo?

If you've already got these files locally, you don't need the build-from-scratch
prompt above — the analyzer is already written. Just tell Claude Code:

```text
This repo is an AI bike-fit tool. Set it up for me (install dependencies with uv or
pip, and ffmpeg if it's missing), then run analyze_bikefit.py on the video I'm about
to give you and explain the report in plain English.
```

Or run it yourself — see the [README](README.md#-the-manual-way--run-it-yourself).

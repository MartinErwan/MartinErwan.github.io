# Animations

Source of the explainer animations on
[`projets/thales.html`](../../projets/thales.html), written with
[Manim Community Edition](https://www.manim.community/).

| Scene | What it shows | Used as |
|---|---|---|
| `TravelingWaveTube` | The full explainer: the tube, the electron beam and its focusing, why the helix slows the wave down, bunching and exponential gain | `assets/twt/twt-explainer.mp4` |
| `ElectronGunProblem` | How gun parameters bend the beam trajectory, what interception costs, and why a learned surrogate was needed | `assets/twt/gun-problem.mp4` + `gun-problem-still.jpg` |
| `TWTLoop3D` (in `twt3d.py`) | The same figure with a real helix, seen from a camera level with the axis: the signal spirals round the beam instead of oscillating past it | `assets/twt/twt-loop-3d.gif` |
| `TWTLoop` | The labelled figure used on the page. The signal is lit along the circuit it really travels — in at one RF connector, round every turn of the helix, out at the other — so the slow-wave trick is visible rather than asserted; its amplitude is plotted in a lane of its own below. Loops exactly: the wave covers the whole wire in one loop, and six wavelengths fit on it | `assets/twt/twt-loop.gif` |

## Rendering

```bash
pip install manim                     # needs ffmpeg, cairo and pango
manim -r 1600,900 --fps 30 --format png twt.py TravelingWaveTube
```

Frames are then encoded outside Manim, which keeps the flat dark background free
of the compression ghosting that a low-bitrate encode leaves behind:

```bash
# video
ffmpeg -framerate 30 -start_number 0 -i TravelingWaveTube%04d.png \
       -vf scale=1280:720 -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p \
       -movflags +faststart -an twt-explainer.mp4

# gif — no dithering, the artwork is flat enough that it only adds noise
ffmpeg -framerate 30 -start_number 0 -i TWTLoop%04d.png \
       -vf "crop=1600:816:0:12,fps=15,scale=900:-1:flags=lanczos,split[a][b];\
            [a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=none" \
       -loop 0 raw.gif
gifsicle -O3 --lossy=25 raw.gif -o twt-loop.gif
```

## Narration

The long clip is spoken. The captions are the script, so the two can never
drift apart:

```bash
TWT_COLLECT=1 manim --dry_run twt.py TravelingWaveTube   # captions -> script.json
python narrate.py --voice /path/to/en-us-ryan-high.onnx  # -> audio/*.wav, durations.json
manim -r 1600,900 --fps 30 --format png twt.py TravelingWaveTube
python narrate.py --mix --video silent.mp4 --out narrated.mp4
```

Each caption is held for exactly as long as its clip lasts, and the render
logs the moment each one appeared (`beats.json`) so the clips land on the
right frames. Without `durations.json` the scene falls back to a reading-speed
estimate and still renders on its own.

Voice: [Piper](https://github.com/rhasspy/piper), `en_US-ryan-high`. That model
is trained on RyanSpeech, which is CC BY-NC-SA 4.0 — personal use only.

## Note on the physics

The bunching in act 4 is integrated, not drawn: every macro-particle obeys

    dv/dt = -a · E(x) · sin(k(x - v_phi·t)),   E(x) = E0 · exp(x / L_gain)

with the beam launched slightly faster than the wave, which is what makes the
bunches settle into the decelerating phase and hand their energy over. Note the
sign: the force on an electron is -eE, so the half-cycles with `sin > 0` are the
ones that *slow it down*.

In `TWTLoop` the input lead, the helix and the output lead are cut into short
pieces, and each is lit by the phase of the wave at its own arc length *along the
wire*, not at its x. That is the whole point: the signal covers 31 units of wire
to advance 8 units down the tube, so it goes round and round while barely moving
forward. The helix is drawn with a phase offset of pi so that it starts and ends
at the bottom of a turn, where the two leads come up to meet it. The helix
is drawn with a pitch-to-circumference ratio that really does give a ~4x
slow-down, so the "four times more wire" claim matches the picture on screen.

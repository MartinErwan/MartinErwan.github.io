# Animations

Source of the explainer animations on
[`projets/thales.html`](../../projets/thales.html), written with
[Manim Community Edition](https://www.manim.community/).

| Scene | What it shows | Used as |
|---|---|---|
| `TravelingWaveTube` | The full explainer: the tube, the electron beam and its focusing, why the helix slows the wave down, bunching and exponential gain | `assets/twt/twt-explainer.mp4` |
| `ElectronGunProblem` | How gun parameters bend the beam trajectory, what interception costs, and why a learned surrogate was needed | `assets/twt/gun-problem.mp4` + `gun-problem-still.jpg` |
| `TWTLoop` | The labelled figure used on the page: the wave drawn along the beam itself, a row of arrows giving the force it exerts on each electron, the magnets, and every part named. Loops exactly — one crest crosses the helix in one loop, and the helix is six wavelengths long | `assets/twt/twt-loop.gif` |

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
       -vf "crop=1600:714:0:12,fps=15,scale=900:-1:flags=lanczos,split[a][b];\
            [a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=none" \
       -loop 0 raw.gif
gifsicle -O3 --lossy=25 raw.gif -o twt-loop.gif
```

## Note on the physics

The bunching in act 4 is integrated, not drawn: every macro-particle obeys

    dv/dt = -a · E(x) · sin(k(x - v_phi·t)),   E(x) = E0 · exp(x / L_gain)

with the beam launched slightly faster than the wave, which is what makes the
bunches settle into the decelerating phase and hand their energy over. Note the
sign: the force on an electron is -eE, so the half-cycles with `sin > 0` are the
ones that *slow it down* — those are the shaded bands. The helix
is drawn with a pitch-to-circumference ratio that really does give a ~4x
slow-down, so the "four times more wire" claim matches the picture on screen.

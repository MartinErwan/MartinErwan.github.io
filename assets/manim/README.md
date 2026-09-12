# Animations

Source of the explainer animations on
[`projets/thales.html`](../../projets/thales.html), written with
[Manim Community Edition](https://www.manim.community/).

| Scene | What it shows | Used as |
|---|---|---|
| `TravelingWaveTube` | The full explainer: the tube, the electron beam and its focusing, why the helix slows the wave down, bunching and exponential gain | `assets/twt/twt-explainer.*` |
| `ElectronGunProblem` | How gun parameters bend the beam trajectory, what interception costs, and why a learned surrogate was needed | `assets/twt/gun-problem.*` |
| `TWTLoop` | A short, seamlessly looping clip of the tube in steady state | `assets/twt/twt-loop.*` |

## Rendering

```bash
pip install manim                     # needs ffmpeg, cairo and pango
manim -r 1600,900 --fps 30 --format png twt.py TravelingWaveTube
```

Frames are then encoded outside Manim, which keeps the flat dark background free
of the compression ghosting that a low-bitrate encode leaves behind:

```bash
ffmpeg -framerate 30 -start_number 0 -i TravelingWaveTube%04d.png \
       -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p \
       -movflags +faststart -an twt-explainer.mp4
```

## Note on the physics

The bunching in act 4 is integrated, not drawn: every macro-particle obeys

    dv/dt = -a · E(x) · sin(k(x - v_phi·t)),   E(x) = E0 · exp(x / L_gain)

with the beam launched slightly faster than the wave, which is what makes the
bunches settle into the decelerating phase and hand their energy over. The helix
is drawn with a pitch-to-circumference ratio that really does give a ~4x
slow-down, so the "four times more wire" claim matches the picture on screen.

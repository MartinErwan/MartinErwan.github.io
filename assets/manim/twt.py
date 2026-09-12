"""
Inside a Traveling-Wave Tube — animated explainer.

Source of the animations shown on
https://martinerwan.github.io/projets/thales.html

Rendered with Manim Community Edition:

    pip install manim
    manim -qh -r 1600,900 twt.py TravelingWaveTube
    manim -r 1600,900 --fps 30 --format png magnets.py MagnetScatter

Physics notes
-------------
A traveling-wave tube (TWT) amplifies a microwave signal by letting it surf on a
DC electron beam.  The RF wave is wrapped around a helix so that its *axial*
phase velocity drops from c to roughly c x pitch / circumference ~ 0.1-0.3 c,
which is the velocity of an electron accelerated through ~10-30 kV.  Wave and
beam then travel together, the axial electric field of the wave sorts the
electrons into bunches, and because the beam is set slightly *faster* than the
wave the bunches end up in the decelerating phase: on average the beam loses
energy and the wave grows exponentially along the tube (Pierce's small-signal
theory), typically 40-50 dB of gain.

The electron dynamics in Act 4 are integrated, not faked: each macro-particle
obeys dv/dt = -a E(x) sin(k(x - v_phi t)) with an exponentially growing field
envelope E(x), which is what produces the bunching you see.
"""

from manim import *
import numpy as np
import json
import os
import textwrap
from pathlib import Path

# --------------------------------------------------------------------------
# Narration
#
# The captions are the script. A collecting pass (TWT_COLLECT=1) writes them
# out, `narrate.py` turns them into clips, and the real render then holds each
# caption for exactly as long as its clip lasts and logs when it started, so
# the audio can be laid back onto the finished frames.
# --------------------------------------------------------------------------
NARRATION = Path(__file__).resolve().parent / "narration"
COLLECT = os.environ.get("TWT_COLLECT") == "1"
DURATIONS = (json.loads((NARRATION / "durations.json").read_text())
             if (NARRATION / "durations.json").exists() else {})

READING_SPEED = 13.0     # characters per second, when there is no clip to time to
BEAT_GAP = 0.6           # breath between one caption and the next


# --------------------------------------------------------------------------
# Palette — matches the website (martinerwan.github.io)
# --------------------------------------------------------------------------
BG        = "#0d1b2a"
PANEL     = "#112240"
TXT       = "#e8edf2"
MUTED     = "#7a9bb5"
FAINT     = "#4a6a85"
ACCENT    = "#378ADD"
ACCENT_LT = "#5b9bd5"
ELECTRON  = "#7cd4ff"
DECEL     = "#ff9f63"   # wave takes energy from the electrons
ACCEL     = "#59d49b"   # wave gives energy to the electrons
WARN      = "#ffcc66"
BAD       = "#e2574c"

FONT = "Inter"

config.background_color = BG


def T(s, size=26, color=TXT, weight=NORMAL, wrap=None, **kw):
    if wrap:
        s = "\n".join(textwrap.wrap(s, width=wrap))
    return Text(s, font=FONT, font_size=size, color=color, weight=weight,
                line_spacing=0.8, **kw)


def M(s, size=26, color=TXT, **kw):
    """Pango markup — lets us write subscripts without a LaTeX install."""
    return MarkupText(s, font=FONT, font_size=size, color=color, **kw)


# --------------------------------------------------------------------------
# Tube geometry (scene units)
# --------------------------------------------------------------------------
AXIS_Y   = 1.15          # the tube axis sits above centre; lanes go below
X_CATH   = -6.25
X_ANODE  = -4.55
X_H0     = -4.00         # helix entrance (RF input)
X_H1     =  4.15         # helix exit     (RF output)
X_COL0   =  4.55
X_COL1   =  6.20
R_TUBE   = 0.92
R_HELIX  = 0.60
R_BEAM   = 0.155
R_CATH   = 0.38          # emitting radius of the (convergent) cathode

WAVE_Y   = -1.95         # lane where the RF signal is drawn
CAP_Y    = -3.25         # caption line
TURNS    = 8
H_PHASE  = PI            # coil starts at the bottom of a turn, where the leads arrive
WIRE     = "#4b7ba3"     # the helix, unlit
GLOW     = "#ffd27a"     # the signal running along it

LAMBDA   = 1.36                      # on-screen RF wavelength
K        = 2 * np.pi / LAMBDA
V_PHASE  = 1.70                      # axial phase velocity, scene units / s
V_BEAM   = 1.06 * V_PHASE            # beam slightly faster than the wave
L_GAIN   = (X_H1 - X_H0) / np.log(9) # e-folding length of the growing wave


def helix_points(x0, x1, radius=R_HELIX, turns=TURNS, samples=900, phase=0.0):
    """Side view of a helix wound along the x axis, with a touch of depth."""
    th = np.linspace(0, turns * TAU, samples) + phase
    x = x0 + (x1 - x0) * (th - phase) / (turns * TAU) + 0.92 * radius * np.sin(th)
    y = AXIS_Y + radius * np.cos(th)
    return np.stack([x, y, np.zeros_like(x)], axis=1)


def helix_samples(n, x0=X_H0, x1=X_H1, radius=R_HELIX, turns=TURNS, phase=0.0):
    """Points along the drawn helix, paired with the axial position of each.

    The wire is sampled uniformly in turn angle, so the index is also uniform
    in *arc length along the wire* — which is what the travelling wave runs on.
    """
    pts = helix_points(x0, x1, radius=radius, turns=turns, samples=n, phase=phase)
    axial = np.linspace(x0, x1, n)
    return pts, axial


def helix_wire_length(turns=1, radius=R_HELIX, span=(X_H1 - X_H0), total_turns=TURNS):
    """True 3-D length of `turns` turns of the physical wire."""
    pitch = span / total_turns
    return turns * np.hypot(TAU * radius, pitch)


def build_tube():
    """The static cutaway: envelope, gun, helix, collector, RF ports."""
    g = VGroup()

    envelope = RoundedRectangle(
        width=(X_COL1 - X_CATH) + 0.30, height=2 * R_TUBE + 0.34, corner_radius=0.22,
        stroke_color=FAINT, stroke_width=1.6, fill_color=PANEL, fill_opacity=0.35,
    ).move_to([(X_CATH + X_COL1) / 2 - 0.05, AXIS_Y, 0])

    axis = DashedLine([X_CATH, AXIS_Y, 0], [X_COL1, AXIS_Y, 0],
                      dash_length=0.09, stroke_color=FAINT,
                      stroke_width=1, stroke_opacity=0.5)

    # ---- electron gun ----------------------------------------------------
    # dished (convergent) cathode, emitting surface facing right
    cathode = Arc(radius=0.92, start_angle=PI - 0.44, angle=0.88,
                  arc_center=[X_CATH + 1.05, AXIS_Y, 0],
                  stroke_color=WARN, stroke_width=7)
    halo = cathode.copy().set_stroke(WARN, 16, opacity=0.18)

    def electrode(x, y0, y1, w, tilt=0.0):
        return Polygon([x, y0, 0], [x + w, y0 + tilt, 0], [x + w, y1 + tilt, 0], [x, y1, 0],
                       stroke_color=MUTED, stroke_width=1.2,
                       fill_color="#1b3a5c", fill_opacity=0.9)

    focus = VGroup(electrode(X_CATH + 0.42, AXIS_Y + 0.46, AXIS_Y + 0.86, 0.52, -0.12),
                   electrode(X_CATH + 0.42, AXIS_Y - 0.86, AXIS_Y - 0.46, 0.52, 0.12))
    anode = VGroup(electrode(X_ANODE, AXIS_Y + 0.26, AXIS_Y + 0.86, 0.26),
                   electrode(X_ANODE, AXIS_Y - 0.86, AXIS_Y - 0.26, 0.26))

    gun = VGroup(halo, cathode, focus, anode)

    # ---- slow-wave structure --------------------------------------------
    helix = VMobject(stroke_color=WIRE, stroke_width=2.6)
    helix.set_points_smoothly(helix_points(X_H0, X_H1, phase=H_PHASE))

    # ---- collector -------------------------------------------------------
    collector = Polygon(
        [X_COL0, AXIS_Y + 0.78, 0], [X_COL1, AXIS_Y + 0.55, 0],
        [X_COL1, AXIS_Y - 0.55, 0], [X_COL0, AXIS_Y - 0.78, 0],
        stroke_color=MUTED, stroke_width=1.3, fill_color="#1b3a5c", fill_opacity=0.9)

    # ---- RF ports --------------------------------------------------------
    def port(x, up=False):
        y = AXIS_Y + (R_TUBE + 0.17) * (1 if up else -1)
        y2 = y + (0.42 if up else -0.42)
        return VGroup(Line([x, y, 0], [x, y2, 0], stroke_color=ACCENT, stroke_width=3),
                      Dot([x, y2, 0], radius=0.055, color=ACCENT))

    rf_in, rf_out = port(X_H0 + 0.15), port(X_H1 - 0.15)

    g.add(envelope, axis, gun, helix, collector, rf_in, rf_out)
    g.envelope, g.axis, g.gun, g.cathode = envelope, axis, gun, cathode
    g.helix, g.collector = helix, collector
    g.rf_in, g.rf_out, g.anode, g.focus = rf_in, rf_out, anode, focus
    return g


def leader(text_mob, tip, side=UP):
    """A thin leader line from a label to the part it names."""
    start = text_mob.get_edge_center(-side) + 0.06 * (-side)
    return Line(start, tip, stroke_color=FAINT, stroke_width=1, stroke_opacity=0.8)


# --------------------------------------------------------------------------
# Electron beam: a small macro-particle simulation
# --------------------------------------------------------------------------
class Beam:
    """N macro-particles streaming from the cathode to the collector.

    In the gun they follow v = v0 sqrt(U/U_anode) (linear potential drop);
    downstream they are pushed by the axial field of the RF wave, which is
    what makes them bunch.
    """

    X_EMIT = X_CATH + 0.20
    X_ACC  = X_ANODE + 0.26

    def __init__(self, n=130, seed=7, v_phase=V_PHASE, lam=LAMBDA):
        rng = np.random.default_rng(seed)
        self.n = n
        self.v_phase = v_phase
        self.k = TAU / lam
        self.v_beam = 1.06 * v_phase          # beam a hair faster than the wave
        self.x = np.linspace(self.X_EMIT, X_COL1, n) + rng.uniform(-0.02, 0.02, n)
        self.v = np.full(n, self.v_beam)
        self.y0 = rng.uniform(-1, 1, n)                   # normalised transverse offset
        self.t = 0.0
        self.coupling = ValueTracker(0.0)   # strength of the wave <-> beam force
        self.defocus = ValueTracker(0.0)    # 0 = magnetically focused, 1 = blow-up
        self.flow = ValueTracker(1.0)       # 0 = frozen, 1 = running
        self.opac = ValueTracker(1.0)       # dim the beam while we talk about the wave

        self.dots = VGroup(*[
            Dot(radius=0.042, color=ELECTRON, fill_opacity=1.0) for _ in range(n)])
        self._place()

    # -- kinematics --------------------------------------------------------
    def _gun_velocity(self, x):
        u = np.clip((x - self.X_EMIT) / (self.X_ACC - self.X_EMIT), 0.015, 1.0)
        return self.v_beam * np.sqrt(u)

    def field(self, x, t):
        """Axial electric field of the growing wave, in arbitrary units."""
        env = np.exp(np.clip(x - X_H0, 0, None) / L_GAIN)
        return env * np.sin(self.k * (x - self.v_phase * t))

    def step(self, dt):
        dt *= self.flow.get_value()
        if dt <= 0:
            self._place()
            return
        self.t += dt
        c = self.coupling.get_value()
        for _ in range(3):                       # sub-stepping keeps it stable
            h = dt / 3
            in_gun = self.x < self.X_ACC
            self.v = np.where(in_gun, self._gun_velocity(self.x), self.v)
            if c > 0:
                inside = (self.x > X_H0) & (self.x < X_H1)
                a = -0.16 * c * self.field(self.x, self.t) * inside
                self.v = np.where(in_gun, self.v, self.v + a * h)
            self.x = self.x + self.v * h
        # recycle at the collector
        out = self.x > X_COL1
        if out.any():
            self.x[out] = self.X_EMIT
            self.v[out] = self.v_beam
        self._place()

    def _place(self):
        d = self.defocus.get_value()
        spread = 1 + d * 7.0 * np.clip((self.x - X_H0) / (X_H1 - X_H0), 0, 1) ** 1.5
        # the gun compresses a wide emitting surface into a thin pencil beam
        conv = np.clip((self.x - self.X_EMIT) / (self.X_ACC - self.X_EMIT), 0, 1)
        radius = R_CATH + (R_BEAM - R_CATH) * conv ** 0.7
        y = AXIS_Y + self.y0 * radius * spread
        y = np.clip(y, AXIS_Y - R_HELIX - 0.04, AXIS_Y + R_HELIX + 0.04)
        hit = np.abs(y - AXIS_Y) > R_HELIX - 0.05
        for i, dot in enumerate(self.dots):
            dot.move_to([self.x[i], y[i], 0])
            dot.set_color(BAD if hit[i] else ELECTRON)
            dot.set_opacity(self.opac.get_value())


# --------------------------------------------------------------------------
class TWTScene(Scene):
    """Shared chrome: an act label top-left, a caption at the bottom."""

    def wait(self, duration=DEFAULT_WAIT_TIME, stop_condition=None, frozen_frame=False):
        """Always render a real frame per tick.

        Manim freezes a wait when nothing on screen has a time-based updater,
        which collapses it to a single frame in PNG output — every pause for
        reading would vanish from the exported frames.
        """
        super().wait(duration, stop_condition=stop_condition, frozen_frame=frozen_frame)

    # -- narration ---------------------------------------------------------
    def hold_for(self, text, minimum=0.0):
        """How long this beat stays up: as long as it is spoken, or read."""
        self._beat = getattr(self, "_beat", 0) + 1
        key = f"b{self._beat:02d}"
        if COLLECT:
            self.script.append({"key": key, "text": text})
        spoken = DURATIONS.get(key)
        if spoken is None:
            spoken = len(text) / READING_SPEED + 0.9
        self.beats.append({"key": key, "t": round(self.renderer.time, 3)})
        return max(spoken + BEAT_GAP, minimum)

    def write_narration(self):
        NARRATION.mkdir(exist_ok=True)
        name = "script.json" if COLLECT else "beats.json"
        payload = self.script if COLLECT else self.beats
        (NARRATION / name).write_text(json.dumps(payload, indent=2))

    def init_chrome(self):
        self.script, self.beats = [], []
        self.gain = ValueTracker(0.0)      # 0 = uniform wave, 1 = exponential growth
        self.energy = ValueTracker(0.0)    # 0 = dark wire, 1 = signal running on it
        self.leads_in = ValueTracker(0.0)  # the RF leads fade in with the ports
        self.lane_op = ValueTracker(1.0)   # the signal lane, faded out for the closing
        self.act = T("", 21, ACCENT_LT, weight=MEDIUM).to_corner(UL, buff=0.5)
        self.cap = VGroup().move_to([0, CAP_Y, 0])
        self.add(self.act, self.cap)

    def set_act(self, text):
        new = T(text, 21, ACCENT_LT, weight=MEDIUM).to_corner(UL, buff=0.5)
        self.play(FadeOut(self.act, shift=UP * 0.15, run_time=0.35),
                  FadeIn(new, shift=UP * 0.15, run_time=0.35))
        self.remove(self.act)
        self.act = new
        self.add(self.act)

    def say(self, line, sub=None, wait=0.0):
        grp = VGroup(T(line, 27, TXT, wrap=70))
        if sub:
            grp.add(T(sub, 21, MUTED, wrap=88))
        grp.arrange(DOWN, buff=0.24)
        grp.move_to([0, CAP_Y, 0]).align_to([0, -3.80, 0], DOWN)
        if len(self.cap) == 0:
            self.play(FadeIn(grp, shift=UP * 0.15), run_time=0.45)
        else:
            self.play(FadeOut(self.cap, shift=UP * 0.15, run_time=0.3),
                      FadeIn(grp, shift=UP * 0.15, run_time=0.45))
        self.remove(self.cap)
        self.cap = grp
        self.add(self.cap)
        self.wait(self.hold_for(line if not sub else f"{line} {sub}", minimum=wait))

    def clear_caption(self):
        if len(self.cap):
            self.play(FadeOut(self.cap), run_time=0.3)
        self.cap = VGroup()

    # -- the signal, lit along the wire it travels -------------------------
    def strength(self, x):
        """Envelope of the wave: flat while `gain` is 0, exponential at 1."""
        g = self.gain.get_value()
        e = np.exp(np.clip(np.asarray(x, dtype=float) - X_H0, 0, None) / L_GAIN) / 9.0
        return (1 - g) * 0.5 + g * e

    def lit_circuit(self, nseg=300, y_port=-0.36):
        """Input lead, helix, output lead: one wire, lit by the wave on it.

        Each piece is lit by the phase of the wave where it sits *along the
        wire*, so the light climbs the input lead, runs round every turn and
        drops back down at the far end — the same picture as the figure on the
        page, rather than a second way of drawing the same thing.
        """
        beam = self.beam
        pts = helix_points(X_H0, X_H1, samples=nseg + 1, phase=H_PHASE)
        axial = np.linspace(X_H0, X_H1, nseg + 1)
        ratio = helix_wire_length(TURNS) / (X_H1 - X_H0)    # wire per unit of tube
        y_join = AXIS_Y - R_HELIX

        n_l = 20
        step = (y_join - y_port) / n_l
        pieces = []
        lead_in = [np.array([X_H0, y, 0]) for y in np.linspace(y_port, y_join, n_l + 1)]
        for j, (a, b) in enumerate(zip(lead_in[:-1], lead_in[1:])):
            back = (n_l - j - 0.5) * step / ratio           # still short of the helix
            pieces.append((a, b, X_H0 - back, X_H0, True))
        for i in range(nseg):
            pieces.append((pts[i], pts[i + 1], axial[i], axial[i], False))
        lead_out = [np.array([X_H1, y, 0]) for y in np.linspace(y_join, y_port, n_l + 1)]
        for j, (a, b) in enumerate(zip(lead_out[:-1], lead_out[1:])):
            pieces.append((a, b, X_H1 + (j + 0.5) * step / ratio, X_H1, True))

        segs = VGroup(*[Line(a, b, stroke_color=WIRE, stroke_width=2.6)
                        for a, b, _, _, _ in pieces])
        base, glow = ManimColor(WIRE), ManimColor(GLOW)

        def paint(_):
            e, lead, t = self.energy.get_value(), self.leads_in.get_value(), beam.t
            for seg, (_, _, x_eq, x_env, is_lead) in zip(segs, pieces):
                bead = (0.5 * (1 + np.sin(beam.k * (x_eq - beam.v_phase * t)))) ** 4
                g = e * bead * (0.45 + 0.55 * float(self.strength(x_env)))
                seg.set_stroke(color=interpolate_color(base, glow, g),
                               width=2.6 + 4.4 * g,
                               opacity=(0.8 + 0.2 * g) * (lead if is_lead else 1.0))
        segs.add_updater(paint)
        paint(None)

        ports = VGroup(*[Dot([x, y_port, 0], radius=0.055, color=ACCENT)
                         for x in (X_H0, X_H1)])
        return segs, ports

    # -- the signal lane under the tube ------------------------------------
    def make_wave_layer(self):
        beam, amp = self.beam, 0.62
        base = DashedLine([X_H0, WAVE_Y, 0], [X_H1, WAVE_Y, 0], dash_length=0.08,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.4)
        wave = always_redraw(lambda: FunctionGraph(
            lambda x: WAVE_Y + amp * float(self.strength(x))
            * np.sin(beam.k * (x - beam.v_phase * beam.t)),
            x_range=[X_H0, X_H1, 0.02], color=GLOW, stroke_width=3,
            stroke_opacity=self.lane_op.get_value()))
        env = VGroup(*[always_redraw(lambda k=sgn: FunctionGraph(
            lambda x: WAVE_Y + k * amp * float(self.strength(x)),
            x_range=[X_H0, X_H1, 0.05], color=GLOW, stroke_width=1.4,
            stroke_opacity=0.45 * self.lane_op.get_value())) for sgn in (1, -1)])
        lbl = VGroup(T("the signal", 19, MUTED), T("on the helix", 19, MUTED)
                     ).arrange(DOWN, buff=0.10).move_to([-5.55, WAVE_Y, 0])
        return base, lbl, wave, env

# --------------------------------------------------------------------------
# Main explainer
# --------------------------------------------------------------------------
class TravelingWaveTube(TWTScene):

    def construct(self):
        self.init_chrome()
        self.opening()
        self.tube = build_tube()
        # the beam exists from the start so the wire knows the wave's numbers;
        # its particles only join the scene in act 2
        self.beam = Beam()
        self.act1_device()
        self.act2_beam()
        self.act3_slow_wave()
        self.act4_bunching()
        self.closing()
        self.write_narration()

    # -- 0 ---------------------------------------------------------------
    def opening(self):
        title = T("Inside a Traveling-Wave Tube", 46, TXT, weight=MEDIUM)
        sub = T("how a microwave signal surfs on a beam of electrons", 25, MUTED)
        VGroup(title, sub).arrange(DOWN, buff=0.36)
        rule = Line(LEFT * 1.3, RIGHT * 1.3, stroke_color=ACCENT, stroke_width=2.5)
        rule.next_to(sub, DOWN, buff=0.45)
        self.play(FadeIn(title, shift=UP * 0.25), run_time=1.0)
        self.play(FadeIn(sub), Create(rule), run_time=0.8)
        self.wait(self.hold_for("Inside a traveling-wave tube: how a microwave signal "
                                "surfs on a beam of electrons.", minimum=1.5))
        self.play(FadeOut(VGroup(title, sub, rule), shift=UP * 0.3), run_time=0.7)

    # -- 1 ---------------------------------------------------------------
    def act1_device(self):
        tb = self.tube
        self.set_act("1 — The device")
        self.play(Create(tb.envelope), run_time=1.0)
        self.play(Create(tb.axis), run_time=0.5)

        def tag(txt, x, y, tip, size=20):
            lbl = T(txt, size, MUTED).move_to([x, y, 0])
            return VGroup(lbl, leader(lbl, tip, side=UP if y > AXIS_Y else DOWN))

        gun_tag = tag("Electron gun", -5.15, 2.80, [X_CATH + 0.75, AXIS_Y + 0.95, 0])
        helix_tag = tag("Helix — the slow-wave structure", 0.25, 2.80, [0.25, AXIS_Y + 0.68, 0])
        col_tag = tag("Collector", 5.30, 2.80, [5.25, AXIS_Y + 0.80, 0])

        self.play(FadeIn(tb.gun, shift=RIGHT * 0.2), Write(gun_tag), run_time=1.0)
        self.play(Create(tb.helix, run_time=1.6), FadeIn(helix_tag, run_time=0.8))
        self.play(FadeIn(tb.collector, shift=LEFT * 0.2), FadeIn(col_tag), run_time=0.8)

        in_lbl = T("RF in", 19, ACCENT_LT).move_to([X_H0 + 0.15, -0.82, 0])
        in_sub = T("a few milliwatts", 16, FAINT).next_to(in_lbl, DOWN, buff=0.12)
        out_lbl = T("RF out", 19, ACCENT_LT).move_to([X_H1 - 0.15, -0.82, 0])
        out_sub = T("up to 100 000×  the power", 16, FAINT).next_to(out_lbl, DOWN, buff=0.12)
        # the plain coil becomes the wire the signal will run on, leads and all
        self.circuit, self.ports = self.lit_circuit()
        self.remove(tb.helix, tb.rf_in, tb.rf_out)
        self.add(self.circuit)
        self.play(self.leads_in.animate.set_value(1.0),
                  FadeIn(VGroup(self.ports, in_lbl, in_sub, out_lbl, out_sub)), run_time=0.8)

        self.say("A traveling-wave tube is a microwave amplifier.",
                 "Radar, satellite links, electronic warfare — where solid-state amplifiers run out of power.",
                 wait=2.4)
        self.top_tags = VGroup(gun_tag, helix_tag, col_tag)
        self.port_tags = VGroup(in_lbl, in_sub, out_lbl, out_sub)

    # -- 2 ---------------------------------------------------------------
    def act2_beam(self):
        tb = self.tube
        self.set_act("2 — The beam")
        self.say("Everything starts with a hot cathode boiling off electrons.")

        glow = tb.cathode.copy().set_stroke(WARN, 16, opacity=0.25)
        self.add(glow)
        self.play(glow.animate.set_stroke(opacity=0.55), run_time=0.6,
                  rate_func=there_and_back_with_pause)

        self.beam.dots.add_updater(lambda m, dt: self.beam.step(dt))
        self.add(self.beam.dots)
        self.wait(1.6)

        volt = M('U<sub>0</sub> ≈ 20 kV', 21, WARN).move_to([X_ANODE - 0.15, AXIS_Y - 1.45, 0])
        arrow = Arrow([X_CATH + 0.7, AXIS_Y - 1.15, 0], [X_ANODE + 0.2, AXIS_Y - 1.15, 0],
                      buff=0, stroke_width=2.5, color=WARN, max_tip_length_to_length_ratio=0.06)
        self.play(GrowArrow(arrow), FadeIn(volt), run_time=0.7)
        self.say("Twenty thousand volts push them to roughly a quarter of the speed of light.",
                 wait=2.0)
        self.play(FadeOut(VGroup(arrow, volt)), run_time=0.5)

        # space charge blow-up
        self.say("Left alone the beam destroys itself — like charges repel.")
        self.play(self.beam.defocus.animate.set_value(1.0), run_time=2.0)
        flash = Rectangle(width=X_H1 - X_H0, height=2 * R_HELIX + 0.2,
                          stroke_width=0, fill_color=BAD, fill_opacity=0.0
                          ).move_to([(X_H0 + X_H1) / 2, AXIS_Y, 0])
        self.add(flash)
        self.play(flash.animate.set_fill(opacity=0.16), run_time=0.5,
                  rate_func=there_and_back)
        self.say("Electrons that hit the helix turn it into a heater. The tube dies.", wait=1.6)

        # magnetic focusing
        magnets = VGroup()
        for i, x in enumerate(np.arange(X_H0 + 0.25, X_H1, 0.98)):
            up_is_n = i % 2 == 0
            for sgn in (1, -1):
                c = ACCENT if (up_is_n == (sgn > 0)) else "#9a5ad6"
                magnets.add(Rectangle(width=0.72, height=0.22, stroke_width=0,
                                      fill_color=c, fill_opacity=0.85)
                            .move_to([x, AXIS_Y + sgn * (R_TUBE + 0.30), 0]))
        self.say("So a stack of permanent magnets squeezes it back into a pencil about a millimetre wide.")
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in magnets], lag_ratio=0.04),
                  self.beam.defocus.animate.set_value(0.0), run_time=2.0)
        self.remove(flash)
        self.magnets = magnets
        self.wait(1.2)
        self.play(FadeOut(self.top_tags), run_time=0.6)

    # -- 3 ---------------------------------------------------------------
    def act3_slow_wave(self):
        self.set_act("3 — The trick")
        self.play(FadeOut(self.port_tags), FadeOut(self.magnets),
                  self.beam.opac.animate.set_value(0.18), run_time=0.7)
        self.say("A radio wave travels at the speed of light — far too fast to keep pace with the electrons.")
        self.wait(1.2)

        # three turns of wire, and the same wire unrolled
        x3 = X_H0 + (X_H1 - X_H0) * 3 / TURNS
        pts = helix_points(X_H0, x3, turns=3, samples=500, phase=H_PHASE)
        seg = VMobject(stroke_color=WARN, stroke_width=3.5)
        seg.set_points_smoothly(pts)
        wire_len = helix_wire_length(3)

        unrolled = Line([-6.40, -0.95, 0], [-6.40 + wire_len, -0.95, 0],
                        stroke_color=WARN, stroke_width=3.5)
        unrolled_lbl = T("the same wire, unrolled", 19, MUTED).next_to(unrolled, DOWN, buff=0.22).align_to(unrolled, LEFT)

        self.play(Create(seg), run_time=0.8)
        self.play(Create(unrolled), FadeIn(unrolled_lbl), run_time=0.8)

        d_helix = Dot(pts[0], radius=0.075, color=WARN)
        d_line = Dot(unrolled.get_start(), radius=0.075, color=WARN)
        self.add(d_helix, d_line)
        self.play(MoveAlongPath(d_helix, seg), MoveAlongPath(d_line, unrolled),
                  run_time=3.0, rate_func=linear)

        adv = BraceBetweenPoints([X_H0, AXIS_Y - R_TUBE - 0.30, 0],
                                 [x3, AXIS_Y - R_TUBE - 0.30, 0], direction=DOWN,
                                 color=FAINT)
        adv_lbl = T("what the wave actually advances", 18, MUTED).next_to(adv, DOWN, buff=0.10)
        self.play(GrowFromCenter(adv), FadeIn(adv_lbl), run_time=0.7)
        self.say("Wound into a helix, the signal must cover about four times more wire "
                 "than the distance it moves forward.",
                 "Its forward speed collapses to roughly a quarter of c — exactly the speed of the electrons.",
                 wait=3.2)

        self.play(FadeOut(VGroup(seg, unrolled, unrolled_lbl, d_helix, d_line, adv, adv_lbl)),
                  self.beam.opac.animate.set_value(1.0), run_time=0.8)

        self.build_wave_layer()
        self.say("Now the wave and the beam drift along together, and they start to feel each other.",
                 wait=2.0)

    def build_wave_layer(self):
        base, lbl, wave, env = self.make_wave_layer()
        self.play(Create(base), FadeIn(lbl), run_time=0.5)
        self.add(wave, env)
        self.play(self.energy.animate.set_value(1.0), run_time=1.2)
        self.wave_layer = VGroup(base, lbl)
        self.lane_live = (wave, env)

    # -- 4 ---------------------------------------------------------------
    def act4_bunching(self):
        self.set_act("4 — The exchange")

        self.say("The wave's own electric field sorts the beam: some electrons are slowed, some sped up.")
        self.play(self.beam.coupling.animate.set_value(1.0), run_time=2.0)
        self.wait(2.5)
        self.say("Within a few centimetres the smooth stream has turned into a train of bunches.",
                 wait=3.2)

        self.say("The beam is set a hair faster than the wave, so the bunches drift into the "
                 "region that holds them back —",
                 "and every electron that is slowed hands its energy straight to the wave.",
                 wait=3.4)

        self.say("The signal grows exponentially along the tube.")
        self.play(self.gain.animate.set_value(1.0), run_time=4.0, rate_func=smooth)
        self.wait(1.5)

        gain_box = VGroup(
            T("40 – 50 dB", 30, ACCENT_LT, weight=MEDIUM),
            T("10 000 – 100 000 ×\nthe input power", 18, MUTED),
        ).arrange(DOWN, buff=0.16).move_to([5.75, WAVE_Y, 0])
        self.play(FadeIn(gain_box, shift=UP * 0.15), run_time=0.7)
        self.wait(2.0)
        self.play(FadeOut(gain_box), run_time=0.6)

    # -- closing -----------------------------------------------------------
    def closing(self):
        self.set_act("5 — And the hard part")
        self.play(self.beam.coupling.animate.set_value(0.35), run_time=1.0)

        self.play(self.lane_op.animate.set_value(0.0),
                  FadeOut(self.wave_layer), run_time=0.6)
        self.remove(*self.lane_live)          # its caption needs the room

        magnets = getattr(self, "magnets", VGroup())
        box = RoundedRectangle(width=X_H1 - X_H0 + 0.6, height=2 * (R_TUBE + 0.55),
                               corner_radius=0.15, stroke_color=WARN, stroke_width=2,
                               fill_opacity=0).move_to([(X_H0 + X_H1) / 2, AXIS_Y, 0])
        self.play(Create(box), FadeIn(magnets), run_time=0.9)   # act 3 had put them away
        self.say("None of it happens unless the beam stays a thin pencil the whole way — "
                 "and what holds it is that stack of magnets.",
                 "The focusing comes from their field being periodic, so every magnet has to "
                 "match its neighbours.",
                 wait=3.0)
        self.play(FadeOut(box), run_time=0.5)
        self.say("They never quite do. How much manufacturing scatter the tube can absorb, and "
                 "which dimension it is most sensitive to, is what this project set out to "
                 "measure.", wait=2.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        self.wait(0.4)


# --------------------------------------------------------------------------
# The standalone looping figure used on the page
# --------------------------------------------------------------------------
class TWTLoop(TWTScene):
    """The wave drawn where it actually acts — through the beam itself.

    The RF wave rides on the axis, so its crests and troughs sweep across the
    electrons; a row of arrows under the beam gives the push each electron is
    getting at that instant, and the bunches form exactly where those arrows
    converge. The loop closes on itself: one crest crosses the helix in
    T_LOOP seconds and the helix is six wavelengths long.
    """

    T_LOOP = 7.2                                  # seconds, an exact loop
    LAM    = (X_H1 - X_H0) / 6                    # six wavelengths of helix
    VPH    = (X_H1 - X_H0) / T_LOOP               # crossed in one loop
    AMP    = 0.55                                 # amplitude drawn in the signal lane
    NSEG   = 360                                  # pieces the wire is cut into
    Y_PORT = -0.95                                # where the RF connectors sit

    WIRE   = "#3e6486"                            # the wire, unlit
    GLOW   = "#ffd27a"                            # the signal running along it

    def strength(self, x):
        """Envelope of the wave: it grows exponentially down the tube."""
        return np.exp(np.clip(x - X_H0, 0, None) / L_GAIN) / 9.0

    def e_field(self, x, t):
        return self.strength(x) * np.sin(self.beam.k * (x - self.VPH * t))

    # ----------------------------------------------------------------------
    def construct(self):
        tube = build_tube()
        for part in (tube.helix, tube.rf_in, tube.rf_out):
            tube.remove(part)                     # replaced by the lit circuit
        self.beam = Beam(v_phase=self.VPH, lam=self.LAM)
        self.beam.coupling.set_value(1.0)

        circuit, ports = self.lit_circuit()
        magnets = self.magnet_row()
        lane = self.signal_lane()
        chrome = self.annotate()

        dt = 1 / config.frame_rate
        for _ in range(int(round(2 * self.T_LOOP / dt))):   # let the bunches settle
            self.beam.step(dt)

        self.add(tube, magnets, circuit, ports, self.beam.dots, lane, chrome)
        self.beam.dots.add_updater(lambda m, dt: self.beam.step(dt))
        self.wait(self.T_LOOP)

    # -- the signal, lit along the circuit it actually travels -------------
    def lit_circuit(self):
        """Input lead, helix, output lead: one wire, lit by the wave on it.

        Each piece is lit by the phase of the wave at its own arc length along
        the wire. The wave covers the 31 units of wire in one loop while only
        advancing the 8 units of tube length — which is the whole point of a
        slow-wave structure, and why it keeps pace with the electrons.
        """
        pts, axial = helix_samples(self.NSEG + 1, phase=PI)   # starts at the bottom
        s_helix = helix_wire_length(TURNS)
        ds_h = s_helix / self.NSEG
        y_join = AXIS_Y - R_HELIX                            # where the leads meet it

        n_l = 24
        ds_l = (y_join - self.Y_PORT) / n_l
        lead_in = [np.array([X_H0, y, 0]) for y in np.linspace(self.Y_PORT, y_join, n_l + 1)]
        lead_out = [np.array([X_H1, y, 0]) for y in np.linspace(y_join, self.Y_PORT, n_l + 1)]

        pieces, s = [], 0.0
        for a, b in zip(lead_in[:-1], lead_in[1:]):
            pieces.append((a, b, s + ds_l / 2, self.strength(X_H0))); s += ds_l
        for i in range(self.NSEG):
            pieces.append((pts[i], pts[i + 1], s + ds_h / 2, self.strength(axial[i]))); s += ds_h
        for a, b in zip(lead_out[:-1], lead_out[1:]):
            pieces.append((a, b, s + ds_l / 2, self.strength(X_H1))); s += ds_l

        segs = VGroup(*[Line(a, b, stroke_color=self.WIRE, stroke_width=1.8)
                        for a, b, _, _ in pieces])
        base, glow = ManimColor(self.WIRE), ManimColor(self.GLOW)
        lam_w = s_helix / 6                        # six wavelengths fit on the wire
        v_wire = s_helix / self.T_LOOP

        def paint(_):
            t = self.beam.t
            for seg, (_, _, sm, env) in zip(segs, pieces):
                bead = (0.5 * (1 + np.sin(TAU * (sm - v_wire * t) / lam_w))) ** 4
                g = bead * (0.45 + 0.55 * env)
                seg.set_stroke(color=interpolate_color(base, glow, g),
                               width=1.8 + 4.6 * g, opacity=0.75 + 0.25 * g)
        segs.add_updater(paint)
        paint(None)

        ports = VGroup(*[Dot([x, self.Y_PORT, 0], radius=0.075, color=ACCENT)
                         for x in (X_H0, X_H1)])
        return segs, ports

    # -- the amplitude, kept in a lane of its own --------------------------
    def signal_lane(self):
        base = DashedLine([X_H0, WAVE_Y, 0], [X_H1, WAVE_Y, 0], dash_length=0.08,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.4)
        env = VGroup(*[FunctionGraph(lambda x, k=sgn: WAVE_Y + k * self.AMP * self.strength(x),
                                     x_range=[X_H0, X_H1, 0.05], color=self.GLOW,
                                     stroke_width=1.2, stroke_opacity=0.32) for sgn in (1, -1)])
        trace = always_redraw(lambda: FunctionGraph(
            lambda x: WAVE_Y + self.AMP * self.e_field(x, self.beam.t),
            x_range=[X_H0, X_H1, 0.015], color=self.GLOW, stroke_width=3.0))
        drops = VGroup(*[DashedLine([x, self.Y_PORT - 0.14, 0], [x, WAVE_Y + 0.02, 0],
                                    dash_length=0.07, stroke_color=FAINT,
                                    stroke_width=1, stroke_opacity=0.5)
                         for x in (X_H0, X_H1)])
        label = VGroup(T("the same signal,", 18, MUTED), T("amplitude only", 18, MUTED)
                       ).arrange(DOWN, buff=0.10).move_to([-5.55, WAVE_Y, 0])
        return VGroup(base, env, trace, drops, label)

    # -- the magnets that keep the beam pinched ----------------------------
    def magnet_row(self):
        g = VGroup()
        y = R_TUBE + 0.38
        for i, x in enumerate(np.arange(X_H0 + 0.75, X_H1 - 0.70, 0.96)):
            for sgn in (1, -1):
                north = (i % 2 == 0) == (sgn > 0)
                col = "#4f7fd6" if north else "#9a5ad6"
                block = RoundedRectangle(width=0.78, height=0.30, corner_radius=0.05,
                                         stroke_width=0, fill_color=col, fill_opacity=0.9)
                block.move_to([x, AXIS_Y + sgn * y, 0])
                g.add(block, T("N" if north else "S", 15, "#0d1b2a", weight=BOLD)
                      .move_to(block.get_center()))
        return g

    # -- naming every part -------------------------------------------------
    def annotate(self):
        def tag(txt, x, y, tip, size=21, color=MUTED):
            lbl = T(txt, size, color).move_to([x, y, 0])
            return VGroup(lbl, leader(lbl, tip, side=UP if y > AXIS_Y else DOWN))

        title = T("How a traveling-wave tube amplifies a signal", 26, TXT,
                  weight=MEDIUM).move_to([0, 3.55, 0])

        above = VGroup(
            tag("cathode", -6.02, 2.92, [X_CATH + 0.20, AXIS_Y + 0.42, 0]),
            tag("anode", -4.42, 2.92, [X_ANODE + 0.13, AXIS_Y + 0.88, 0]),
            tag("helix — the slow-wave structure", 0.55, 2.92, [0.55, AXIS_Y + 0.62, 0]),
            tag("collector", 5.45, 2.92, [5.35, AXIS_Y + 0.74, 0]),
        )

        electrons = tag("electrons", -3.45, AXIS_Y + 0.46,
                        [-3.45, AXIS_Y + 0.17, 0], size=19, color=ELECTRON)
        magnets = tag("focusing magnets — they keep the beam pinched", 0.0, -0.88,
                      [-0.37, -0.31, 0], size=19)

        rf_in = VGroup(T("RF in", 21, ACCENT_LT), T("weak signal", 18, FAINT)
                       ).arrange(DOWN, buff=0.09)
        rf_in.move_to([0, self.Y_PORT, 0]).align_to([X_H0 - 0.28, 0, 0], RIGHT)
        rf_out = VGroup(T("RF out", 21, ACCENT_LT), T("amplified", 18, FAINT)
                        ).arrange(DOWN, buff=0.09)
        rf_out.move_to([0, self.Y_PORT, 0]).align_to([X_H1 + 0.28, 0, 0], LEFT)

        key = T("It enters at one connector and leaves at the other. Along the wire it runs at "
                "nearly the speed of light — coiled into a helix it can only creep forward, at "
                "the speed of the electrons.", 19, MUTED, wrap=100)
        key.move_to([0, -2.98, 0])

        return VGroup(title, above, electrons, magnets, rf_in, rf_out, key)

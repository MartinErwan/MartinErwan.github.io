"""
Inside a Traveling-Wave Tube — animated explainer.

Source of the animations shown on
https://martinerwan.github.io/projets/thales.html

Rendered with Manim Community Edition:

    pip install manim
    manim -qh -r 1600,900 twt.py TravelingWaveTube
    manim -qh -r 1600,900 twt.py ElectronGunProblem

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
import textwrap

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

LAMBDA   = 1.36                      # on-screen RF wavelength
K        = 2 * np.pi / LAMBDA
V_PHASE  = 1.70                      # axial phase velocity, scene units / s
V_BEAM   = 1.06 * V_PHASE            # beam slightly faster than the wave
L_GAIN   = (X_H1 - X_H0) / np.log(9) # e-folding length of the growing wave


def helix_points(x0, x1, radius=R_HELIX, turns=TURNS, samples=900):
    """Side view of a helix wound along the x axis, with a touch of depth."""
    th = np.linspace(0, turns * TAU, samples)
    x = x0 + (x1 - x0) * th / (turns * TAU) + 0.92 * radius * np.sin(th)
    y = AXIS_Y + radius * np.cos(th)
    return np.stack([x, y, np.zeros_like(x)], axis=1)


def helix_samples(n, x0=X_H0, x1=X_H1, radius=R_HELIX, turns=TURNS):
    """Points along the drawn helix, paired with the axial position of each.

    The wire is sampled uniformly in turn angle, so the index is also uniform
    in *arc length along the wire* — which is what the travelling wave runs on.
    """
    pts = helix_points(x0, x1, radius=radius, turns=turns, samples=n)
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
    helix = VMobject(stroke_color=ACCENT_LT, stroke_width=2.6)
    helix.set_points_smoothly(helix_points(X_H0, X_H1))

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

    def init_chrome(self):
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
        if wait:
            self.wait(wait)

    def clear_caption(self):
        if len(self.cap):
            self.play(FadeOut(self.cap), run_time=0.3)
        self.cap = VGroup()

    # -- wave layer --------------------------------------------------------
    def make_wave_layer(self, gain=0.0, only_decel=False):
        """Build (but do not animate in) the field bands and the RF trace.

        `only_decel` shades just the half-cycles that hold the electrons back,
        which needs no two-colour key to read.
        """
        beam = self.beam
        k, vph = beam.k, beam.v_phase
        self.gain = ValueTracker(gain)    # 0 = uniform wave, 1 = exponential growth

        def strength(x):
            g = self.gain.get_value()
            e = np.exp(np.clip(x - X_H0, 0, None) / L_GAIN) / 9.0
            return (1 - g) * 0.5 + g * e

        # axial field of the wave, painted as bands inside the tube
        n_band = 180
        w = (X_H1 - X_H0) / n_band
        bands = VGroup(*[
            Rectangle(width=w * 1.02, height=2 * R_TUBE - 0.06, stroke_width=0,
                      fill_color=ACCEL, fill_opacity=0.0)
            .move_to([X_H0 + (i + 0.5) * w, AXIS_Y, 0]) for i in range(n_band)])

        def paint(_):
            t = beam.t
            for i, b in enumerate(bands):
                x = X_H0 + (i + 0.5) * w
                s = np.sin(k * (x - vph * t))
                # the force on an electron is -e E, so sin > 0 slows it down
                if only_decel:
                    b.set_fill(DECEL, opacity=0.52 * strength(x) * max(s, 0.0) ** 0.85)
                else:
                    b.set_fill(DECEL if s > 0 else ACCEL,
                               opacity=0.02 + 0.46 * strength(x) * abs(s))
        bands.add_updater(paint)
        paint(None)
        self.add(bands)
        bands.set_z_index(-1)

        # the RF signal itself, drawn in its own lane
        amp = 0.62

        def wave_curve():
            return FunctionGraph(
                lambda x: WAVE_Y + amp * strength(x) * np.sin(k * (x - vph * beam.t)),
                x_range=[X_H0, X_H1, 0.02], color=ACCENT_LT, stroke_width=3)

        def envelope_curve(sgn):
            return FunctionGraph(lambda x: WAVE_Y + sgn * amp * strength(x),
                                 x_range=[X_H0, X_H1, 0.05],
                                 color=ACCENT, stroke_width=1.4, stroke_opacity=0.45)

        base = DashedLine([X_H0, WAVE_Y, 0], [X_H1, WAVE_Y, 0], dash_length=0.08,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.4)
        wave = always_redraw(wave_curve)
        env_up = always_redraw(lambda: envelope_curve(+1))
        env_dn = always_redraw(lambda: envelope_curve(-1))
        wave_lbl = VGroup(T("the signal", 19, MUTED),
                          T("on the helix", 19, MUTED)
                          ).arrange(DOWN, buff=0.10).move_to([-5.55, WAVE_Y, 0])

        self.bands = bands
        self.wave_parts = (base, wave_lbl, wave, env_up, env_dn)
        return bands, base, wave_lbl, wave, env_up, env_dn


# --------------------------------------------------------------------------
# Main explainer
# --------------------------------------------------------------------------
class TravelingWaveTube(TWTScene):

    def construct(self):
        self.init_chrome()
        self.opening()
        self.tube = build_tube()
        self.act1_device()
        self.act2_beam()
        self.act3_slow_wave()
        self.act4_bunching()
        self.closing()

    # -- 0 ---------------------------------------------------------------
    def opening(self):
        title = T("Inside a Traveling-Wave Tube", 46, TXT, weight=MEDIUM)
        sub = T("how a microwave signal surfs on a beam of electrons", 25, MUTED)
        VGroup(title, sub).arrange(DOWN, buff=0.36)
        rule = Line(LEFT * 1.3, RIGHT * 1.3, stroke_color=ACCENT, stroke_width=2.5)
        rule.next_to(sub, DOWN, buff=0.45)
        self.play(FadeIn(title, shift=UP * 0.25), run_time=1.0)
        self.play(FadeIn(sub), Create(rule), run_time=0.8)
        self.wait(1.5)
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
        self.play(FadeIn(VGroup(tb.rf_in, in_lbl, in_sub)),
                  FadeIn(VGroup(tb.rf_out, out_lbl, out_sub)), run_time=0.8)

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

        self.beam = Beam()
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
        pts = helix_points(X_H0, x3, turns=3, samples=500)
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
        bands, base, wave_lbl, wave, env_up, env_dn = self.make_wave_layer()
        self.play(Create(base), FadeIn(wave_lbl), run_time=0.5)
        self.add(wave, env_up, env_dn, bands)
        self.play(FadeIn(bands), run_time=0.8)
        self.wave_layer = VGroup(base, wave_lbl)

    # -- 4 ---------------------------------------------------------------
    def act4_bunching(self):
        self.set_act("4 — The exchange")

        sw_a = VGroup(Square(0.17, stroke_width=0, fill_color=ACCEL, fill_opacity=0.8),
                      T("field pushes electrons forward", 17, MUTED)).arrange(RIGHT, buff=0.16)
        sw_d = VGroup(Square(0.17, stroke_width=0, fill_color=DECEL, fill_opacity=0.8),
                      T("field holds them back", 17, MUTED)).arrange(RIGHT, buff=0.16)
        legend = VGroup(sw_a, sw_d).arrange(RIGHT, buff=0.9).move_to([0.3, -0.62, 0])
        self.play(FadeIn(legend), run_time=0.6)

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
        self.play(FadeOut(VGroup(legend, gain_box)), run_time=0.6)

    # -- closing -----------------------------------------------------------
    def closing(self):
        self.set_act("5 — And the hard part")
        self.play(self.beam.coupling.animate.set_value(0.35), run_time=1.0)

        box = RoundedRectangle(width=2.5, height=2.5, corner_radius=0.15,
                               stroke_color=WARN, stroke_width=2,
                               fill_opacity=0).move_to([X_CATH + 1.0, AXIS_Y, 0])
        self.play(Create(box), run_time=0.8)
        self.say("All of it rests on one thing: the beam the gun actually delivers.",
                 "Cathode voltage, electrode angles, magnetic field — each one bends the trajectory.",
                 wait=3.0)
        self.play(FadeOut(box), run_time=0.5)
        self.say("And that trajectory is exactly what this project set out to predict.", wait=2.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        self.wait(0.4)


# --------------------------------------------------------------------------
# Second animation: why the beam trajectory had to be learned
# --------------------------------------------------------------------------
G_AXIS   = 1.35          # beam axis for this scene
G_X0     = -6.30         # cathode
G_XW     = -2.40         # nominal waist / helix entrance
G_X1     =  6.20         # end of the interaction region
G_WALL   = 0.62          # helix wall


class ElectronGunProblem(TWTScene):
    """Gun parameters -> beam envelope -> why a surrogate model was needed."""

    def construct(self):
        self.init_chrome()
        self.build_stage()
        self.act_knobs()
        self.act_failures()
        self.act_cost()
        self.act_surrogate()

    # -- the picture -------------------------------------------------------
    def build_stage(self):
        self.set_act("The design problem")

        wall_up = Line([G_XW, G_AXIS + G_WALL, 0], [G_X1, G_AXIS + G_WALL, 0],
                       stroke_color=ACCENT_LT, stroke_width=2.5)
        wall_dn = wall_up.copy().shift(DOWN * 2 * G_WALL)
        wall_lbl = T("helix wall", 17, FAINT).next_to(wall_up, UP, buff=0.10).shift(RIGHT * 2)
        axis = DashedLine([G_X0, G_AXIS, 0], [G_X1, G_AXIS, 0], dash_length=0.09,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.45)

        cathode = Arc(radius=2.2, start_angle=PI - 0.35, angle=0.70,
                      arc_center=[G_X0 + 2.20, G_AXIS, 0], stroke_color=WARN, stroke_width=7)
        focus = VGroup(*[Polygon([G_X0 + 0.55, G_AXIS + s * 0.90, 0],
                                 [G_X0 + 1.45, G_AXIS + s * 1.22, 0],
                                 [G_X0 + 1.45, G_AXIS + s * 1.52, 0],
                                 [G_X0 + 0.55, G_AXIS + s * 1.20, 0],
                                 stroke_color=MUTED, stroke_width=1.2,
                                 fill_color="#1b3a5c", fill_opacity=0.9) for s in (1, -1)])
        anode = VGroup(*[Rectangle(width=0.28, height=0.72, stroke_color=MUTED, stroke_width=1.2,
                                   fill_color="#1b3a5c", fill_opacity=0.9)
                         .move_to([G_XW - 0.55, G_AXIS + s * 0.74, 0]) for s in (1, -1)])

        self.stage = VGroup(axis, wall_up, wall_dn, wall_lbl, cathode, focus, anode)

        # knobs -> envelope
        self.p_rc   = ValueTracker(0.70)   # cathode radius
        self.p_wai  = ValueTracker(0.00)   # focusing (moves the waist)
        self.p_rmin = ValueTracker(0.22)   # waist radius
        self.p_amp  = ValueTracker(0.06)   # magnetic mismatch -> scalloping

        self.beam_area = always_redraw(self.make_envelope)
        self.play(FadeIn(self.stage), run_time=0.9)
        self.add(self.beam_area)
        self.say("Before any of that works, the gun has to deliver the right beam.",
                 wait=1.8)

    def radius(self, x):
        rc, rmin = self.p_rc.get_value(), self.p_rmin.get_value()
        xw = G_XW + 1.9 * self.p_wai.get_value()
        amp = self.p_amp.get_value()
        u = np.clip((x - G_X0) / max(xw - G_X0, 0.4), 0, 1)
        r_gun = rc + (rmin - rc) * u ** 1.3
        r_dft = rmin * (1 + amp * 9.0 * np.sin(TAU * (x - xw) / 2.6))
        return np.where(x < xw, r_gun, np.abs(r_dft)) + 0.02

    def make_envelope(self):
        xs = np.linspace(G_X0 + 0.18, G_X1, 320)
        rs = self.radius(xs)
        # only interception *inside* the helix counts — the gun itself is wider
        inside = xs > G_XW + 1.9 * self.p_wai.get_value()
        hit = bool(rs[inside].max() > G_WALL) if inside.any() else False
        col = BAD if hit else ELECTRON
        top = np.stack([xs, G_AXIS + rs, np.zeros_like(xs)], axis=1)
        bot = np.stack([xs[::-1], G_AXIS - rs[::-1], np.zeros_like(xs)], axis=1)
        area = VMobject(stroke_width=0, fill_color=col, fill_opacity=0.22)
        area.set_points_as_corners(np.concatenate([top, bot, top[:1]]))
        edge_t = VMobject(stroke_color=col, stroke_width=2.5)
        edge_t.set_points_smoothly(top)
        edge_b = VMobject(stroke_color=col, stroke_width=2.5)
        edge_b.set_points_smoothly(bot)
        return VGroup(area, edge_t, edge_b)

    # -- sliders -----------------------------------------------------------
    def act_knobs(self):
        specs = [("cathode radius", self.p_rc, 0.40, 0.95),
                 ("focusing electrode", self.p_wai, -1.0, 1.0),
                 ("anode aperture", self.p_rmin, 0.12, 0.34),
                 ("magnetic field", self.p_amp, 0.0, 0.26)]
        sliders = VGroup()
        for name, tr, lo, hi in specs:
            bar = Line(ORIGIN, RIGHT * 1.65, stroke_color=FAINT, stroke_width=2)
            knob = always_redraw(lambda b=bar, t=tr, lo=lo, hi=hi: Dot(
                b.get_start() + RIGHT * 1.65 * float(np.clip((t.get_value() - lo) / (hi - lo), 0, 1)),
                radius=0.075, color=ACCENT_LT))
            lbl = T(name, 17, MUTED)
            grp = VGroup(VGroup(bar, knob), lbl).arrange(DOWN, buff=0.20)
            sliders.add(grp)
        sliders.arrange(RIGHT, buff=0.75).move_to([0, -1.15, 0])
        self.sliders = sliders

        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.15) for s in sliders],
                              lag_ratio=0.15), run_time=1.3)
        self.say("A handful of geometric and electrical parameters set the whole trajectory.",
                 wait=1.6)

    # -- what goes wrong ---------------------------------------------------
    def act_failures(self):
        self.say("Push them a little and the beam scallops —")
        self.play(self.p_amp.animate.set_value(0.235),
                  self.p_wai.animate.set_value(0.55), run_time=2.2)
        self.wait(0.8)

        burn = VGroup(*[Dot([x, G_AXIS + s * G_WALL, 0], radius=0.09, color=BAD)
                        for x, s in [(-0.70, 1), (1.90, -1), (4.50, 1)]])
        self.say("— and where it touches the helix it burns it. That tube is scrap.")
        self.play(LaggedStart(*[Flash(d, color=BAD, line_length=0.22, num_lines=10)
                                for d in burn], lag_ratio=0.25),
                  FadeIn(burn), run_time=1.6)
        self.wait(1.0)

        self.say("Get them right and the beam threads the whole tube untouched.")
        self.play(FadeOut(burn),
                  self.p_amp.animate.set_value(0.040),
                  self.p_wai.animate.set_value(-0.08),
                  self.p_rmin.animate.set_value(0.20), run_time=2.4)
        self.wait(1.4)

    # -- the cost ----------------------------------------------------------
    def act_cost(self):
        self.play(FadeOut(self.sliders), run_time=0.6)
        self.say("The trouble: the only honest way to know is to solve the physics.",
                 "Monte-Carlo particle tracking in ANSYS — hours of CPU for a single configuration.",
                 wait=2.6)

        grid = VGroup()
        rng = np.random.default_rng(3)
        for i in range(11):
            for j in range(7):
                d = Dot([0, 0, 0], radius=0.045, color=FAINT, fill_opacity=0.35)
                d.move_to([-3.0 + i * 0.60, -0.60 - j * 0.28, 0])
                grid.add(d)
        self.play(FadeIn(grid), run_time=0.8)
        picked = [grid[i] for i in rng.choice(len(grid), 9, replace=False)]
        self.play(LaggedStart(*[d.animate.set_color(WARN).set_opacity(1).scale(1.5)
                                for d in picked], lag_ratio=0.12), run_time=1.6)
        self.say("The design space is enormous. The simulation budget is not.", wait=2.2)
        self.grid = grid

    # -- the answer --------------------------------------------------------
    def act_surrogate(self):
        self.play(FadeOut(VGroup(self.stage, self.beam_area, self.grid)), run_time=0.8)
        self.remove(self.beam_area)

        def card(title, sub, w=3.3, accent=False):
            box = RoundedRectangle(width=w, height=1.5, corner_radius=0.14,
                                   stroke_color=ACCENT if accent else FAINT,
                                   stroke_width=1.4, fill_color=PANEL, fill_opacity=0.5)
            txt = VGroup(T(title, 22, ACCENT_LT if accent else TXT, weight=MEDIUM),
                         T(sub, 16, MUTED, wrap=26)).arrange(DOWN, buff=0.14)
            return VGroup(box, txt.move_to(box.get_center()))

        c1 = card("gun parameters", "voltage, geometry, field")
        c2 = card("learned model", "AutoML + neural network", accent=True)
        c3 = card("beam trajectory", "in milliseconds")
        row = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.85).move_to([0, 0.95, 0])
        a1 = Arrow(c1.get_right(), c2.get_left(), buff=0.12, stroke_width=2.5,
                   color=FAINT, max_tip_length_to_length_ratio=0.18)
        a2 = Arrow(c2.get_right(), c3.get_left(), buff=0.12, stroke_width=2.5,
                   color=FAINT, max_tip_length_to_length_ratio=0.18)

        self.play(FadeIn(c1, shift=RIGHT * 0.2), run_time=0.6)
        self.play(GrowArrow(a1), FadeIn(c2, scale=0.9), run_time=0.7)
        self.play(GrowArrow(a2), FadeIn(c3, shift=RIGHT * 0.2), run_time=0.7)

        self.say("The simulations become the training data, and a model learns the map.",
                 "A few hundred runs bought a surrogate that answers in milliseconds.",
                 wait=3.0)

        foot = T("Monte-Carlo simulation  ·  H2O AutoML  ·  TensorFlow", 19, FAINT)
        foot.move_to([0, -0.95, 0])
        self.play(FadeIn(foot), run_time=0.8)
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        self.wait(0.3)


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
    AMP    = 0.48                                 # drawn amplitude at the output
    NSEG   = 360                                  # pieces the wire is cut into

    WIRE   = "#3e6486"                            # the wire, unlit
    GLOW   = "#ffd27a"                            # the wave running along it

    def strength(self, x):
        """Envelope of the wave: it grows exponentially down the tube."""
        return np.exp(np.clip(x - X_H0, 0, None) / L_GAIN) / 9.0

    def e_field(self, x, t):
        return self.strength(x) * np.sin(self.beam.k * (x - self.VPH * t))

    # ----------------------------------------------------------------------
    def construct(self):
        tube = build_tube()
        tube.remove(tube.helix)                   # replaced by the lit version
        self.beam = Beam(v_phase=self.VPH, lam=self.LAM)
        self.beam.coupling.set_value(1.0)

        wire = self.lit_helix()
        magnets = self.magnet_row()
        wave = always_redraw(self.wave_curve)
        chrome = self.annotate()

        dt = 1 / config.frame_rate
        for _ in range(int(round(2 * self.T_LOOP / dt))):   # let the bunches settle
            self.beam.step(dt)

        self.add(tube, magnets, wire, wave, self.beam.dots, chrome)
        self.beam.dots.add_updater(lambda m, dt: self.beam.step(dt))
        self.wait(self.T_LOOP)

    # -- the wave, running along the wire itself ---------------------------
    def lit_helix(self):
        """The helix cut into short pieces, each lit by the wave passing through it.

        The signal moves along the *wire* at the speed of light. Six wavelengths
        fit on the wire of the whole helix, and the wave covers that wire in one
        loop — so the lit beads slide right round every turn while the pattern
        as a whole only creeps forward, at the speed of the beam. That gap is
        the whole point of a slow-wave structure.
        """
        pts, axial = helix_samples(self.NSEG + 1)
        segs = VGroup(*[Line(pts[i], pts[i + 1], stroke_color=self.WIRE,
                             stroke_width=1.8) for i in range(self.NSEG)])
        base, glow = ManimColor(self.WIRE), ManimColor(self.GLOW)

        def paint(_):
            u = self.beam.t / self.T_LOOP
            for i, seg in enumerate(segs):
                ph = TAU * 6 * (i / self.NSEG - u)
                bead = (0.5 * (1 + np.sin(ph))) ** 4        # narrow, so it reads as motion
                g = bead * (0.45 + 0.55 * self.strength(axial[i]))
                seg.set_stroke(color=interpolate_color(base, glow, g),
                               width=1.8 + 4.6 * g, opacity=0.75 + 0.25 * g)
        segs.add_updater(paint)
        paint(None)
        return segs

    # -- the field that wave puts on the axis, where the beam is -----------
    def wave_curve(self):
        t = self.beam.t
        return FunctionGraph(lambda x: AXIS_Y + self.AMP * self.e_field(x, t),
                             x_range=[X_H0, X_H1, 0.015],
                             color="#ffd27a", stroke_width=2.8)

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
        magnets = tag("focusing magnets — they keep the beam pinched", -0.37, -0.98,
                      [-0.37, -0.31, 0], size=19)

        rf_in = VGroup(T("RF in", 21, ACCENT_LT), T("weak signal", 18, FAINT)
                       ).arrange(DOWN, buff=0.09)
        rf_in.move_to([0, -0.45, 0]).align_to([X_H0 - 0.30, 0, 0], RIGHT)
        rf_out = VGroup(T("RF out", 21, ACCENT_LT), T("amplified", 18, FAINT)
                        ).arrange(DOWN, buff=0.09)
        rf_out.move_to([0, -0.45, 0]).align_to([X_H1 + 0.30, 0, 0], LEFT)

        key = T("Along the wire the signal runs at nearly the speed of light. Coiled into a "
                "helix, it can only creep forward — at the speed of the electrons.",
                19, MUTED, wrap=82)
        key.move_to([0, -1.78, 0])

        return VGroup(title, above, electrons, magnets, rf_in, rf_out, key)

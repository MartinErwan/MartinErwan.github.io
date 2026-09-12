"""
What a manufacturing tolerance on the focusing magnets does to the beam.

    manim -r 1600,900 --fps 30 --format png magnets.py MagnetScatter

A traveling-wave tube holds its beam with a stack of permanent magnets of
alternating polarity. The focusing comes from the *periodicity* of that field,
so the beam is only as good as the magnets are alike. This scene scales one
fixed pattern of manufacturing deviations up and back down, and shows what
comes out of it: the field goes ragged, the envelope scallops, and the tail of
the distribution starts to touch the helix.

The envelope is integrated, not drawn: r'' = K/r - kappa B(z)^2 r, the paraxial
envelope equation for periodic permanent-magnet focusing, with K the space
charge term. The histogram is the same equation run over 400 draws of the
magnet deviations at the tolerance currently on screen — a Monte-Carlo study in
miniature, which is what the project it illustrates actually did.
"""

from manim import *
import numpy as np

from twt import (TWTScene, T, TXT, MUTED, FAINT, ACCENT, ACCENT_LT, ELECTRON, WARN,
                 BAD, BG)

config.background_color = BG

# --------------------------------------------------------------------------
# The tube
# --------------------------------------------------------------------------
Z0, Z1 = -5.50, 5.50
N_MAG = 14
PERIOD = (Z1 - Z0) / N_MAG
AXIS_Y = 1.75
R_WALL = 0.55
Y_MAG = 0.87             # magnet rows, above and below the axis
H_MAG = 0.26

FIELD_Y, FIELD_A = -0.15, 0.36
HIST_X0, HIST_X1, HIST_Y, HIST_H = 0.25, 6.55, -2.85, 1.10
BAR_X0, BAR_X1, BAR_Y = -6.50, -2.10, -1.95

# envelope equation constants, tuned so a perfect stack gives a quiet beam
# Tuned so that a perfect stack advances the betatron phase by ~1.2 rad per
# magnet period — well inside the stable band — and settles at r ~ 0.17 with
# the small ripple a real periodic-focused beam has.
KAPPA = 3.5              # focusing strength of the field
K_PERV = 0.0507          # space charge
NZ = 700
GOOD = "#59d49b"


def sigma_at(t, t_loop, smax):
    """Scatter over the loop: nought at both ends, so the clip joins up."""
    return smax * (1 - np.cos(TAU * t / t_loop)) / 2


class MagnetScatter(TWTScene):

    T_LOOP = 8.0
    SMAX = 0.24              # widest scatter drawn, in units of nominal size
    DRAWS = 400              # Monte-Carlo draws behind the histogram
    LEVELS = 49              # scatter levels the histogram is precomputed at

    # -- physics -----------------------------------------------------------
    def field(self, z, dev):
        """Axial field of the stack; dev is one deviation per magnet."""
        centres = Z0 + (np.arange(N_MAG) + 0.5) * PERIOD
        sign = (-1.0) ** np.arange(N_MAG)
        w = 0.40 * PERIOD * (1 + dev)                     # a bigger magnet, a wider lobe
        b = ((sign * (1 + dev))[:, None]
             * np.exp(-((z[None, :] - centres[:, None]) / w[:, None]) ** 2))
        return b.sum(axis=0)

    @staticmethod
    def transmission(r):
        """Fraction of the beam that reaches the collector.

        A hard-edged beam of radius r carries its current uniformly over the
        area, so an excursion out to r > R_WALL scrapes everything outside the
        wall: what is left is (R_WALL / r)^2 of the current. The worst
        excursion sets the loss — once a shell is gone it is gone.
        """
        peak = np.max(r, axis=-1)
        return np.minimum(1.0, (R_WALL / np.maximum(peak, 1e-6)) ** 2)

    def envelope(self, devs):
        """r(z) for a stack of draws. devs: (M, N_MAG) -> (M, NZ)."""
        z = np.linspace(Z0, Z1, NZ)
        dz = z[1] - z[0]
        b2 = np.stack([self.field(z, d) for d in np.atleast_2d(devs)]) ** 2
        m = b2.shape[0]
        r = np.full(m, self.r_matched)
        rp = np.zeros(m)
        out = np.empty((m, NZ))
        for j in range(NZ):
            out[:, j] = r
            rp += (K_PERV / r - KAPPA * b2[:, j] * r) * dz
            r = np.clip(r + rp * dz, 0.03, 1.4)
        return z, out

    def setup_physics(self):
        self.r_matched = 0.17
        self.rng = np.random.default_rng(5)
        # The stack drawn on screen is a genuine draw from the same distribution
        # as the cloud — not a normalised one, which would always be milder than
        # its own histogram. This one loses nothing at half scatter and about a
        # quarter of the beam at full scatter.
        self.pattern = np.random.default_rng(409).normal(0, 1, N_MAG)
        # the Monte-Carlo cloud, precomputed once per scatter level
        self.levels = np.linspace(0, self.SMAX, self.LEVELS)
        cloud = self.rng.normal(0, 1, (self.DRAWS, N_MAG))
        self.edges = np.linspace(0.55, 1.0, 25)
        self.hist, self.p5 = [], []
        for s in self.levels:
            _, r = self.envelope(cloud * s)
            t = self.transmission(r[:, NZ // 4:])
            h, _ = np.histogram(np.clip(t, self.edges[0], self.edges[-1] - 1e-9),
                                bins=self.edges)
            # square root, or the spike at "no loss at all" flattens its own tail
            h = np.sqrt(h)
            self.hist.append(h / max(h.max(), 1))
            self.p5.append(float(np.percentile(t, 5)))
        self.hist = np.array(self.hist)

    def scatter_now(self):
        return sigma_at(self.tt.get_value(), self.T_LOOP, self.SMAX)

    def devs_now(self):
        return self.pattern * self.scatter_now()

    # ----------------------------------------------------------------------
    def construct(self):
        self.setup_physics()
        self.tt = ValueTracker(0.0)
        self.tt.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self.tt)

        self.add(self.chrome())
        self.add(always_redraw(self.magnet_stack))
        self.add(self.tube_walls())
        self.add(always_redraw(self.beam_band))
        self.add(always_redraw(self.field_trace))
        self.add(always_redraw(self.scatter_bar))
        self.add(always_redraw(self.histogram))
        self.add(always_redraw(self.verdict))
        self.wait(self.T_LOOP)

    # -- the tube ----------------------------------------------------------
    def tube_walls(self):
        up = Line([Z0, AXIS_Y + R_WALL, 0], [Z1, AXIS_Y + R_WALL, 0],
                  stroke_color=ACCENT_LT, stroke_width=2)
        dn = up.copy().shift(DOWN * 2 * R_WALL)
        axis = DashedLine([Z0, AXIS_Y, 0], [Z1, AXIS_Y, 0], dash_length=0.09,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.45)
        lbl = T("helix wall", 17, FAINT).move_to([Z1 + 0.95, AXIS_Y + R_WALL, 0])
        return VGroup(axis, up, dn, lbl)

    def magnet_stack(self):
        dev = self.devs_now()
        g = VGroup()
        for i in range(N_MAG):
            x = Z0 + (i + 0.5) * PERIOD
            w = PERIOD * 0.74 * (1 + dev[i])
            h = H_MAG * (1 + 0.5 * dev[i])
            for sgn in (1, -1):
                north = (i % 2 == 0) == (sgn > 0)
                col = "#4f7fd6" if north else "#9a5ad6"
                g.add(RoundedRectangle(width=w, height=h, corner_radius=0.05,
                                       stroke_width=0, fill_color=col, fill_opacity=0.9)
                      .move_to([x, AXIS_Y + sgn * Y_MAG, 0]))
        return g

    def beam_band(self):
        """The core that gets through, and in red the shell scraped off on the way."""
        z, r = self.envelope(self.devs_now())
        r = r[0]
        core = np.minimum(r, R_WALL)

        def band(lo, hi, colour, fill):
            top = np.stack([z, AXIS_Y + hi, np.zeros_like(z)], axis=1)
            bot = np.stack([z[::-1], AXIS_Y + lo[::-1], np.zeros_like(z)], axis=1)
            a = VMobject(stroke_width=0, fill_color=colour, fill_opacity=fill)
            a.set_points_as_corners(np.concatenate([top, bot, top[:1]]))
            return a

        g = VGroup(band(-core, core, ELECTRON, 0.22))
        if r.max() > R_WALL:                      # what never makes it to the collector
            g.add(band(np.full_like(r, R_WALL), np.maximum(r, R_WALL), BAD, 0.85),
                  band(-np.maximum(r, R_WALL), np.full_like(r, -R_WALL), BAD, 0.85))
            # below the tube: the only band of clear space near the excursion
            lost = T("scraped off on the wall — these electrons never arrive", 17, BAD)
            lost.move_to([float(np.clip(z[int(np.argmax(r))], Z0 + 3.0, Z1 - 3.0)), 0.62, 0])
            g.add(lost)
        for sgn in (1, -1):
            e = VMobject(stroke_color=BAD if r.max() > R_WALL else ELECTRON,
                         stroke_width=2.4)
            e.set_points_as_corners(
                np.stack([z, AXIS_Y + sgn * r, np.zeros_like(z)], axis=1))
            g.add(e)
        return g

    # -- the field ---------------------------------------------------------
    def field_trace(self):
        z = np.linspace(Z0, Z1, 700)
        b = self.field(z, self.devs_now())
        nominal = self.field(z, np.zeros(N_MAG))
        ref = VMobject(stroke_color=FAINT, stroke_width=1.4, stroke_opacity=0.75)
        ref.set_points_as_corners(
            np.stack([z, FIELD_Y + FIELD_A * nominal, np.zeros_like(z)], axis=1))
        ref = DashedVMobject(ref, num_dashes=150, dashed_ratio=0.45)
        cur = VMobject(stroke_color=WARN, stroke_width=2.6)
        cur.set_points_as_corners(
            np.stack([z, FIELD_Y + FIELD_A * b, np.zeros_like(z)], axis=1))
        return VGroup(ref, cur)

    # -- the controls ------------------------------------------------------
    def scatter_bar(self):
        u = self.scatter_now() / self.SMAX
        track = Line([BAR_X0, BAR_Y, 0], [BAR_X1, BAR_Y, 0],
                     stroke_color=FAINT, stroke_width=3)
        fill = Line([BAR_X0, BAR_Y, 0], [BAR_X0 + u * (BAR_X1 - BAR_X0), BAR_Y, 0],
                    stroke_color=WARN, stroke_width=6)
        knob = Dot([BAR_X0 + u * (BAR_X1 - BAR_X0), BAR_Y, 0], radius=0.085, color=WARN)
        title = T("magnet size scatter", 20, TXT).next_to(track, UP, buff=0.30)
        ends = VGroup(T("all identical", 16, FAINT).move_to([BAR_X0 + 0.75, BAR_Y - 0.32, 0]),
                      T("loose tolerance", 16, FAINT).move_to([BAR_X1 - 0.80, BAR_Y - 0.32, 0]))
        return VGroup(track, fill, knob, title, ends)

    def verdict(self):
        """What the study actually measures: how much of the beam gets through."""
        _, r = self.envelope(self.devs_now())
        t = float(self.transmission(r[:, NZ // 4:])[0])
        col = GOOD if t > 0.985 else (WARN if t > 0.93 else BAD)
        num = T(f"{t * 100:.0f} %", 44, col, weight=MEDIUM)
        lbl = T("of the beam reaches the collector", 19, MUTED)
        g = VGroup(num, lbl).arrange(DOWN, buff=0.16)
        g.move_to([(BAR_X0 + BAR_X1) / 2, BAR_Y - 1.25, 0])
        return g

    # -- the Monte-Carlo cloud --------------------------------------------
    def histogram(self):
        i = int(np.clip(np.searchsorted(self.levels, self.scatter_now()),
                        0, self.LEVELS - 1))
        h, e = self.hist[i], self.edges
        span, lo, hi = HIST_X1 - HIST_X0, e[0], e[-1]

        def sx(v):
            return HIST_X0 + span * (v - lo) / (hi - lo)

        bars = VGroup()
        for k, v in enumerate(h):
            if v <= 0:
                continue
            x0, x1 = sx(e[k]), sx(e[k + 1])
            height = max(v * HIST_H, 0.004)
            bars.add(Rectangle(width=(x1 - x0) * 0.88, height=height, stroke_width=0,
                               fill_color=ACCENT, fill_opacity=0.65)
                     .move_to([(x0 + x1) / 2, HIST_Y + height / 2, 0]))

        base = Line([HIST_X0 - 0.1, HIST_Y, 0], [HIST_X1 + 0.1, HIST_Y, 0],
                    stroke_color=FAINT, stroke_width=1.5)
        ticks = VGroup()
        for v in (0.6, 0.8, 1.0):
            ticks.add(T(f"{v * 100:.0f} %", 15, FAINT).move_to([sx(v), HIST_Y - 0.22, 0]))

        # where the stack drawn above sits in that distribution
        _, r = self.envelope(self.devs_now())
        t = float(self.transmission(r[:, NZ // 4:])[0])
        needle = DashedLine([sx(t), HIST_Y, 0], [sx(t), HIST_Y + HIST_H + 0.2, 0],
                            dash_length=0.08, stroke_color=WARN, stroke_width=2)
        ntag = T("the stack above", 15, WARN).next_to(needle, UP, buff=0.05)
        if sx(t) > HIST_X1 - 1.1:
            ntag.shift(LEFT * 0.9)

        cap = T("how much gets through, over 400 magnet stacks", 18, MUTED)
        cap.move_to([(HIST_X0 + HIST_X1) / 2, HIST_Y - 0.62, 0])
        p5 = self.p5[i]
        worst = T(f"the worst 5 % of stacks deliver {p5 * 100:.0f} % or less",
                  18, GOOD if p5 > 0.985 else (WARN if p5 > 0.93 else BAD))
        worst.move_to([(HIST_X0 + HIST_X1) / 2, HIST_Y - 0.98, 0])
        return VGroup(base, bars, needle, ntag, ticks, cap, worst)

    # -- fixed text --------------------------------------------------------
    def chrome(self):
        title = T("What a magnet tolerance costs in beam power", 27, TXT,
                  weight=MEDIUM).move_to([0, 3.66, 0])
        sub = T("the focusing comes from the field being periodic — break it and electrons "
                "are lost to the walls on the way", 19, FAINT).move_to([0, 3.20, 0])
        flab = T("magnetic field along the axis", 18, MUTED)
        flab.move_to([0, FIELD_Y - 0.80, 0])
        return VGroup(title, sub, flab)

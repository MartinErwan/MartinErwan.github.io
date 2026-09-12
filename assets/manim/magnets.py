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
HIST_X0, HIST_X1, HIST_Y, HIST_H = 0.25, 6.55, -3.05, 1.15
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
        # the stack drawn on screen: picked so that it is comfortably inside the
        # tube at half scatter and grazes the helix at full scatter
        self.pattern = np.random.default_rng(300).normal(0, 1, N_MAG)
        self.pattern /= np.abs(self.pattern).max()
        # the Monte-Carlo cloud, precomputed once per scatter level
        self.levels = np.linspace(0, self.SMAX, self.LEVELS)
        cloud = self.rng.normal(0, 1, (self.DRAWS, N_MAG))
        self.hist = []
        edges = np.linspace(0.10, 0.95, 27)
        self.edges = edges
        for s in self.levels:
            _, r = self.envelope(cloud * s)
            peak = r[:, NZ // 4:].max(axis=1)
            h, _ = np.histogram(np.clip(peak, edges[0], edges[-1] - 1e-6), bins=edges)
            self.hist.append(h / max(h.max(), 1))
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
        z, r = self.envelope(self.devs_now())
        r = r[0]
        hit = r.max() > R_WALL
        col = BAD if hit else ELECTRON
        top = np.stack([z, AXIS_Y + r, np.zeros_like(z)], axis=1)
        bot = np.stack([z[::-1], AXIS_Y - r[::-1], np.zeros_like(z)], axis=1)
        area = VMobject(stroke_width=0, fill_color=col, fill_opacity=0.22)
        area.set_points_as_corners(np.concatenate([top, bot, top[:1]]))
        edge = VGroup()
        for pts in (top, bot):
            e = VMobject(stroke_color=col, stroke_width=2.4)
            e.set_points_as_corners(pts)
            edge.add(e)
        return VGroup(area, edge)

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
        z, r = self.envelope(self.devs_now())
        hit = r[0].max() > R_WALL
        col = BAD if hit else GOOD
        txt = "the beam is touching the helix" if hit else "the beam clears the helix"
        dot = Dot(radius=0.09, color=col)
        lbl = T(txt, 19, col)
        g = VGroup(dot, lbl).arrange(RIGHT, buff=0.22)
        g.move_to([(BAR_X0 + BAR_X1) / 2, BAR_Y - 0.95, 0])
        return g

    # -- the Monte-Carlo cloud --------------------------------------------
    def histogram(self):
        i = int(np.clip(np.searchsorted(self.levels, self.scatter_now()),
                        0, self.LEVELS - 1))
        h = self.hist[i]
        e = self.edges
        span = HIST_X1 - HIST_X0
        g = VGroup()
        for k, v in enumerate(h):
            x0 = HIST_X0 + span * (e[k] - e[0]) / (e[-1] - e[0])
            x1 = HIST_X0 + span * (e[k + 1] - e[0]) / (e[-1] - e[0])
            over = e[k] >= R_WALL
            if v <= 0:
                continue
            g.add(Rectangle(width=(x1 - x0) * 0.88, height=max(v * HIST_H, 0.004),
                            stroke_width=0, fill_color=BAD if over else ACCENT,
                            fill_opacity=0.85 if over else 0.55)
                  .move_to([(x0 + x1) / 2, HIST_Y + max(v * HIST_H, 0.004) / 2, 0]))
        base = Line([HIST_X0 - 0.1, HIST_Y, 0], [HIST_X1 + 0.1, HIST_Y, 0],
                    stroke_color=FAINT, stroke_width=1.5)
        xw = HIST_X0 + span * (R_WALL - e[0]) / (e[-1] - e[0])
        wall = DashedLine([xw, HIST_Y, 0], [xw, HIST_Y + HIST_H + 0.18, 0],
                          dash_length=0.08, stroke_color=BAD, stroke_width=1.6)
        wlbl = T("helix wall", 15, BAD).next_to(wall, UP, buff=0.05)
        cap = T("peak beam radius over 400 magnet stacks", 18, MUTED)
        cap.move_to([(HIST_X0 + HIST_X1) / 2, HIST_Y - 0.36, 0])
        return VGroup(base, g, wall, wlbl, cap)

    # -- fixed text --------------------------------------------------------
    def chrome(self):
        title = T("What a magnet tolerance does to the beam", 27, TXT,
                  weight=MEDIUM).move_to([0, 3.66, 0])
        sub = T("the focusing comes from the field being periodic — the beam is only as good "
                "as the magnets are alike", 19, FAINT).move_to([0, 3.20, 0])
        flab = T("magnetic field along the axis", 18, MUTED)
        flab.move_to([0, FIELD_Y - 0.80, 0])
        return VGroup(title, sub, flab)

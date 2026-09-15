"""
Inside a Traveling-Wave Tube — the same figure, in three dimensions.

A 3-D companion to `TWTLoop` in twt.py: the helix is a real helix, so the
signal is seen spiralling round the beam instead of oscillating past it.

    manim -r 1600,900 --fps 30 --format png twt3d.py TWTLoop3D

The physics and the timing are the same as the 2-D version: the wave covers
the whole wire in one loop and six wavelengths fit on it, so the clip closes
on itself exactly.
"""

from manim import *
import numpy as np

from twt import (T, Beam, L_GAIN, TXT, MUTED, FAINT, ACCENT, ACCENT_LT,
                 ELECTRON, WARN, BG)

config.background_color = BG

# --------------------------------------------------------------------------
# Geometry (world units)
# --------------------------------------------------------------------------
X_CATH3 = -5.15          # emitting surface
X_ANOD3 = -4.05          # anode aperture
X_H0_3  = -3.55          # helix entrance
X_H1_3  =  3.95          # helix exit
X_COL3  =  4.45          # collector mouth
X_END3  =  5.35
R_HELIX3 = 0.78
R_MAG3   = 1.14
R_CATH3  = 0.46
R_BEAM3  = 0.115
TURNS3   = 8
Z_PORT   = -1.70         # where the RF connectors sit, below the tube

WIRE = "#4b7ba3"
GLOW = "#ffd27a"


def helix3(n, phase=-PI / 2):
    """Points of the real helix, plus the axial position of each sample."""
    th = np.linspace(0, TURNS3 * TAU, n) + phase
    x = np.linspace(X_H0_3, X_H1_3, n)
    return np.stack([x, R_HELIX3 * np.cos(th), R_HELIX3 * np.sin(th)], axis=1), x


def ring(radius, x, color, width=4, opacity=1.0):
    """A circle encircling the axis at x."""
    c = Circle(radius=radius, stroke_color=color, stroke_width=width,
               stroke_opacity=opacity)
    return c.rotate(PI / 2, axis=UP).shift(RIGHT * x)


class Beam3D(Beam):
    """The 2-D beam dynamics, with the particles spread over a real disc."""

    def __init__(self, *args, **kwargs):
        self.facing = kwargs.pop("facing")        # matrix that turns a disc to the camera
        super().__init__(*args, **kwargs)
        rng = np.random.default_rng(11)
        a = rng.uniform(0, TAU, self.n)
        r = np.sqrt(rng.uniform(0, 1, self.n))
        self.oy, self.oz = r * np.cos(a), r * np.sin(a)
        proto = Circle(radius=0.048, stroke_width=0, fill_color=ELECTRON,
                       fill_opacity=1).apply_matrix(self.facing)
        self.dots = VGroup(*[proto.copy() for _ in range(self.n)])
        self._place()

    def _place(self):
        if not hasattr(self, "oy"):               # called once before we are ready
            return
        conv = np.clip((self.x - self.X_EMIT) / (self.X_ACC - self.X_EMIT), 0, 1)
        radius = R_CATH3 + (R_BEAM3 - R_CATH3) * conv ** 0.7
        for i, dot in enumerate(self.dots):
            dot.move_to([self.x[i], self.oy[i] * radius[i], self.oz[i] * radius[i]])
            dot.set_opacity(0.0 if self.x[i] > 5.15 else 1.0)   # caught by the collector


class TWTLoop3D(ThreeDScene):
    """The wave spiralling down the helix, around the electron beam."""

    T_LOOP = 7.2
    LAM    = (X_H1_3 - X_H0_3) / 6
    VPH    = (X_H1_3 - X_H0_3) / T_LOOP
    NSEG   = 340
    PHI, THETA = 86 * DEGREES, -72 * DEGREES
    ZOOM = 1.18

    # -- the growing envelope ---------------------------------------------
    def strength(self, x):
        return np.exp(np.clip(x - X_H0_3, 0, None) / L_GAIN) / 9.0

    def facing_matrix(self):
        """Rotation that turns a disc in the xy-plane to face the camera."""
        d = np.array([np.sin(self.PHI) * np.cos(self.THETA),
                      np.sin(self.PHI) * np.sin(self.THETA),
                      np.cos(self.PHI)])
        z = np.array([0.0, 0.0, 1.0])
        v, c = np.cross(z, d), float(np.dot(z, d))
        if np.linalg.norm(v) < 1e-9:
            return np.eye(3)
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + vx + vx @ vx / (1 + c)

    # ----------------------------------------------------------------------
    def construct(self):
        self.set_camera_orientation(phi=self.PHI, theta=self.THETA, zoom=self.ZOOM)
        M = self.facing_matrix()

        self.beam = Beam3D(n=150, v_phase=self.VPH, lam=self.LAM, facing=M)
        self.beam.coupling.set_value(1.0)
        self.beam.X_EMIT = X_CATH3
        self.beam.X_ACC = X_ANOD3

        gun, collector = self.gun_and_collector(M)
        magnets = self.magnet_rings()
        circuit, ports = self.lit_circuit()
        axis = DashedLine([X_CATH3, 0, 0], [X_END3, 0, 0], dash_length=0.10,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.45)

        dt = 1 / config.frame_rate
        for _ in range(int(round(2 * self.T_LOOP / dt))):
            self.beam.step(dt)

        self.add(axis, gun, collector, magnets, circuit, ports, self.beam.dots)
        self.add_fixed_in_frame_mobjects(*self.chrome(), *self.signal_lane())
        self.beam.dots.add_updater(lambda m, dt: self.beam.step(dt))
        self.wait(self.T_LOOP)

    # -- gun and collector --------------------------------------------------
    def gun_and_collector(self, M):
        cathode = Circle(radius=R_CATH3, stroke_color=WARN, stroke_width=5,
                         fill_color=WARN, fill_opacity=0.18)
        cathode.rotate(PI / 2, axis=UP).shift(RIGHT * X_CATH3)
        focus = ring(R_CATH3 + 0.34, X_CATH3 + 0.45, MUTED, 3, 0.7)
        anode = ring(0.52, X_ANOD3, MUTED, 5, 0.85)
        gun = VGroup(cathode, focus, anode)

        mouth, back = ring(0.72, X_COL3, MUTED, 4, 0.9), ring(0.42, X_END3, MUTED, 4, 0.9)
        struts = VGroup(*[Line([X_COL3, 0.72 * np.cos(a), 0.72 * np.sin(a), ][0:3],
                               [X_END3, 0.42 * np.cos(a), 0.42 * np.sin(a)],
                               stroke_color=MUTED, stroke_width=2, stroke_opacity=0.6)
                          for a in np.linspace(0, TAU, 9)[:-1]])
        return gun, VGroup(mouth, back, struts)

    # -- the magnets --------------------------------------------------------
    def magnet_rings(self):
        g = VGroup()
        for i, x in enumerate(np.arange(X_H0_3 + 0.55, X_H1_3 - 0.40, 0.92)):
            col = "#4f7fd6" if i % 2 == 0 else "#9a5ad6"
            g.add(ring(R_MAG3, x, col, 4, 0.45))
        return g

    # -- the signal, lit along the wire it travels -------------------------
    def lit_circuit(self):
        pts, axial = helix3(self.NSEG + 1)
        pitch = (X_H1_3 - X_H0_3) / TURNS3
        s_helix = TURNS3 * float(np.hypot(TAU * R_HELIX3, pitch))
        ds_h = s_helix / self.NSEG

        n_l = 22
        z_join = -R_HELIX3
        ds_l = (z_join - Z_PORT) / n_l
        lead_in = [np.array([X_H0_3, 0, z]) for z in np.linspace(Z_PORT, z_join, n_l + 1)]
        lead_out = [np.array([X_H1_3, 0, z]) for z in np.linspace(z_join, Z_PORT, n_l + 1)]

        pieces, s = [], 0.0
        for a, b in zip(lead_in[:-1], lead_in[1:]):
            pieces.append((a, b, s + ds_l / 2, self.strength(X_H0_3))); s += ds_l
        for i in range(self.NSEG):
            pieces.append((pts[i], pts[i + 1], s + ds_h / 2, self.strength(axial[i]))); s += ds_h
        for a, b in zip(lead_out[:-1], lead_out[1:]):
            pieces.append((a, b, s + ds_l / 2, self.strength(X_H1_3))); s += ds_l

        segs = VGroup(*[Line(a, b, stroke_color=WIRE, stroke_width=3.0)
                        for a, b, _, _ in pieces])
        base, glow = ManimColor(WIRE), ManimColor(GLOW)
        lam_w, v_wire = s_helix / 6, s_helix / self.T_LOOP

        def paint(_):
            t = self.beam.t
            for seg, (_, _, sm, env) in zip(segs, pieces):
                bead = (0.5 * (1 + np.sin(TAU * (sm - v_wire * t) / lam_w))) ** 4
                g = bead * (0.45 + 0.55 * env)
                seg.set_stroke(color=interpolate_color(base, glow, g),
                               width=3.0 + 5.4 * g, opacity=0.75 + 0.25 * g)
        segs.add_updater(paint)
        paint(None)

        ports = VGroup(*[Dot3D(point=[x, 0, Z_PORT], radius=0.09, color=ACCENT,
                               resolution=(8, 8)) for x in (X_H0_3, X_H1_3)])
        return segs, ports

    # ----------------------------------------------------------------------
    # Chrome. The camera never moves, so screen positions can be written down
    # directly; SX/SY are the measured projection of the world axes.
    # ----------------------------------------------------------------------
    @staticmethod
    def SX(wx):
        return 1.126 * wx + 0.47

    @staticmethod
    def SY(wz):
        return 1.045 * wz - 0.04

    def chrome(self):
        def tag(txt, x, y, tip, size=20, color=MUTED):
            lbl = T(txt, size, color).move_to([x, y, 0])
            d = UP if y > tip[1] else DOWN
            start = lbl.get_edge_center(-d) + 0.06 * (-d)
            return VGroup(lbl, Line(start, tip, stroke_color=FAINT,
                                    stroke_width=1, stroke_opacity=0.8))

        title = T("How a traveling-wave tube amplifies a signal", 26, TXT,
                  weight=MEDIUM).move_to([0, 3.62, 0])
        sub = T("along the wire it runs at nearly the speed of light — coiled into a helix "
                "it only creeps forward", 18, FAINT).move_to([0, 3.14, 0])

        parts = VGroup(
            tag("electron gun", -5.30, 2.30, [self.SX(X_ANOD3) - 0.3, 0.62, 0]),
            tag("helix — the slow-wave structure", -1.20, 2.72, [-1.20, 0.92, 0]),
            tag("focusing magnets", 3.40, 2.20, [3.40, 1.28, 0]),
            tag("collector", 6.05, 1.75, [self.SX(X_COL3) + 0.4, 0.78, 0]),
            tag("electrons", -4.95, -1.15, [-4.42, -0.20, 0], size=19, color=ELECTRON),
        )

        rf_in = VGroup(T("RF in", 20, ACCENT_LT), T("weak signal", 17, FAINT)
                       ).arrange(DOWN, buff=0.08)
        rf_in.move_to([0, self.SY(Z_PORT), 0]).align_to([self.SX(X_H0_3) - 0.30, 0, 0], RIGHT)
        rf_out = VGroup(T("RF out", 20, ACCENT_LT), T("amplified", 17, FAINT)
                        ).arrange(DOWN, buff=0.08)
        rf_out.move_to([0, self.SY(Z_PORT), 0]).align_to([self.SX(X_H1_3) + 0.30, 0, 0], LEFT)

        return [title, sub, parts, rf_in, rf_out]

    def signal_lane(self):
        x0, x1, y0, amp = self.SX(X_H0_3), self.SX(X_H1_3), -2.92, 0.42
        xs = np.linspace(x0, x1, 280)
        world = (xs - 0.47) / 1.126

        base = DashedLine([x0, y0, 0], [x1, y0, 0], dash_length=0.08,
                          stroke_color=FAINT, stroke_width=1, stroke_opacity=0.4)
        env = VGroup(*[Line([x0, y0 + k * amp * self.strength(world[0]), 0],
                            [x1, y0 + k * amp * self.strength(world[-1]), 0],
                            stroke_color=GLOW, stroke_width=1.2, stroke_opacity=0.3)
                       for k in (1, -1)])
        drops = VGroup(*[DashedLine([x, self.SY(Z_PORT) - 0.16, 0], [x, y0 + 0.02, 0],
                                    dash_length=0.07, stroke_color=FAINT,
                                    stroke_width=1, stroke_opacity=0.5)
                         for x in (x0, x1)])
        label = VGroup(T("the same signal,", 17, MUTED), T("amplitude only", 17, MUTED)
                       ).arrange(DOWN, buff=0.09).move_to([x0 - 1.55, y0, 0])

        trace = VMobject(stroke_color=GLOW, stroke_width=3.0)

        def follow(m):
            ys = y0 + amp * self.strength(world) * np.sin(
                self.beam.k * (world - self.VPH * self.beam.t))
            m.set_points_as_corners(np.stack([xs, ys, np.zeros_like(xs)], axis=1))
        trace.add_updater(follow)
        follow(trace)
        return [base, env, drops, label, trace]

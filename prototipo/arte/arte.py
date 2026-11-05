"""Original watercolour-style floral art for the debutante invitation.

Everything here is generated procedurally (SVG -> PNG via Chromium -> WebP),
so the invitation does not reuse any artwork from the reference platform.
"""
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # prototipo/
BUILD = ROOT / ".construcao"                            # intermédios (SVG/PNG), ignorados pelo git
FONTS = ROOT / "node_modules" / "@fontsource"

# ----------------------------------------------------------------- palettes
PAL = {
    # light -> dark
    "blush": ["#fff6f6", "#fbe1e4", "#f4c5cd", "#e8a2b1", "#d18395", "#ad6077"],
    "rose":  ["#fdecef", "#f7cfd7", "#eeaabb", "#de879d", "#c3667f", "#9c4c64"],
    "ivory": ["#ffffff", "#fcfaf7", "#f3efe9", "#e3e2da", "#c9cbc1", "#a3aaa0"],
    "peach": ["#fff7f1", "#fde6d8", "#f7ceb9", "#eaae96", "#d08f78", "#ab705d"],
    "mauve": ["#f8edf2", "#ead0dc", "#d8adc0", "#bf89a3", "#9d6984", "#764b62"],
}
LEAF = {
    "euc":   ["#dfe8e3", "#c5d4cc", "#aec2b8", "#93aa9f", "#738c81"],
    "sage":  ["#d8e3d3", "#b9cbb2", "#9bb293", "#7d9775", "#5f7959"],
    "olive": ["#e1e6cf", "#c6cfaa", "#a8b487", "#8a976a", "#6b774f"],
}


def polar(cx, cy, r, a):
    t = math.radians(a)
    return (cx + r * math.cos(t), cy + r * math.sin(t))


def f(p):
    return f"{p[0]:.1f},{p[1]:.1f}"


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class Canvas:
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.defs = []
        self.layers = {"back": [], "mid": [], "flowers": [], "front": [], "top": []}
        self.n = 0
        self.rng = random.Random(seed)

    def uid(self, p="i"):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, s, layer="mid"):
        self.layers[layer].append(s)

    def lin(self, p1, p2, stops):
        gid = self.uid("lg")
        st = "".join(
            f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops
        )
        self.defs.append(
            f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
            f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}">{st}</linearGradient>'
        )
        return gid

    def rad(self, c, r, stops, fc=None):
        gid = self.uid("rg")
        st = "".join(
            f'<stop offset="{o}" stop-color="{col}" stop-opacity="{a}"/>' for o, col, a in stops
        )
        fx = f' fx="{fc[0]:.1f}" fy="{fc[1]:.1f}"' if fc else ""
        self.defs.append(
            f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r:.1f}"{fx}>{st}</radialGradient>'
        )
        return gid

    def svg(self, extra_defs=""):
        body = "".join("".join(self.layers[k]) for k in ("back", "mid", "flowers", "front", "top"))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">'
            f"<defs>{FILTERS}{extra_defs}{''.join(self.defs)}</defs>{body}</svg>"
        )


FILTERS = """
<filter id="wc" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="3" seed="7" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="6" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feGaussianBlur in="d" stdDeviation="0.5"/>
</filter>
<filter id="wcleaf" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="3" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feGaussianBlur in="d" stdDeviation="0.4"/>
</filter>
<filter id="bleed" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
<filter id="wash" x="-30%" y="-30%" width="160%" height="160%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="23" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="38" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feGaussianBlur in="d" stdDeviation="7"/>
</filter>
"""


# ------------------------------------------------------------------ petals
def outer_petal(cx, cy, th, phi, rb, ro, rng):
    b1 = polar(cx, cy, rb, th - phi * 0.55)
    b2 = polar(cx, cy, rb, th + phi * 0.55)
    o1 = polar(cx, cy, ro * 0.84, th - phi)
    o2 = polar(cx, cy, ro * 0.84, th + phi)
    notch = rng.uniform(0.94, 0.99)
    a = polar(cx, cy, ro * notch, th + rng.uniform(-4, 4))
    return (
        f"M{f(b1)} C{f(polar(cx, cy, ro * 0.5, th - phi * 1.18))} {f(polar(cx, cy, ro * 0.78, th - phi * 1.14))} {f(o1)} "
        f"C{f(polar(cx, cy, ro * 0.98, th - phi * 0.9))} {f(polar(cx, cy, ro * 1.04, th - phi * 0.38))} {f(a)} "
        f"C{f(polar(cx, cy, ro * 1.04, th + phi * 0.38))} {f(polar(cx, cy, ro * 0.98, th + phi * 0.9))} {f(o2)} "
        f"C{f(polar(cx, cy, ro * 0.78, th + phi * 1.14))} {f(polar(cx, cy, ro * 0.5, th + phi * 1.18))} {f(b2)} Z"
    )


def crescent(cx, cy, th, phi, ro, ri, rng):
    A = polar(cx, cy, ro * 0.97, th - phi)
    B = polar(cx, cy, ro * 0.97, th + phi)
    # outer edge: two cubic halves through the apex, slightly ruffled
    apex = polar(cx, cy, ro * rng.uniform(1.0, 1.05), th + rng.uniform(-6, 6))
    k = 0.5523
    c1 = polar(cx, cy, ro * 1.02, th - phi * (1 - k * 0.55))
    c2 = polar(cx, cy, ro * 1.03, th - phi * 0.35)
    c3 = polar(cx, cy, ro * 1.03, th + phi * 0.35)
    c4 = polar(cx, cy, ro * 1.02, th + phi * (1 - k * 0.55))
    M = polar(cx, cy, ri, th + rng.uniform(-8, 8))
    # inner edge as quadratic through M
    C = (2 * M[0] - (A[0] + B[0]) / 2, 2 * M[1] - (A[1] + B[1]) / 2)
    return f"M{f(A)} C{f(c1)} {f(c2)} {f(apex)} C{f(c3)} {f(c4)} {f(B)} Q{f(C)} {f(A)} Z", apex, M


def rose(cv, cx, cy, R, pal, rot=0.0, squash=1.0, layer="flowers", seed=None, bleed=True):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    p = PAL[pal]
    parts = []
    sw = max(0.6, R / 110)
    if bleed:
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R * 1.02:.1f}" ry="{R * 0.98:.1f}" fill="{p[2]}" opacity="0.1" filter="url(#bleed)"/>'
        )
    # outer petals
    n = rng.choice([5, 6, 6])
    off = rng.uniform(0, 360)
    for i in range(n):
        th = off + i * 360 / n + rng.uniform(-9, 9)
        phi = 360 / n * 0.5 + rng.uniform(-3, 6)
        ro = R * rng.uniform(0.9, 1.0)
        d = outer_petal(cx, cy, th, phi, R * 0.3, ro, rng)
        g = cv.rad((cx, cy), R, [(0, p[3], 0.85), (0.45, p[2], 0.72), (0.8, p[1], 0.8), (1, p[0], 0.9)])
        parts.append(
            f'<path d="{d}" fill="url(#{g})" stroke="{p[4]}" stroke-opacity="0.34" stroke-width="{sw:.2f}"/>'
        )
    # cupped rings
    rings = [(0.82, 0.24, 4), (0.68, 0.22, 4), (0.55, 0.2, 4), (0.43, 0.17, 3), (0.32, 0.15, 3), (0.22, 0.11, 3)]
    for k, (ro_f, thick, m) in enumerate(rings):
        off = rng.uniform(0, 360)
        for j in range(m):
            th = off + j * 360 / m + rng.uniform(-14, 14)
            phi = rng.uniform(52, 78) if k < 3 else rng.uniform(60, 95)
            ro = R * ro_f * rng.uniform(0.95, 1.03)
            ri = ro - R * thick
            d, apex, M = crescent(cx, cy, th, phi, ro, ri, rng)
            if k < 2:
                stops = [(0, p[3], 0.8), (0.5, p[2], 0.6), (1, p[0], 0.9)]
            elif k < 4:
                stops = [(0, p[4], 0.82), (0.5, p[3], 0.66), (1, p[1], 0.9)]
            else:
                stops = [(0, p[5], 0.85), (0.55, p[4], 0.72), (1, p[2], 0.9)]
            g = cv.lin(M, apex, stops)
            parts.append(
                f'<path d="{d}" fill="url(#{g})" stroke="{p[5]}" stroke-opacity="0.3" stroke-width="{sw:.2f}"/>'
            )
            # light rim on the curled edge
            if rng.random() < 0.45:
                a1 = polar(cx, cy, ro * 0.985, th - phi * 0.55)
                a2 = polar(cx, cy, ro * 0.985, th + phi * 0.55)
                ap = polar(cx, cy, ro * 1.035, th)
                parts.append(
                    f'<path d="M{f(a1)} Q{f(ap)} {f(a2)}" fill="none" stroke="#ffffff" stroke-opacity="0.45" stroke-width="{max(0.8, R / 70):.2f}" stroke-linecap="round"/>'
                )
    # centre
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R * 0.08:.1f}" fill="{p[5]}" opacity="0.6"/>')
    for j in range(3):
        th = rng.uniform(0, 360)
        d, _, _ = crescent(cx, cy, th, rng.uniform(70, 110), R * 0.13, R * 0.05, rng)
        parts.append(f'<path d="{d}" fill="{p[4]}" opacity="0.6"/>')
    tr = f"rotate({rot:.1f} {cx:.1f} {cy:.1f})"
    if squash != 1.0:
        tr += f" translate({cx:.1f} {cy:.1f}) scale(1 {squash:.3f}) translate({-cx:.1f} {-cy:.1f})"
    cv.add(f'<g transform="{tr}" filter="url(#wc)" style="isolation:isolate">{"".join(parts)}</g>', layer)


def bud(cv, x, y, ang, L, pal, layer="flowers", seed=None):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    p = PAL[pal]
    lp = LEAF["sage"]
    d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    nrm = (-d[1], d[0])
    tip = (x + d[0] * L, y + d[1] * L)
    W = L * 0.36

    def pt(t, s):
        return (x + d[0] * L * t + nrm[0] * W * s, y + d[1] * L * t + nrm[1] * W * s)

    body = f"M{f(pt(0.05, 0))} C{f(pt(0.15, 1.1))} {f(pt(0.75, 0.9))} {f(tip)} C{f(pt(0.75, -0.9))} {f(pt(0.15, -1.1))} {f(pt(0.05, 0))} Z"
    g = cv.lin(pt(0, 0), tip, [(0, p[4], 0.95), (0.6, p[3], 0.9), (1, p[1], 0.9)])
    parts = [
        f'<path d="{body}" fill="url(#{g})" stroke="{p[5]}" stroke-opacity="0.35" stroke-width="1" style="mix-blend-mode:multiply"/>',
        f'<path d="M{f(pt(0.25, 0.1))} Q{f(pt(0.6, 0.55))} {f(pt(0.92, 0.05))}" fill="none" stroke="{p[5]}" stroke-opacity="0.35" stroke-width="1"/>',
    ]
    # sepals
    for s in (1, -1):
        sep = f"M{f(pt(0.02, 0))} C{f(pt(0.2, 0.9 * s))} {f(pt(0.45, 1.05 * s))} {f(pt(0.62, 0.75 * s))} C{f(pt(0.42, 0.55 * s))} {f(pt(0.22, 0.3 * s))} {f(pt(0.02, 0))} Z"
        parts.append(f'<path d="{sep}" fill="{lp[3]}" fill-opacity="0.85" stroke="{lp[4]}" stroke-opacity="0.4" stroke-width="0.8"/>')
    cv.add(f'<g filter="url(#wcleaf)">{"".join(parts)}</g>', layer)


# ------------------------------------------------------------------ foliage
def qbez(p0, p1, p2, t):
    a = lerp(p0, p1, t)
    b = lerp(p1, p2, t)
    return lerp(a, b, t)


def qtan(p0, p1, p2, t):
    dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    return math.degrees(math.atan2(dy, dx))


def leaf_path(base, ang, L, W, bend=0.0):
    d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    n = (-d[1], d[0])

    def pt(t, s):
        bb = bend * L * (t ** 2)
        return (
            base[0] + d[0] * L * t + n[0] * (W * s + bb),
            base[1] + d[1] * L * t + n[1] * (W * s + bb),
        )

    tip = pt(1, 0)
    path = f"M{f(base)} C{f(pt(0.2, 0.95))} {f(pt(0.72, 0.85))} {f(tip)} C{f(pt(0.72, -0.85))} {f(pt(0.2, -0.95))} {f(base)} Z"
    rib = f"M{f(pt(0.04, 0))} Q{f(pt(0.5, 0.08))} {f(pt(0.93, 0))}"
    return path, tip, rib


def spray(cv, p0, p2, kind="sage", n=9, size=46, width_ratio=0.32, layer="back", bend=0.25, seed=None, lean=40, stem=True):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    c = LEAF[kind]
    mid = lerp(p0, p2, 0.5)
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    p1 = (mid[0] - dy * bend, mid[1] + dx * bend)
    parts = []
    if stem:
        parts.append(
            f'<path d="M{f(p0)} Q{f(p1)} {f(p2)}" fill="none" stroke="{c[4]}" stroke-opacity="0.75" stroke-width="{max(1.2, size / 26):.2f}" stroke-linecap="round"/>'
        )
    for i in range(n):
        t = 0.12 + 0.86 * i / max(1, n - 1)
        base = qbez(p0, p1, p2, t)
        tang = qtan(p0, p1, p2, t)
        side = 1 if i % 2 == 0 else -1
        ang = tang + side * (lean + rng.uniform(-10, 10))
        L = size * (1.12 - 0.42 * t) * rng.uniform(0.85, 1.12)
        W = L * width_ratio
        path, tip, rib = leaf_path(base, ang, L, W, bend=side * rng.uniform(0.0, 0.12))
        col = c[rng.choice([1, 2, 2, 3])]
        dark = c[4]
        g = cv.lin(base, tip, [(0, c[3], 0.85), (0.55, col, 0.78), (1, c[1], 0.75)])
        parts.append(
            f'<path d="{path}" fill="url(#{g})" stroke="{dark}" stroke-opacity="0.22" stroke-width="0.8"/>'
        )
        parts.append(f'<path d="{rib}" fill="none" stroke="{c[0]}" stroke-opacity="0.55" stroke-width="0.9"/>')
    # terminal leaf
    tang = qtan(p0, p1, p2, 1)
    L = size * 0.62
    path, tip, rib = leaf_path(p2, tang, L, L * width_ratio)
    g = cv.lin(p2, tip, [(0, c[3], 0.9), (1, c[1], 0.85)])
    parts.append(f'<path d="{path}" fill="url(#{g})" stroke="{c[4]}" stroke-opacity="0.22" stroke-width="0.8"/>')
    cv.add(f'<g filter="url(#wcleaf)" style="isolation:isolate">{"".join(parts)}</g>', layer)


def leaf_fan(cv, x, y, angles, L, kind="sage", layer="back", seed=None, width_ratio=0.36):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    c = LEAF[kind]
    parts = []
    for a in angles:
        ll = L * rng.uniform(0.8, 1.15)
        path, tip, rib = leaf_path((x, y), a + rng.uniform(-6, 6), ll, ll * width_ratio, bend=rng.uniform(-0.12, 0.12))
        col = c[rng.choice([2, 2, 3])]
        g = cv.lin((x, y), tip, [(0, c[4], 0.85), (0.5, col, 0.8), (1, c[1], 0.78)])
        parts.append(f'<path d="{path}" fill="url(#{g})" stroke="{c[4]}" stroke-opacity="0.25" stroke-width="0.8"/>')
        parts.append(f'<path d="{rib}" fill="none" stroke="{c[0]}" stroke-opacity="0.5" stroke-width="0.9"/>')
    cv.add(f'<g filter="url(#wcleaf)" style="isolation:isolate">{"".join(parts)}</g>', layer)


def fan(cv, origin, specs, seed=0):
    """specs: list of (kind, angle_deg, length, size, bend)."""
    rng = random.Random(seed)
    for i, (kind, ang, length, size, bend) in enumerate(specs):
        end = polar(origin[0], origin[1], length, ang)
        start = polar(origin[0], origin[1], rng.uniform(10, 40), ang + rng.uniform(-20, 20))
        if kind == "euc":
            eucalyptus(cv, start, end, n=max(7, int(length / 34)), size=size, bend=bend, seed=rng.random())
        else:
            spray(cv, start, end, kind=kind, n=max(6, int(length / 40)), size=size,
                  width_ratio=0.2 if kind == "olive" else 0.33, bend=bend, seed=rng.random())


def eucalyptus(cv, p0, p2, n=11, size=26, layer="back", bend=0.18, seed=None):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    c = LEAF["euc"]
    mid = lerp(p0, p2, 0.5)
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    p1 = (mid[0] - dy * bend, mid[1] + dx * bend)
    parts = [
        f'<path d="M{f(p0)} Q{f(p1)} {f(p2)}" fill="none" stroke="#a39892" stroke-opacity="0.75" stroke-width="{max(1.0, size / 20):.2f}" stroke-linecap="round"/>'
    ]
    for i in range(n):
        t = 0.06 + 0.92 * i / max(1, n - 1)
        base = qbez(p0, p1, p2, t)
        tang = qtan(p0, p1, p2, t)
        r = size * (1.0 - 0.55 * t) * rng.uniform(0.8, 1.15)
        sides = (1, -1) if rng.random() < 0.55 else ((1,) if i % 2 else (-1,))
        for side in sides:
            ang = math.radians(tang + side * rng.uniform(55, 105))
            cxy = (base[0] + math.cos(ang) * r * 0.85, base[1] + math.sin(ang) * r * 0.85)
            col = c[rng.choice([0, 1, 1, 2, 2, 3])]
            g = cv.rad(cxy, r * 1.1, [(0, "#ffffff", 0.55), (0.35, col, 0.72), (1, c[3], 0.85)], fc=(cxy[0] - r * 0.35, cxy[1] - r * 0.35))
            rot = math.degrees(ang)
            ry = r * rng.uniform(0.78, 0.95)
            parts.append(
                f'<ellipse cx="{cxy[0]:.1f}" cy="{cxy[1]:.1f}" rx="{r * 1.02:.1f}" ry="{ry:.1f}" transform="rotate({rot:.1f} {cxy[0]:.1f} {cxy[1]:.1f})" '
                f'fill="url(#{g})" stroke="{c[4]}" stroke-opacity="0.22" stroke-width="0.8"/>'
            )
            # faint midrib
            e = (cxy[0] + math.cos(ang) * r * 0.85, cxy[1] + math.sin(ang) * r * 0.85)
            parts.append(f'<path d="M{f(base)} L{f(e)}" stroke="{c[3]}" stroke-opacity="0.35" stroke-width="0.7"/>')
    cv.add(f'<g filter="url(#wcleaf)" style="isolation:isolate">{"".join(parts)}</g>', layer)


def gypsophila(cv, p0, p2, branches=10, layer="mid", seed=None, spread=0.6, dot=3.9):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    parts = []
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    L = math.hypot(dx, dy)
    ang0 = math.degrees(math.atan2(dy, dx))
    stem = "#b2bcae"
    parts.append(f'<path d="M{f(p0)} L{f(p2)}" stroke="{stem}" stroke-width="1" fill="none"/>')
    blooms = []
    for b in range(branches):
        t = rng.uniform(0.25, 1.0)
        s0 = lerp(p0, p2, t)
        a = ang0 + rng.uniform(-70, 70) * spread
        l = L * rng.uniform(0.15, 0.4)
        e = polar(s0[0], s0[1], l, a)
        parts.append(f'<path d="M{f(s0)} L{f(e)}" stroke="{stem}" stroke-width="0.75" fill="none"/>')
        for k in range(rng.randint(5, 9)):
            q = polar(e[0], e[1], rng.uniform(3, 12), rng.uniform(0, 360))
            parts.append(f'<path d="M{f(e)} L{f(q)}" stroke="{stem}" stroke-width="0.55" fill="none"/>')
            blooms.append(q)
    for q in blooms:
        r = dot * rng.uniform(0.7, 1.25)
        parts.append(
            f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{r:.1f}" fill="#ffffff" stroke="#cdd3cb" stroke-width="0.6"/>'
        )
        for _ in range(3):
            o = polar(q[0], q[1], r * 0.45, rng.uniform(0, 360))
            parts.append(f'<circle cx="{o[0]:.1f}" cy="{o[1]:.1f}" r="{r * 0.42:.1f}" fill="#ffffff" stroke="#dde1da" stroke-width="0.4"/>')
        parts.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{r * 0.22:.1f}" fill="#e9e3c9"/>')
    cv.add(f'<g>{"".join(parts)}</g>', layer)


def blossom(cv, x, y, r, pal, layer="flowers", seed=None, rot=0):
    """Small five-petal filler blossom (wax flower)."""
    rng = random.Random(seed if seed is not None else cv.rng.random())
    p = PAL[pal]
    parts = []
    for i in range(5):
        th = rot + i * 72 + rng.uniform(-6, 6)
        c = polar(x, y, r * 0.55, th)
        g = cv.rad((x, y), r * 1.05, [(0, p[3], 0.85), (0.5, p[1], 0.8), (1, p[0], 0.9)])
        parts.append(
            f'<ellipse cx="{c[0]:.1f}" cy="{c[1]:.1f}" rx="{r * 0.55:.1f}" ry="{r * 0.42:.1f}" transform="rotate({th:.1f} {c[0]:.1f} {c[1]:.1f})" fill="url(#{g})" stroke="{p[4]}" stroke-opacity="0.25" stroke-width="0.6"/>'
        )
    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 0.2:.1f}" fill="{p[5]}" opacity="0.7"/>')
    cv.add(f'<g filter="url(#wcleaf)">{"".join(parts)}</g>', layer)


def blossom_cluster(cv, x, y, spread, n, pal, layer="flowers", seed=None, size=(9, 14)):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    for _ in range(n):
        q = polar(x, y, rng.uniform(0, spread), rng.uniform(0, 360))
        blossom(cv, q[0], q[1], rng.uniform(*size), pal, layer=layer, seed=rng.random(), rot=rng.uniform(0, 72))


def petals_scatter(cv, box, n, pal, layer="front", seed=None, size=(8, 16)):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    p = PAL[pal]
    out = []
    for _ in range(n):
        x = rng.uniform(box[0], box[2])
        y = rng.uniform(box[1], box[3])
        s = rng.uniform(*size)
        rot = rng.uniform(0, 360)
        col = p[rng.choice([1, 2, 2, 3])]
        out.append(
            f'<path d="M{x:.1f},{y:.1f} c{s * 0.5:.1f},{-s * 0.6:.1f} {s * 1.2:.1f},{-s * 0.2:.1f} {s:.1f},{s * 0.45:.1f} '
            f'c{-s * 0.25:.1f},{s * 0.45:.1f} {-s * 0.85:.1f},{s * 0.25:.1f} {-s:.1f},{-s * 0.45:.1f}z" '
            f'transform="rotate({rot:.0f} {x:.1f} {y:.1f})" fill="{col}" fill-opacity="0.75" stroke="{p[4]}" stroke-opacity="0.3" stroke-width="0.6"/>'
        )
    cv.add(f'<g filter="url(#wcleaf)">{"".join(out)}</g>', layer)


def sparkles(cv, box, n, color="#c9a253", layer="top", seed=None, size=(3, 9)):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    out = []
    for _ in range(n):
        x = rng.uniform(box[0], box[2])
        y = rng.uniform(box[1], box[3])
        s = rng.uniform(*size)
        if rng.random() < 0.55:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s * 0.28:.1f}" fill="{color}" opacity="{rng.uniform(0.45, 0.9):.2f}"/>')
        else:
            out.append(
                f'<path d="M{x:.1f},{y - s:.1f} Q{x:.1f},{y:.1f} {x + s:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y + s:.1f} '
                f'Q{x:.1f},{y:.1f} {x - s:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y - s:.1f}Z" fill="{color}" opacity="{rng.uniform(0.55, 0.95):.2f}"/>'
            )
    cv.add("".join(out), layer)


# ------------------------------------------------------------- compositions
def corner_a(seed=11):
    cv = Canvas(640, 640, seed)
    fan(cv, (18, 18), [
        ("euc", 6, 610, 22, -0.04), ("olive", 16, 520, 50, -0.05), ("sage", 26, 440, 52, 0.06),
        ("euc", 37, 470, 20, 0.08), ("olive", 46, 560, 50, -0.04), ("sage", 55, 430, 52, -0.06),
        ("olive", 64, 500, 48, 0.05), ("sage", 74, 470, 50, 0.05), ("euc", 84, 610, 22, 0.04),
    ], seed=3)
    gypsophila(cv, (270, 150), (560, 215), branches=12, seed=9)
    gypsophila(cv, (150, 270), (215, 560), branches=12, seed=10)
    gypsophila(cv, (270, 270), (430, 400), branches=9, seed=12)
    leaf_fan(cv, 170, 150, [-10, 15, 40, 65, 90, 115], 150, seed=13)
    rose(cv, 160, 142, 110, "blush", rot=20, squash=0.94, seed=21)
    rose(cv, 45, 322, 86, "ivory", rot=-30, squash=0.9, seed=22)
    rose(cv, 342, 56, 72, "ivory", rot=60, squash=0.88, seed=23)
    rose(cv, 294, 228, 46, "rose", rot=10, squash=0.92, seed=24)
    blossom_cluster(cv, 392, 168, 26, 4, "blush", seed=25)
    blossom_cluster(cv, 176, 338, 24, 4, "rose", seed=26)
    bud(cv, 400, 108, -18, 46, "blush", seed=31)
    bud(cv, 214, 316, 112, 42, "rose", seed=32)
    bud(cv, 118, 434, 96, 38, "blush", seed=33)
    spray(cv, (225, 245), (330, 335), kind="sage", n=4, size=40, bend=0.1, seed=41, layer="front")
    spray(cv, (255, 110), (425, 40), kind="sage", n=4, size=34, bend=-0.15, seed=42, layer="front")
    return cv


def corner_b(seed=12):
    cv = Canvas(640, 640, seed)
    fan(cv, (18, 18), [
        ("euc", 9, 600, 23, -0.05), ("sage", 19, 480, 52, 0.05), ("olive", 29, 560, 50, -0.04),
        ("euc", 40, 430, 19, 0.06), ("sage", 50, 520, 54, -0.05), ("olive", 60, 470, 48, 0.06),
        ("sage", 70, 430, 50, -0.05), ("euc", 81, 600, 23, 0.05),
    ], seed=7)
    gypsophila(cv, (300, 180), (600, 250), branches=12, seed=56)
    gypsophila(cv, (190, 320), (285, 600), branches=12, seed=57)
    leaf_fan(cv, 150, 160, [0, 25, 50, 75, 100], 150, seed=14)
    rose(cv, 140, 150, 106, "ivory", rot=-15, squash=0.93, seed=61)
    rose(cv, 320, 84, 72, "blush", rot=40, squash=0.9, seed=62)
    rose(cv, 62, 335, 74, "peach", rot=12, squash=0.9, seed=63)
    rose(cv, 266, 262, 50, "blush", rot=-20, squash=0.9, seed=64)
    blossom_cluster(cv, 420, 190, 24, 4, "rose", seed=68)
    blossom_cluster(cv, 160, 420, 22, 3, "blush", seed=69)
    bud(cv, 418, 112, -5, 44, "rose", seed=65)
    bud(cv, 170, 300, 100, 40, "blush", seed=66)
    spray(cv, (240, 200), (395, 235), kind="sage", n=4, size=36, bend=0.2, seed=67, layer="front")
    return cv


def garland(seed=13):
    cv = Canvas(1200, 520, seed)
    eucalyptus(cv, (600, 60), (8, 130), n=17, size=24, bend=0.08, seed=71)
    eucalyptus(cv, (600, 60), (1192, 120), n=17, size=24, bend=-0.08, seed=72)
    spray(cv, (560, 70), (110, 300), kind="olive", n=13, size=54, width_ratio=0.2, bend=0.1, seed=73)
    spray(cv, (640, 70), (1090, 300), kind="olive", n=13, size=54, width_ratio=0.2, bend=-0.1, seed=74)
    spray(cv, (560, 60), (250, 380), kind="sage", n=9, size=56, bend=0.15, seed=75)
    spray(cv, (640, 60), (950, 380), kind="sage", n=9, size=56, bend=-0.15, seed=76)
    spray(cv, (520, 40), (180, 40), kind="sage", n=8, size=44, bend=0.1, seed=90, layer="mid")
    spray(cv, (680, 40), (1020, 40), kind="sage", n=8, size=44, bend=-0.1, seed=91, layer="mid")
    eucalyptus(cv, (600, 70), (600, 440), n=10, size=20, bend=0.05, seed=77, layer="mid")
    gypsophila(cv, (390, 120), (170, 250), branches=11, seed=78)
    gypsophila(cv, (810, 120), (1030, 250), branches=11, seed=79)
    gypsophila(cv, (560, 200), (515, 410), branches=9, seed=80)
    gypsophila(cv, (660, 200), (700, 400), branches=9, seed=92)
    rose(cv, 520, 92, 102, "blush", rot=10, squash=0.92, seed=81)
    rose(cv, 708, 84, 90, "ivory", rot=-25, squash=0.9, seed=82)
    rose(cv, 370, 62, 64, "ivory", rot=30, squash=0.9, seed=83)
    rose(cv, 852, 80, 60, "blush", rot=-10, squash=0.9, seed=84)
    rose(cv, 620, 228, 52, "rose", rot=5, squash=0.9, seed=85)
    blossom_cluster(cv, 430, 175, 26, 4, "rose", seed=93)
    blossom_cluster(cv, 790, 185, 26, 4, "blush", seed=94)
    bud(cv, 284, 96, 170, 44, "blush", seed=86)
    bud(cv, 938, 118, 8, 44, "rose", seed=87)
    bud(cv, 470, 228, 120, 38, "rose", seed=88)
    bud(cv, 762, 222, 60, 38, "blush", seed=89)
    return cv


def write(cv, name, extra_defs=""):
    BUILD.mkdir(exist_ok=True)
    (BUILD / f"{name}.svg").write_text(cv.svg(extra_defs))


if __name__ == "__main__":
    which = sys.argv[1:] or ["corner_a", "corner_b", "garland"]
    for w in which:
        write(globals()[w](), w)
        print("wrote", w)


# ------------------------------------------------------------- gold & crown
GOLD_DEFS = """
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="0.35">
  <stop offset="0" stop-color="#b3843c"/><stop offset="0.28" stop-color="#f2dc9e"/>
  <stop offset="0.5" stop-color="#cf9f55"/><stop offset="0.72" stop-color="#f7e7bb"/>
  <stop offset="1" stop-color="#b68841"/>
</linearGradient>
<linearGradient id="goldv" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#f6e4b0"/><stop offset="0.5" stop-color="#d1a35a"/><stop offset="1" stop-color="#a97b36"/>
</linearGradient>
<filter id="goldtex" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.97  0 0 0 0 0.86  0.9 0 0 0 -0.55" result="sp"/>
  <feComposite in="sp" in2="SourceAlpha" operator="in" result="sp2"/>
  <feDropShadow in="SourceGraphic" dx="0" dy="3" stdDeviation="3" flood-color="#7a5524" flood-opacity="0.28" result="sh"/>
  <feMerge><feMergeNode in="sh"/><feMergeNode in="sp2"/></feMerge>
</filter>
"""


def crown(cv, cx, cy, w, layer="top"):
    """Delicate tiara: five peaks with pearls and a central jewel."""
    h = w * 0.42
    base_y = cy + h * 0.5
    left, right = cx - w / 2, cx + w / 2
    pts = []
    peaks = [(-0.5, 0.25), (-0.3, 0.62), (-0.15, 0.45), (0.0, 1.0), (0.15, 0.45), (0.3, 0.62), (0.5, 0.25)]
    d = f"M{left:.1f},{base_y:.1f} "
    prev = (left, base_y)
    for i, (px, ph) in enumerate(peaks[1:-1]):
        x = cx + px * w
        y = base_y - ph * h
        mx = (prev[0] + x) / 2
        d += f"Q{mx:.1f},{base_y - h * 0.08:.1f} {x:.1f},{y:.1f} "
        prev = (x, y)
        pts.append((x, y))
    d += f"Q{(prev[0] + right) / 2:.1f},{base_y - h * 0.08:.1f} {right:.1f},{base_y:.1f}"
    band = f"M{left:.1f},{base_y:.1f} Q{cx:.1f},{base_y + h * 0.22:.1f} {right:.1f},{base_y:.1f}"
    out = [
        f'<path d="{d}" fill="none" stroke="url(#gold)" stroke-width="{w * 0.028:.1f}" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<path d="{band}" fill="none" stroke="url(#gold)" stroke-width="{w * 0.05:.1f}" stroke-linecap="round"/>',
    ]
    # filigree loops
    for i in range(6):
        t = (i + 0.5) / 6
        x = left + w * t
        y = base_y - h * 0.18
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{w * 0.035:.1f}" fill="none" stroke="url(#gold)" stroke-width="{w * 0.012:.1f}"/>')
    for (x, y) in pts:
        out.append(f'<circle cx="{x:.1f}" cy="{y - w * 0.03:.1f}" r="{w * 0.03:.1f}" fill="#fffaf3" stroke="#d9c39a" stroke-width="{w * 0.006:.1f}"/>')
    # central jewel
    jx, jy = cx, base_y - h * 0.42
    out.append(f'<path d="M{jx:.1f},{jy - w * 0.07:.1f} L{jx + w * 0.045:.1f},{jy:.1f} L{jx:.1f},{jy + w * 0.07:.1f} L{jx - w * 0.045:.1f},{jy:.1f}Z" fill="#e58fa5" stroke="url(#gold)" stroke-width="{w * 0.012:.1f}"/>')
    out.append(f'<path d="M{jx - w * 0.015:.1f},{jy - w * 0.03:.1f} L{jx + w * 0.01:.1f},{jy - w * 0.045:.1f}" stroke="#fff" stroke-width="{w * 0.01:.1f}" stroke-linecap="round" opacity="0.8"/>')
    for k in (-1, 1):
        out.append(f'<circle cx="{cx + k * w * 0.22:.1f}" cy="{base_y - h * 0.08:.1f}" r="{w * 0.022:.1f}" fill="#f4b7c5" stroke="url(#gold)" stroke-width="{w * 0.008:.1f}"/>')
    cv.add(f'<g filter="url(#goldtex)">{"".join(out)}</g>', layer)


def gold_number(cv, cx, cy, size, text="15", family="Cinzel", weight=700, layer="top"):
    cv.add(
        f'<g filter="url(#goldtex)"><text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" font-family="{family}" font-weight="{weight}" '
        f'font-size="{size:.0f}" fill="url(#gold)" stroke="#a87c38" stroke-opacity="0.45" stroke-width="{size / 160:.1f}" letter-spacing="{-size * 0.02:.1f}">{text}</text></g>',
        layer,
    )


def wash(cv, d, color, opacity, layer="back"):
    cv.add(f'<path d="{d}" fill="{color}" opacity="{opacity}" filter="url(#wash)"/>', layer)


def cluster(cv, x, y, scale, palettes, seed, foliage_dir=None, layer="flowers"):
    """A rose cluster: 2-3 roses, buds, blossoms and a little foliage."""
    rng = random.Random(seed)
    if foliage_dir is not None:
        angs = [foliage_dir + a for a in (-70, -35, 0, 35, 70)]
        for a in angs:
            e = polar(x, y, scale * rng.uniform(1.9, 2.6), a)
            kind = rng.choice(["sage", "olive", "euc"])
            if kind == "euc":
                eucalyptus(cv, (x, y), e, n=7, size=scale * 0.2, bend=rng.uniform(-0.15, 0.15), seed=rng.random())
            else:
                spray(cv, (x, y), e, kind=kind, n=6, size=scale * 0.48, width_ratio=0.2 if kind == "olive" else 0.33, bend=rng.uniform(-0.15, 0.15), seed=rng.random())
        gypsophila(cv, polar(x, y, scale * 0.6, foliage_dir + 30), polar(x, y, scale * 2.1, foliage_dir + 40), branches=8, seed=rng.random())
    big = palettes[0]
    rose(cv, x, y, scale, big, rot=rng.uniform(-40, 40), squash=rng.uniform(0.88, 0.95), seed=rng.random(), layer=layer)
    for i, pal in enumerate(palettes[1:]):
        a = rng.uniform(0, 360)
        q = polar(x, y, scale * rng.uniform(0.95, 1.2), a)
        rose(cv, q[0], q[1], scale * rng.uniform(0.55, 0.72), pal, rot=rng.uniform(-40, 40), squash=rng.uniform(0.86, 0.94), seed=rng.random(), layer=layer)
    for _ in range(2):
        a = rng.uniform(0, 360)
        q = polar(x, y, scale * 1.25, a)
        bud(cv, q[0], q[1], a + rng.uniform(-20, 20), scale * 0.42, rng.choice(["blush", "rose"]), seed=rng.random(), layer=layer)
    q = polar(x, y, scale * 1.3, rng.uniform(0, 360))
    blossom_cluster(cv, q[0], q[1], scale * 0.25, 3, rng.choice(["blush", "rose"]), seed=rng.random(), layer=layer, size=(scale * 0.1, scale * 0.15))


def hero(seed=21):
    """Floral arch with a gold '15' and a tiara (replaces the reference's pergola scene)."""
    cv = Canvas(1200, 1000, seed)
    # soft ground & backdrop washes
    cv.add('<ellipse cx="600" cy="975" rx="430" ry="36" fill="#e4b9c2" opacity="0.3" filter="url(#bleed)"/>', "back")
    wash(cv, "M260,900 C240,520 380,250 600,230 C820,250 960,520 940,900 Z", "#fdf3ef", 0.55)
    # arch frame (thin gold)
    arch = "M245,1000 L245,560 C245,260 400,135 600,135 C800,135 955,260 955,560 L955,1000"
    cv.add(f'<path d="{arch}" fill="none" stroke="url(#goldv)" stroke-width="7" opacity="0.85"/>', "back")
    cv.add(f'<path d="M275,1000 L275,565 C275,290 420,170 600,170 C780,170 925,290 925,565 L925,1000" fill="none" stroke="url(#goldv)" stroke-width="3" opacity="0.6"/>', "back")
    # foliage along the arch
    pts = [(260, 980), (255, 820), (258, 660), (275, 470), (330, 320), (420, 210), (520, 158), (600, 150),
           (680, 158), (780, 210), (870, 320), (925, 470), (942, 660), (945, 820), (940, 980)]
    rng = random.Random(seed)
    for (a, b) in zip(pts[:-1], pts[1:]):
        kind = rng.choice(["sage", "olive", "euc", "sage"])
        if kind == "euc":
            eucalyptus(cv, a, b, n=7, size=19, bend=rng.uniform(-0.25, 0.25), seed=rng.random())
        else:
            spray(cv, a, b, kind=kind, n=7, size=44, width_ratio=0.2 if kind == "olive" else 0.33, bend=rng.uniform(-0.25, 0.25), seed=rng.random())
        spray(cv, b, (b[0] + rng.uniform(-90, 90), b[1] + rng.uniform(-60, 90)), kind="sage", n=4, size=38, bend=0.2, seed=rng.random(), layer="mid")
    # flower clusters
    cluster(cv, 600, 150, 74, ["blush", "ivory", "rose"], seed=101, foliage_dir=90)
    cluster(cv, 352, 270, 58, ["ivory", "blush"], seed=102)
    cluster(cv, 848, 270, 58, ["ivory", "peach"], seed=103)
    cluster(cv, 262, 600, 48, ["blush", "ivory"], seed=104)
    cluster(cv, 938, 600, 48, ["rose", "ivory"], seed=105)
    cluster(cv, 250, 905, 78, ["ivory", "blush", "rose"], seed=106, foliage_dir=-90)
    cluster(cv, 950, 905, 78, ["blush", "ivory", "peach"], seed=107, foliage_dir=-90)
    gypsophila(cv, (430, 205), (330, 400), branches=9, seed=108)
    gypsophila(cv, (770, 205), (870, 400), branches=9, seed=109)
    # centre: tiara + gold 15
    crown(cv, 600, 372, 190)
    gold_number(cv, 600, 715, 330)
    sparkles(cv, (360, 300, 840, 820), 46, seed=110)
    petals_scatter(cv, (300, 880, 900, 990), 26, "blush", seed=111)
    return cv


GOWN_PINK = dict(w1="#fbe6e8", w2="#fffaf6", under=("#e7a8b6", "#d88a9d"), main=("#f9e1e6", "#f2c3cd", "#e9a9b8"), skirt_stroke="#d68fa1",
                 fold_dark="#cf8396", fold_light_op=0.5, tulle="#fff6f8", tulle_op=(0.32, 0.28), bod=("#f6d2d9", "#e9adbb"), bod_stroke="#cf8b9c",
                 darts="#cd8698", lace="#ffffff", sash=("#c97489", "#dc93a6", "#c26c82"), sash_stroke="#a9566d", sash_rose="rose",
                 beads=["#ffffff", "#ffffff", "#f3d9a4"], sparks=["#ffffff", "#ffffff", "#ffffff", "#ecd193"], clusters=(["blush", "ivory", "rose"], ["ivory", "blush", "peach"]), petals="blush")
GOWN_WINE = dict(w1="#f1e2cf", w2="#fffaf1", under=("#5a1426", "#3d0a18"), main=("#a9485f", "#86304a", "#5c1628"), skirt_stroke="#4a0f1f",
                 fold_dark="#3d0a18", fold_light_op=0.28, tulle="#f7dfe4", tulle_op=(0.16, 0.13), bod=("#9c3b53", "#661a2e"), bod_stroke="#3d0a18",
                 darts="#3d0a18", lace="#ecd393", sash=("#a8843b", "#f2dea2", "#a07c35"), sash_stroke="#7a5b22", sash_rose="ivory",
                 beads=["#f6e3ad", "#ffffff", "#e3c47c"], sparks=["#f3dc9c", "#ffffff", "#e8c979", "#f8eccb"], clusters=(["blush", "ivory", "peach"], ["ivory", "blush", "rose"]), petals="blush")


def gown(seed=31, w=1200, h=1100, fade=True, k=None):
    """Debutante ball gown on a dress form, with florals (replaces the reference's swing scene)."""
    k = k or GOWN_PINK
    cv = Canvas(w, h, seed)
    rng = random.Random(seed)
    # backdrop washes
    wash(cv, "M600,90 C900,90 1060,330 1060,560 C1060,800 880,980 600,980 C320,980 140,800 140,560 C140,330 300,90 600,90 Z", k["w1"], 0.75)
    wash(cv, "M600,200 C820,200 930,380 930,560 C930,760 800,900 600,900 C400,900 270,760 270,560 C270,380 380,200 600,200 Z", k["w2"], 0.6)
    # dress-form neck and finial
    neck = cv.lin((570, 0), (632, 0), [(0, "#d9c8b4", 1), (0.45, "#f3e9dc", 1), (1, "#cdb9a2", 1)])
    cv.add(f'<ellipse cx="600" cy="138" rx="26" ry="11" fill="#b99a74"/><rect x="590" y="110" width="20" height="30" rx="6" fill="#c9ab83"/>'
           f'<path d="M574,148 C574,190 566,215 556,240 L644,240 C634,215 626,190 626,148 Z" fill="url(#{neck})" stroke="#bfa98f" stroke-width="1.2"/>', "mid")
    shoulders = cv.lin((470, 0), (730, 0), [(0, "#d6c4ae", 1), (0.5, "#f4ebdf", 1), (1, "#cbb69d", 1)])
    cv.add(f'<path d="M462,312 C470,270 520,246 560,238 L640,238 C680,246 730,270 738,312 C700,322 500,322 462,312 Z" fill="url(#{shoulders})" stroke="#bfa98f" stroke-width="1.2"/>', "mid")
    # skirt under-layer
    under = cv.lin((600, 480), (600, 1010), [(0, k["under"][0], 0.95), (1, k["under"][1], 0.95)])
    cv.add(f'<path d="M540,486 L660,486 C780,600 950,800 1000,1012 C800,1050 400,1050 200,1012 C250,800 420,600 540,486 Z" fill="url(#{under})" filter="url(#wcleaf)"/>', "flowers")
    # main skirt
    main = cv.lin((600, 480), (600, 1010), [(0, k["main"][0], 1), (0.55, k["main"][1], 1), (1, k["main"][2], 1)])
    hem = []
    x = 975
    while x > 225:
        nx = x - rng.uniform(46, 64)
        hem.append(f"Q{(x + nx) / 2:.1f},{1012 + rng.uniform(14, 24):.1f} {max(nx, 225):.1f},{1000 + rng.uniform(-3, 3):.1f}")
        x = nx
    skirt = f"M548,488 L652,488 C760,600 925,800 975,1000 {' '.join(hem)} C275,800 440,600 548,488 Z"
    cv.add(f'<path d="{skirt}" fill="url(#{main})" stroke="{k['skirt_stroke']}" stroke-opacity="0.35" stroke-width="1.5" filter="url(#wcleaf)"/>', "flowers")
    # folds
    folds = []
    for i in range(11):
        t = (i + 0.5) / 11
        xh = 250 + 700 * t
        xw = 556 + 88 * t
        cx1 = xw + (xh - xw) * 0.25
        dark = rng.random() < 0.6
        col = k["fold_dark"] if dark else "#ffffff"
        op = 0.28 if dark else k["fold_light_op"]
        wdt = rng.uniform(5, 12)
        folds.append(f'<path d="M{xw:.1f},500 C{cx1:.1f},640 {xh - (xh - 600) * 0.15:.1f},820 {xh:.1f},1000" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{wdt:.1f}" stroke-linecap="round"/>')
    cv.add(f'<g filter="url(#soft)" clip-path="none">{"".join(folds)}</g>', "flowers")
    # tulle overlay with scalloped edge (follows the skirt silhouette)
    for (yy, xl, xr, op) in [(800, 345, 855, k["tulle_op"][0]), (915, 282, 918, k["tulle_op"][1])]:
        d = f"M548,490 L652,490 C735,580 {xr - 50:.1f},{yy - 150:.1f} {xr:.1f},{yy:.1f} "
        x = xr
        while x > xl + 1:
            nx = max(x - 52, xl)
            d += f"Q{(x + nx) / 2:.1f},{yy + 24:.1f} {nx:.1f},{yy:.1f} "
            x = nx
        d += f"C{xl + 50:.1f},{yy - 150:.1f} 465,580 548,490 Z"
        cv.add(f'<path d="{d}" fill="{k['tulle']}" fill-opacity="{op}" stroke="#ffffff" stroke-opacity="0.75" stroke-width="1.4"/>', "flowers")
    # bodice
    bod = cv.lin((600, 290), (600, 490), [(0, k["bod"][0], 1), (1, k["bod"][1], 1)])
    bodice = "M486,318 C500,292 535,282 560,294 C578,302 592,312 600,326 C608,312 622,302 640,294 C665,282 700,292 714,318 C700,380 672,440 656,490 L544,490 C528,440 500,380 486,318 Z"
    cv.add(f'<path d="{bodice}" fill="url(#{bod})" stroke="{k['bod_stroke']}" stroke-opacity="0.5" stroke-width="1.4" filter="url(#wcleaf)"/>', "front")
    # bodice darts & beading
    cv.add(f'<path d="M560,300 C565,380 562,440 568,488 M640,300 C635,380 638,440 632,488 M600,330 L600,488" stroke="{k['darts']}" stroke-opacity="0.35" stroke-width="2" fill="none"/>', "front")
    beads = []
    for _ in range(140):
        bx = rng.uniform(500, 700)
        by = rng.uniform(305, 486)
        # keep inside bodice roughly
        half = 108 - (by - 318) * 0.32
        if abs(bx - 600) < half:
            beads.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{rng.uniform(1.2, 2.4):.1f}" fill="{rng.choice(k['beads'])}" opacity="{rng.uniform(0.6, 1):.2f}"/>')
    cv.add("".join(beads), "front")
    # neckline lace scallops
    lace = "M488,318 " + " ".join(f"Q{488 + i * 14 + 7:.1f},{326 + (i % 2) * 2:.1f} {488 + (i + 1) * 14:.1f},{318 + 0.0:.1f}" for i in range(0))
    cv.add(f'<path d="M486,318 C500,292 535,282 560,294 C578,302 592,312 600,326 C608,312 622,302 640,294 C665,282 700,292 714,318" fill="none" stroke="{k['lace']}" stroke-opacity="0.85" stroke-width="3" stroke-dasharray="1 6" stroke-linecap="round"/>', "front")
    # sash with rose
    sash = cv.lin((540, 0), (660, 0), [(0, k["sash"][0], 1), (0.5, k["sash"][1], 1), (1, k["sash"][2], 1)])
    cv.add(f'<path d="M540,478 C580,486 620,486 660,478 L664,500 C622,508 578,508 536,500 Z" fill="url(#{sash})" stroke="{k['sash_stroke']}" stroke-opacity="0.4" stroke-width="1"/>', "front")
    rose(cv, 650, 489, 24, k["sash_rose"], rot=10, squash=0.95, seed=401, layer="top", bleed=False)
    spray(cv, (650, 489), (700, 540), kind="sage", n=3, size=22, bend=0.2, seed=402, layer="front")
    # sparkles on the skirt (denser near the waist)
    sp = []
    for _ in range(420):
        yy = 500 + (rng.random() ** 1.6) * 500
        spread = 50 + (yy - 490) * 0.78
        xx = 600 + rng.uniform(-spread, spread)
        sp.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="{rng.uniform(0.9, 2.3):.1f}" fill="{rng.choice(k['sparks'])}" opacity="{rng.uniform(0.45, 0.95):.2f}"/>')
    cv.add("".join(sp), "top")
    sparkles(cv, (330, 160, 870, 560), 26, seed=403)
    # florals at the hem
    cluster(cv, 255, 985, 86, k["clusters"][0], seed=404, foliage_dir=-115)
    cluster(cv, 945, 990, 86, k["clusters"][1], seed=405, foliage_dir=-65)
    petals_scatter(cv, (330, 1010, 880, 1070), 22, k["petals"], seed=406)
    defs = GOLD_DEFS
    if fade:
        defs += ('<linearGradient id="fadeg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
                 '<stop offset="0.8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
                 f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="url(#fadeg)"/></mask>')
    return cv, defs


def bouquet(seed=41):
    cv = Canvas(800, 1000, seed)
    bg = cv.lin((0, 0), (800, 1000), [(0, "#f8e3e5", 1), (0.55, "#f3d3d8", 1), (1, "#ecc1c9", 1)])
    cv.add(f'<rect width="800" height="1000" fill="url(#{bg})"/>', "back")
    wash(cv, "M-40,-40 L840,-40 L840,380 C620,330 380,420 -40,330 Z", "#fdf1f0", 0.7)
    wash(cv, "M-40,1040 L840,1040 L840,760 C600,820 300,700 -40,800 Z", "#e7b2bd", 0.45)
    rng = random.Random(seed)
    for a in range(-170, 10, 16):
        e = polar(400, 560, rng.uniform(330, 470), a)
        kind = rng.choice(["sage", "olive", "euc"])
        if kind == "euc":
            eucalyptus(cv, (400, 560), e, n=10, size=24, bend=rng.uniform(-0.15, 0.15), seed=rng.random())
        else:
            spray(cv, (400, 560), e, kind=kind, n=9, size=54, width_ratio=0.2 if kind == "olive" else 0.33, bend=rng.uniform(-0.15, 0.15), seed=rng.random())
    gypsophila(cv, (300, 420), (120, 230), branches=12, seed=411)
    gypsophila(cv, (500, 420), (690, 220), branches=12, seed=412)
    gypsophila(cv, (400, 380), (420, 130), branches=10, seed=413)
    # stems and ribbon
    stems = "".join(f'<path d="M{400 + o:.1f},640 L{400 + o * 0.3:.1f},960" stroke="#86a07f" stroke-width="5" stroke-linecap="round"/>' for o in range(-40, 44, 10))
    cv.add(f'<g filter="url(#wcleaf)">{stems}</g>', "mid")
    rose(cv, 400, 470, 120, "blush", rot=10, squash=0.95, seed=421)
    rose(cv, 245, 520, 92, "ivory", rot=-20, squash=0.92, seed=422)
    rose(cv, 560, 515, 95, "rose", rot=30, squash=0.92, seed=423)
    rose(cv, 320, 350, 76, "peach", rot=15, squash=0.9, seed=424)
    rose(cv, 490, 340, 72, "ivory", rot=-35, squash=0.9, seed=425)
    rose(cv, 400, 610, 70, "blush", rot=0, squash=0.9, seed=426)
    blossom_cluster(cv, 180, 400, 30, 5, "rose", seed=427)
    blossom_cluster(cv, 630, 390, 30, 5, "blush", seed=428)
    bud(cv, 600, 300, -50, 52, "rose", seed=429)
    bud(cv, 200, 300, -130, 50, "blush", seed=430)
    rib = cv.lin((330, 0), (470, 0), [(0, "#c36d84", 1), (0.5, "#e19aad", 1), (1, "#c06a81", 1)])
    cv.add(f'<path d="M352,700 C380,690 420,690 448,700 L452,736 C420,746 380,746 348,736 Z" fill="url(#{rib})"/>'
           f'<path d="M400,718 C360,690 300,700 318,740 C330,768 380,742 400,720 Z M400,718 C440,690 500,700 482,740 C470,768 420,742 400,720 Z" fill="url(#{rib})" stroke="#a9566d" stroke-opacity="0.4"/>'
           f'<path d="M392,724 C380,790 360,850 330,900 M408,724 C420,790 445,850 470,905" stroke="#d17f95" stroke-width="10" fill="none" stroke-linecap="round"/>', "front")
    sparkles(cv, (60, 80, 740, 900), 30, color="#ffffff", seed=431)
    return cv


# ------------------------------------------------------------ vinho, preto e ouro
def use_wine_theme():
    PAL["blush"] = ["#f6dfe3", "#dca1ad", "#b8627a", "#8e2f4a", "#6a1830", "#470b1d"]   # vinho
    PAL["rose"] = ["#fbe9ec", "#eab9c3", "#cc8396", "#a54d67", "#7c2a44", "#561531"]    # vinho claro
    PAL["peach"] = ["#fffaf0", "#f7ead0", "#ead19f", "#d4b06e", "#b38b47", "#86652c"]   # champanhe / dourado
    PAL["ivory"] = ["#ffffff", "#fdf9f2", "#f3eadb", "#e3d5bd", "#c7b391", "#a28a66"]   # marfim
    LEAF["sage"] = ["#dfe6d6", "#b9c7ad", "#8fa384", "#6b8261", "#4c6345"]
    LEAF["olive"] = ["#f8ecc8", "#ead18f", "#d4b062", "#b38d3f", "#8a6a28"]             # folhas douradas
    LEAF["euc"] = ["#dde5df", "#bccbc2", "#98ad9f", "#76907f", "#587264"]


def berries(cv, x, y, n=7, spread=26, layer="mid", seed=None, r=(5, 8)):
    rng = random.Random(seed if seed is not None else cv.rng.random())
    out = []
    for _ in range(n):
        q = polar(x, y, rng.uniform(0, spread), rng.uniform(0, 360))
        rr = rng.uniform(*r)
        col = rng.choice(["#1c1416", "#2a1a1e", "#4a0f1f"])
        out.append(f'<path d="M{x:.1f},{y:.1f} L{q[0]:.1f},{q[1]:.1f}" stroke="#6b5a50" stroke-width="0.8"/>')
        out.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{rr:.1f}" fill="{col}"/>'
                   f'<circle cx="{q[0] - rr * 0.35:.1f}" cy="{q[1] - rr * 0.35:.1f}" r="{rr * 0.28:.1f}" fill="#ffffff" opacity="0.45"/>')
    cv.add(f'<g filter="url(#wcleaf)">{"".join(out)}</g>', layer)


BALLOON = {
    "wine": [(0, "#d07087", 1), (0.42, "#8f2541", 1), (1, "#4b0c1c", 1)],
    "black": [(0, "#6b6064", 1), (0.38, "#261d20", 1), (1, "#0a0708", 1)],
    "gold": [(0, "#fff6d6", 1), (0.3, "#ecd08a", 1), (0.7, "#bd903f", 1), (1, "#7a5820", 1)],
}


def balloon(cv, x, y, r, kind, layer="flowers"):
    g = cv.rad((x, y), r * 1.15, BALLOON[kind], fc=(x - r * 0.38, y - r * 0.42))
    hl = 0.75 if kind == "gold" else 0.38
    cv.add(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#{g})" stroke="#000" stroke-opacity="0.12" stroke-width="1"/>'
        f'<ellipse cx="{x - r * 0.36:.1f}" cy="{y - r * 0.42:.1f}" rx="{r * 0.2:.1f}" ry="{r * 0.12:.1f}" transform="rotate(-35 {x - r * 0.36:.1f} {y - r * 0.42:.1f})" fill="#ffffff" opacity="{hl}"/>',
        layer,
    )


def hero_baloes(seed=27):
    """Arch backdrop in wine and gold with a balloon garland (as in the party décor) and the gold 15."""
    cv = Canvas(1200, 1000, seed)
    rng = random.Random(seed)
    cv.add('<ellipse cx="606" cy="975" rx="420" ry="34" fill="#cdb894" opacity="0.28" filter="url(#bleed)"/>', "back")

    def arch(cx, top, half, bottom):
        r = half
        return f"M{cx - half},{bottom} L{cx - half},{top + r} A{r},{r} 0 0 1 {cx + half},{top + r} L{cx + half},{bottom}"
    gold = cv.lin((260, 0), (940, 0), [(0, "#b8893f", 1), (0.3, "#ecd394", 1), (0.55, "#c79b4c", 1), (0.8, "#f2dfa6", 1), (1, "#b28640", 1)])
    cv.add(f'<path d="{arch(578, 120, 336, 985)}" fill="none" stroke="url(#{gold})" stroke-width="42" filter="url(#wcleaf)"/>', "back")
    wine = cv.lin((260, 0), (940, 0), [(0, "#5c1426", 1), (0.5, "#7e2239", 1), (1, "#561224", 1)])
    cv.add(f'<path d="{arch(606, 170, 290, 985)}" fill="none" stroke="url(#{wine})" stroke-width="64" filter="url(#wcleaf)"/>', "back")
    cv.add(f'<path d="{arch(606, 170, 248, 985)}" fill="none" stroke="url(#{gold})" stroke-width="5" opacity="0.9"/>', "back")

    def along(t):  # t in [0,1] over the arch (left foot -> top -> right foot)
        cx, top, half, bottom = 606, 170, 318, 985
        r = half
        straight = bottom - (top + r)
        total = 2 * straight + math.pi * r
        s_ = t * total
        if s_ < straight:
            return (cx - half, bottom - s_), 180
        s_ -= straight
        if s_ < math.pi * r:
            a = 180 + s_ / r * 180 / math.pi
            return polar(cx, top + r, r, a), a
        s_ -= math.pi * r
        return (cx + half, top + r + s_), 0

    def garland_run(t0, t1, n, spread):
        pts = []
        for i in range(n):
            t = t0 + (t1 - t0) * (i + rng.random()) / n
            (px, py), a = along(t)
            nx, ny = math.cos(math.radians(a)), math.sin(math.radians(a))
            off = rng.uniform(-spread, spread)
            pts.append((px + nx * off + rng.uniform(-14, 14), py + ny * off + rng.uniform(-14, 14)))
        return pts
    left = garland_run(0.0, 0.2, 40, 60)
    right = garland_run(0.4, 1.0, 110, 64)
    spots = left + right
    rng.shuffle(spots)
    big = [(s, rng.uniform(54, 74), rng.choice(["wine", "gold", "black", "wine", "gold"])) for s in spots[:18]]
    mid = [(s, rng.uniform(30, 44), rng.choice(["wine", "gold", "black", "wine", "gold", "gold"])) for s in spots[18:60]]
    small = [(s, rng.uniform(12, 22), rng.choice(["gold", "wine", "gold", "wine", "black"])) for s in spots[60:150]]
    for group in (big, mid, small):
        for (x, y), r, kind in group:
            balloon(cv, x, y, r, kind)

    crown(cv, 606, 395, 190)
    gold_number(cv, 606, 735, 330)
    sparkles(cv, (380, 330, 830, 840), 40, seed=111)
    petals_scatter(cv, (340, 900, 860, 990), 18, "blush", seed=112, size=(7, 12))
    sparkles(cv, (330, 880, 880, 985), 26, seed=113, size=(2, 5))
    return cv


def wine_corner(base, adds):
    cv = base()
    for (x, y, n, sp) in adds:
        berries(cv, x, y, n=n, spread=sp, seed=x * 7 + y)
    return cv


# ------------------------------------------------------------ A Bela e o Príncipe
def royal_crown(cv, cx, base, w, layer="top"):
    """Prince's crown: band with jewels and five points topped with pearls."""
    h = w * 0.6
    band = h * 0.26
    tb = base - band
    l, r = cx - w / 2, cx + w / 2
    pk = [(l - w * 0.03, 0.88), (cx - w * 0.25, 0.7), (cx, 1.05), (cx + w * 0.25, 0.7), (r + w * 0.03, 0.88)]
    vx = [l + w * 0.125, cx - w * 0.125, cx + w * 0.125, r - w * 0.125]
    d = f"M{l:.1f},{tb:.1f} L{pk[0][0]:.1f},{tb - pk[0][1] * h:.1f}"
    for i in range(4):
        d += f" Q{vx[i]:.1f},{tb - 0.2 * h:.1f} {pk[i + 1][0]:.1f},{tb - pk[i + 1][1] * h:.1f}"
    d += f" L{r:.1f},{tb:.1f} Z"
    out = [f'<path d="{d}" fill="url(#goldv)" stroke="#8f6a2a" stroke-width="{w * 0.012:.1f}" stroke-linejoin="round"/>',
           f'<rect x="{l - w * 0.02:.1f}" y="{tb:.1f}" width="{w * 1.04:.1f}" height="{band:.1f}" rx="{band * 0.3:.1f}" fill="url(#gold)" stroke="#8f6a2a" stroke-width="{w * 0.01:.1f}"/>']
    for (x, f_) in pk:
        y = tb - f_ * h
        out.append(f'<circle cx="{x:.1f}" cy="{y - w * 0.035:.1f}" r="{w * 0.045:.1f}" fill="#fffaf0" stroke="#c9a253" stroke-width="{w * 0.008:.1f}"/>')
    out.append(f'<ellipse cx="{cx:.1f}" cy="{tb + band / 2:.1f}" rx="{w * 0.075:.1f}" ry="{band * 0.34:.1f}" fill="#7a1f33" stroke="#f0d9a0" stroke-width="{w * 0.008:.1f}"/>')
    for k in (-1, 1):
        out.append(f'<circle cx="{cx + k * w * 0.27:.1f}" cy="{tb + band / 2:.1f}" r="{band * 0.26:.1f}" fill="#7a1f33" stroke="#f0d9a0" stroke-width="{w * 0.007:.1f}"/>')
        for j in range(1, 4):
            out.append(f'<circle cx="{cx + k * (w * 0.1 + j * w * 0.055):.1f}" cy="{tb + band / 2:.1f}" r="{band * 0.12:.1f}" fill="#fffaf0"/>')
    # inner jewelled lines of the points
    out.append(f'<path d="M{cx:.1f},{tb - 0.15 * h:.1f} L{cx:.1f},{tb - 0.8 * h:.1f}" stroke="#fff3cf" stroke-width="{w * 0.012:.1f}" opacity="0.6"/>')
    cv.add(f'<g filter="url(#goldtex)">{"".join(out)}</g>', layer)


def espelho(seed=51, W=1200, H=1300):
    """Enchanted mirror (from the original tale) with a single wine rose, crowned for the prince."""
    cv = Canvas(W, H, seed)
    rng = random.Random(seed)
    cx, cy, rx, ry = 600, 735, 290, 385
    wash(cv, f"M{cx},{cy - 470} C{cx + 330},{cy - 470} {cx + 470},{cy - 250} {cx + 470},{cy} C{cx + 470},{cy + 260} {cx + 300},{cy + 470} {cx},{cy + 470} C{cx - 300},{cy + 470} {cx - 470},{cy + 260} {cx - 470},{cy} C{cx - 470},{cy - 250} {cx - 330},{cy - 470} {cx},{cy - 470} Z", "#efe0c9", 0.55)
    cv.defs.append(f'<clipPath id="mclip"><ellipse cx="{cx}" cy="{cy}" rx="{rx - 8}" ry="{ry - 8}"/></clipPath>')
    glass = cv.rad((cx - 70, cy - 120), ry * 1.15, [(0, "#fffdf8", 1), (0.55, "#f3ebdf", 1), (1, "#ddcfb9", 1)])
    cv.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - 6}" ry="{ry - 6}" fill="url(#{glass})"/>', "back")
    cv.add(f'<g clip-path="url(#mclip)" opacity="0.55"><path d="M{cx - 330},{cy + 40} L{cx - 120},{cy - 420} L{cx - 40},{cy - 420} L{cx - 250},{cy + 40} Z" fill="#ffffff"/>'
           f'<path d="M{cx - 200},{cy + 200} L{cx + 40},{cy - 420} L{cx + 75},{cy - 420} L{cx - 165},{cy + 200} Z" fill="#ffffff" opacity="0.7"/></g>', "back")
    # the rose: stem, thorns, leaves, head, fallen petals
    stem = f"M{cx + 4},{cy - 70} C{cx - 14},{cy + 60} {cx + 22},{cy + 170} {cx + 6},{cy + 300}"
    cv.add(f'<g filter="url(#wcleaf)"><path d="{stem}" fill="none" stroke="#4f6b49" stroke-width="10" stroke-linecap="round"/>'
           f'<path d="{stem}" fill="none" stroke="#7d9a72" stroke-width="3" stroke-linecap="round" opacity="0.7" transform="translate(-2,0)"/></g>', "mid")
    for (ty, side) in [(cy + 40, -1), (cy + 120, 1), (cy + 210, -1)]:
        tx = cx + 2 + rng.uniform(-6, 6)
        cv.add(f'<path d="M{tx:.1f},{ty:.1f} l{side * 14},-6 l{-side * 12},-6 z" fill="#4f6b49"/>', "mid")
    spray(cv, (cx + 4, cy + 95), (cx - 150, cy + 20), kind="sage", n=4, size=62, bend=-0.15, seed=511, layer="mid")
    spray(cv, (cx + 8, cy + 175), (cx + 150, cy + 120), kind="sage", n=4, size=58, bend=0.15, seed=512, layer="mid")
    rose(cv, cx + 2, cy - 140, 118, "blush", rot=15, squash=0.92, seed=513)
    bud(cv, cx - 120, cy - 40, -150, 48, "rose", seed=514)
    petals_scatter(cv, (cx - 150, cy + 300, cx + 150, cy + 345), 7, "blush", seed=515, size=(16, 26))
    sparkles(cv, (cx - 240, cy - 340, cx + 240, cy + 260), 34, seed=516, size=(3, 9))
    # gilded frame
    beads = "".join(
        f'<circle cx="{cx + (rx + 2) * math.cos(math.radians(a)):.1f}" cy="{cy + (ry + 2) * math.sin(math.radians(a)):.1f}" r="5" fill="#f6e3ad" stroke="#a87c38" stroke-width="1"/>'
        for a in range(0, 360, 7))
    cv.add(f'<g filter="url(#goldtex)"><ellipse cx="{cx}" cy="{cy}" rx="{rx + 22}" ry="{ry + 22}" fill="none" stroke="url(#gold)" stroke-width="30"/>'
           f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - 10}" ry="{ry - 10}" fill="none" stroke="url(#gold)" stroke-width="7"/>{beads}</g>', "front")
    # scroll ornaments at the sides and the foot of the frame
    def scroll(x, y, s, flip):
        k = -1 if flip else 1
        return (f'<path d="M{x},{y - 70 * s} C{x + k * 60 * s},{y - 70 * s} {x + k * 70 * s},{y - 10 * s} {x + k * 35 * s},{y} '
                f'C{x + k * 10 * s},{y + 8 * s} {x + k * 5 * s},{y - 22 * s} {x + k * 25 * s},{y - 26 * s}" fill="none" stroke="url(#gold)" stroke-width="{11 * s:.1f}" stroke-linecap="round"/>'
                f'<path d="M{x},{y + 70 * s} C{x + k * 60 * s},{y + 70 * s} {x + k * 70 * s},{y + 10 * s} {x + k * 35 * s},{y} " fill="none" stroke="url(#gold)" stroke-width="{11 * s:.1f}" stroke-linecap="round"/>')
    cv.add(f'<g filter="url(#goldtex)">{scroll(cx - rx - 26, cy, 1.0, True)}{scroll(cx + rx + 26, cy, 1.0, False)}</g>', "front")
    royal_crown(cv, cx, cy - ry - 24, 210)
    sparkles(cv, (cx - 200, cy - ry - 190, cx + 200, cy - ry - 40), 10, seed=517)
    # flowers at the foot of the mirror
    cluster(cv, cx - 150, cy + ry + 10, 70, ["blush", "ivory", "peach"], seed=518, foliage_dir=-160)
    cluster(cv, cx + 160, cy + ry + 15, 66, ["ivory", "blush", "rose"], seed=519, foliage_dir=-20)
    berries(cv, cx + 20, cy + ry + 40, n=8, spread=30, layer="front", seed=520)
    return cv

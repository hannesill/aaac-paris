"""Generate Eiffel Tower line art (front elevation) for the AAAC Paris hero SVG.

Real dimensions in metres: base 125 m square, legs 25 m wide at the feet,
first floor 57.6 m, second floor 115.7 m, third floor 276 m, tip 330 m.
The outer profile follows w(m) = 44.5 * exp(-0.01073 m) + 3 (SVG units).

Prints the <g class="eiffel"> group used in assets/paris-skyline.svg:
    python3 scripts/eiffel.py
The group in that file wraps the output in a transform that scales it 1.35x.
"""
import math
import sys

CX = 560.0
GROUND = 272.0
S = 0.76  # SVG units per metre


def y(m):
    return GROUND - S * m


def outer(m):
    return 44.5 * math.exp(-0.01073 * m) + 3.0


F1_BOT, F1_TOP = 52.0, 60.0
F2_BOT, F2_TOP = 113.0, 118.0
F3_BOT, F3_TOP = 270.0, 281.0


def leg(m):
    """Visible leg width in front view."""
    if m <= F1_BOT:
        return 19.0 - (19.0 - 11.5) * (m / F1_BOT)
    t = (m - F1_TOP) / (F2_BOT - F1_TOP)
    return 11.5 + t * (outer(F2_BOT) - 1.2 - 11.5)


def inner(m):
    return outer(m) - leg(m)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def poly(points):
    head, *rest = points
    return f"M{f(head[0])} {f(head[1])}" + "".join(f"L{f(x)} {f(yy)}" for x, yy in rest)


def edge(fn, m0, m1, side, step=3.0):
    pts = []
    m = m0
    while m < m1:
        pts.append((CX + side * fn(m), y(m)))
        m += step
    pts.append((CX + side * fn(m1), y(m1)))
    return pts


def zigzag(m0, m1, left, right, count):
    pts = []
    for i in range(count + 1):
        m = m0 + (m1 - m0) * i / count
        pts.append((left(m) if i % 2 == 0 else right(m), y(m)))
    return poly(pts)


def x_bracing(m0, m1, left, right, count):
    segs = []
    for i in range(count):
        a = m0 + (m1 - m0) * i / count
        b = m0 + (m1 - m0) * (i + 1) / count
        segs.append(poly([(left(a), y(a)), (right(b), y(b))]))
        segs.append(poly([(right(a), y(a)), (left(b), y(b))]))
    return "".join(segs)


main, detail = [], []

# Outer silhouette, both sides, ground to third floor.
for side in (-1, 1):
    main.append(poly(edge(outer, 0, F1_BOT, side)))
    main.append(poly(edge(outer, F1_TOP, F2_BOT, side)))
    main.append(poly(edge(outer, F2_TOP, F3_BOT, side, step=6.0)))

# Inner leg edges: feet to first floor, first floor to where the legs meet.
ARCH_FOOT = 9.0
for side in (-1, 1):
    main.append(poly(edge(inner, 0, ARCH_FOOT, side)))
    main.append(poly(edge(inner, ARCH_FOOT, F1_BOT, side)))
    main.append(poly(edge(inner, F1_TOP, F2_BOT, side)))

# Decorative base arch, a half-ellipse springing from the inner leg edges.
ARCH_TOP = 51.0
# Cubic halves leave the springing point along the inner leg edge, so the arch
# never bulges into the legs, and meet flat under the first-floor girder.
rx = inner(ARCH_FOOT)
c1m = ARCH_FOOT + 22.0
arch = f"M{f(CX - rx)} {f(y(ARCH_FOOT))}"
arch += f"C{f(CX - inner(c1m))} {f(y(c1m))} {f(CX - rx * 0.55)} {f(y(ARCH_TOP))} {f(CX)} {f(y(ARCH_TOP))}"
arch += f"C{f(CX + rx * 0.55)} {f(y(ARCH_TOP))} {f(CX + inner(c1m))} {f(y(c1m))} {f(CX + rx)} {f(y(ARCH_FOOT))}"
main.append(arch)

# Platforms.
def platform(m_bot, m_top, overhang):
    w = outer(m_bot) + overhang
    return f"M{f(CX - w)} {f(y(m_bot))}H{f(CX + w)}V{f(y(m_top))}H{f(CX - w)}Z"


main.append(platform(F1_BOT, F1_TOP, 4.0))
main.append(platform(F2_BOT, F2_TOP, 3.0))

# First-floor railing posts and the arcade frieze under the first-floor girder.
def balustrade(m_top, half, height, posts):
    top = y(m_top)
    rail = top - height
    d = f"M{f(CX - half)} {f(rail)}H{f(CX + half)}"
    for i in range(posts + 1):
        x = CX - half + 2 * half * i / posts
        d += f"M{f(x)} {f(top)}V{f(rail)}"
    return d


w1 = outer(F1_BOT) + 4.0
detail.append(balustrade(F1_TOP, w1 - 1.5, 3.2, 12))
n_arches = 10
span = (2 * w1) / n_arches
frieze = []
for i in range(n_arches):
    x0 = CX - w1 + i * span
    frieze.append(
        f"M{f(x0)} {f(y(F1_BOT))}Q{f(x0 + span / 2)} {f(y(F1_BOT) - 4.5)} {f(x0 + span)} {f(y(F1_BOT))}"
    )
detail.append("".join(frieze))

# Second-floor railing.
w2 = outer(F2_BOT) + 3.0
detail.append(balustrade(F2_TOP, w2 - 1.2, 2.6, 6))

# Lattice in the legs.
for side in (-1, 1):
    out_fn = lambda m, s=side: CX + s * outer(m)
    in_fn = lambda m, s=side: CX + s * inner(m)
    detail.append(zigzag(0, F1_BOT, out_fn, in_fn, 7))
    detail.append(zigzag(F1_TOP, F2_BOT, out_fn, in_fn, 6))

# Upper shaft: X-bracing that tightens as the tower narrows.
left = lambda m: CX - outer(m)
right = lambda m: CX + outer(m)
bands = [(F2_TOP, 150.0, 3), (150.0, 190.0, 3), (190.0, 232.0, 3), (232.0, F3_BOT, 3)]
for m0, m1, n in bands:
    detail.append(x_bracing(m0, m1, left, right, n))
    if m1 in (190.0,):
        main.append(poly([(left(m1), y(m1)), (right(m1), y(m1))]))

# Third floor cabin, lantern and antenna.
w3 = outer(F3_BOT) + 2.2
main.append(f"M{f(CX - w3)} {f(y(F3_BOT))}H{f(CX + w3)}V{f(y(F3_TOP))}H{f(CX - w3)}Z")
main.append(
    f"M{f(CX - w3 + 1.2)} {f(y(F3_TOP))}L{f(CX - 2.4)} {f(y(298))}H{f(CX + 2.4)}L{f(CX + w3 - 1.2)} {f(y(F3_TOP))}"
)
main.append(f"M{f(CX)} {f(y(298))}V{f(y(330))}")
detail.append(f"M{f(CX - w3)} {f(y(F3_BOT + 5.5))}H{f(CX + w3)}")
detail.append(f"M{f(CX - 1.6)} {f(y(312))}H{f(CX + 1.6)}")

# Stone piers under each foot.
for side in (-1, 1):
    a, b = CX + side * outer(0), CX + side * inner(0)
    lo, hi = min(a, b) - 2, max(a, b) + 2
    main.append(f"M{f(lo)} {f(GROUND)}V{f(GROUND - 4)}H{f(hi)}V{f(GROUND)}")

out = sys.stdout
out.write('  <g class="eiffel">\n')
out.write('    <g class="lineart-main">\n')
for d in main:
    out.write(f'      <path d="{d}"></path>\n')
out.write("    </g>\n")
out.write('    <g class="lineart-detail">\n')
for d in detail:
    out.write(f'      <path d="{d}"></path>\n')
out.write("    </g>\n")
out.write("  </g>\n")

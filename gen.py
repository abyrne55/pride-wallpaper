"""Generate progress-pride.svg wallpaper (3440x1440) with 11 rainbow stripes.

Uses cubic beziers for outer boundaries (preserving original shape).
The innermost boundary bezier is subdivided into 4 sub-segments using
de Casteljau's algorithm for smoother rendering.
Each stripe fills from its outer boundary to the innermost boundary,
drawn outermost-first to eliminate gaps.
"""
import math

colors = [
    "#1a1a1a", "#7d5a41", "#81c3e8", "#e696a6", "#ffffff",
    "#cf413d", "#e38d3b", "#e9c24e", "#6e8b54", "#4b6691", "#735382",
]
n = len(colors)

bg_color = "#e7e2db"

# --- Color transformation helpers ---
import colorsys

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f'#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}'

def tint_color(hex_color, tint_rgb, amount, sat_mult=1.0, val_mult=1.0):
    """Simulate lighting: adjust HSV, then blend toward a tint color."""
    r, g, b = [x / 255.0 for x in hex_to_rgb(hex_color)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s * sat_mult)
    v = min(1.0, v * val_mult)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r, g, b = r * 255, g * 255, b * 255
    tr, tg, tb = tint_rgb
    r = r + (tr - r) * amount
    g = g + (tg - g) * amount
    b = b + (tb - b) * amount
    return rgb_to_hex(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

# Time-of-day variants: each defines background + lighting for stripe colors
variants = {
    "morning": {
        "bg": "#f0d0c0",          # rosy sunrise cream
        "tint": (255, 150, 120),  # pinkish-red sunrise glow
        "amount": 0.12,
        "sat": 1.15,
        "val": 1.05,
    },
    "midday": {
        "bg": "#e7e2db",          # neutral warm gray
        "tint": (255, 255, 255),  # no tint
        "amount": 0.0,
        "sat": 1.0,
        "val": 1.0,
    },
    "evening": {
        "bg": "#8a7090",          # dusky purple-mauve
        "tint": (180, 100, 140),  # purple-pink dusk glow
        "amount": 0.12,
        "sat": 1.15,
        "val": 0.95,
    },
    "night": {
        "bg": "#191d2d",          # deep navy
        "tint": (60, 70, 120),    # soft blue moonlight
        "amount": 0.10,
        "sat": 0.90,
        "val": 0.60,
    },
}

# --- Canvas and layout ---
canvas_w, canvas_h = 3440, 1440

vert_x_left = 2147
vert_x_right = 7371
y_bottom = -417

# Layout constraints:
#   1. Leftmost 10% is pure background — outermost arc left edge at 10%
#   2. Arc bottom touches canvas bottom
#   3. All 11 arc stripes fully visible (outermost y_right within canvas)
#   4. Vertical stripe width < 25% of canvas width
# Scale derived from constraint 4 (target 24%)
scale = 0.21 * canvas_w / (vert_x_right - vert_x_left)

# Constraint 1: outermost arc's leftmost x at 10% from left
margin_left = round(canvas_w * 0.10)  # 344px
x_bottom_outer = -531  # orig_bounds[0][0], leftmost point of outermost arc
tx = margin_left - scale * x_bottom_outer

# Constraint 2: center horizontal rainbow vertically
# Equal distance from top-of-black-bar to top edge, and bottom-of-purple-bar to bottom edge
# outermost y_right = 7171 (orig_bounds[0][4]), innermost y_right = 3018 (orig_bounds[8][4])
ty = (canvas_h + scale * (7171 + 3018)) / 2

style_base = 'fill-opacity:1;fill-rule:nonzero;stroke:none'


def lerp(a, b, t):
    return a + (b - a) * t

def lerp_pt(p0, p1, t):
    return (lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t))

def subdivide_cubic(p0, p1, p2, p3, t=0.5):
    q0 = lerp_pt(p0, p1, t)
    q1 = lerp_pt(p1, p2, t)
    q2 = lerp_pt(p2, p3, t)
    r0 = lerp_pt(q0, q1, t)
    r1 = lerp_pt(q1, q2, t)
    s = lerp_pt(r0, r1, t)
    return (p0, q0, r0, s), (s, r1, q2, p3)

def subdivide_n(p0, p1, p2, p3, depth):
    if depth == 0:
        return [(p0, p1, p2, p3)]
    left, right = subdivide_cubic(p0, p1, p2, p3)
    return subdivide_n(*left, depth - 1) + subdivide_n(*right, depth - 1)

def bezier_path(segments):
    parts = []
    for _, p1, p2, p3 in segments:
        parts.append(f"C{round(p1[0])} {round(p1[1])} "
                     f"{round(p2[0])} {round(p2[1])} "
                     f"{round(p3[0])} {round(p3[1])}")
    return "".join(parts)


# Original 9 arc boundaries: (x_bottom, cp1_y, cp2_x, x_right, y_right)
orig_bounds = [
    (-531, 3710, 2814, 6940, 7171),
    (  -4, 3411, 3099, 6927, 6630),
    ( 510, 3111, 3370, 6898, 6087),
    (1090, 2805, 3701, 6922, 5532),
    (1612, 2519, 3993, 6928, 5015),
    (2147, 2219, 4283, 6919, 4472),
    (2682, 1919, 4575, 6910, 3928),
    (3226, 1647, 4898, 6962, 3435),
    (3686, 1417, 5291, 7124, 3018),
]

# Both rainbows 30% skinnier, equators fixed
skinny = 0.56
arc_bounds = []
for i in range(n + 1):
    t = i / n
    t_mapped = (1 - skinny) / 2 + t * skinny  # [0,1] → [0.15, 0.85]
    arc_bounds.append(tuple(
        round(lerp(orig_bounds[0][j], orig_bounds[8][j], t_mapped)) for j in range(5)
    ))

# Shift arc 50% closer to left edge; keep vertical stripes in place
arc_left_screen = scale * arc_bounds[0][0] + tx
tx -= arc_left_screen / 2  # move arc left so its left edge is 50% closer to x=0
vert_internal_shift = round(arc_left_screen / 2 / scale)  # compensate vertical stripes

right_edge = math.ceil((canvas_w - tx) / scale) + 20
transform = f'matrix({scale:.4f} 0 0 {-scale:.4f} {tx:.2f} {ty:.2f})'

# Bottom 25% of image is straight vertical; curve starts above
y_straight = round((ty - 0.75 * canvas_h) / scale)

# Circular quarter-arc approximation constant
k_circ = 0.5523

# Inner boundary: quarter circle (r = vertical span) + horizontal line
inner = arc_bounds[n]
xbi, cp1yi, cp2xi, xri, yri = inner

inner_r = yri - y_straight  # radius = vertical span for true circle
inner_arc_x = xbi + inner_r  # where the circular arc meets the horizontal

inner_p0 = (xbi, y_straight)
inner_p1 = (xbi, y_straight + k_circ * inner_r)
inner_p2 = (inner_arc_x - k_circ * inner_r, yri)
inner_p3 = (inner_arc_x, yri)

inner_segments = subdivide_n(inner_p0, inner_p1, inner_p2, inner_p3, 2)
inner_bezier = bezier_path(inner_segments) + f"H{xri}"

# Vertical stripe params — position so purple overlaps foreground arc purple
arc_total_width = arc_bounds[0][4] - arc_bounds[n][4]
xbo_purple = arc_bounds[n - 1][0]  # left edge of foreground arc purple
vert_x_left_s = xbo_purple
vert_x_right_s = vert_x_left_s + arc_total_width
vert_step = (vert_x_right_s - vert_x_left_s) / n
vert_y_top = math.ceil(ty / scale) + 10   # exit through top of canvas
vert_y_bottom = y_bottom                   # exit through bottom of canvas
vert_colors = list(reversed(colors))

def build_svg(bg, c_arc, c_vert, c_stroke):
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}">')
    lines.append(f'  <rect width="{canvas_w}" height="{canvas_h}" fill="{bg}"/>')
    lines.append(f'  <g transform="{transform}">')

    # Vertical stripes
    for i in range(n):
        color = c_vert[i]
        x1 = round(vert_x_left_s + i * vert_step)
        x2 = round(vert_x_left_s + (i + 1) * vert_step)
        overlap = 15 if i < n - 1 else 0
        left_ext = 0
        w = x2 - x1 + overlap + left_ext
        h = vert_y_top - vert_y_bottom
        d = f"M{x2 + overlap} {vert_y_top}V{vert_y_bottom}h-{w}v{h}z"
        lines.append(f'    <path d="{d}" style="fill:{color};{style_base}" />')

    # Arc stripes — tighter curve above y_straight, straight vertical below
    for i in range(n):
        color = c_arc[i]
        xbo, cp1yo, cp2xo, xro, yro = arc_bounds[i]
        dx_bottom = xbi - xbo
        r_outer = yro - y_straight
        arc_start_x = round(xbo + r_outer)
        cp2xo_circ = round(xbo + r_outer * (1 - k_circ))
        cp1yo_circ = round(y_straight + k_circ * r_outer)

        d = (f"M{right_edge} {yro}"
             f"H{arc_start_x}"
             f"C{cp2xo_circ} {yro} {xbo} {cp1yo_circ} {xbo} {y_straight}"
             f"V{y_bottom}"
             f"h{dx_bottom}"
             f"V{y_straight}"
             f"{inner_bezier}"
             f"H{right_edge}z")
        lines.append(f'    <path d="{d}" style="fill:{color};{style_base}" />')

    # Anti-fringe stroke — clipped to vertical stripe region
    lines.append(f'    <clipPath id="vc"><rect x="{vert_x_left_s}" y="{vert_y_bottom}" '
                 f'width="{vert_x_right_s - vert_x_left_s}" height="{vert_y_top - vert_y_bottom}"/></clipPath>')
    stroke_d = f"M{xbi} {y_bottom}V{y_straight}{inner_bezier}"
    lines.append(f'    <path d="{stroke_d}" style="fill:none;stroke:{c_stroke};stroke-width:8" '
                 f'clip-path="url(#vc)" />')

    lines.append('  </g>')
    lines.append('</svg>')
    return '\n'.join(lines) + '\n'

# Write default SVG (midday = original colors)
with open('progress-pride.svg', 'w') as f:
    f.write(build_svg(bg_color, colors, list(reversed(colors)), colors[-1]))
print(f"Wrote progress-pride.svg  (scale={scale:.4f}, tx={tx:.1f}, ty={ty:.1f})")

# Write time-of-day variants with tinted stripe colors
for name, v in variants.items():
    tinted = [tint_color(c, v["tint"], v["amount"], v["sat"], v["val"]) for c in colors]
    fname = f'progress-pride-{name}.svg'
    with open(fname, 'w') as f:
        f.write(build_svg(v["bg"], tinted, list(reversed(tinted)), tinted[-1]))
    print(f"Wrote {fname}  (bg={v['bg']}, tint={v['amount']:.0%})")

"""gen_paper.py - Construction-paper-style pride wallpapers.

Reads progress-pride-*.svg and produces textured PNGs simulating
construction paper: fiber texture, wobbly hand-cut edges, embossed
layer shadows, and chalky matte finish.

Requires: cairosvg, Pillow, numpy, scipy
"""

import glob
import hashlib
import os
import sys
from io import BytesIO

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.ndimage import map_coordinates

W, H = 6880, 2880


def stable_seed(s):
    """Deterministic seed from string (unlike hash(), not randomised)."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % (2**31)


def render_svg(path):
    """Rasterise SVG at wallpaper resolution."""
    png = cairosvg.svg2png(url=path, output_width=W, output_height=H)
    return np.array(Image.open(BytesIO(png)).convert('RGB'))


# ---------------------------------------------------------------------------
# Paper fiber texture
# ---------------------------------------------------------------------------

def paper_texture(h, w, seed=0):
    """Multiplicative fiber texture centred ~1.0.

    Uses gaussian-filtered full-resolution noise at multiple scales
    to avoid zoom-interpolation seam artefacts.
    """
    rng = np.random.RandomState(seed)
    tex = np.ones((h, w), dtype=np.float32)

    def noise():
        return rng.randn(h, w).astype(np.float32)

    # Large-scale dye variation
    tex += ndimage.gaussian_filter(noise(), 60) * 0.05

    # Medium blotches
    tex += ndimage.gaussian_filter(noise(), 20) * 0.03

    # Directional fibers (blur σ_y=2, σ_x=14 → horizontal streaks)
    tex += ndimage.gaussian_filter(noise(), [2, 14]) * 0.045

    # Fine fiber detail
    tex += ndimage.gaussian_filter(noise(), 1.5) * 0.03

    # Pixel-level grain
    tex += noise() * 0.012

    return tex


# ---------------------------------------------------------------------------
# Edge wobble via displacement field
# ---------------------------------------------------------------------------

def displacement_field(h, w, amp=4.0, scale=35, seed=0):
    """Smooth noise displacement (dx, dy) for wobbly scissors-cut edges."""
    rng = np.random.RandomState(seed)

    def field():
        r, c = h // scale + 2, w // scale + 2
        raw = rng.randn(r, c).astype(np.float32)
        f = ndimage.zoom(raw, (h / r, w / c))[:h, :w]
        return f / (f.std() + 1e-8) * amp

    return field(), field()


def warp(data, dx, dy, order=1):
    """Apply displacement to 2-D or 3-D array."""
    h, w = dx.shape
    yy, xx = np.mgrid[:h, :w]
    coords = [np.clip(yy + dy, 0, h - 1), np.clip(xx + dx, 0, w - 1)]

    if data.ndim == 2:
        return map_coordinates(data.astype(np.float32), coords,
                               order=order, mode='nearest')

    out = np.empty(data.shape, dtype=np.float32)
    for c in range(data.shape[2]):
        out[:, :, c] = map_coordinates(
            data[:, :, c].astype(np.float32), coords,
            order=order, mode='nearest')
    return out


# ---------------------------------------------------------------------------
# Per-region texture variation
# ---------------------------------------------------------------------------

def region_ids(img):
    """Hash quantised pixel colours → integer region ID (0-6)."""
    q = img.astype(np.int32) // 48
    return (q[:, :, 0] * 73 + q[:, :, 1] * 127 + q[:, :, 2] * 31) % 7


def multi_texture(base_tex, rid_map, seed=0):
    """Shift/flip base texture per region for per-strip variation."""
    h, w = base_tex.shape
    out = np.ones_like(base_tex)
    for rid in range(7):
        rng = np.random.RandomState(seed + rid)
        t = np.roll(base_tex, rng.randint(h), axis=0)
        t = np.roll(t, rng.randint(w), axis=1)
        if rng.rand() > 0.5:
            t = t[::-1]
        mask = rid_map == rid
        out[mask] = t[mask]
    return out


# ---------------------------------------------------------------------------
# Paper-layering shadows at colour transitions
# ---------------------------------------------------------------------------

def paper_shadows(img, blur=8, shadow_str=0.22, highlight_str=0.03,
                  offset=(4, 4)):
    """Soft drop shadow at colour edges, as if strips are layered paper."""
    f = img.astype(np.float32)

    # Colour-space edge magnitude
    mag = np.zeros((img.shape[0], img.shape[1]), dtype=np.float32)
    for c in range(3):
        mag += ndimage.sobel(f[:, :, c], 0) ** 2
        mag += ndimage.sobel(f[:, :, c], 1) ** 2
    mag = np.sqrt(mag)
    mx = mag.max()
    if mx > 0:
        mag /= mx

    # Binarise: any colour transition → uniform shadow (paper thickness
    # is constant regardless of colour contrast)
    mag = (mag > 0.05).astype(np.float32)

    # Wide, soft shadow offset down-right (simulates light from upper-left)
    b = ndimage.gaussian_filter(mag, blur)
    sh = ndimage.shift(b, list(offset), mode='constant', cval=0)
    mx_sh = sh.max() or 1e-8
    sh = sh / mx_sh * shadow_str

    # Very faint highlight on the lit side
    hi = ndimage.shift(b, [-offset[0] * 0.4, -offset[1] * 0.4],
                       mode='constant', cval=0)
    mx_hi = hi.max() or 1e-8
    hi = hi / mx_hi * highlight_str

    r = f.copy()
    for c in range(3):
        r[:, :, c] = r[:, :, c] * (1 - sh) + 255.0 * hi
    return np.clip(r, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process(svg, out):
    """SVG → construction-paper PNG."""
    s = stable_seed(svg)
    img = render_svg(svg)

    rids = region_ids(img)

    # Per-region paper texture
    base = paper_texture(H, W, seed=s + 1)
    tex = multi_texture(base, rids, seed=s + 100)

    result = img.astype(np.float32)
    for c in range(3):
        result[:, :, c] *= tex

    # Chalky matte finish — paper-base bleed-through
    paper_base = np.array([235, 225, 210], dtype=np.float32)
    for c in range(3):
        result[:, :, c] = result[:, :, c] * 0.97 + paper_base[c] * 0.03

    img = np.clip(result, 0, 255).astype(np.uint8)

    # Emboss at colour transitions
    img = paper_shadows(img)

    Image.fromarray(img).save(out, optimize=True)
    print(f"  {os.path.basename(out)}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

    svgs = sorted(glob.glob('progress-pride-*.svg'))
    base = 'progress-pride.svg'
    if os.path.exists(base) and base not in svgs:
        svgs.insert(0, base)
    if not svgs:
        print("No progress-pride*.svg found.")
        sys.exit(1)

    print(f"Generating {len(svgs)} construction-paper wallpapers...")
    for svg in svgs:
        process(svg, os.path.splitext(svg)[0] + '-paper.png')
    print("Done!")


if __name__ == '__main__':
    main()

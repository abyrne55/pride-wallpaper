"""gen_spanned.py - Spanned wallpapers for dual-monitor setups.

Takes progress-pride-*-paper.png images and composites them into a
single image for GNOME's "spanned" wallpaper mode.

Layout: left monitor (1920x1080) + right monitor (3440x1440),
top edges flush.  The right monitor gets the full image; the left
monitor gets a cropped left-center region (left-aligned, vertically
centred) to capture the rainbow arc.

Requires: Pillow
"""

import glob
import os
import sys

from PIL import Image

LEFT_W, LEFT_H = 1920, 1080
RIGHT_W, RIGHT_H = 3440, 1440
CANVAS_W = LEFT_W + RIGHT_W   # 5360
CANVAS_H = RIGHT_H            # 1440


def process(src_path, out_path):
    """Create a spanned wallpaper from a paper PNG."""
    src = Image.open(src_path)
    src_w, src_h = src.size

    # --- Right monitor: full image scaled to native resolution ---
    right_img = src.resize((RIGHT_W, RIGHT_H), Image.LANCZOS)

    # --- Left monitor: crop left-centre region at 16:9, then scale ---
    # Crop height proportional to monitor height ratio (1080/1440 of source)
    crop_h = round(src_h * LEFT_H / RIGHT_H)
    crop_w = round(crop_h * LEFT_W / LEFT_H)
    crop_x = 0
    crop_y = (src_h - crop_h) // 2

    left_crop = src.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    left_img = left_crop.resize((LEFT_W, LEFT_H), Image.LANCZOS)

    # --- Compose spanned canvas ---
    # Sample background colour from top-right corner (plain paper area)
    bg = right_img.getpixel((RIGHT_W - 1, 0))
    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), bg)

    canvas.paste(left_img, (0, 0))
    canvas.paste(right_img, (LEFT_W, 0))

    canvas.save(out_path, optimize=True)
    print(f"  {os.path.basename(out_path)}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

    pngs = sorted(glob.glob('progress-pride-*-paper.png'))
    if not pngs:
        print("No progress-pride-*-paper.png found.")
        sys.exit(1)

    print(f"Generating {len(pngs)} spanned wallpapers...")
    for png in pngs:
        out = png.replace('-paper.png', '-paper-spanned.png')
        process(png, out)
    print("Done!")


if __name__ == '__main__':
    main()

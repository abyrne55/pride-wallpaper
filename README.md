# pride-wallpaper

Generates desktop wallpapers (3440x1440) with a design inspired by LGBTQIA+ progress pride flag colors. Two output formats:

- **SVG wallpapers** (`gen.py`): Vector wallpapers with 11 rainbow stripes using cubic bezier curves. Generates 4 time-of-day variants (morning, midday, evening, night) with tinted colors and different backgrounds.
- **Construction-paper PNGs** (`gen_paper.py`): Textured PNGs at 2x resolution (6880x2880) simulating construction paper with fiber texture, wobbly edges, embossed shadows, and chalky finish.

A GNOME dynamic wallpaper XML (`progress-pride-dynamic.xml`) crossfades between the time-of-day SVGs on a 24-hour schedule.

## Usage

```bash
# Generate SVG wallpapers (no dependencies beyond Python stdlib)
python gen.py

# Generate construction-paper PNGs (requires: cairosvg, Pillow, numpy, scipy)
python gen_paper.py
```

## Architecture

- `gen.py` is self-contained (stdlib only). It defines the stripe geometry, color palette, and bezier math, then writes `progress-pride.svg` plus 4 time-of-day variants. The `variants` dict controls per-variant background color and HSV tinting. The `build_svg()` function assembles both the vertical stripes and curved arc stripes.
- `gen_paper.py` depends on `cairosvg`, `Pillow`, `numpy`, `scipy`. It applies a pipeline: SVG rasterization → per-region paper texture → edge wobble via displacement fields → paper-layer shadows → chalky matte finish. Output is deterministic (seeded from filename).
- The SVG coordinate system uses a transform matrix that maps original design coordinates to the 3440x1440 canvas. Layout is controlled by `scale`, `tx`, `ty` derived from margin/centering constraints.

#!/usr/bin/env python3
"""
Post-processing: Add a gradient border with rounded corners to YouTube thumbnails.
Extracts dominant colors from the thumbnail to create a contextual gradient border.

Usage:
  python3 add_gradient_border.py --input thumbnail.png --output thumbnail_bordered.png
  python3 add_gradient_border.py --input thumbnail.png  # overwrites in-place
  python3 add_gradient_border.py --input thumbnail.png --color1 "#E6FF05" --color2 "#00EBFA"
"""

import argparse
import colorsys
import os
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed. Run: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

# Constants — must stay consistent across all thumbnails
CANVAS_W, CANVAS_H = 1280, 720
BORDER_THICKNESS = 18
OUTER_RADIUS = 0    # no outer rounding — YouTube crops corners itself
INNER_RADIUS = 32   # inner image corner radius (matches Figma spec)


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_dominant_colors(img: Image.Image, n_colors: int = 2) -> list:
    """Extract the two most vibrant accent colors from the thumbnail.

    Prioritizes saturated, bright accent colors over dark backgrounds.
    Returns a list of 2 RGB tuples suitable for a vivid gradient border.
    """
    # Resize for speed
    small = img.copy()
    small = small.resize((64, 36), Image.LANCZOS)
    small = small.convert("RGB")

    # Count all pixel colors, quantized to reduce noise
    pixels = []
    for y in range(small.height):
        for x in range(small.width):
            r, g, b = small.getpixel((x, y))
            # Quantize to 32-level buckets
            r = (r // 32) * 32 + 16
            g = (g // 32) * 32 + 16
            b = (b // 32) * 32 + 16
            r, g, b = min(r, 255), min(g, 255), min(b, 255)
            pixels.append((r, g, b))

    counter = Counter(pixels)

    # Score each color by vibrancy: prioritize high saturation AND brightness
    # This ensures accent colors beat dark backgrounds even if less frequent
    scored = []
    for color, count in counter.most_common(80):
        r, g, b = color
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        # Skip very dark or very desaturated colors
        if v < 0.2 or (s < 0.15 and v < 0.7):
            continue
        # Vibrancy score: saturation * value * sqrt(count)
        # This balances "how colorful" with "how present" in the image
        vibrancy = s * v * (count ** 0.5)
        scored.append((color, count, h, s, v, vibrancy))

    if len(scored) == 0:
        return [(100, 200, 255), (255, 180, 50)]  # safe fallback

    # Sort by vibrancy score (most vibrant first)
    scored.sort(key=lambda x: x[5], reverse=True)

    # Pick the most vibrant color as color1
    color1 = scored[0][0]
    hue1 = scored[0][2]

    # Pick color2: the most vibrant color with a distinct hue
    color2 = None
    for entry in scored[1:]:
        hue_diff = min(abs(entry[2] - hue1), 1.0 - abs(entry[2] - hue1))
        if hue_diff > 0.08:  # at least ~30 degrees apart on hue wheel
            color2 = entry[0]
            break

    if color2 is None:
        # No distinct second color found — shift hue of color1
        r, g, b = color1
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h2 = (h + 0.15) % 1.0  # shift 54 degrees
        r2, g2, b2 = colorsys.hsv_to_rgb(h2, min(s * 1.2, 1.0), min(v * 1.1, 1.0))
        color2 = (int(r2 * 255), int(g2 * 255), int(b2 * 255))

    # Boost both colors to neon-vivid levels matching the channel's signature border
    # Target: near-full saturation (0.90+) and near-full brightness (0.95+)
    # Reference: #E6FF05 (electric lime) → #00EBFA (electric cyan)
    result = []
    for color in [color1, color2]:
        r, g, b = color
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        s = max(s, 0.85)   # floor saturation at 85%
        s = min(s * 1.3, 1.0)  # then boost aggressively
        v = max(v, 0.90)  # floor brightness at 90%
        v = min(v * 1.2, 1.0)  # then boost to near-max
        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
        result.append((int(r2 * 255), int(g2 * 255), int(b2 * 255)))

    return result


def create_gradient(width: int, height: int, color1: tuple, color2: tuple) -> Image.Image:
    """Create a diagonal gradient from top-left (color1) to bottom-right (color2)."""
    gradient = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(gradient)

    for y in range(height):
        for x in range(width):
            # Diagonal interpolation factor
            t = (x / width + y / height) / 2.0
            r = int(color1[0] * (1 - t) + color2[0] * t)
            g = int(color1[1] * (1 - t) + color2[1] * t)
            b = int(color1[2] * (1 - t) + color2[2] * t)
            draw.point((x, y), fill=(r, g, b))

    return gradient


def create_rounded_mask(width: int, height: int, radius: int) -> Image.Image:
    """Create a mask with rounded corners using 4x supersampling for smooth antialiased edges."""
    scale = 4
    mask_large = Image.new("L", (width * scale, height * scale), 0)
    draw = ImageDraw.Draw(mask_large)
    draw.rounded_rectangle(
        [(0, 0), (width * scale - 1, height * scale - 1)],
        radius=radius * scale,
        fill=255,
    )
    mask = mask_large.resize((width, height), Image.LANCZOS)
    return mask


def add_gradient_border(input_path: str, output_path: str = None,
                        color1: tuple = None, color2: tuple = None) -> str:
    """Add gradient border with rounded corners to a thumbnail.

    Args:
        input_path: Path to the input thumbnail image
        output_path: Path for the output (default: overwrite input)
        color1: RGB tuple for gradient start (top-left). Auto-extracted if None.
        color2: RGB tuple for gradient end (bottom-right). Auto-extracted if None.

    Returns:
        Path to the output file
    """
    if output_path is None:
        output_path = input_path

    img = Image.open(input_path).convert("RGBA")

    # Resize inner image to fit within the border
    inner_w = CANVAS_W - 2 * BORDER_THICKNESS
    inner_h = CANVAS_H - 2 * BORDER_THICKNESS
    inner = img.resize((inner_w, inner_h), Image.LANCZOS)

    # Auto-extract colors if not provided
    if color1 is None or color2 is None:
        auto_colors = extract_dominant_colors(inner)
        if color1 is None:
            color1 = auto_colors[0]
        if color2 is None:
            color2 = auto_colors[1]

    # 1. Create the gradient background (full canvas, no outer rounding)
    gradient = create_gradient(CANVAS_W, CANVAS_H, color1, color2)
    canvas = gradient.convert("RGBA")

    # 2. Create inner rounded mask for the thumbnail content
    inner_mask = create_rounded_mask(inner_w, inner_h, INNER_RADIUS)

    # 3. Paste the inner image onto the canvas with rounded corners
    inner_rgba = inner.convert("RGBA")
    canvas.paste(inner_rgba, (BORDER_THICKNESS, BORDER_THICKNESS), inner_mask)

    # 4. Save as PNG
    canvas.save(output_path, "PNG")
    print(f"  Border added: {output_path} (gradient: {rgb_to_hex(*color1)} → {rgb_to_hex(*color2)})")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Add gradient border to YouTube thumbnails")
    parser.add_argument("--input", required=True, help="Path to input thumbnail")
    parser.add_argument("--output", default=None, help="Output path (default: overwrite input)")
    parser.add_argument("--color1", default=None, help="Gradient start color as hex (e.g., '#E6FF05'). Auto-detected if omitted.")
    parser.add_argument("--color2", default=None, help="Gradient end color as hex (e.g., '#00EBFA'). Auto-detected if omitted.")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    c1 = hex_to_rgb(args.color1) if args.color1 else None
    c2 = hex_to_rgb(args.color2) if args.color2 else None

    add_gradient_border(args.input, args.output, c1, c2)


if __name__ == "__main__":
    main()

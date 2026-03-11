#!/usr/bin/env python3
"""
YouTube Thumbnail Generator using Nano Banana 2 (Gemini 3.1 Flash Image API).
Generates professional, high-CTR thumbnails from a headshot + prompt.

Supports two modes:
  1. --cells-dir: Auto-select headshot + reference from analyzed grid cells (recommended)
  2. --headshot:   Manual headshot path (legacy, still works)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed. Run: pip3 install google-genai", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)


# Maps target emotions to preferred cell expressions (in priority order)
EMOTION_TO_EXPRESSION = {
    "excited": ["grin", "smile_teeth", "surprised", "smile_no_teeth"],
    "proud": ["grin", "smile_teeth", "smile_no_teeth"],
    "amazed": ["surprised", "grin", "smile_teeth"],
    "confident": ["smile_no_teeth", "neutral", "smile_teeth"],
    "curious": ["neutral", "smile_no_teeth", "surprised"],
    "happy": ["smile_teeth", "grin", "smile_no_teeth"],
    "serious": ["serious", "neutral"],
    "neutral": ["neutral", "smile_no_teeth"],
    "grin": ["grin", "smile_teeth"],
    "smile": ["smile_teeth", "smile_no_teeth", "grin"],
}


def load_image(path: str) -> tuple:
    """Load image and return (bytes, mime_type)."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        print(f"ERROR: Image not found at: {path}", file=sys.stderr)
        sys.exit(1)

    ext = Path(path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(path, "rb") as f:
        image_bytes = f.read()

    return image_bytes, mime_type


def select_cells(cells_dir: str, emotion: str = "excited") -> tuple:
    """Auto-select headshot + reference cell from cells.json based on target emotion.

    Returns (headshot_path, reference_path) where:
      - headshot_path: cell matching the target emotion best
      - reference_path: frontal_neutral cell (identity baseline), or None
    """
    json_path = os.path.join(cells_dir, "cells.json")
    if not os.path.exists(json_path):
        print(f"ERROR: cells.json not found in {cells_dir}. Run analyze_grid.py first.", file=sys.stderr)
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    cells = data.get("cells", {})

    # Find frontal neutral (identity baseline)
    frontal_neutral = None
    for fname, info in cells.items():
        if info.get("angle") == "frontal" and info.get("expression") == "neutral":
            frontal_neutral = fname
            break

    # Find best expression match for the target emotion
    emotion_lower = emotion.lower().strip()
    preferred = EMOTION_TO_EXPRESSION.get(emotion_lower, ["grin", "smile_teeth", "neutral"])

    best_cell = None
    for target_expr in preferred:
        for fname, info in cells.items():
            if info.get("expression") == target_expr and fname != frontal_neutral:
                best_cell = fname
                break
        if best_cell:
            break

    # Fallback: use any cell that isn't frontal_neutral
    if not best_cell:
        for fname in cells:
            if fname != frontal_neutral:
                best_cell = fname
                break

    # If still nothing, use first cell
    if not best_cell:
        best_cell = list(cells.keys())[0]

    headshot_path = os.path.join(cells_dir, best_cell)
    reference_path = os.path.join(cells_dir, frontal_neutral) if frontal_neutral else None

    return headshot_path, reference_path


def generate_thumbnail(client, prompt: str, headshot_bytes: bytes, headshot_mime: str,
                       variation: int, reference_images: list = None) -> Optional[bytes]:
    """Generate a single thumbnail variation."""

    # Build content: face reference(s) first, then headshot (identity anchor) last before prompt
    contents = []
    if reference_images:
        for ref_bytes, ref_mime in reference_images:
            contents.append(types.Part.from_bytes(data=ref_bytes, mime_type=ref_mime))
    contents.append(types.Part.from_bytes(data=headshot_bytes, mime_type=headshot_mime))
    contents.append(types.Part.from_text(text=prompt))

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=config,
        )
    except Exception as e:
        print(f"  ERROR (primary model) v{variation}: {e}", file=sys.stderr)
        # Try fallback model
        try:
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=contents,
                config=config,
            )
        except Exception as e2:
            print(f"  ERROR (fallback model) v{variation}: {e2}", file=sys.stderr)
            return None

    # Extract image from response
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data
            if hasattr(part, 'text') and part.text:
                print(f"  Model note (v{variation}): {part.text[:200]}")

    print(f"  WARNING: No image returned for variation {variation}", file=sys.stderr)
    return None


def save_thumbnail(image_data: bytes, output_path: str):
    """Save image data to file, converting to PNG if needed."""
    with open(output_path, "wb") as f:
        f.write(image_data)

    # Verify and resize to 1280x720 if needed
    try:
        img = Image.open(output_path)
        if img.size != (1280, 720):
            img = img.resize((1280, 720), Image.LANCZOS)
            img.save(output_path, "PNG")
    except Exception:
        pass  # Keep original if resize fails


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnails with Nano Banana 2 (Gemini 3.1 Flash Image)")

    # Cell-based mode (recommended)
    parser.add_argument("--cells-dir", default=None,
                        help="Path to analyzed cells directory (with cells.json). Auto-selects headshot + reference.")
    parser.add_argument("--emotion", default="excited",
                        help="Target emotion for cell selection (default: excited). "
                             "Options: excited, proud, amazed, confident, curious, happy, serious, neutral, grin, smile")

    # Legacy manual mode
    parser.add_argument("--headshot", default=None, help="Path to headshot reference image (legacy mode)")
    parser.add_argument("--references", default=None,
                        help="Comma-separated paths to reference images (face refs only, NO style refs with other people)")

    # Common options
    parser.add_argument("--prompt", required=True, help="Full thumbnail generation prompt")
    parser.add_argument("--output", default="./thumbnails", help="Output directory (default: ./thumbnails)")
    parser.add_argument("--variation", type=int, default=0, help="Variation number (0=all, 1-3=specific)")
    parser.add_argument("--prompt-v2", default=None, help="Modified prompt for variation 2")
    parser.add_argument("--prompt-v3", default=None, help="Modified prompt for variation 3")
    parser.add_argument("--title", default=None, help="Video title used for naming output files")
    parser.add_argument("--suffix", default="", help="Suffix appended to filename before extension, e.g. 'a', 'b', 'c'")

    args = parser.parse_args()

    # Validate: need either --cells-dir or --headshot
    if not args.cells_dir and not args.headshot:
        print("ERROR: Provide either --cells-dir (recommended) or --headshot.", file=sys.stderr)
        sys.exit(1)

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set. Export it or add to ~/.zshrc", file=sys.stderr)
        sys.exit(1)

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Determine headshot and references
    reference_images = []

    if args.cells_dir:
        # Auto-select from cells.json
        headshot_path, ref_path = select_cells(args.cells_dir, args.emotion)
        print(f"Auto-selected headshot: {headshot_path}")
        if ref_path:
            print(f"Auto-selected reference (identity baseline): {ref_path}")
            ref_bytes, ref_mime = load_image(ref_path)
            reference_images.append((ref_bytes, ref_mime))
    else:
        headshot_path = args.headshot

    # Load manual references if provided (face refs only)
    if args.references:
        for ref_path in args.references.split(","):
            ref_path = ref_path.strip()
            if ref_path:
                ref_bytes, ref_mime = load_image(ref_path)
                reference_images.append((ref_bytes, ref_mime))
                print(f"  Reference loaded: {ref_path}")

    # Load headshot
    print(f"Loading headshot: {headshot_path}")
    headshot_bytes, headshot_mime = load_image(headshot_path)
    print(f"  Loaded ({len(headshot_bytes)} bytes, {headshot_mime})")

    # Create output directory
    output_dir = os.path.expanduser(args.output)
    os.makedirs(output_dir, exist_ok=True)

    # Determine which variations to generate
    prompts = {}
    if args.variation == 0:
        prompts[1] = args.prompt
        prompts[2] = args.prompt_v2 or args.prompt
        prompts[3] = args.prompt_v3 or args.prompt
    else:
        prompts[args.variation] = args.prompt

    # Build filename prefix: YYYY-MM-DD_slug
    date_str = datetime.now().strftime("%Y-%m-%d")
    if args.title:
        slug = re.sub(r'[^a-zA-Z0-9äöüÄÖÜß]+', '-', args.title).strip('-').lower()
        slug = slug[:50]  # cap length
    else:
        slug = "thumbnail"
    filename_prefix = f"{date_str}_{slug}"

    # Generate each variation
    results = []
    for var_num, prompt in prompts.items():
        print(f"\nGenerating variation {var_num}...")
        image_data = generate_thumbnail(client, prompt, headshot_bytes, headshot_mime, var_num,
                                        reference_images or None)

        if image_data:
            output_path = os.path.join(output_dir, f"{filename_prefix}_v{var_num}{args.suffix}.png")
            save_thumbnail(image_data, output_path)
            print(f"  Saved: {output_path}")
            results.append(output_path)
        else:
            print(f"  Failed to generate variation {var_num}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Generated {len(results)} thumbnail(s) in: {output_dir}")
    for r in results:
        print(f"  - {r}")
    print(f"{'='*50}")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())

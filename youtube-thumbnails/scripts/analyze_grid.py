#!/usr/bin/env python3
"""
Analyze and prepare a 3x3 headshot grid for YouTube thumbnail generation.

Crops the grid into 9 individual cells, then uses Gemini Vision to auto-label
each cell with its camera angle and facial expression. Outputs a cells.json
that the thumbnail generator uses to pick the right cell per variation.

Usage:
  python3 analyze_grid.py --grid "Headshots/person-grid.png"
  python3 analyze_grid.py --grid "Headshots/person-grid.png" --output "Headshots/person-cells/"
"""

import argparse
import json
import os
import sys
from pathlib import Path

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


ANALYSIS_PROMPT = """Analyze this headshot photo. Respond with ONLY a JSON object, no other text.

Determine:
1. **angle**: The camera angle relative to the person's face. Choose exactly one:
   - "frontal" — camera directly facing the person
   - "34_left" — camera is 30-45 degrees to the person's left (you see more of their right cheek)
   - "34_right" — camera is 30-45 degrees to the person's right (you see more of their left cheek)
   - "profile_left" — camera is ~90 degrees to the left (side view, looking left)
   - "profile_right" — camera is ~90 degrees to the right (side view, looking right)

2. **expression**: The facial expression. Choose exactly one:
   - "neutral" — relaxed, no smile, resting face
   - "smile_no_teeth" — closed-mouth smile, lips together
   - "smile_teeth" — open smile showing teeth
   - "grin" — broad grin, wide open smile showing teeth
   - "surprised" — eyebrows raised, eyes wide, mouth may be open
   - "serious" — intense or focused look, slight frown or tension

3. **description**: A brief 5-10 word description of the pose (e.g., "looking right, relaxed neutral expression")

Respond with ONLY:
{"angle": "...", "expression": "...", "description": "..."}"""


def crop_grid(grid_path: str, output_dir: str) -> list:
    """Crop a 3x3 grid into 9 individual cells. Returns list of (filename, row, col)."""
    img = Image.open(grid_path)
    w, h = img.size
    cell_w, cell_h = w // 3, h // 3

    os.makedirs(output_dir, exist_ok=True)

    cells = []
    for row in range(3):
        for col in range(3):
            idx = row * 3 + col + 1
            filename = f"cell_{idx:02d}.png"
            cell = img.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            cell.save(os.path.join(output_dir, filename), "PNG")
            cells.append((filename, row, col))
            print(f"  Cropped {filename} (row={row}, col={col}, {cell.size[0]}x{cell.size[1]})")

    return cells


def analyze_cell(client, image_path: str) -> dict:
    """Use Gemini Vision to analyze a single headshot cell."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    ext = Path(image_path).suffix.lower()
    mime_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=ANALYSIS_PROMPT),
    ]

    config = types.GenerateContentConfig(response_modalities=["TEXT"])

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
    except Exception as e:
        print(f"  WARNING: Analysis failed for {image_path}: {e}", file=sys.stderr)
        return {"angle": "unknown", "expression": "unknown", "description": "analysis failed"}

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text = part.text.strip()
                # Handle markdown code blocks
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    import re
                    match = re.search(r'\{[^}]+\}', text)
                    if match:
                        try:
                            return json.loads(match.group())
                        except json.JSONDecodeError:
                            pass
                    return {"angle": "unknown", "expression": "unknown", "description": f"parse error: {text[:100]}"}

    return {"angle": "unknown", "expression": "unknown", "description": "no response"}


def main():
    parser = argparse.ArgumentParser(description="Analyze and prepare a 3x3 headshot grid")
    parser.add_argument("--grid", required=True, help="Path to the 3x3 headshot grid image")
    parser.add_argument("--output", default=None, help="Output directory for cells (default: auto from grid name)")

    args = parser.parse_args()

    grid_path = os.path.expanduser(args.grid)
    if not os.path.exists(grid_path):
        print(f"ERROR: Grid not found: {grid_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        grid_name = Path(grid_path).stem
        grid_parent = Path(grid_path).parent
        output_dir = str(grid_parent / f"{grid_name}-cells")

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Step 1: Crop the grid
    print(f"Cropping grid: {grid_path}")
    img = Image.open(grid_path)
    print(f"  Grid size: {img.size[0]}x{img.size[1]}")
    cells = crop_grid(grid_path, output_dir)
    print(f"  Cropped {len(cells)} cells into: {output_dir}\n")

    # Step 2: Analyze each cell with Gemini Vision
    print("Analyzing cells with Gemini Vision...")
    cells_data = {}

    for filename, row, col in cells:
        cell_path = os.path.join(output_dir, filename)
        print(f"  Analyzing {filename}...", end=" ", flush=True)
        result = analyze_cell(client, cell_path)
        result["row"] = row
        result["col"] = col
        cells_data[filename] = result
        print(f"→ {result['angle']} / {result['expression']} — {result.get('description', '')}")

    # Step 3: Write cells.json
    output = {
        "grid_source": os.path.basename(grid_path),
        "grid_size": f"{img.size[0]}x{img.size[1]}",
        "cells_dir": output_dir,
        "cells": cells_data,
    }

    json_path = os.path.join(output_dir, "cells.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved analysis: {json_path}")

    # Step 4: Print summary with recommended cell selection
    print(f"\n{'='*60}")
    print("CELL SUMMARY")
    print(f"{'='*60}")

    # Find the frontal neutral cell (identity baseline)
    frontal_neutral = None
    for fname, data in cells_data.items():
        if data["angle"] == "frontal" and data["expression"] == "neutral":
            frontal_neutral = fname
            break

    if frontal_neutral:
        print(f"\n  Identity baseline (frontal neutral): {frontal_neutral}")
    else:
        print("\n  WARNING: No frontal neutral cell found! Consider re-shooting the grid.")

    print("\n  All cells:")
    for fname, data in cells_data.items():
        marker = " ← BASELINE" if fname == frontal_neutral else ""
        print(f"    {fname}: {data['angle']} / {data['expression']}{marker}")

    print(f"\n{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

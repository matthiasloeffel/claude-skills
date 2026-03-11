#!/usr/bin/env python3
"""
Build 15 thumbnail prompts from a single JSON style brief.

Usage:
  python3 build_prompts.py --brief style_brief.json --output .prompts/topic/

The style brief JSON contains all 15 scene cards (5 variations × 3 sub-scenes).
The script fills a battle-tested prompt template with the variable sections,
keeping the boilerplate (face lock, wardrobe rules, avoid list) consistent.

Output: 15 .txt files (v1a.txt through v5c.txt) ready for generate_thumbnail.py.
Optionally also outputs a run.sh script to generate all thumbnails.
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ============================================================
# BOILERPLATE BLOCKS (never change — proven to work)
# ============================================================

FACE_LOCK = """**FACE REFERENCE — Identity Locking (CRITICAL):**
The last image provided is the FACE REFERENCE. This is the identity anchor for the entire image.
- Preserve EXACTLY: face shape (jawline, cheekbones, forehead width), nose shape and size, eye shape and color, eyebrow shape and thickness, lip shape, ear shape, skin tone and texture, hair color, hair texture, hairline position
- The person's bone structure and proportions must remain photorealistic and unchanged — do NOT idealize, smooth, or reshape the face
- Expression may change (see below) — but expression is a MUSCLE change only, not a structural change. The underlying face shape stays identical
- Any deviation in bone structure, nose shape, eye spacing, or skin tone = failure. Regenerate if the face does not match the reference"""

WARDROBE_RULES = """No suit, no blazer, no formal attire of any kind."""

AVOID_BLOCK = """AVOID: cluttered backgrounds, distorted facial features, unreadable text, plastic-looking skin, flat even studio lighting, tiny elements, low contrast, extra fingers or eyes, watermarks, flat 2D logo PNGs, generic sans-serif fonts, formal clothes, blazers, suits, uniforms, business attire, different person, altered bone structure, changed nose shape, different eye shape or spacing, smoothed or idealized skin, skin tone change, generic AI face, different hair color or style, misspelled words, mixed German/English text, extra letters in text overlays, invented words."""


def build_prompt(scene: dict) -> str:
    """Build a complete thumbnail prompt from a scene card dict."""

    # Extract fields with defaults
    emotion = scene.get("emotion", "excited")
    emotion_desc = scene.get("emotion_desc", "big genuine open smile, eyebrows raised, forward energy")
    position = scene.get("position", "RIGHT")
    framing = scene.get("framing", "medium shot from waist up")
    pose = scene.get("pose", "")
    wardrobe = scene.get("wardrobe", "Clean fitted white crew-neck t-shirt — sporty-casual, minimal.")
    lighting = scene.get("lighting", "")
    primary_prop = scene.get("primary_prop", "")
    secondary_element = scene.get("secondary_element", "")
    ambient_details = scene.get("ambient_details", "")
    hero_text = scene.get("hero_text", "")
    hero_style = scene.get("hero_style", "")
    hero_placement = scene.get("hero_placement", "upper-left")
    context_text = scene.get("context_text", "")
    context_style = scene.get("context_style", "bold white uppercase, strong black drop shadow")
    context_placement = scene.get("context_placement", "below hero text")
    accent_text = scene.get("accent_text", "")
    accent_style = scene.get("accent_style", "")
    text_elements_extra = scene.get("text_elements_extra", "")
    background = scene.get("background", "")
    composition = scene.get("composition", "")
    style = scene.get("style", "")
    graphics = scene.get("graphics", "")

    # Build TEXT ELEMENTS section
    hero_word_count = len(hero_text.split())
    context_word_count = len(context_text.split())
    text_elements = f'- Hero: "{hero_text}" ({hero_word_count} word{"s" if hero_word_count != 1 else ""}, all caps, {hero_style})'
    text_elements += f'\n- Context: "{context_text}" ({context_word_count} words, all caps, German, {context_style})'
    if accent_text:
        text_elements += f'\n- Accent: "{accent_text}" ({accent_style})'
    text_elements += "\n- No other text anywhere in the image"

    # Build SCENE & PROPS section
    props_section = f"- PRIMARY PROP: {primary_prop}"
    if secondary_element:
        props_section += f"\n- SECONDARY ELEMENT: {secondary_element}"
    if ambient_details:
        props_section += f"\n- AMBIENT DETAILS: {ambient_details}"

    # Build TEXT & GRAPHICS section
    text_graphics = f'- HERO TEXT: "{hero_text}" — {hero_style}. Placement: {hero_placement}.'
    text_graphics += f'\n- CONTEXT TEXT: "{context_text}" — {context_style}. Placement: {context_placement}.'
    if accent_text:
        text_graphics += f'\n- ACCENT TEXT: "{accent_text}" — {accent_style}.'
    if graphics:
        text_graphics += f"\n- {graphics}"

    prompt = f"""Design a professional YouTube video thumbnail in 16:9 aspect ratio (1280x720) using the person from the reference image.

SUBJECT:
{FACE_LOCK}

- Change only their expression to {emotion.upper()}: {emotion_desc} — ONLY the muscles around the eyes and mouth change, all bone structure remains identical to the reference
- Position the person on the {position} third of the frame
- Framing: {framing}

POSE & GESTURE:
{pose}

WARDROBE:
{wardrobe} {WARDROBE_RULES}

LIGHTING:
{lighting}

SCENE & PROPS:
{props_section}

TEXT & GRAPHICS:
{text_graphics}

TEXT ELEMENTS (spell exactly as written):
{text_elements}

BACKGROUND:
{background}

COMPOSITION:
{composition}

STYLE:
{style}

{AVOID_BLOCK}"""

    return prompt.strip()


def build_run_script(brief: dict, output_dir: str, cells_dir: str, title: str) -> str:
    """Build a bash script to run all 15 thumbnail generations."""
    lines = [
        "#!/bin/bash",
        "# Auto-generated thumbnail generation script",
        'SKILL_ROOT="$HOME/.claude/skills/youtube-thumbnails"',
        f'CELLS_DIR="{cells_dir}"',
        f'OUTPUT_DIR="{output_dir}"',
        f'TITLE="{title}"',
        "",
    ]

    variations = brief.get("variations", [])
    suffixes = ["a", "b", "c"]

    for batch_idx, suffix in enumerate(suffixes):
        lines.append(f'echo "Starting Batch {batch_idx + 1} (suffix {suffix})..."')
        for v_idx, variation in enumerate(variations):
            v_num = v_idx + 1
            emotion = variation.get("emotion", "excited")
            prompt_file = f"v{v_num}{suffix}.txt"
            lines.append(
                f'python3 "${{SKILL_ROOT}}/scripts/generate_thumbnail.py" \\\n'
                f'  --cells-dir "${{CELLS_DIR}}" --emotion "{emotion}" \\\n'
                f'  --prompt "$(cat "${{OUTPUT_DIR}}/../prompts/{prompt_file}")" \\\n'
                f'  --output "${{OUTPUT_DIR}}" --variation {v_num} --suffix {suffix} --title "${{TITLE}}" &'
            )
        lines.append("wait")
        lines.append(f'echo "Batch {batch_idx + 1} done"')
        lines.append("")

    # Organize into subfolders
    lines.append("# Organize into subfolders")
    lines.append("for v in 1 2 3 4 5; do")
    lines.append('  mkdir -p "${OUTPUT_DIR}/v${v}"')
    lines.append('  for f in "${OUTPUT_DIR}"/*_v${v}*.png; do')
    lines.append('    [ -f "$f" ] && mv "$f" "${OUTPUT_DIR}/v${v}/"')
    lines.append("  done")
    lines.append("done")
    lines.append('echo "All 15 thumbnails generated and organized"')

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build 15 thumbnail prompts from a JSON style brief"
    )
    parser.add_argument(
        "--brief", required=True,
        help="Path to style_brief.json"
    )
    parser.add_argument(
        "--output", required=True,
        help="Output directory for prompt .txt files"
    )
    parser.add_argument(
        "--generate-script", action="store_true",
        help="Also generate a run.sh script for thumbnail generation"
    )
    parser.add_argument(
        "--cells-dir", default="",
        help="Cells directory for run.sh (only used with --generate-script)"
    )
    parser.add_argument(
        "--thumbnails-dir", default="",
        help="Thumbnails output dir for run.sh (only used with --generate-script)"
    )
    parser.add_argument(
        "--title", default="",
        help="Video title for run.sh (only used with --generate-script)"
    )

    args = parser.parse_args()

    # Load style brief
    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"ERROR: Style brief not found: {brief_path}", file=sys.stderr)
        sys.exit(1)

    with open(brief_path) as f:
        brief = json.load(f)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build prompts
    variations = brief.get("variations", [])
    if len(variations) != 5:
        print(f"WARNING: Expected 5 variations, got {len(variations)}", file=sys.stderr)

    suffixes = ["a", "b", "c"]
    total = 0

    for v_idx, variation in enumerate(variations):
        v_num = v_idx + 1
        scenes = variation.get("scenes", [])

        # Shared fields across scenes in this variation
        shared = {
            "hero_text": variation.get("hero_text", ""),
            "hero_style": variation.get("hero_style", ""),
            "context_text": variation.get("context_text", ""),
            "context_style": variation.get("context_style", ""),
            "accent_text": variation.get("accent_text", ""),
            "accent_style": variation.get("accent_style", ""),
            "emotion": variation.get("emotion", "excited"),
            "wardrobe": variation.get("wardrobe", ""),
        }

        for s_idx, scene in enumerate(scenes):
            if s_idx >= len(suffixes):
                break
            suffix = suffixes[s_idx]

            # Merge shared fields with scene-specific fields
            # Scene-specific fields override shared fields
            merged = {**shared, **scene}

            prompt = build_prompt(merged)
            filename = f"v{v_num}{suffix}.txt"
            filepath = output_dir / filename

            with open(filepath, "w") as f:
                f.write(prompt)

            total += 1
            print(f"  Written: {filename}")

    print(f"\n{'=' * 50}")
    print(f"Generated {total} prompt files in: {output_dir}")
    print(f"{'=' * 50}")

    # Optionally generate run script
    if args.generate_script:
        script = build_run_script(
            brief,
            args.thumbnails_dir or str(output_dir),
            args.cells_dir,
            args.title,
        )
        script_path = output_dir / "run.sh"
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        print(f"Generated run script: {script_path}")


if __name__ == "__main__":
    main()

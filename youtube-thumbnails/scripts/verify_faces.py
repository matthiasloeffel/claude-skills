#!/usr/bin/env python3
"""
Face Verification for YouTube Thumbnails.
Compares generated thumbnails against a headshot reference using Gemini Vision.
Returns a confidence score (1-10) for each thumbnail.

Usage:
  python3 verify_faces.py --headshot path/to/headshot.png --thumbnails path/to/thumbnails/
  python3 verify_faces.py --headshot path/to/headshot.png --thumbnails path/to/thumbnails/ --auto-delete
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed. Run: pip3 install google-genai", file=sys.stderr)
    sys.exit(1)


VERIFICATION_PROMPT = """You are a strict face verification expert specializing in detecting AI-generated face drift. The THUMBNAIL (first image) is AI-generated and the HEADSHOT REFERENCE (second image) is a real photo. Your job is to determine if the AI preserved the SAME person's identity or drifted to a different face.

CRITICAL CONTEXT: AI image generators frequently produce attractive, plausible faces that look like a DIFFERENT person than the reference. This is called "face drift" and is the #1 failure mode. Your job is to CATCH these cases, not excuse them. Be suspicious by default — assume drift until proven otherwise.

STEP-BY-STEP EVALUATION — assess each feature independently:

1. FACE SHAPE & PROPORTIONS: Compare the overall face shape (round, oval, square, rectangular, heart). Compare face width-to-height ratio. Compare forehead width and height. Are these the same or different?

2. NOSE: Compare nose bridge width, nose length, tip shape (pointed, bulbous, upturned), nostril size and shape. The nose is the hardest feature for AI to preserve — scrutinize it carefully.

3. EYES: Compare eye shape (round, almond, hooded), eye SIZE relative to face, eye SPACING (close-set vs wide-set), eyelid crease depth, iris color. Ignore expression-related changes (wide vs squinting).

4. JAWLINE & CHIN: Compare jawline angle (sharp vs soft), chin shape (pointed, square, rounded), chin prominence. Is the jaw the same width?

5. MOUTH & LIPS: Compare lip fullness (thin, medium, full), cupid's bow shape, mouth width relative to face. Ignore smile vs neutral expression.

6. SKIN & COMPLEXION: Compare skin tone (light, medium, dark), undertone (warm, cool, neutral), visible texture or features (freckles, moles, skin type). AI often lightens or smooths skin — flag if the skin tone shifted noticeably.

7. HAIR: Compare hair color, hairline position, hair texture (straight, wavy, curly), hair density. Minor styling differences are OK.

8. APPARENT AGE & BUILD: Compare apparent age range and face maturity. AI often makes people look younger or more conventionally attractive — if the thumbnail person looks 10+ years younger, that's face drift.

IMPORTANT — DISTINGUISH between "AI idealization" and "different person":

NORMAL AI EFFECTS (do NOT count against the score):
- Smoother, more even skin texture
- Slightly thinner nose bridge or slightly more refined nose tip
- Slightly sharper or more defined jawline
- Slightly more symmetrical features
- Brighter, more vivid eyes
- Minor skin lightening or evening of skin tone
- Looking 5-8 years younger
These are ALL standard AI generation artifacts. They happen to EVERY face. They do NOT indicate a different person.

TRUE FACE DRIFT (DO count against the score):
- Completely different face width-to-height ratio (e.g., round face → long narrow face)
- Entirely different nose TYPE (e.g., broad flat nose → narrow pointed nose, or upturned → downturned)
- Different eye spacing (close-set → wide-set or vice versa)
- Different apparent ethnicity or skin undertone
- Looking 15+ years younger (adult → teenager)
- A generic "AI model" face with no distinguishing features from the reference
- The face could belong to dozens of different people — no unique identifying features preserved

STEP 9 — HOLISTIC JUDGMENT (most important step):
After analyzing individual features, step back and ask: "If I showed both images to a friend of this person, would they say 'yes, that's them' about the thumbnail?"
- If YES → score 7-10, regardless of how many individual features show minor AI changes
- If UNCERTAIN → score 4-6
- If NO, they'd say "who is that?" → score 1-3

SCORING:
- 1-3: DIFFERENT PERSON. A friend would NOT recognize this as the same person. The face has fundamentally different proportions or structure, not just AI smoothing. Auto-delete.
- 4-6: UNCERTAIN. A friend might hesitate. Some features match but the overall impression is ambiguous.
- 7-8: SAME PERSON, AI-STYLED. A friend would immediately recognize them. AI has smoothed and idealized, but the person is clearly identifiable. Normal AI effects are present but the fundamental face structure is preserved.
- 9-10: EXCELLENT MATCH. Very faithful, minimal AI drift.

KEY RULE: Matching hair color/style alone is NOT sufficient for a high score. The FACE STRUCTURE must match independently of hair.

KEY RULE: Count ONLY true face drift features against the score, NOT normal AI effects. If you find yourself marking features as "mismatch" purely because of smoothing or slight refinement, reconsider — those are normal AI artifacts, not identity changes.

Respond with ONLY a JSON object, no other text:
{"score": <number 1-10>, "features": {"face_shape": "<match/mismatch/uncertain>", "nose": "<match/mismatch/uncertain>", "eyes": "<match/mismatch/uncertain>", "jaw": "<match/mismatch/uncertain>", "skin_tone": "<match/mismatch/uncertain>"}, "reason": "<brief explanation focusing on what matches or doesn't>"}"""


def load_image(path: str) -> tuple:
    """Load image and return (bytes, mime_type)."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        sys.exit(1)

    ext = Path(path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(path, "rb") as f:
        image_bytes = f.read()

    return image_bytes, mime_type


def _parse_gemini_response(response) -> dict:
    """Parse Gemini response into a dict with score and reason."""
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text = part.text.strip()
                # Extract JSON from response (handle markdown code blocks)
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Try to find JSON in the response
                    import re
                    match = re.search(r'\{[^}]+\}', text)
                    if match:
                        try:
                            return json.loads(match.group())
                        except json.JSONDecodeError:
                            pass
                    return {"score": 5, "reason": f"Could not parse response: {text[:200]}"}
    return {"score": 5, "reason": "No response from model"}


def _single_verify(client, thumbnail_bytes: bytes, thumbnail_mime: str,
                   headshot_bytes: bytes, headshot_mime: str) -> dict:
    """Run a single verification call."""
    contents = [
        types.Part.from_bytes(data=thumbnail_bytes, mime_type=thumbnail_mime),
        types.Part.from_bytes(data=headshot_bytes, mime_type=headshot_mime),
        types.Part.from_text(text=VERIFICATION_PROMPT),
    ]

    config = types.GenerateContentConfig(
        response_modalities=["TEXT"],
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
    except Exception as e:
        return {"score": 5, "reason": f"API error: {e}"}

    return _parse_gemini_response(response)


def verify_face(client, thumbnail_bytes: bytes, thumbnail_mime: str,
                headshot_bytes: bytes, headshot_mime: str,
                threshold: int = 3) -> dict:
    """Verify if thumbnail face matches headshot with double-check for low scores.

    Runs verification once. If the score is at or below the fail threshold,
    runs a second check to confirm. Uses the HIGHER of the two scores to
    reduce false positives from Gemini's inconsistency.

    Returns {"score": int, "reason": str, "features": dict, "double_checked": bool}.
    """
    result1 = _single_verify(client, thumbnail_bytes, thumbnail_mime,
                             headshot_bytes, headshot_mime)
    score1 = result1.get("score", 5)

    # If first score is above threshold, no need for double-check
    if score1 > threshold:
        result1["double_checked"] = False
        return result1

    # Score is at or below threshold — run second verification to confirm
    result2 = _single_verify(client, thumbnail_bytes, thumbnail_mime,
                             headshot_bytes, headshot_mime)
    score2 = result2.get("score", 5)

    # Use the HIGHER score (benefit of the doubt — reduce false positives)
    if score2 >= score1:
        result2["double_checked"] = True
        result2["score_run1"] = score1
        result2["score_run2"] = score2
        return result2
    else:
        result1["double_checked"] = True
        result1["score_run1"] = score1
        result1["score_run2"] = score2
        return result1


def main():
    parser = argparse.ArgumentParser(description="Verify face identity in generated thumbnails")
    parser.add_argument("--headshot", required=True, help="Path to headshot reference image")
    parser.add_argument("--thumbnails", required=True, help="Path to thumbnails directory")
    parser.add_argument("--auto-delete", action="store_true",
                        help="Automatically delete thumbnails with score <= 3")
    parser.add_argument("--threshold", type=int, default=3,
                        help="Score threshold for auto-delete (default: 3, meaning <= 3 gets deleted)")

    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Load headshot
    print(f"Loading headshot reference: {args.headshot}")
    headshot_bytes, headshot_mime = load_image(args.headshot)

    # Find all thumbnails
    thumb_dir = os.path.expanduser(args.thumbnails)
    if not os.path.isdir(thumb_dir):
        print(f"ERROR: Thumbnails directory not found: {thumb_dir}", file=sys.stderr)
        sys.exit(1)

    thumbnails = sorted([
        f for f in os.listdir(thumb_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ])

    if not thumbnails:
        print("No thumbnails found in directory.")
        sys.exit(0)

    print(f"Verifying {len(thumbnails)} thumbnails in parallel...\n")

    # Verify all thumbnails in parallel
    results = {"pass": [], "warn": [], "fail": []}
    output_lines = {}  # thumb_name -> formatted output line

    def _verify_one(thumb_name):
        thumb_path = os.path.join(thumb_dir, thumb_name)
        thumb_bytes, thumb_mime = load_image(thumb_path)
        return thumb_name, verify_face(client, thumb_bytes, thumb_mime, headshot_bytes, headshot_mime,
                                       threshold=args.threshold)

    with ThreadPoolExecutor(max_workers=min(len(thumbnails), 5)) as executor:
        futures = {executor.submit(_verify_one, name): name for name in thumbnails}
        for future in as_completed(futures):
            thumb_name, result = future.result()
            score = result.get("score", 5)
            reason = result.get("reason", "unknown")

            if score <= args.threshold:
                status = "FAIL"
                results["fail"].append((thumb_name, score, reason))
            elif score <= 6:
                status = "WARN"
                results["warn"].append((thumb_name, score, reason))
            else:
                status = "PASS"
                results["pass"].append((thumb_name, score, reason))

            icon = {"FAIL": "X", "WARN": "?", "PASS": "OK"}[status]
            features = result.get("features", {})
            feature_str = ""
            if features:
                feature_parts = []
                for feat, val in features.items():
                    symbol = {"match": "+", "mismatch": "X", "uncertain": "?"}.get(val, "?")
                    feature_parts.append(f"{feat}:{symbol}")
                feature_str = f" [{', '.join(feature_parts)}]"
            dc_str = ""
            if result.get("double_checked"):
                dc_str = f" (double-checked: run1={result.get('score_run1')}, run2={result.get('score_run2')})"
            output_lines[thumb_name] = f"  [{icon}] {thumb_name}: {score}/10{feature_str}{dc_str} — {reason}"

    # Print results in sorted order for readability
    for name in sorted(output_lines):
        print(output_lines[name])

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(results['pass'])} passed, {len(results['warn'])} warnings, {len(results['fail'])} failed")
    print(f"{'='*60}")

    if results["fail"]:
        print(f"\nFAILED (score <= {args.threshold}) — wrong person detected:")
        for name, score, reason in results["fail"]:
            print(f"  - {name} ({score}/10): {reason}")

        if args.auto_delete:
            print(f"\nAuto-deleting {len(results['fail'])} failed thumbnail(s)...")
            deleted = []
            for name, score, reason in results["fail"]:
                path = os.path.join(thumb_dir, name)
                os.remove(path)
                deleted.append(name)
                print(f"  Deleted: {name}")
            # Output deleted filenames for the caller to regenerate
            print(f"\nDELETED_FILES={','.join(deleted)}")
        else:
            print("\nRun with --auto-delete to remove failed thumbnails automatically.")

    if results["warn"]:
        print(f"\nWARNINGS (score 4-6) — uncertain match, review manually:")
        for name, score, reason in results["warn"]:
            print(f"  - {name} ({score}/10): {reason}")

    # Exit code: 0 if no failures, 1 if there are failures
    return 1 if results["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())

name: youtube-thumbnail
description: Generate professional, high-CTR YouTube thumbnails from a video title and headshot using Nano Banana Pro (Gemini). Creates 5 variations with 3 thumbnails each (15 total) with text effects, face compositing, and proven design psychology. Use when user wants to create YouTube thumbnails, generate thumbnails, or mentions thumbnail creation.
---

# YouTube Thumbnail Generator

Generate professional YouTube thumbnails that force viewers to click. Uses Nano Banana Pro (Gemini 3 Pro Image) with Identity Locking to composite the user's face into scroll-stopping thumbnail designs.

## When to Use

- User asks to create/generate a YouTube thumbnail
- User mentions "thumbnail" + a video title or topic
- User wants to create visual content for YouTube

## Required Inputs

1. **Video title or keyword** — The topic of the video (e.g., "How ChatGPT is replacing marketing agencies")
2. **Headshot path** — Path to a reference photo of the person to feature in the thumbnail

## Headshot Grid Workflow (works with ANY person)

For best face accuracy, use a **3x3 headshot grid** that gets automatically cropped and labeled. This works with any person — no manual cell labeling needed.

### Step 0: Prepare the Grid (one-time setup per person)

1. The user provides a 3x3 headshot grid image (any person, any layout)
2. Run `analyze_grid.py` to auto-crop and auto-label all 9 cells:

```bash
SKILL_ROOT="$HOME/.claude/skills/youtube-thumbnails"
python3 "${SKILL_ROOT}/scripts/analyze_grid.py" --grid "Headshots/person-grid.png"
```

This produces:
- 9 cropped cell images in `Headshots/person-grid-cells/` (cell_01.png through cell_09.png)
- A `cells.json` with auto-detected angle and expression per cell:
```json
{
  "grid_source": "person-grid.png",
  "cells": {
    "cell_01.png": {"angle": "profile_right", "expression": "neutral", "row": 0, "col": 0},
    "cell_02.png": {"angle": "frontal", "expression": "smile_teeth", "row": 0, "col": 1},
    ...
  }
}
```

### Using cells in thumbnail generation

The `generate_thumbnail.py` script auto-selects the right cells via `--cells-dir`:

```bash
python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
  --cells-dir "Headshots/person-grid-cells/" \
  --emotion "excited" \
  --prompt "..." --output "..." --variation 1 --suffix a
```

The script reads `cells.json` and automatically:
- Picks the cell whose expression best matches `--emotion` as the **headshot** (identity anchor)
- Picks the **frontal neutral** cell as the **reference** (identity baseline)

### Key rules
- **Never pass the full grid as a single image** — the model treats it as a moodboard and generates random faces
- **NEVER pass style reference thumbnails that contain other people's faces** — this causes face blending/drift
- Only pass face reference cells from the SAME person — max 2 images total (headshot + frontal neutral reference)
- Style is controlled entirely through the prompt text, NOT through reference images
- The `--cells-dir` + `--emotion` system handles cell selection automatically — no manual mapping needed

## Always Include

- **Competitor research** — Always run Step -1 (topic research), Step 0 (YouTube competitor search), and Step 0.5 (Style Brief) before generating. The Style Brief shapes every prompt.
- **NO style reference images with faces** — Style guidance goes in the prompt text only. Reference images are ONLY for face identity (same person's cells).

## Optional Overrides

- `--emotion` — shocked, excited, serious, curious, confident, skeptical (default: auto from title)
- `--text` — Custom text overlay, 1-3 words (default: auto-generated curiosity gap from title)
- `--colors` — dark, bright, neon, warm, cool (default: auto from title mood)
- `--style` — described in Style Brief's Visual World (default: auto-derived from topic research)
- `--output` — Output directory (default: ./thumbnails/)

## Process

### Step -1: Understand the Topic (MANDATORY FIRST STEP)

Before any competitor research or design work, you MUST understand what the video is actually about. The title alone is not enough.

**Research the topic itself using Firecrawl:**
```
firecrawl_search: "[TOPIC/TOOL NAME] what is it features launch"
firecrawl_search: "[TOPIC] explained demo use case"
```

**Answer these questions before proceeding:**
- What is this product/concept exactly?
- What is the KEY benefit or shocking fact? (e.g., "$15M campaign done in 40 hours for $20K")
- What does it replace or disrupt?
- Who uses it and for what?
- What would a viewer PICTURE if they heard this title?

**Logo Research (MANDATORY when the topic involves ANY tools, platforms, or services):**

The image generation model does NOT reliably know what specific logos look like. If you just write "Claude logo" in the prompt, it will generate a generic AI logo (often resembling ChatGPT). You MUST research every relevant logo and describe it by its VISUAL GEOMETRY — shapes, colors, proportions — not by name.

```
firecrawl_search: "[TOOL NAME] logo design description"
firecrawl_search: "[TOOL NAME] brand logo what does it look like"
```

For EACH tool/platform mentioned in or relevant to the video title, document:
- **Shape**: The geometric form (e.g., "a stylized starburst with curved radiating rays", "a hexagonal flower with 6 petals", "an envelope shape formed by a multicolor M")
- **Colors**: Exact brand colors with hex codes (e.g., "#D97757 terracotta orange", "#10A37F teal-green")
- **Proportions**: Key distinguishing features (e.g., "rays are thick at center and taper outward", "the M spans the full width of the envelope")
- **What it is NOT**: Explicitly note which OTHER logos it must not be confused with (e.g., "Claude logo is NOT a chat bubble, NOT a hexagon, NOT teal/green — those are ChatGPT")

**This applies broadly — not just to the primary tool:**
- If the title mentions "E-Mail mit KI automatisieren" → research Gmail logo, Outlook logo, and whichever AI tool logos are relevant
- If the title mentions "Claude Cowork" → research Claude logo AND Anthropic logo
- If the title mentions a comparison → research ALL compared tools' logos
- If the topic involves a workflow with multiple tools → research every tool in the chain (e.g., n8n, Zapier, Make, Gmail, Slack)

Store these descriptions — they feed directly into the Style Brief's Logo Descriptions section and into every prompt that includes a logo.

**Why this matters for thumbnails:**
- Wrong topic understanding → wrong visuals (e.g., showing automation workflow diagrams for a creative AI tool)
- Wrong logos → instant credibility loss (viewers notice when you show ChatGPT's logo on a Claude video)
- The shocking fact or core capability should inform the thumbnail concept directly
- Visuals must represent what the video ACTUALLY covers, not a vague interpretation of the title

**⚡ LAUNCH IN PARALLEL — do not wait for Step -1 to finish before starting Step 0.** Both phases are fully independent. Start all Firecrawl queries (topic + logos) AND all 4 Subscribr queries simultaneously in a single message. This cuts total research time in half.

### Step 0: Research Competitors on YouTube

Before generating anything, research what's already out there for this topic.

**Use Subscribr Intel MCP tools** (NOT Firecrawl `site:youtube.com` — those lack metrics).

**Always search BOTH German AND English in parallel** — run all 4 queries simultaneously:

```
# 1. German videos — exact topic keywords
intel_search_videos(
  query="[THEMA AUF DEUTSCH]",
  min_outlier_score=2.0,
  limit=20
)

# 2. English videos — same topic in English
intel_search_videos(
  query="[TOPIC IN ENGLISH]",
  min_outlier_score=2.0,
  limit=20
)

# 3. German competitor channels in this niche
intel_search_channels(
  query="[THEMA/NISCHE AUF DEUTSCH]",
  limit=10
)

# 4. English competitor channels
intel_search_channels(
  query="[TOPIC/NICHE IN ENGLISH]",
  limit=10
)
```

**Why both languages matter:**
- German results → what the direct competition does → saturated patterns to AVOID
- English results → what the biggest global creators do → proven concepts at scale
- English outliers often reveal thumbnail angles not yet done in German → competitive advantage

**Run all 4 queries in parallel** — they are fully independent.

**For each top result, collect:**
- Video title (exact wording, hook structure, angle)
- `outlier_score` — higher = stronger overperformer, most important for design inspiration
- `format` + `angle` + `goals` — auto-parsed by Subscribr (e.g., "Tutorial / Hands-on / Inform")
- `thumbnail_url` — collect ALL thumbnail URLs from top results (needed for visual analysis below)
- Views, likes — absolute scale of the channel/topic

**Step 0.1: Download + Visually Analyze Competitor Thumbnails (MANDATORY)**

After the 4 Subscribr queries, collect the top 10-15 `thumbnail_url` values (prioritize highest `outlier_score`) and download them locally so you can SEE what they actually look like:

```bash
SKILL_ROOT="$HOME/.claude/skills/youtube-thumbnails"
THUMB_DIR="/tmp/competitor_thumbs_$(date +%s)"
mkdir -p "${THUMB_DIR}"

# Build a tab-separated urls file: url<TAB>title (one per line)
# Replace the lines below with actual URLs + titles from Subscribr results:
cat > /tmp/competitor_urls.txt << 'EOF'
https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg	Video Title Here
https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg	Another Video Title
EOF

python3 "${SKILL_ROOT}/scripts/fetch_competitor_thumbnails.py" \
  --urls-file /tmp/competitor_urls.txt \
  --output "${THUMB_DIR}"
```

After downloading, **use the Read tool to visually analyze each thumbnail**:

```
# Read and analyze each downloaded image file, e.g.:
Read: /tmp/competitor_thumbs_XXX/01_video-title.jpg
Read: /tmp/competitor_thumbs_XXX/02_another-title.jpg
...
```

**For each thumbnail you analyze visually, note:**
- **Dominant colors** — background color, text color, accent color (exact shades)
- **Text on thumbnail** — exact words, size hierarchy, font weight (bold/thin), language
- **Person presence** — is there a person? If yes: expression, position (left/right/center), framing (tight/medium/wide), pose/gesture
- **Props** — what objects appear? Are they held, floating, or in the background?
- **Composition** — where is text vs. person vs. props? Is it busy or minimal?
- **Style** — photorealistic? Illustrated? Flat/graphic? Cinematic? Studio?
- **What stands out** — what made you notice this thumbnail vs. skipping it?

**Then identify patterns across ALL analyzed thumbnails:**

**Identify patterns (what competitors ALL do):**
- Common color schemes → avoid these (you've now SEEN them, not just inferred them)
- Common text patterns — exact words, position, style that repeats
- Common expressions (everyone shocked? everyone pointing?)
- Common compositions — person always on right? text always upper-left?
- Common prop types — phone, laptop, money, charts?

**Identify the gap (what NONE of them do):**
- A color combination not seen in ANY downloaded thumbnail
- A text treatment (3D, neon, editorial, handwritten) no competitor uses
- A pose/gesture that doesn't appear in any thumbnail
- A composition angle (person in center, text at bottom, no props) that's unused
- A style direction (film-noir, warm editorial, outdoor) not present in the set

**Output a brief differentiation strategy:**
```
VISUAL COMPETITOR ANALYSIS (from actual thumbnail inspection):
- [List 5-8 competitor thumbnails with: title, outlier_score, dominant colors, text style, person pose, overall impression]

PATTERNS — WHAT EVERY COMPETITOR DOES (seen visually):
- Colors: [exact colors that saturate this niche]
- Text: [patterns — position, style, words]
- Composition: [person placement, layout patterns]
- Expressions: [dominant expressions across the set]
- Props: [what objects appear repeatedly]

YOUR VISUAL DIFFERENTIATOR:
- Color: [specific color not seen in any downloaded thumbnail — justified by topic color DNA]
- Text treatment: [style not used by any competitor]
- Composition: [layout angle not present in the set]
- Expression/pose: [what no competitor showed]
- One unique element: [visual idea visible only in your thumbnails]
```

Use this visual differentiation strategy to inform the Style Brief. The competitor thumbnails you have SEEN are now the baseline — your thumbnails must look unmistakably different at a glance.

### Research-Zusammenfassung (MANDATORY — direkt im Chat ausgeben, NICHT als Datei)

Nach Step -1 und Step 0 IMMER diese Zusammenfassung im Chat ausgeben — bevor der Style Brief geschrieben wird. Sie ist der Kontrollpunkt zwischen Research und Designentscheidungen.

**Format: maximal 1 Bildschirmseite, scanbar strukturiert, jedes Finding endet mit explizitem "→ deshalb"-Impact.**

```
## 🔍 Research-Zusammenfassung: [VIDEO TITEL]

### Topic Essence
[2-3 Sätze: Was das Video wirklich ist — nicht der Titel, das Ding dahinter.
Was ist der shocking fact / die Kernaussage?
Was würde ein Viewer VISUALISIEREN wenn er den Titel hört?]

### Logo Matrix
| Tool | Geometrie | Farben | NICHT verwechseln mit |
|------|-----------|--------|----------------------|
| [Tool] | [Geometrie] | [Hex] | [Anderes Tool] |
⚠️ Kein Logo für [X] gefunden → wird weggelassen. Ein falsches Logo ist schlimmer als keins.

### Top 5 Competitor Thumbnails
1. **[Titel]** — Outlier: [Score] | [Kanal]
   ✓ Was funktioniert: [1 Satz]
   ✗ Was saturiert ist: [1 Satz]
   🖼️ [Thumbnail URL]

2. **[Titel]** — Outlier: [Score] | [Kanal]
   ✓ [was funktioniert]  ✗ [was saturiert]  🖼️ [URL]

[... bis 5 Stück]

### 3 Overused Patterns (zu vermeiden)
- **[Farbe/Element]**: [Konkret — z.B. "6 von 8 deutschen Videos: shocked face + gelber Text auf dunkelblauem BG"]
- **[Text-Pattern]**: [Konkret]
- **[Kompositions-Pattern]**: [Konkret]

### Unsere Differenzierung
- **Farbe**: [Was wir stattdessen nutzen] → weil [Begründung aus Research]
- **Text-Energie**: [Welcher Angle noch nicht besetzt ist] → weil [niemand dieses Konzept gezeigt hat]
- **Visual**: [Was kein Competitor zeigte] → direkt abgeleitet aus [Finding]

### Topic Color DNA
| Farbe | Hex | Herkunft | Warum sie hierher gehört |
|-------|-----|----------|--------------------------|
| [Name] | [#HEX] | Brand / Environment / Emotional / Gap | [Begründung] |
[4-6 Farben]

### 5 Text-Kompositions-Ideen (Rohentwurf)
V1: Hero "[HERO]" + Context "[CONTEXT]" — Angle: [1 Wort]
V2: Hero "[HERO]" + Context "[CONTEXT]" — Angle: [1 Wort]
V3: Hero "[HERO]" + Context "[CONTEXT]" — Angle: [1 Wort]
V4: Hero "[HERO]" + Context "[CONTEXT]" — Angle: [1 Wort]
V5: Hero "[HERO]" + Context "[CONTEXT]" — Angle: [1 Wort]

→ Weiter mit Style Brief? Oder Anpassungen?
```

**Regeln:**
- Thumbnail-URLs als anklickbare Links ausgeben (nicht nur Text)
- Jede Zeile in der Logo Matrix muss eine "NICHT verwechseln mit"-Warnung haben
- Wenn ein Logo nicht recherchiert werden konnte → explizit warnen und weglassen ankündigen
- Die 5 Text-Ideen sind Rohentwürfe — sie werden im Style Brief ausgearbeitet, aber der User sieht die Richtung schon hier
- Erst nach dieser Zusammenfassung → Style Brief schreiben

### Step 0.5: Create the Style Brief (MANDATORY — the single most important step)

Before writing ANY prompts, you MUST produce a **Style Brief** — a structured document that derives ALL visual decisions exclusively from your topic research and competitor analysis. This brief becomes the SOLE source for every design choice in every variation. No design decision may come from a reference table, a template, or a preset — only from this brief.

**Why this step exists:** Without it, the LLM defaults to recycled patterns (crown for "best", teal for "tech", neon text for "AI") regardless of the topic. The Style Brief forces every choice to be justified by THIS specific topic's visual world.

**The Style Brief has 11 sections. Complete ALL of them before proceeding.**

#### 1. VISUAL WORLD

Describe the specific visual universe this topic lives in. Not a generic category ("tech", "business") but the ACTUAL environment a viewer would picture.

Ask yourself:
- "If I walked into the ROOM where this topic happens, what would I see?"
- "What does the SCREEN look like when someone uses this tool/does this thing?"
- "What TIME OF DAY, what LOCATION, what ATMOSPHERE does this topic evoke?"

Write 2-3 sentences describing this visual world. Be hyper-specific.

**BAD:** "A tech workspace with screens" (generic, works for any tech video)
**GOOD:** "The Claude desktop app open on a MacBook in a home office — the Cowork tab is active, showing a running task with a progress indicator. The screen glows softly in a dimly lit room at 11pm because the user set up automation and is about to go to bed."

#### 2. TOPIC COLOR DNA

Every topic has colors that BELONG to it — colors a viewer instinctively associates with the subject. Extract these. Do NOT pick colors for "variety" or "contrast" — pick colors because they ARE this topic.

Sources for color DNA:
- **Brand colors** of the tool/platform (e.g., Claude = terracotta/orange, ChatGPT = teal-green, Notion = black/white)
- **Environment colors** from the Visual World (e.g., a nighttime automation setup = deep blues, screen glow, notification amber)
- **Emotional colors** from the title's energy (e.g., "besser als 99%" = competitive red/gold vs. "Anfänger Guide" = approachable warm white)
- **Competitor gaps** — what colors did competitors NOT use? Those are your opportunities.

Output a **Topic Color Palette** of 4-6 colors with hex codes and justification:
```
TOPIC COLOR DNA:
- [#HEX] [Color name] — [WHY this color belongs to this topic]
- [#HEX] [Color name] — [WHY]
- [#HEX] [Color name] — [WHY]
- [#HEX] [Color name] — [WHY]
```

Each variation will draw from this palette (not all colors in every variation, but all variations draw from the SAME topic-derived palette). This ensures visual coherence while preventing generic "variety for variety's sake" color rotation.

#### 3. LOGO DESCRIPTIONS (MANDATORY when tools/platforms are involved)

If the video topic involves ANY tools, platforms, or services, their logos must be described here by VISUAL GEOMETRY — never by name alone. The image generation model does not reliably know what specific logos look like. Describing a logo by name (e.g., "Claude logo") produces wrong results (e.g., a ChatGPT-like hexagon).

**Use the logo research from Step -1.** For each relevant logo, write a rendering description that the image model can follow:

```
LOGO DESCRIPTIONS:
- [TOOL NAME]: [GEOMETRIC DESCRIPTION] in [EXACT COLORS with hex codes]. [KEY DISTINGUISHING FEATURES]. NOT [what it must NOT be confused with].
- [TOOL NAME]: [GEOMETRIC DESCRIPTION] in [EXACT COLORS with hex codes]. [KEY DISTINGUISHING FEATURES]. NOT [what it must NOT be confused with].
```

**Examples of good logo descriptions:**
- **Claude (Anthropic)**: A stylized starburst/sunburst symbol with ~12 curved radiating rays forming a circular shape, in warm terracotta orange (#D97757). The rays are organic and slightly tapered. NOT a chat bubble, NOT a hexagon, NOT teal/green (those are ChatGPT).
- **ChatGPT (OpenAI)**: A hexagonal flower shape made of 6 interlocking curved segments forming a spiral-like pattern, in teal-green (#10A37F). NOT a starburst, NOT orange (that's Claude).
- **Gmail (Google)**: A white envelope shape with a multicolored "M" formed by red (#EA4335), blue (#4285F4), yellow (#FBBC05), and green (#34A853) diagonal folds. The M spans the full envelope width.
- **n8n**: The text "n8n" in a clean bold sans-serif font, with a coral/salmon (#FF6D5A) color and a distinctive node-connection visual style.
- **Notion**: A bold black "N" with a slight serif, on a white background. Minimal, typographic, monochrome.

**Rules:**
- Every logo in the prompt MUST use its geometric description from this section, NOT just the tool name
- If you cannot find reliable visual information about a logo → do NOT include it. A missing logo is better than a wrong logo.
- When multiple tools are relevant (e.g., "E-Mail automatisieren mit KI" → Gmail, Claude, n8n), describe ALL of them
- The logo descriptions feed directly into the SECONDARY ELEMENT field in the prompt template

#### 4. TOPIC PROPS — 7-10 UNIQUE OBJECTS

Brainstorm 7-10 physical objects, props, and visual elements that are UNIQUE to this specific topic. These become the pool from which each variation's props are selected.

**The generation process:**
1. List every PHYSICAL OBJECT directly involved in this topic (the tool's UI, the device, the output)
2. List every METAPHOR that's specific to this title's hook (not generic metaphors — metaphors that only work for THIS title)
3. List every VISUAL SYMBOL a viewer would recognize as "oh, this is about [TOPIC]"

**The uniqueness test:** Could this prop appear in a thumbnail for a DIFFERENT video topic? If yes → too generic, remove it. If no → keep it.

**BANNED generic props** (these appear in every job and must never be used unless they are LITERALLY the topic):
- Crown, trophy, medal (unless the video is literally about winning an award)
- Magnifying glass (unless the video is literally about research/investigation)
- Lightbulb (unless the video is literally about ideas/invention)
- Rocket (unless the video is literally about launches/startups)
- Shield (unless the video is literally about security)
- Generic smartphone showing nothing specific
- Generic laptop showing nothing specific
- Stack of money (unless the video is literally about income/finance)

**GOOD props are hyper-specific:**
- For "Claude Cowork besser nutzen": the Cowork tab interface showing completed tasks, a to-do list with AI-generated checkmarks, a before/after file organization split, a "99%" statistic overlay, the Claude desktop app with multiple tabs
- For "Google Maps Platz 1": a Google Maps business listing card, a 5-star review popup, a map pin with "#1" on it, a phone showing the Maps search results, a "Platz 1" ranking badge

#### 5. BACKGROUND SCENES — 5 LOCATIONS × 3 SUB-SCENES (MANDATORY)

Every thumbnail must be set in a **recognizable real-world location** that tells part of the video's story. The background is NOT decoration — it's narrative context. A viewer should be able to guess the video topic from the background alone.

**The default is ALWAYS a real location.** Abstract gradients, solid colors, and "studio void" backgrounds are the RARE EXCEPTION — only allowed when the topic is purely conceptual with no physical setting (e.g., "What is consciousness?"). For 95% of videos, there is a real place where the topic happens. Use it.

**Brainstorm 5 distinct locations**, one per variation. Each location must:
1. Be MOTIVATED BY THE TOPIC — ask: "Where does this scene physically take place?"
2. Be visually distinct from the other 4 (different room, different time of day, indoor vs outdoor)
3. Be specific enough to recognize at thumbnail size (blurred but identifiable)
4. Add meaning to the thumbnail (the location says something about the video's message)

**Then for each location, create 3 SUB-SCENE VARIANTS (a/b/c).** The 3 runs within a variation should NOT use the same prompt — each gets a different sub-scene that keeps the same text and concept angle but varies the background and pose. This gives genuine variety within each variation instead of near-duplicate outputs.

Sub-scene variants can differ by:
- **Time of day** (morning light vs evening vs nighttime)
- **Specific room/area** (living room vs bedroom vs kitchen — all "home" but different)
- **Camera angle/framing** (wider establishing shot vs tight close-up vs medium)
- **Environmental details** (what's visible in the background — different objects, different screen content)

**BANNED backgrounds** (these are lazy defaults that add no storytelling):
- Plain black, white, or single-color backgrounds
- Generic "tech" gradient (dark blue to purple)
- Abstract mesh gradients with no scene context
- "Studio void" with just lighting and no environment
- The same 5 recycled locations for every video (home office, café, outdoor golden hour, clean studio, tech workspace) — UNLESS the topic actually takes place there

**GOOD backgrounds are topic-specific:**
- For "3 AI Agents arbeiten für mich": bedroom at night (agents work while you sleep), cozy couch with laptop (passive income vibe), empty office with screens running (business runs itself)
- For "Google Maps Platz 1": German shopping street / Fußgängerzone, inside a local business storefront, Google Maps search results visible on a large monitor in a small office
- For "Claude Cowork besser nutzen": dimly lit home office at 11pm with screen glow, modern coworking space with glass walls, living room couch with laptop and coffee

```
BACKGROUND SCENES (5 locations × 3 sub-scenes each):
V1 location: [SPECIFIC PLACE] — [WHY this location fits this variation's concept]
  a: [sub-scene detail — time of day, specific area, camera angle]
  b: [different sub-scene — different time/area/angle]
  c: [third sub-scene variant]
V2 location: [DIFFERENT PLACE] — [WHY]
  a: [sub-scene] b: [sub-scene] c: [sub-scene]
V3 location: [DIFFERENT PLACE] — [WHY]
  a: [sub-scene] b: [sub-scene] c: [sub-scene]
V4 location: [DIFFERENT PLACE] — [WHY]
  a: [sub-scene] b: [sub-scene] c: [sub-scene]
V5 location: [DIFFERENT PLACE] — [WHY]
  a: [sub-scene] b: [sub-scene] c: [sub-scene]
```

#### 6. POSES & GESTURES — 5 TITLE-DRIVEN POSES × 3 VARIANTS (MANDATORY)

The person's body language must TELL THE STORY of the video title. Expression (face muscles) is handled separately in Section 7 — this section is about what the **body is doing**: posture, hand position, gesture, physical interaction with the scene.

**The key test:** "If I muted the text and blurred the props, would the person's body language alone hint at the video's topic?"

**Brainstorming process for each variation:**
1. What is the person's RELATIONSHIP to the topic? (teaching it, discovering it, benefiting from it, showing it off, relaxing because of it)
2. What PHYSICAL ACTION does the title imply? ("while I sleep" → relaxing, "Geheim-Tipps" → whispering/leaning in, "besser als 99%" → confident lean)
3. What pose would make a viewer CURIOUS about what's happening?

**Pose vocabulary by title energy** (inspiration, not templates — always derive from THIS title):
- **"I found something amazing"** → holding proof toward camera, leaning forward, presenting with both hands
- **"This works without effort"** → leaning back relaxed, hands behind head, feet up, casual with arms crossed
- **"Secret/insider knowledge"** → leaning in conspiratorially, hand cupped near mouth, finger on lips, peeking around corner
- **"Look at this result"** → pointing at element, presenting with open palm, holding screen toward viewer, thumbs up
- **"I'm in control"** → arms crossed confidently, slight lean, one eyebrow raised, standing tall
- **"Mind blown"** → hands on head/temples, both hands up, stepping back in positive disbelief
- **"Before/After transformation"** → one hand pushing away "before", other presenting "after"
- **"Competition/winning"** → fist pump, victory gesture, standing above something
- **"Active doing"** → typing, reading, writing on whiteboard, talking on phone, working at desk
- **"Peeking/teasing"** → looking around a corner, peeking from behind object, lifting a curtain

**Then for each variation, create 3 POSE VARIANTS (a/b/c)** that pair with the 3 background sub-scenes. Each pose keeps the same ENERGY but varies the specific gesture or interaction:

```
POSES & GESTURES (5 poses × 3 variants each):
V1 pose energy: [WHAT THE BODY COMMUNICATES] — derived from: [TITLE ELEMENT]
  a: [specific pose + prop interaction]
  b: [different pose, same energy]
  c: [third variant]
V2 pose energy: [DIFFERENT BODY LANGUAGE] — derived from: [TITLE ELEMENT]
  a: [pose] b: [pose] c: [pose]
V3 pose energy: [DIFFERENT] — derived from: [TITLE ELEMENT]
  a: [pose] b: [pose] c: [pose]
V4 pose energy: [DIFFERENT] — derived from: [TITLE ELEMENT]
  a: [pose] b: [pose] c: [pose]
V5 pose energy: [DIFFERENT] — derived from: [TITLE ELEMENT]
  a: [pose] b: [pose] c: [pose]
```

**Rules:**
- The pose comes FIRST, then the prop follows naturally from it (not: pick a prop, then awkwardly attach to person)
- No two variations may share the same pose energy (e.g., can't have two "pointing at something" variations)
- At least 2 of the 5 variations should use poses WITHOUT held props (arms crossed, hands behind head, leaning in, peeking) — not every thumbnail needs the person holding a device
- The pose must be physically plausible and describable in enough detail for the image model

#### 7. EMOTION — ALWAYS POSITIVE (mandatory)

Facial expressions must always communicate positive energy. The viewer should feel excitement, curiosity, or inspiration — never fear, worry, or alarm.

**Approved expressions:**
- **Amazed/Blown away**: eyes wide open, mouth open in genuine delight — "I can't believe how good this is"
- **Excited**: big open smile, forward energy, eyebrows raised — enthusiastic, can't wait to share
- **Surprised (positive)**: eyebrows up, mouth slightly open, pleasant discovery — NOT horror/shock
- **Confident + approving**: warm direct gaze, slight smile — "this is solid, trust me"
- **Curious/Interested**: one eyebrow raised, engaged, leaning in — "let me show you something cool"
- **Joyful**: genuine open smile, relaxed, warm
- **Wonder**: soft open expression, slightly upward gaze — amazed by possibility

**NEVER use:** fear, horror, worry, aggression, cold stares, stressed looks
Exception: only if the video topic is explicitly a warning or threat.

**Per topic:**
- AI tool launch → amazed / excited (positive shock at what's possible)
- Tutorials → confident + approving (warm smile, direct gaze)
- Comparisons → curious/interested (engaged, thoughtful)
- Surprising results → positive amazement (wide eyes, open smile)
- Trends → excited / forward-leaning

Choose the primary emotion for this video. Each variation can use a slightly different nuance (e.g., V1 = excited, V3 = confident), but all must stay positive.

#### 8. TEXT COMPOSITIONS — 5 UNIQUE (one per variation, MANDATORY)

Each of the 5 thumbnail variations MUST have its own unique text composition. Never reuse the same text across variations. This gives the user 5 genuinely different concepts to choose from — not just visual variants of the same message.

**Each text composition consists of 2-3 text elements** that together form a complete, meaningful thought. A single isolated phrase is NOT enough — the viewer must understand the message at a glance.

**Text element hierarchy (MANDATORY for every variation):**
1. **Hero element** — The biggest, most prominent text. Usually the keyword, number, or core concept. MASSIVE size, bold effect (3D, gradient, neon, etc.)
2. **Context element** — Smaller text that completes the sentence or adds meaning. Different font weight, size, or color than the hero. Positioned above, below, or beside the hero.
3. **Optional accent element** — A third text piece like a label, badge, question mark, or subtitle for additional context. Can be styled as a tag, underline, or small caption.

**Rules for text compositions:**
- Together, the 2-3 elements must form a complete thought that makes sense on its own — NOT a disconnected fragment
- Each element gets its OWN style: different size, weight, color, or effect — creating visual hierarchy
- The hero element is 2-3x larger than the context element
- All text in correct German (or English if the channel is English) — no spelling errors, no mixed languages
- Each variation must take a DIFFERENT angle on the same topic

**How to create the 5 text compositions — TOPIC-DRIVEN, not from a fixed list:**

The 5 text compositions must emerge from the SPECIFIC video topic, not from a reusable template. Do NOT cycle through the same 5 generic angles (provocative claim, value/benefit, disruption, personal, curiosity gap) for every video. Instead:

1. **Extract the core concepts** from the video title — what are the 3-5 most important words, numbers, or ideas?
2. **Brainstorm 5 different ways a viewer might REACT** to hearing this specific title — what would they think, feel, or want to know? Each reaction suggests a different text angle.
3. **Each composition must feel like it could ONLY belong to THIS video** — if you could swap the text onto a different video's thumbnail and it still works, it's too generic.

**The test for good compositions:** Can this text ONLY make sense for this specific video? If yes → good. If it could work for any video → too generic, redo it.

**BAD (too generic — works for any video):** "GAME CHANGER", "DER TRICK", "SO GEHT'S", "MEIN GEHEIMNIS"
**BAD (too short, no context):** "7 SKILLS", "KI", "WOW"

**GOOD — topic-specific examples:**

For "Platz 1 bei Google Maps":
- "PLATZ #1" + "BEI GOOGLE" — states the specific achievement
- "JEDER SUCHT" + "DICH ZUERST" — what ranking #1 actually means for the viewer
- "GOOGLE MAPS" + "DOMINIEREN" — action-oriented, specific platform
- "VOR ALLEN" + "ANDEREN" — competitive angle unique to rankings
- "5 STERNE" + "GARANTIERT" — specific Google Maps element (stars)

For "3 AI Agents That Run My Business While I Sleep":
- "3 AGENTS" + "ARBEITEN FÜR MICH" — specific to agent count
- "ICH SCHLAFE" + "SIE ARBEITEN" — the sleep/work contrast from the title
- "MEIN BUSINESS" + "LÄUFT ALLEIN" — the autonomy angle
- "24/7" + "OHNE MICH" — time-specific, automation angle
- "3 ROBOTER" + "1 BUSINESS" — ratio/contrast unique to this topic

Notice: every composition is deeply tied to its specific topic. None of them would work on a random other video.

Output all 5 compositions clearly:
```
TEXT COMPOSITIONS:
V1: Hero "[HERO]" + Context "[CONTEXT]" [+ optional Accent "[ACCENT]"]
V2: Hero "[HERO]" + Context "[CONTEXT]" [+ optional Accent "[ACCENT]"]
V3: Hero "[HERO]" + Context "[CONTEXT]" [+ optional Accent "[ACCENT]"]
V4: Hero "[HERO]" + Context "[CONTEXT]" [+ optional Accent "[ACCENT]"]
V5: Hero "[HERO]" + Context "[CONTEXT]" [+ optional Accent "[ACCENT]"]
```

#### 9. TYPOGRAPHY MOOD

Derive the font treatment from the topic's EMOTIONAL ENERGY — not from a list of preset styles.

Ask: "What does this title SOUND LIKE when spoken aloud? What's the energy?"
- Urgent/breaking news → sharp, angular, compressed letterforms
- Confident/authoritative → clean, wide, heavy weight with generous spacing
- Playful/surprising → bouncy, slightly irregular, mixed sizes
- Premium/exclusive → thin elegant serifs or ultra-light sans-serif with wide tracking
- Technical/precise → monospaced or geometric, clean edges, mathematical feel
- Bold/confrontational → ultra-black condensed, tight kerning, fills the frame

Write the typography mood as a description, not a template name:
```
TYPOGRAPHY MOOD: [2 sentences describing how the text should FEEL — its weight, spacing, energy, and personality. Reference the title's emotional tone, not a style template.]
```

Each variation can interpret this mood differently (different weights, sizes, arrangements) but all should feel like they belong to the same topic.

#### 10. COMPACT SCENE OVERVIEW (5 lines — output in chat, then proceed to JSON)

Do **NOT** write full scene details here — they go directly into `style_brief.json` in Step 3a. Instead, output a compact overview so the user can verify concept angles and text before the JSON is written.

**Output exactly this format — 1 line per variation:**

```
V1: Hero "[HERO]" + "[CONTEXT]" | Pose: [1-word energy] | Location: [specific place] | Color: [dominant hex]
V2: Hero "[HERO]" + "[CONTEXT]" | Pose: [1-word energy] | Location: [specific place] | Color: [dominant hex]
V3: Hero "[HERO]" + "[CONTEXT]" | Pose: [1-word energy] | Location: [specific place] | Color: [dominant hex]
V4: Hero "[HERO]" + "[CONTEXT]" | Pose: [1-word energy] | Location: [specific place] | Color: [dominant hex]
V5: Hero "[HERO]" + "[CONTEXT]" | Pose: [1-word energy] | Location: [specific place] | Color: [dominant hex]
```

The 3 sub-scenes (a/b/c) within each variation share the same text and concept — they differ in background sub-scene, pose variant, and camera framing. Those differences are defined directly in `style_brief.json`, not written here.

**Quality rules (enforced at JSON-writing time):**
- No two variations share a primary prop, dominant color, OR concept angle
- Every variation must pass: "Could this work for a different video?" → If yes, make it more specific
- Each a/b/c uses a different background sub-scene + different pose variant

#### 11. SELF-CHECK (mandatory before proceeding)

Before writing any prompts, verify:

**Props & Colors:**
- [ ] Do any two variations share a primary prop? → Fix it
- [ ] Do any two variations share a dominant color? → Fix it
- [ ] Did I use any BANNED generic prop (crown, trophy, rocket, lightbulb, magnifying glass, shield)? → Replace it
- [ ] Are ALL colors justified by the topic, not by "variety"? → Fix any unjustified colors

**Backgrounds (CRITICAL — the #1 failure mode):**
- [ ] Does EVERY background depict a recognizable real-world location? → If any uses a gradient, solid color, or abstract void, replace it with a real location UNLESS you can justify why no physical setting exists for that concept
- [ ] Are all 5 variation locations DIFFERENT from each other? → Fix duplicates
- [ ] Do the 3 sub-scenes (a/b/c) within each variation use DIFFERENT background details? → Fix any identical sub-scenes
- [ ] Does each location ADD MEANING to the thumbnail (tells part of the story)? → Replace any that are purely decorative

**Poses & Gestures (CRITICAL — the #2 failure mode):**
- [ ] Does each pose TELL THE STORY of the title without reading the text? → Replace generic "holding device" poses
- [ ] Are all 5 variation poses DIFFERENT energies? → Fix if two share the same gesture type (e.g., two "pointing at something")
- [ ] Do the 3 sub-scenes (a/b/c) use DIFFERENT pose variants? → Fix identical poses within a variation
- [ ] Are at least 2 of the 5 variations using poses WITHOUT held props? → Add variety (arms crossed, leaning back, peeking, etc.)
- [ ] Is each pose physically plausible and describable? → Fix impossible poses

**Text & Logos:**
- [ ] Does each variation have its OWN unique text composition? → Fix duplicates
- [ ] Are all text compositions topic-specific (would NOT work on a different video)? → Replace generic ones
- [ ] Are ALL logos described by VISUAL GEOMETRY, not by name? → Fix any "[Tool] logo" descriptions
- [ ] Could any logo be confused with a DIFFERENT tool's logo? → Add disambiguation

**General:**
- [ ] Would any variation work as a thumbnail for a DIFFERENT video? → Make it more specific
- [ ] Does the typography mood reflect THIS title's energy? → Rewrite if preset
- [ ] Is the emotion positive? → Fix if negative
- [ ] Do the 15 scene cards (5×3) provide genuine variety? → Each card should feel like a different photograph, not a re-run of the same prompt

Only after passing ALL checks → proceed to Step 2.

---

### Step 1: (Removed — merged into Style Brief)

All analysis that was previously in Step 1 (emotion, text compositions, scene concepts, color scheme, topic visual vocabulary, background scenes, poses & gestures) is now part of the Style Brief (Step 0.5). Proceed directly from the Style Brief to Step 2.

### Step 2: Build the Nano Banana Pro Prompt

Use this exact structure. Fill in the bracketed sections based on the Style Brief.

```
Design a professional YouTube video thumbnail in 16:9 aspect ratio (1280x720) using the person from the reference image.

SUBJECT:
**FACE REFERENCE — Identity Locking (CRITICAL):**
The last image provided is the FACE REFERENCE. This is the identity anchor for the entire image.
- Preserve EXACTLY: face shape (jawline, cheekbones, forehead width), nose shape and size, eye shape and color, eyebrow shape and thickness, lip shape, ear shape, skin tone and texture, hair color, hair texture, hairline position
- The person's bone structure and proportions must remain photorealistic and unchanged — do NOT idealize, smooth, or reshape the face
- Expression may change (see below) — but expression is a MUSCLE change only, not a structural change. The underlying face shape stays identical
- Any deviation in bone structure, nose shape, eye spacing, or skin tone = failure. Regenerate if the face does not match the reference

- Change only their expression to [EMOTION]: [describe the specific expression - e.g., "eyes wide open, mouth slightly open in shock, eyebrows raised — ONLY the muscles around the eyes and mouth change, all bone structure remains identical to the reference"]
- Position the person on the [LEFT/RIGHT/CENTER-RIGHT] third of the frame
- [FRAMING: tight close-up from chest up / medium shot from waist up / etc. — vary per sub-scene]

POSE & GESTURE (MANDATORY — the body tells the story):
The person's body language must communicate the video's message BEFORE the viewer reads any text. The pose comes first — props follow naturally from it.
- [DESCRIBE THE FULL BODY POSE: what is the person's posture? What are their hands doing? What direction are they facing/leaning? What energy does the pose communicate?]
- [IF HOLDING A PROP: describe the prop interaction as a natural extension of the pose — e.g., "leaning back relaxed in a chair with a laptop open on their lap, screen glowing" or "leaning forward conspiratorially, holding a phone toward the camera showing [CONTENT]"]
- [IF NO PROP: describe the gesture — e.g., "arms crossed confidently, slight lean forward, one eyebrow raised" or "hands behind head, leaning back, completely relaxed" or "peeking around the left edge of the frame, one hand on the frame edge, curious expression"]
- The pose must be physically plausible, visually clear at thumbnail size, and MOTIVATED BY THE VIDEO TITLE
- Sharp focus on face, natural skin texture

WARDROBE (MANDATORY — no formal clothes):
- The person wears sporty-elegant casual clothing ONLY: fitted crew-neck t-shirt, polo shirt, clean minimal hoodie, or open-collar casual shirt — relaxed but polished
- NEVER: suit jacket, blazer, business shirt, tie, uniform, formal attire of any kind
- Colors: clean neutrals (white, grey, navy, black) or muted tones that complement the thumbnail palette

LIGHTING (cinematic — ALWAYS cinematic, but CONTEXT-DEPENDENT):
Lighting must always be cinematic (directional, dimensional, NOT flat studio) — but the specific setup must fit the SCENE and COLOR PALETTE of the thumbnail. Do NOT default to the same harsh amber key every time.

Choose the lighting setup that matches the scene:
- **Warm interior / office / home**: Soft key light motivated by window or desk lamp, warm color temperature matching the environment. Gentle shadows, commercial-quality softness.
- **Outdoor / golden hour**: Warm directional sun as key, natural rim light, atmospheric haze. Let the environment dictate the warmth.
- **Tech / neon / cool scene**: Cooler key, blue or teal rim, color temperatures matching the neon/screen elements in the scene.
- **Dramatic / triumphant**: Harder key, stronger contrast (4:1+), rim light matching the dominant accent color.
- **Urban / dusk**: Mixed color temperatures — warm practicals, cool ambient, the city provides the lighting.

ALWAYS include:
- Rim/separation light from behind (color and intensity fitting the scene) — separates subject from background
- Visible catch-lights in both eyes
- Directional light (not flat/even) — face must have dimensional shadows
- Light colors must match and complement the scene colors and thumbnail palette

NEVER:
- Flat even studio lighting with no shadows
- Lighting color that contradicts the scene (e.g., warm amber key in a cool neon scene)
- Same lighting setup for every thumbnail regardless of context

SCENE & PROPS (MANDATORY — the thumbnail must feel like a living scene, not a static portrait):
The person MUST physically interact with at least one prop. The scene must feel active, dynamic, and lovingly detailed — every element contributes to storytelling.

- PRIMARY PROP: [DETAILED PROP DESCRIPTION — describe the physical object, its material, size, lighting, and WHAT IS VISIBLE ON IT]
  - Interaction: [HOW the person holds/grips/presents the prop — e.g., "held with both hands, tilted 15° toward camera, screen facing viewer"]
  - Content on prop: [SPECIFIC visible content — e.g., "Google Maps listing showing business name, 5 gold stars, and 'Platz #1' label"]
  - The prop must be LARGE (at least 25% of the person's visible body area), photorealistic, and break the person's silhouette for depth
  - The prop catches the scene's rim light on its edges, creating specular highlights

- SECONDARY ELEMENT: [ONE additional 3D-rendered visual element that floats in the scene]
  - **If this is a tool/platform logo**: Use the GEOMETRIC VISUAL DESCRIPTION from the Style Brief's Logo Descriptions section — describe it by shapes, colors (hex codes), and proportions. NEVER write just "a [Tool Name] logo" — the model will generate the wrong logo. Example: instead of "a Claude logo", write "a stylized starburst symbol with ~12 curved radiating rays in warm terracotta orange (#D97757), photorealistic 3D-rendered with soft volumetric glow"
  - **If this is another visual element**: e.g., "a photorealistic 3D golden map pin with a '#1' label, floating above the phone with soft volumetric glow and drop shadow, catching dramatic side light"
  - Must be described as a dimensional object (never flat/clipart)
  - Position: [WHERE in the frame — e.g., "upper-left, slightly behind the person's head"]

- AMBIENT DETAILS (optional but encouraged for richness): [Subtle particles, sparkles, glow effects — e.g., "scattered golden star particles floating in the air around the prop, with soft depth-of-field blur on the distant ones" or "subtle warm bokeh particles drifting upward"]

TEXT & GRAPHICS:
The thumbnail must have 2-3 text elements that together form a complete, meaningful message. Each element has its own size, style, and effect — creating clear visual hierarchy.

- HERO TEXT: "[HERO WORD/NUMBER]" — the largest, most prominent element
  - Size: MASSIVE, 2-3x larger than other text
  - Style: [HERO EFFECT: e.g., "3D extruded gold letters with depth shadow" or "massive bold white with thick black outline" or "neon glow lettering"]
  - Placement: [POSITION: e.g., "upper-right, partially behind the person's head"]

- CONTEXT TEXT: "[CONTEXT PHRASE]" — completes the thought, smaller but still bold and readable
  - Size: Medium-large, clearly smaller than hero but still readable at thumbnail size
  - Style: [CONTEXT STYLE: e.g., "clean white bold sans-serif" or "thin condensed uppercase in accent color"]
  - Placement: [POSITION: e.g., "directly above/below the hero text"]

- [OPTIONAL ACCENT TEXT]: "[ACCENT PHRASE]" — additional label, subtitle, or badge
  - Size: Smallest text element, still legible
  - Style: [ACCENT STYLE: e.g., "small pill-shaped badge" or "thin italic subtitle"]

- [OPTIONAL GRAPHICS: e.g., "Add a bold yellow arrow pointing from the person toward the key visual element" or "Add subtle glowing particles around the text"]

TEXT ELEMENTS (spell exactly as written):
- Hero: "[EXACT TEXT]" ([word count], all caps, [language])
- Context: "[EXACT TEXT]" ([word count], all caps, [language])
- [Optional] Accent: "[EXACT TEXT]"
- No other text anywhere in the image

BACKGROUND (REAL LOCATION — the #1 priority):
The background MUST be a recognizable real-world location that tells part of the video's story. The viewer should be able to guess the video topic from the background alone.
- Use the SPECIFIC LOCATION from the Style Brief's Background Scenes (Section 5) for this sub-scene (a/b/c)
- All backgrounds must have **depth of field** (bokeh blur) to separate the sharp foreground subject from the softer background
- The lighting in the background must feel MOTIVATED BY THE ENVIRONMENT (window light, desk lamp, street lights, screen glow) — not generic studio lighting imposed on top

**Describe the location with enough detail to be recognizable even when blurred:**
- What ROOM or PLACE is this? (bedroom, office, coworking space, shopping street, café, living room, etc.)
- What TIME OF DAY? (morning light, afternoon sun, evening warmth, nighttime screen glow)
- What KEY OBJECTS are visible in the background? (desk, monitor, bookshelf, window, street signs, other people walking — all blurred but identifiable)
- What is the LIGHTING MOOD of the environment? (warm desk lamp, cool monitor glow, golden hour through window, neon signs)

**NEVER:**
- Plain black, white, or single-color backgrounds
- Abstract gradients or mesh gradients as the SOLE background (gradients can OVERLAY a real location for added richness)
- "Studio void" with lighting but no environment
- The same generic location for every thumbnail

**The rare exception:** Abstract/gradient backgrounds are ONLY acceptable when the topic has genuinely no physical setting (e.g., purely philosophical concepts). For 95% of videos — especially tool tutorials, productivity tips, business topics — there IS a real place where this happens. Use it.

- Background must not compete with subject — supportive but visually rich and dimensional
- High saturation and contrast
- [BACKGROUND DESCRIPTION: describe the specific real-world location, its time of day, lighting mood, and key visible environmental details]

COMPOSITION:
- Follow the rule of thirds — subject on one third, text/graphics filling the other space
- Ensure the thumbnail reads clearly even at small mobile size
- One clear focal point, one clear message

STYLE (cinematic — ALWAYS apply):
- Photorealistic, cinematic film look — NOT generic stock photo or flat studio aesthetic
- COLOR GRADE: Cinematic commercial/comedy quality — lifted blacks (shadows are dark grey, never pure black), dimensional lighting, high production value. The SPECIFIC color palette and grade must match the scene and topic — it can range from natural/photographic (neutral tones, realistic light colors) to stylized (colored gels, neon accents, teal/orange split). Choose the grade that fits THIS specific thumbnail's world and mood. The grade should feel intentional and cinematic, whether that's warm and natural or bold and colorful.
- LENS: shot on anamorphic 50mm — shallow depth of field, smooth oval bokeh in background, subtle horizontal lens flare from rim light
- FILM TEXTURE: subtle film grain overlay across entire image, slight vignette darkening the corners, adding cinematic depth
- High contrast, approachable — commercial energy, not dark thriller
- [STYLE REFERENCE: describe the specific look for THIS variation — e.g., "Natural warm interior photography, soft window light, muted tones" OR "Bold neon tech look, cyan rim light, deep shadows" OR "Golden hour outdoor, warm sunlight, creamy bokeh"]

AVOID: cluttered backgrounds, distorted facial features, unreadable text, plastic-looking skin, flat even studio lighting, tiny elements, low contrast, extra fingers or eyes, watermarks, flat 2D logo PNGs (use 3D-rendered logos instead), flat PowerPoint-style clipart icons, generic sans-serif fonts, plain color gradients with no texture, old-school diagram boxes and arrows, formal clothes, blazers, suits, uniforms, business attire, WRONG LOGOS (never generate a logo from memory — only use the geometric description provided above; a wrong logo is worse than no logo).
```

### Step 3: Generate 15 Unique Thumbnails (5 Variations × 3 Distinct Sub-Scenes)

#### Step 3a: Write the Style Brief JSON (ONE Write call)

Instead of writing 15 prompt files individually, write a **single `style_brief.json`** file. The `build_prompts.py` script will generate all 15 prompts from it in one Bash call.

The JSON structure:
```json
{
  "title": "Video title here",
  "cells_dir": "Headshots/person-grid-cells/",
  "variations": [
    {
      "hero_text": "HERO WORD",
      "hero_style": "massive 3D extruded amber-gold letters...",
      "context_text": "CONTEXT PHRASE HERE",
      "context_style": "bold white uppercase, black drop shadow",
      "accent_text": "",
      "accent_style": "",
      "emotion": "excited",
      "wardrobe": "Clean fitted white crew-neck t-shirt — sporty, minimal.",
      "scenes": [
        {
          "suffix": "a",
          "emotion_desc": "big genuine open smile, eyebrows raised...",
          "position": "RIGHT",
          "framing": "medium shot from waist up",
          "pose": "Full pose description...",
          "lighting": "Full lighting description...",
          "primary_prop": "Full prop description...",
          "secondary_element": "Full secondary element description...",
          "ambient_details": "Optional ambient details...",
          "hero_placement": "upper-left",
          "context_placement": "below hero text",
          "background": "Full background description...",
          "composition": "Full composition description...",
          "style": "Full style description..."
        },
        { "suffix": "b", ... },
        { "suffix": "c", ... }
      ]
    },
    // ... variations 2-5
  ]
}
```

**Scene-specific fields override variation-level fields** — so if scene "b" needs a different wardrobe or hero_style, just include it in the scene object.

**ALL design decisions come from the Style Brief (Step 0.5).** The 15 scene cards were already defined in Section 10, drawing from:
- Text compositions → Section 8
- Background scenes → Section 5 (different sub-scene per a/b/c)
- Poses & gestures → Section 6 (different pose per a/b/c)
- Props → Section 4
- Colors → Section 2
- Logos → Section 3
- Emotion → Section 7
- Typography → Section 9

**The 5 variations MUST differ in ALL of these dimensions:**
- **Different text composition** — each variation uses its own unique topic-specific text
- **Different text treatment** — each variation interprets the Typography Mood differently
- **Different pose energy** — each variation's body language tells a different part of the story
- **Different background location** — each variation is set in a different real-world place
- **Different prop interaction** — each variation uses a DIFFERENT prop from the Topic Props list
- **Different dominant color** — each variation emphasizes a different color from the Topic Color DNA

**The 3 sub-scenes (a/b/c) within each variation MUST differ in:**
- **Different background sub-scene** — different time of day, room area, or camera angle
- **Different pose variant** — different gesture or body position, same energy
- **Different framing** — vary person placement (left/right/center) or camera tightness

#### Step 3b: Build prompts + Generate thumbnails (TWO Bash calls)

```bash
SKILL_ROOT="$HOME/.claude/skills/youtube-thumbnails"
CELLS_DIR="[CELLS_DIR]"  # e.g., Headshots/person-grid-cells/
OUTPUT_DIR="[OUTPUT_DIR]"  # e.g., thumbnails/2026-03-10_topic-name
PROMPTS_DIR=".prompts/[DATE]_[TOPIC]"
TITLE="[VIDEO TITLE]"

# Step 1: Build all 15 prompts from style_brief.json (instant, ~1 second)
python3 "${SKILL_ROOT}/scripts/build_prompts.py" \
  --brief "${PROMPTS_DIR}/style_brief.json" \
  --output "${PROMPTS_DIR}"
```

Then generate in 3 batches of 5 parallel jobs:

```bash
# Batch 1: suffix a (5 parallel jobs)
for v in 1 2 3 4 5; do
  EMOTION=$(python3 -c "import json; d=json.load(open('${PROMPTS_DIR}/style_brief.json')); print(d['variations'][$((v-1))].get('emotion','excited'))")
  python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
    --cells-dir "${CELLS_DIR}" --emotion "${EMOTION}" \
    --prompt "$(cat "${PROMPTS_DIR}/v${v}a.txt")" \
    --output "${OUTPUT_DIR}" --variation ${v} --suffix a --title "${TITLE}" &
done
wait
echo "Batch 1 (suffix a) done"

# Batch 2: suffix b
for v in 1 2 3 4 5; do
  EMOTION=$(python3 -c "import json; d=json.load(open('${PROMPTS_DIR}/style_brief.json')); print(d['variations'][$((v-1))].get('emotion','excited'))")
  python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
    --cells-dir "${CELLS_DIR}" --emotion "${EMOTION}" \
    --prompt "$(cat "${PROMPTS_DIR}/v${v}b.txt")" \
    --output "${OUTPUT_DIR}" --variation ${v} --suffix b --title "${TITLE}" &
done
wait
echo "Batch 2 (suffix b) done"

# Batch 3: suffix c
for v in 1 2 3 4 5; do
  EMOTION=$(python3 -c "import json; d=json.load(open('${PROMPTS_DIR}/style_brief.json')); print(d['variations'][$((v-1))].get('emotion','excited'))")
  python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
    --cells-dir "${CELLS_DIR}" --emotion "${EMOTION}" \
    --prompt "$(cat "${PROMPTS_DIR}/v${v}c.txt")" \
    --output "${OUTPUT_DIR}" --variation ${v} --suffix c --title "${TITLE}" &
done
wait
echo "All 15 thumbnails done"
```

**IMPORTANT: Use `--cells-dir` (not `--headshot` + `--references`).** The `--emotion` flag selects the best cell automatically.

Output filenames: `2026-03-10_thumbnail_v1a.png`, `_v1b.png`, `_v1c.png`, `_v2a.png` … `_v5c.png`.

Each of the 15 thumbnails is a genuinely different image — different background, different pose, different framing. The 3 within a variation share the same headline text and concept direction, giving you real choice within each messaging angle.

### Step 3.1: Post-Processing — Organize + Verify + Border (one combined step)

Run all three post-processing actions in sequence. The frontal neutral cell (from `cells.json`) is the best identity reference for verification.

```bash
SKILL_ROOT="$HOME/.claude/skills/youtube-thumbnails"
OUTPUT_DIR="[OUTPUT_DIR]"
CELLS_DIR="[CELLS_DIR]"

# 1. Organize into subfolders (v1/–v5/, each with up to 3 thumbnails)
for v in 1 2 3 4 5; do
  mkdir -p "${OUTPUT_DIR}/v${v}"
  for f in "${OUTPUT_DIR}"/*_v${v}*.png; do
    [ -f "$f" ] && mv "$f" "${OUTPUT_DIR}/v${v}/"
  done
done

# 2. Identify frontal neutral cell for verification
HEADSHOT=$(python3 -c "
import json, os
cells = json.load(open('${CELLS_DIR}/cells.json'))['cells']
for name, info in cells.items():
    if info.get('angle') == 'frontal' and info.get('expression') == 'neutral':
        print(os.path.join('${CELLS_DIR}', name)); break
")
echo "Verification headshot: ${HEADSHOT}"

# 3. Verify all 5 variation folders in parallel
for v in 1 2 3 4 5; do
  python3 "${SKILL_ROOT}/scripts/verify_faces.py" \
    --headshot "${HEADSHOT}" \
    --thumbnails "${OUTPUT_DIR}/v${v}" \
    --auto-delete &
done
wait
echo "Verification done"

# 4. Apply gradient border to all passing thumbnails in parallel
for v in 1 2 3 4 5; do
  for f in "${OUTPUT_DIR}/v${v}"/*.png; do
    [ -f "$f" ] && python3 "${SKILL_ROOT}/scripts/add_gradient_border.py" --input "$f" &
  done
done
wait
echo "Borders applied — post-processing complete"
```

**Verification score interpretation:**
- **1-3 = FAIL** — Auto-deleted. Regenerate (same variation + suffix). Max 2 regeneration rounds.
- **4-6 = WARN** — Kept, flagged for manual review.
- **7-10 = PASS** — Same person confirmed.

**After verification, regenerate only failed thumbnails:**
```bash
# Example: v1b and v2a were deleted
python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
  --cells-dir "${CELLS_DIR}" --emotion "[EMOTION_V1]" \
  --prompt "$(cat "[PROMPTS_DIR]/v1b.txt")" \
  --output "${OUTPUT_DIR}" --variation 1 --suffix b --title "[TITLE]" &

python3 "${SKILL_ROOT}/scripts/generate_thumbnail.py" \
  --cells-dir "${CELLS_DIR}" --emotion "[EMOTION_V2]" \
  --prompt "$(cat "[PROMPTS_DIR]/v2a.txt")" \
  --output "${OUTPUT_DIR}" --variation 2 --suffix a --title "[TITLE]" &
wait
```
Then re-run only the verify + border steps on the affected subfolder(s).

**Border design specs (NEVER change — channel consistency):**
- Border thickness: 18px | Inner corner radius: 32px | Canvas: 1280×720
- Gradient: auto-extracted from thumbnail's dominant accent colors, diagonal top-left → bottom-right
- Optional manual override: `--color1 "#E6FF05" --color2 "#00EBFA"`

### Step 4.5: Cleanup Temporary Files (MANDATORY — run before presenting results)

Delete all temporary files created during the workflow. These accumulate across jobs and waste disk space.

```bash
# Delete competitor thumbnails downloaded for visual analysis
rm -rf /tmp/competitor_thumbs_*
rm -f /tmp/competitor_urls.txt

# Delete any other temp files created during this workflow
# (e.g. intermediate txt files outside the project directory)
```

**What to keep (NOT temp):**
- The final thumbnails in `thumbnails/[topic]/v1/` through `v5/` — these are the deliverable
- The `style_brief.json` and prompt `.txt` files in `.prompts/[topic]/` — useful if regeneration is needed
- The `cells.json` and cropped cells in `Headshots/[name]-cells/` — reused across all videos for this person
- The three Markdown docs in `thumbnails/[topic]/` — see Step 4.7 below

### Step 4.7: Save Markdown Documentation (MANDATORY — run after cleanup, before Step 5)

Save Research Summary, Style Brief, and all 15 prompts as Markdown files directly in the thumbnail output folder (`thumbnails/[topic]/`). This makes every job self-contained and reproducible.

```bash
OUTPUT_DIR="thumbnails/[DATE]_[TOPIC]"
PROMPTS_DIR=".prompts/[DATE]_[TOPIC]"

# 1. research-summary.md — copy from the chat Research-Zusammenfassung output
# Write manually as a Write tool call with the Research-Zusammenfassung content

# 2. style-brief.md — derived from style_brief.json, human-readable format
# Write manually as a Write tool call with sections from style_brief.json

# 3. prompts.md — all 15 prompts compiled from .txt files
python3 << 'PYEOF'
import os, json

PROMPTS_DIR = "[PROMPTS_DIR]"
OUT_DIR = "[OUTPUT_DIR]"

lines = ["# Bildgenerierungs-Prompts\n\n**Video:** [TITLE]  \n**Datum:** [DATE]  \n**Gesamt:** 15 Prompts (5 Variationen × 3 Sub-Szenen a/b/c)\n\n---\n"]

for v in range(1, 6):
    for suffix in ['a', 'b', 'c']:
        fname = f"v{v}{suffix}.txt"
        fpath = os.path.join(PROMPTS_DIR, fname)
        with open(fpath, 'r') as f:
            content = f.read()
        lines.append(f"## V{v}{suffix.upper()}\n\n```\n{content}\n```\n\n---\n")

with open(os.path.join(OUT_DIR, "prompts.md"), 'w') as f:
    f.write('\n'.join(lines))
print("Written: prompts.md")
PYEOF
```

**Three files to create:**
- `thumbnails/[topic]/research-summary.md` — Research-Zusammenfassung (Topic Essence, Logo Matrix, Top 5 Competitors, Patterns, Differenzierung, Color DNA, Text-Ideen)
- `thumbnails/[topic]/style-brief.md` — Alle 10 Style Brief Sections in lesbarem Format (Visual World, Color DNA, Logos, Props, Backgrounds, Poses, Emotion, Text Compositions, Typography, Scene Overview + Face Verification Results)
- `thumbnails/[topic]/prompts.md` — Alle 15 generierten Prompts (V1A bis V5C), jeweils als Code-Block

**What to delete (temp):**
- `/tmp/competitor_thumbs_*/` — competitor thumbnails downloaded for visual analysis
- `/tmp/competitor_urls.txt` — temp URL list
- Any other `/tmp/` files created during this session

### Step 5: Present Results

After generation, tell the user:
- Where the thumbnails were saved — organized in subfolders `v1/` through `v5/`
- Which variation (V1/V2/V3/V4/V5) each subfolder represents, including:
  - The **unique headline text** used for that variation
  - The design concept (color palette, text effect, composition)
- Suggest they compare at small size (mobile preview) to pick the winner per variation, then the final overall winner
- Remind them that each variation has a different headline — so they're choosing both the visual design AND the messaging angle

## Design Elements Library

Beyond text and backgrounds, great thumbnails layer in **topic-relevant visual props and graphic elements**. Every element must earn its place — only include what directly represents the video topic.

### Person–Prop Interaction (Most Powerful)
The strongest thumbnails show the person **actively interacting** with a prop — not just standing next to floating elements. This creates a scene, tells a story, and is far more scroll-stopping than a static portrait.

**How to describe interactions in the prompt:**
- "The person is holding up a large printed blueprint/plan toward the camera, pointing at it with one finger"
- "The person is holding a whiteboard showing [CONTENT], grinning at the viewer"
- "The person is holding a large smartphone screen-out toward the camera, showing [APP/RESULT]"
- "The person is gripping a large glowing tablet with both hands, screen facing the camera, showing [SPECIFIC APP/RESULT]"
- "The person is pointing with their index finger at the floating [ELEMENT] to their right"
- "The person is holding a stack of banknotes fanned out, slightly forward toward the viewer"
- "The person is lifting a glowing object [e.g., a crystal ball, a glowing chip] with both hands, looking at it in awe"

**Rule:** The prop must be visually clear, large enough to read at thumbnail size, and 100% relevant to the video topic.

### Props & Visual Elements — ALWAYS from the Style Brief

**DO NOT use category-based prop lookup tables.** All props must come from the Style Brief's "Topic Props" section (Step 0.5, Section 4). That section already contains 7-10 topic-specific props brainstormed from the research.

**When describing any prop or visual element in the prompt, ALWAYS make it photorealistic and dimensional:**
- Describe the physical material, surface texture, and lighting interaction
- Specify WHAT IS VISIBLE on/in the prop (screen content, text, graphics)
- Describe HOW the person interacts with it (both hands? pointing? presenting?)
- The prop must be large enough to read at thumbnail size and break the person's silhouette

**Example of proper prop description:**
- ❌ "a laptop showing the app" (too vague)
- ✅ "a photorealistic silver MacBook held with both hands, screen facing viewer at 20° angle, showing the Claude Cowork interface with 'Cowork' tab highlighted in orange and 4 completed tasks with green checkmarks — the aluminum edges catch warm rim light with specular highlights"

### Tool & Platform Logos
Use when the video is about a specific tool — floating, 3D-rendered, NOT flat:
- **CRITICAL: Always use the geometric visual description from the Style Brief's Logo Descriptions (Section 3).** Never describe a logo by name alone — the image model will generate the wrong logo.
- Describe as a photorealistic 3D-rendered object using shapes, colors (hex codes), and proportions from the Style Brief
- Position: floating top-right or top-left corner, or scattered around the person
- NEVER use flat 2D logo PNGs — describe them as dimensional objects catching light
- If no logo description was researched → do NOT include the logo. A missing logo is better than a wrong one.

### Arrows & Directional Elements
Use to guide the viewer's eye and create visual tension:
- **Bold 3D arrow**: "a thick 3D-rendered neon [color] arrow pointing from the person toward the text/graphic, with a hard shadow"
- **Curved hand-drawn arrow**: "a rough chalk-style curved arrow drawn under the key word, as if circled by hand"
- **Double-headed arrow**: for comparisons (A vs B thumbnails)
- **Pointing finger graphic**: floating illustrated hand pointing at key element

### Circles, Highlights & Callouts
Use to draw attention to specific numbers, text, or interface elements:
- **Highlight box**: "a bold solid [color] rectangle behind the key word, like a text highlighter, slightly rotated 2 degrees"
- **Chalk circle**: "a rough hand-drawn chalk circle around the key number/word"
- **Glow ring**: "a glowing circular halo pulsing around the central graphic element"
- **Callout badge**: "a bold pill-shaped badge in [color] with white text '[WORD]', like a product sticker, with drop shadow"
- **Burst/starburst shape**: behind a number or key word, like a price tag explosion shape

### How to Combine Elements
Layer elements in this order (back to front):
1. Background (gradient/environment)
2. Background props (blurred screenshots, floating logos at low opacity)
3. Text overlay (main + secondary)
4. Text accents (highlights, circles, badges)
5. Person (sharp foreground) — optionally holding/interacting with a prop
6. Foreground props (arrow, money stack, phone — partially overlapping person for depth)

**Person–prop interaction beats floating elements every time.** If the person can hold, point at, or look toward the prop, do that instead of floating it in the background.

**Never use more than 3 distinct element types** — text + 1 prop/interaction + 1 graphic accent is the sweet spot.

**Design placement checklist:**
- Does the prop read at thumbnail size (50×28px)? If not, make it bigger or cut it.
- Does the person's gaze/gesture lead the eye toward the key message?
- Is the most important element (face or text) the highest-contrast thing on screen?
- Do foreground props break the person's silhouette? (Good — creates depth)

---

## Text Accuracy Rules (MANDATORY)

Every text element in the thumbnail must be **100% correct**. Include these rules explicitly in every prompt.

**Language consistency:**
- Choose ONE language for all text in the thumbnail: either fully German OR fully English
- NEVER mix languages (no "WIE KI Works" or "Das EXPLAINED")
- Match the channel language — if the video is German, all badge text, labels, and overlays are German

**Spelling & accuracy:**
- Spell out every word in the prompt using exact characters — never abbreviate or let the model infer
- Include this line in every prompt: `All text in the image must be spelled exactly as specified. No typos, no extra letters, no language switching. German words stay German, English words stay English.`

**In the prompt, always list every text element explicitly:**
```
TEXT ELEMENTS (spell exactly as written):
- Hero: "KI-ASSISTENT" (1 word, all caps, German)
- Context: "DEIN" (1 word, all caps, German, smaller, above hero)
- [Optional] Accent: "FÜR E-MAILS" (2 words, all caps, German, smallest, below hero)
- No other text anywhere in the image
```

**AVOID line addition:** Always add to the AVOID line: `"misspelled words, mixed German/English text, extra letters in text overlays, invented words"`

## Identity Locking — Face Preservation Rules (MANDATORY)

The single biggest failure mode in AI thumbnail generation is **face drift** — the model generates a plausible but different person. These rules prevent that.

### Why it happens
The model blends the reference face with its learned aesthetic for the requested expression or style. To counter this, the prompt must explicitly name every anatomical feature to lock and explicitly separate "expression" (muscle movement) from "structure" (bone/skin).

### Required phrase in EVERY prompt (copy verbatim, customize bracketed parts):

```
FACE REFERENCE — IDENTITY LOCK (non-negotiable):
The last image is the sole identity reference. The following must remain IDENTICAL to the reference photo:
- Bone structure: jawline shape, cheekbone position, forehead width and height, overall face proportions
- Nose: exact shape, bridge width, tip shape, nostril size
- Eyes: exact eye shape, lid crease, eye spacing, iris color
- Eyebrows: exact shape, thickness, arch position
- Lips: exact shape, cupid's bow, lip fullness
- Ears: shape and position
- Skin: exact skin tone, undertone, natural texture — do NOT smooth, lighten, darken, or idealize
- Hair: exact color (not darker, not lighter), hairline position, texture and density

EXPRESSION CHANGE ONLY — muscle movement, not structure change:
The requested expression [EMOTION] changes ONLY the following muscles:
- Smile → zygomatic major pulls lip corners up and back, cheeks lift slightly
- Shock → frontalis raises brows, orbicularis oculi widens eyes, depressor labii opens mouth — but mouth opening stays PROPORTIONAL to reference, never exaggerated
- Confidence → minimal muscle engagement, slight zygomaticus minor, steady gaze
All bone structure, nose, eye shape, and skin tone remain EXACTLY as in the reference. A different-looking person = failed generation.
```

### Quick checklist before writing each prompt
- [ ] Does the SUBJECT section include the full Identity Lock paragraph above?
- [ ] Is the expression described as muscle movement only, not character/look change?
- [ ] Does the AVOID line include: "different face shape, altered nose, changed eye shape, skin tone change, idealized or smoothed skin"?

### The AVOID line must always include:
```
different person, altered bone structure, changed nose shape, different eye shape or spacing, smoothed or idealized skin, skin tone change, generic AI face, different hair color or style
```

---

## Modern Visuals — Required Language

**NEVER use these phrases (they produce PowerPoint/clipart results):**
- "icon", "flat icon", "simple icon", "clip art", "diagram", "chart"
- "brain icon", "gear icon", "arrow icon", "chat bubble icon"

**ALWAYS describe visual elements as 3D, rendered, or stylized objects:**
- ❌ "a brain icon" → ✅ "a photorealistic 3D-rendered glowing brain with neon synapse connections, floating with soft depth-of-field blur"
- ❌ "a gear icon" → ✅ "a gleaming brushed-metal 3D gear with a subtle ambient occlusion shadow, catching dramatic side lighting"
- ❌ "arrows connecting boxes" → ✅ "glowing neon flow lines with particle trails connecting floating glass-panel UI cards"
- ❌ "a diagram" → ✅ "a futuristic holographic interface panel with glowing edges and subtle transparency, like a sci-fi HUD"

**Background patterns — use modern design language:**
- Instead of gradients: "mesh gradient with shifting amber and deep violet tones, organic and fluid"
- Instead of plain dark: "deep dark background with volumetric light rays and subtle bokeh depth"
- Instead of solid colors: "frosted glass panels with glassmorphism blur effect layered over a gradient backdrop"
- Add texture: "subtle film grain overlay", "noise texture for depth", "micro-texture on the background"

**Typography — derive from the Style Brief's Typography Mood, not from a preset list:**
- ❌ "bold sans-serif" — too generic
- ❌ Cycling through the same 6 styles (condensed, editorial, 3D extruded, outlined, stencil, neon) for every job
- ✅ The Style Brief (Step 0.5, Section 9) defines a Typography Mood for this specific topic. Each variation's text treatment must interpret that mood differently, but all must feel connected to the topic's emotional energy.

**How to describe typography in the prompt:**
Instead of naming a template style, describe the VISUAL QUALITIES you want:
- Weight: how heavy/light? ("ultra-black", "hairline thin", "medium bold")
- Width: condensed, normal, or extended?
- Spacing: tight/compressed or airy/tracked out?
- Texture: clean/flat, dimensional/3D, glowing, rough/distressed, metallic?
- Color treatment: solid fill, gradient, outlined, translucent?
- Personality: aggressive, elegant, playful, technical, editorial?

**Example — describing typography from mood rather than template:**
For a video about AI automation with a "confident authority" mood:
- V1: "ultra-heavy geometric sans-serif in solid white, wide letter spacing, clean and commanding — like a tech company's headline font"
- V2: "massive condensed black letters with a subtle terracotta-orange gradient fill, tight tracking, slightly overlapping — bold and dense"
- V3: "mixed-weight editorial: thin 'SO NUTZT DU' above ultra-bold 'COWORK' — the weight contrast creates visual drama"

Notice: each description is unique but all share the same "confident authority" energy derived from the topic. None of them say "use 3D extruded" or "use neon sign" — they describe what the text LOOKS and FEELS like.

- Always mix two font weights for hierarchy: one massive ultra-bold line + one smaller thin/light line

# 📗 SOIL Narrated Motion Slides & Video Builder (`soil-motion-html`) Complete English Tutorial

> This comprehensive guide explains how to use the **`soil-motion-html`** skill to transform key slides in existing **SOIL interactive HTML presentations** (such as Walkthrough and Review decks hosted inside a Teaching Cockpit) into **English-narrated animated slides (Output A)** and automatically render **subtitled MP4 explainer videos (Output B)** from the exact same source.

---

## Table of Contents
1. [Core Philosophy: Build Once, Two Outputs](#1-core-philosophy-build-once-two-outputs)
2. [Prerequisites & Installation](#2-prerequisites--installation)
3. [Anatomy of a Motion Spec Directory](#3-anatomy-of-a-motion-spec-directory)
4. [Step 1: Selecting Candidate Slides (What to Animate vs. Keep Static)](#4-step-1-selecting-candidate-slides-what-to-animate-vs-keep-static)
5. [Step 2: Writing Segmented English Narration & Generating Word Timings (`make_narration.py`)](#5-step-2-writing-segmented-english-narration--generating-word-timings-make_narrationpy)
6. [Steps 3 & 4: Designing Motion Slide Layouts (`slides.html` / `slides.css`) & Choreography (`configs.js`)](#6-steps-3--4-designing-motion-slide-layouts-slideshtml--slidescss--choreography-configsjs)
7. [Step 5: Building a Trial Deck (`build_motion.py`) & Automated Layout Verification (`check_motion.js`)](#7-step-5-building-a-trial-deck-build_motionpy--automated-layout-verification-check_motionjs)
8. [Step 6: Deploying to Teaching Cockpit, Claude Artifact, and Firebase Hosting](#8-step-6-deploying-to-teaching-cockpit-claude-artifact-and-firebase-hosting)
9. [Step 7: Rendering Output B — MP4 Explainer Videos + SRT Subtitles (`render_video.py`)](#9-step-7-rendering-output-b--mp4-explainer-videos--srt-subtitles-render_videopy)
10. [Step 8: Updating & Maintaining Deployed Motion Slides](#10-step-8-updating--maintaining-deployed-motion-slides)
11. [Troubleshooting & 30 Battle-Tested Engineering Lessons](#11-troubleshooting--30-battle-tested-engineering-lessons)

---

## 1. Core Philosophy: Build Once, Two Outputs

| Output | Format & Contents | Primary Use Cases |
| :--- | :--- | :--- |
| **Output A: Narrated Motion Slide**<br>(HTML embedded inside the deck) | Turns key slides into interactive players with **`▶ Play`**, **`⟲ Replay`**, **`🔊 Voice on / 🔇 Voice off`**, clickable step chips (`.mx-chip`), and a progress bar. Every visual change is synced to word-level `edge-tts` timestamps. | Classroom projection & self-paced student study (Teaching Cockpit, Claude Artifact, Firebase Hosting) |
| **Output B: Explainer Video**<br>(`.mp4` + `.srt` captions) | Recorded directly from Output A via `scripts/render_video.py` into a 1280×720 H.264 MP4 with the same voiceover and word-timed `.srt` subtitles (soft subtitle track by default, or burned-in via `--burn`). | Pre-class preview, make-up study, LMS / YouTube upload |

* **Single Source of Truth**: You never build a separate video project. Output A is the sole master; Output B reads the Base64 audio and `.mx-captions` JSON directly from the built HTML deck while recording live browser playback. Timing, wording, and visuals are guaranteed to match 100%.
* **How It Differs from `mathruffian-dot/soil-motion-deck`**: The original `soil-motion-deck` creates silent HyperFrames videos and slices them into `.pptx` slides for live teacher narration. Because decks in this course are HTML files inside a Teaching Cockpit—and students often review them independently without live teacher commentary—`soil-motion-html` builds spoken English narration directly into the HTML slides.
* ⚠️ **Important Note for AI-Assisted Translation Cockpit Native Tabs**: **Native tabs inside the AI-assisted Translation Teaching Cockpit (such as Project 1, Project 2, etc.) are not SOIL slide decks—do NOT run `build_motion.py` on them.** Instead, use the project-specific skill **`translation-cockpit-motion`** inside that course folder (which reuses this skill's `motion_engine.js` and `make_narration.py`, while handling native Cockpit injection locations, script ordering after the Cockpit's own scripts, and pausing/re-measuring height on tab switches).

---

## 2. Prerequisites & Installation

### 1. Python Packages
```bash
# Required for Output A (neural TTS audio + word-boundary timestamps)
pip install edge-tts

# Required for Output B (MP4 + SRT video rendering)
pip install playwright imageio-ffmpeg
```
* **No Extra Browser Download Needed**: `render_video.py` launches your locally installed Microsoft Edge (`--browser msedge`) or Google Chrome (`--browser chrome`), so running `playwright install` is **not** required.
* **Automatic FFmpeg Resolution**: Uses `ffmpeg` from your system `PATH` if available, or falls back automatically to the binary bundled with `imageio-ffmpeg`.

### 2. Installing the Skill into Claude Code / Cowork & AntiGravity
* **Windows (PowerShell)**:
  ```powershell
  git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
  powershell -ExecutionPolicy Bypass -File .\soil-motion-html-skill\install\install.ps1
  ```
* **macOS / Linux**:
  ```bash
  git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
  bash ./soil-motion-html-skill/install/install.sh
  ```

---

## 3. Anatomy of a Motion Spec Directory

For each presentation deck you animate, create a **spec directory** alongside your course slides (for example, `Week 7/slides/motion/gemini-skills-walkthrough/`):

```text
slides/motion/gemini-skills-walkthrough/
├── original.html      # Clean copy of the deck BEFORE any motion slides were added
├── manifest.json      # Declares motion slide IDs, slide numbers, durations, audio folders, and jump chips
├── slides.html        # HTML fragments headed by <!--SLIDE n-->, replacing content after </h2> (includes <!--CTRL name-->)
├── slides.css         # Custom styles specific to this deck's motion slides
├── configs.js         # One makeMotion(name, { end, acts, tracks }) timeline config per motion slide
├── s6/                # Narration assets for Slide 6
│   ├── segments.json  # Segmented script: [["Chip label", "N", "Spoken English text"], ...]
│   ├── narration.mp3  # Joined MP3 audio generated by make_narration.py
│   └── narration.json # Word-level timing data (WordBoundary) generated by make_narration.py
└── s8/                # Narration assets for Slide 8 ...
```

### Example `manifest.json`
```json
{
  "deck": "gemini-skills-walkthrough.html",
  "motions": [
    {
      "name": "g6",
      "slide": 6,
      "end": 47.6,
      "audio": "s6",
      "chips": [
        ["1 Write the prompt", 0],
        ["2 Send", 21.4],
        ["3 Check result", 37.46]
      ]
    }
  ]
}
```

---

## 4. Step 1: Selecting Candidate Slides (What to Animate vs. Keep Static)

Before writing any code, inspect all slides in the HTML deck (`python -I` with `sys.stdout.reconfigure(encoding="utf-8")` on Windows) and evaluate each slide:

### ✅ Great Candidates for Motion Slides (Where *change over time* is the core concept)
1. **UI / Workflow Walkthroughs**: Typing a prompt → clicking Send → viewing the AI reply, typing `/` to open a command menu, or clicking an OAuth permission button.
2. **Cause-and-Effect / Before-and-After Contrasts**: Buggy prompt rule → flawed output → fixing the rule → accurate output.
3. **Myth-Busting Flips**: Common misconception → stamping ❌ → revealing the evidence-based principle ✅.
4. **Cumulative Scoring or 1-to-1 Rubric Mapping**: Tallying rubric points step by step or connecting task requirements to grading rows one by one.

### ❌ Slides That Should Stay Static
* Cover slides, comparison tables, vocabulary lists, checklists, question banks, reference cards, and "Your Turn" hands-on instructions. Students need to read these at their own pace without waiting for a timeline.

> 📌 **User Confirmation First**: Always present a summary table classifying slides as **Great Fit / Possible / Keep Static** with a one-sentence description of the proposed animation, and let the user decide which slides to include (typically 2–4 slides per deck).

---

## 5. Step 2: Writing Segmented English Narration & Generating Word Timings (`make_narration.py`)

### 1. Narration Guidelines
* **Always Spoken English**: Default to spoken English narration even for Review decks—never assume the instructor will narrate live in class.
* **Two Built-In Voice Roles**:
  * `"N"` (Narrator): `en-US-JennyNeural` at `-6%` speaking rate.
  * `"A"` (App / Secondary Voice, e.g., an app reading a sample sentence aloud): `en-GB-RyanNeural`.
* **Pacing & Level**: Aim for **30–70 seconds** per slide divided into **4–7 segments**. Use clear, short **B1-level** English sentences where each segment corresponds to one visual beat.
* **Cite Scholars by Name**: When referencing SLA or pedagogical theories, name the scholars explicitly (`Lyster & Ranta`, `Swain`, `Schmidt`, etc.) for consistency with the rest of the course.

### 2. Running `make_narration.py`
Create `<spec>/s6/segments.json`:
```json
[
  ["1 Write the prompt", "N", "First, let's look at how we write the system instructions."],
  ["2 App demo", "A", "Could you please reschedule our meeting to Thursday?"],
  ["3 Check feedback", "N", "Notice how the feedback highlights both the polite modal and the reason."]
]
```
Run the generator:
```bash
python ~/.claude/skills/soil-motion-html/scripts/make_narration.py "<spec>/s6/segments.json" "<spec>/s6"
```
The script writes `narration.mp3` and `narration.json` into `<spec>/s6/` and prints every word with its timestamp in seconds (e.g., `highlights@12.84`), which you will use to anchor visual actions in Step 4.

---

## 6. Steps 3 & 4: Designing Motion Slide Layouts (`slides.html` / `slides.css`) & Choreography (`configs.js`)

### 1. Layout Rules (`slides.html` + `slides.css`)
* **Preserve the Slide's `<h2>` Heading**: Each `<!--SLIDE n-->` block in `slides.html` replaces the content *after* `</h2>` inside `<div class="slide-inner">`.
* **Two-Column Structure (Wrap Both Columns in `.mx-stage`)**:
  * **Left Column**: Step-by-step explanation cards or bullets with unique `id`s (highlighted with `.on` as the narrator reaches each step).
  * **Right Column**: A **fixed-height** demonstration window (`.win`) so chat bubbles, code blocks, or score cards appear without shifting the outer frame.
  * ⚠️ **`.mx-stage` Scope**: Because `makeMotion`'s `$` helper queries inside `.mx-stage` only, **`.mx-stage` must wrap both the left and right columns** whenever left-column step items need `.on` highlighting.
* **Sub-Labels Under Word Tokens (Normal Flow, Not Absolute Positioning)**:
  * Never use `position: absolute` for small sub-labels beneath words (such as `HEAD` or `STRONG VERB 強動詞`). When a label is wider than the word itself, absolute positioning causes line wraps and text overlap. Place sub-labels in normal flow beneath the word (`white-space: nowrap`, reserving one line of height) and verify label-to-word alignment during layout checks.
* **Self-Explanatory Visuals**: Every key number, label, and takeaway must be visible on screen so the slide makes complete sense even with `🔇 Voice off`.
* **Player Control Placeholder**: Place `<!--CTRL name-->` where the control bar belongs. `build_motion.py` replaces it with `▶ Play`, `⟲ Replay`, `🔊 Voice on`, chapter chips, progress bar, timer, Base64 `<audio>`, and `<script type="application/json" class="mx-captions">`.
* **Flag AI-Supplied Examples**: Use real classroom artifacts whenever available. If you invent sample data (e.g., a simulated Gemini response or sample score), label it `Example …` on screen and list every invented item for user verification at delivery.

### 2. Timeline Configuration (`configs.js`)
```javascript
makeMotion('g8', {
  end: 29.9,
  acts: ({ $, cls, text, html }) => [
    [3.72, () => { cls('#g8L2', 'on'); text('#g8Txt', '/'); }], // exact word timestamp for "slash"
    [5.32, () => cls('#g8Menu', 'show')],
  ],
  tracks: ({ $ }) => [
    [12.58, 19.0, p => typeInto($('#g8Txt'), PROMPT_TEXT, p)]
  ]
});
```
* **`acts` (Discrete Actions)**: Array of `[timestamp_sec, callback]`. Always copy timestamps directly from the word timings in `narration.json`.
  * ⚠️ **Idempotency Rule**: When seeking (`seek(t)`), the engine resets `stage.innerHTML = INIT` and replays all actions from `0` up to `t` with CSS transitions disabled (`.mx-instant`). Actions must only mutate classes or text (`cls`, `text`, `html`) and never rely on external mutable state.
* **`tracks` (Continuous Interpolations)**: Array of `[start_sec, end_sec, progress_fn]`, where `p` runs from `0` to `1`. Built-in helpers include `typeInto(el, text, p)` and `pressEl(el)`.
* **`end` (Total Duration)**: Set to `narration.json`'s `total` duration plus `0.5–1.0` seconds of tail padding.
* **Shared CSS Utilities (`templates/motion.css`)**:
  * `.mx-fold` + `.show`: Smooth accordion reveal (`max-height` and `opacity`).
  * `.mx-fade` + `.show`: Smooth fade-in + subtle upward translation.
  * `.mx-stamp` + `.no` / `.ok`: Pill-shaped status stamps (red ❌ or green/accent ✅).
  * `.mx-caret`: Blinking typing cursor.

---

## 7. Step 5: Building a Trial Deck (`build_motion.py`) & Automated Layout Verification (`check_motion.js`)

### 1. Build a Trial Copy First
```bash
python ~/.claude/skills/soil-motion-html/scripts/build_motion.py "<spec>" "<deck>_motion_trial.html"
```
Never overwrite the production deck or Teaching Cockpit before the user has listened to and approved the trial build.

### 2. Automated Browser Verification (`check_motion.js`)
1. **Serve Over HTTP**: Because inlined Base64 audio pushes deck sizes past ~500 KB, serve the trial file over HTTP (e.g., port 8765) rather than `file://`.
2. **Paste `scripts/check_motion.js` and Run `mxReport()`**:
   * At **`1366×768`**, verify that `fit(over/top)` starts with **`0/`** at every sampled second (zero vertical scroll), `stage` reports a single constant height (confirming `reserve()` locked in the maximum timeline height so the slide title never jumps), and `clip` reports **`ok`** (no internal overflow inside `.gx-body`, `.mx-body`, or `.win-body`).
3. **Check Mobile & Compact Viewports (`390×844`, `844×390`, `932×430`)**:
   * Vertical scrolling is allowed on small screens, but the second number in `fit(over/top)` must not be smaller than the top bar height, and `HSCROLL` must never appear.
   * Always run `window.dispatchEvent(new Event('resize'))` after resizing a headless or hidden preview pane.
4. **Spot-Check Key Moments with `mxStates(name, t, selectors)`**.
5. **User Audio Review**: Deliver the trial file link, duration table, full narration script, and list of `Example …` items for the user to listen to in their own browser.

---

## 8. Step 6: Deploying to Teaching Cockpit, Claude Artifact, and Firebase Hosting

Once the user approves the audio and visuals:
1. Create a Git checkpoint commit in the course repository.
2. Copy `<deck>_motion_trial.html` over the production deck file and bump the `?v=` version query parameter in the Teaching Cockpit HTML.
3. Follow the `teaching-cockpit-builder` workflow to re-bundle `window.DECK_B64` for the standalone Claude Artifact (note: Base64 audio adds ~480 KB per minute of narration; keep total Artifact size under 16 MB) and deploy to Firebase Hosting (`Firebase/public/weekN/`).
4. Verify the live deployment by comparing SHA-256 hashes (`fetch(url, {cache: 'no-store'})`), commit to Git, and log the deployment in `handoff.md`.

---

## 9. Step 7: Rendering Output B — MP4 Explainer Videos + SRT Subtitles (`render_video.py`)

```bash
# Render all motion slides in the built deck and concatenate them into all.mp4
python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<built_deck>.html" "<out_dir>" --join all.mp4

# Render specific motion slides with burned-in subtitles
python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<built_deck>.html" "<out_dir>" --motion g6 --motion g8 --burn
```

* **How It Works**: Playwright launches your installed Edge/Chrome (`--browser msedge` or `chrome`), navigates to each motion slide, hides player chrome (`#footer-shell, #hint, .mx-ctrl`), and captures event-driven JPEG frames via CDP `Page.startScreencast` while the slide plays in real time. `ffmpeg` then combines the held frames, raw MP3 narration, and auto-chunked `.srt` captions into a 1280×720 H.264/AAC MP4.
* **Spot-Checking Frames**: Extract a few frames with `ffmpeg -ss <sec> -i <clip.mp4> -frames:v 1 frame.jpg` to verify visual and subtitle alignment.

---

## 10. Step 8: Updating & Maintaining Deployed Motion Slides

* **Never edit compiled motion code directly inside the production HTML deck.**
* Instead, always edit the source files inside the `spec/` directory (`slides/motion/<deck>/`):
  1. Update `segments.json`, `slides.html`, `slides.css`, or `configs.js`.
  2. If `segments.json` changed, re-run `make_narration.py` and **re-anchor all `acts` timestamps in `configs.js`** to the new word timings.
  3. Run `build_motion.py` (which always compiles fresh from `original.html`), verify with `check_motion.js`, and deploy.

---

## 11. Troubleshooting & 30 Battle-Tested Engineering Lessons

See [`references/lessons.md`](../references/lessons.md) for the complete engineering log. Key highlights include:

1. **Audio Clock as Master Timer**: While narration is playing (even when muted), `audio.currentTime` drives the animation clock `t` so visuals never drift from speech; once the audio finishes, the engine seamlessly switches to `performance.now()` until `end`.
2. **Guarding Against `NaN` Audio Duration on First Play**: Before metadata finishes loading, `audio.duration` may be `NaN`. Always test `if (!(t >= audio.duration))` rather than `if (t < (audio.duration || 0))` so pressing Play immediately starts audio playback.
3. **Preventing Vertical Layout Shifts (`reserve()`)**: Because SOIL slides vertically center `.slide-inner`, expanding an `.mx-fold` card would normally push the slide title upward by 30–40 px. On load and width changes, `reserve()` steps through the timeline every 1.5 seconds, measures the tallest `.mx-stage` height, and locks it in via `min-height`.
4. **Dense Clipping Checks (`mxClip`)**: Sampling every 1–2 seconds catches transient overflow peaks (such as two hint cards + a Listen button appearing simultaneously at `t = 36s`) that 4-second intervals miss. Collapse earlier hints when revealing final answers to stay within the 1366×768 vertical budget.
5. **Windows Drive-Colon Workaround for FFmpeg Subtitles**: FFmpeg's `subtitles=` filter chokes on Windows drive letters (`C:\...`). `render_video.py` runs `ffmpeg` with `cwd=tmp` and passes a relative filename (`subs.srt`) to avoid path escaping failures.
6. **Native Tabs in Teaching Cockpits (Lessons #28–#30)**:
   * Teaching Cockpit native tabs (e.g., Project 1 / Project 2 in AI-assisted Translation) are not SOIL slide decks—do not use `build_motion.py`; use the course's `translation-cockpit-motion` skill instead.
   * `makeMotion`'s `$` only queries inside `.mx-stage`; wrap both the left and right columns inside `.mx-stage` if left-column steps also highlight during playback.
   * Keep sub-labels under word tokens (`HEAD`, `STRONG VERB`) in normal flow (`white-space: nowrap` with a reserved line height) rather than `position: absolute` so wider labels never wrap or overlap the word.

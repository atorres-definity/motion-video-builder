---
name: motion-video-builder
description: Build narrated, animated slide and motion-graphics videos from a style guide, sync them to a voice-over, and export them as an MP4 or a PNG sequence (with alpha). Use this skill whenever the user wants to animate slides, screens or designs, make a tutorial, explainer or course video from slides plus narration (audio or video file), sync text animations to a voice-over or timestamps, build motion graphics or lower thirds with transparency for compositing, or render/export an animation as video or image frames — even if they don't say "skill" or "motion graphics".
compatibility: Built for Cowork and Claude Code (local files, long renders). Needs ffmpeg, Python 3, Playwright + Chromium; faster-whisper (or openai-whisper) for transcription. Run scripts/check_env.py first.
---

# Motion video builder

Turns a style guide + content + narration into an animated video, in six phases.
**Every phase ends with the user's approval before the next one starts.** Never skip
the static review: animating unapproved slides wastes the most time.

```
1 Style intake → 2 Brief → 3 Narration & cues → 4 Static review → 5 Animated preview & refine → 6 Export
```

## Phase 0 — Environment check (silent unless something is missing)

Run `python scripts/check_env.py`. If something is missing, show the user the install
commands it prints and ask before installing. If transcription can't be installed,
continue: Phase 3 can use an SRT/VTT, a timestamp list from the user, or no narration.

## Working folder

Follow the project's own folder and naming conventions if it has them (look for
project instructions, a README, or existing video folders). Otherwise create:

```
<video-folder>/
  style-sheet.md        Phase 1 output (or a pointer to the project's style files)
  brief.md              Phase 2 output
  audio/narration.mp3   Phase 3 (extracted or copied)
  script.md             Phase 3 output: script by slide + cue sheet
  animation.html        Phases 4–5: the one source file (static deck = ?deck)
  assets/               images, cut-outs, fonts, logos
  render/frames/        Phase 6 frames (temporary)
  export/               Phase 6 deliverables
```

Big changes → duplicate the file first (`animation v2.html`) so the previous version survives.
Small changes → change only that; don't "improve" anything else.

## Phase 1 — Style intake

Ask for style guidelines in any form: an .md file, a brand skill, a reference video or
screenshots, an existing project, or a short prompt. Read everything given, then write
`style-sheet.md` (template inside `references/motion-defaults.md` → "Style sheet template")
with: palette (exact hexes), fonts + how they load, minimum text size, logo files and
placement, recurring layouts, and any motion rules.

- Never invent brand values. If a hex, font file or logo is missing, ask.
- **Never invent visual elements.** Use only what the design system or references show.
  No decorative lines/rules above or under titles, accent bars, dividers, eyebrows, numbering,
  icons, shapes, gradients or shadows unless they appear in the client's material. If a
  layout seems to need something the guide doesn't have, ask; otherwise keep it plain.
  The example slides and styles in `assets/engine.html` are placeholders — never carry them
  over (they are not this client's style).
- Fonts must load from **local files** (`@font-face` with `url(assets/fonts/...)`) or a
  source that works from a `file://` page. Web font kits (Typekit etc.) are often locked to
  domains and silently fall back during render. If only a kit is available, test it in
  Phase 4; if it fails, ask the user for the font files.
- Confirm the style sheet with the user in a few lines, not a wall of text.

## Phase 2 — Brief: what to animate, how, and the output

Ask (group into one message, or use a multiple-choice tool if available):

1. **Content** — what gets animated: slides/screens/designs (screenshots, PDF, Figma
   exports, a deck), numbered files to set order (`01.png`, `02.png`…), or a text outline.
   Copy must match the reference **word for word**; if copy is missing, ask.
2. **Format** — resolution (default 1920×1080), fps (default 30), approximate length.
3. **Slide transitions** — always ask; never pick for the user. First give them
   `assets/transitions-demo.html` (copied into the video folder, with its color/font tokens
   set from the style sheet so the examples look like their brand) so they can see each one.
   Then ask as a **multi-select** (use the multiple-choice tool with multi-select if
   available; otherwise a numbered list they answer with numbers):
   1 Cross-fade · 2 Cut · 3 Push · 4 Slide over · 5 Reveal · 6 Rise · 7 Dip to color · 8 Color wipe
   (one-line descriptions are in `references/motion-defaults.md` → "Slide transitions").
   - One picked → it's used for every slide change.
   - Several picked → ask which one is the **default** between slides, and where each other
     one goes (section changes, the first/last slide, specific slides).
   - Use **only** the transitions they picked, exactly where they said. Never add others.
   - For direction-based ones (push, slide over, reveal) ask the direction only if it matters
     to them; default is left (new slide enters from the right).
4. **Text/element animation** — anything specific? If not, propose the defaults in
   `references/motion-defaults.md` in two or three sentences.
5. **Output** — MP4 or PNG sequence. Ask now, not at the end, because transparency changes
   the design. **If the user needs transparency/alpha (overlays, lower thirds, titles to
   composite in an editor), recommend the PNG sequence** — MP4 (H.264) can't carry alpha.
   With alpha: no slide backgrounds, design for the footage it will sit on, and check
   legibility on both light and dark plates.

Save the answers to `brief.md`, including a **Transitions** section: default, others and where each goes.

## Phase 3 — Narration → script and cue sheet

Accept narration as **an audio file or a video file** (MP3, WAV, M4A, MP4, MOV… any size;
large source videos like 4K masters are fine).

```
python scripts/transcribe.py <file> --out-dir <video-folder>
```

It extracts/normalizes the audio to `audio/narration.mp3` (that file is used in the
preview and the export), transcribes with word timestamps, and writes
`transcript.md` + `words.json`. If an `.srt`/`.vtt` is supplied instead, it parses that.

Then Claude writes `script.md` (format in `references/timing.md`):
- the script split by slide, each section headed with the second the narrator starts that topic;
- a **cue sheet**: time · slide · what appears, one row per animated element.

Correct names and numbers to the slide spelling and flag anything uncertain. Ask the user
to check the script before Phase 4 if the transcript had obvious errors.

No narration? Time from the brief: a target duration, the user's timestamp list, music
beats, or reading pace (see `references/timing.md`).

## Phase 4 — Static review

Copy `assets/engine.html` to `<video-folder>/animation.html`. **Delete the example slides and
example styles**, fill the token block from the style sheet, and build each slide only from the
client's design system and references, in a `<section class="slide">`. Put every animated
element's `data-cue` (from the cue sheet, or a placeholder if timing isn't ready).
Set `CONFIG.defaultTransition` to the default from `brief.md` and put `data-transition` only on
the slides the brief names for another transition.

**How to present the review (always the same way):**
- Give the user `animation.html?deck` to open in their browser: **one slide per screen**,
  ←/→ to move, `G` for a grid overview, `#3` in the URL jumps to slide 3. Name the file
  path and the slide count in one line.
- If they want images (to share, or because they can't open the HTML), render **one PNG
  per slide**: `python scripts/render_frames.py animation.html --stills <video-folder>/review`.
- **Never** combine slides into a single image or contact sheet, and never show only
  thumbnails; text must be reviewable at full size.

Feedback comes back numbered by slide ("slide 6: …"); change only what was noted.

Iterate on layout and copy until the user approves. No animation work before approval.

## Phase 5 — Animated preview and refine

Open `animation.html` in the browser (preview mode): narration plays in sync, scrubber,
Space = play/pause, ←/→ = 1 s, Shift+←/→ = 5 s, `,` `.` = one frame, the time readout
shows `m:ss.ss` and the current slide.

- Every cue is **absolute narration time in seconds**.
- Corrections arrive as `m:ss → element`. Convert to seconds, change that cue only,
  update the cue sheet in `script.md` to match.
- Use only the motion vocabulary in the style sheet / `references/motion-defaults.md`
  unless the user asks for something new; custom animations go in `window.CUSTOM_ANIMS`.

## Phase 6 — Export

Read `references/export.md` first. In short:

```
python scripts/render_frames.py animation.html --out render/frames [--alpha]
python scripts/encode.py mp4 --frames render/frames --audio audio/narration.mp3 --out "export/<name> vN.mp4"
python scripts/encode.py png --frames render/frames --audio audio/narration.mp3 --out "export/<name> vN PNG.zip"
```

- **MP4**: H.264, yuv420p, narration included. Default deliverable. One file, no extra
  no-audio copy unless asked.
- **PNG sequence**: RGBA frames (with `--alpha`), zipped with the narration as WAV and a
  README (fps, resolution, frame count). Recommended whenever transparency is needed.
- Render aborts if a declared font didn't load — fix fonts, don't ship fallbacks.
- Before delivering: verify duration with ffprobe, spot-check frames at 3–4 cue times,
  and confirm the audio lines up with the first and last cues.

Deliver: the file path(s) + one short line on what's in them. Keep answers short.

## Reference files

- `references/motion-defaults.md` — default motion vocabulary, rules, style sheet template, alpha design notes.
- `references/timing.md` — script.md format, cue rules, correction protocol, timing without narration.
- `references/export.md` — MP4 vs PNG sequence, render settings, checks, troubleshooting.
- `assets/engine.html` — the animation engine template (preview / deck / render modes).
- `assets/transitions-demo.html` — looping examples of every slide transition, shown in Phase 2.
- `assets/script-template.md` — empty script + cue sheet.

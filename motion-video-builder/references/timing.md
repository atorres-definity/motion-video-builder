# Timing

## Cue rules

- Every cue is an **absolute time in seconds** on the narration (`data-cue="102.4"`).
- **Slide start** = the second the narrator begins that topic (usually the first word of
  the section, sometimes the last word of the previous sentence when it leads in).
- **Element cue** = the start time of the word that introduces it (from `words.json`).
  Subtract ~0.1 s if it feels late; never more than 0.3 s early.
- Wipes are centered on the slide start (half before, half after).
- The last slide (sign-off) runs to the end of the audio; set `CONFIG.duration` if the
  video must be longer than the narration.

## script.md format

```markdown
# Video NN — <Title>: narration script & timings

Source: `audio/narration.mp3` (m:ss). Transcribed automatically; names corrected to slide spelling.
Check names and numbers before treating as final.

## 0:00 — 01 Cover
<narration for this slide, verbatim>

## 0:12 — 02 <Slide name>
<narration>

## Cue sheet
| Time | Slide | What appears |
|---|---|---|
| 0:00 | 01 Cover | Logos, eyebrow, title, subtitle |
| 0:28 / 0:32 | 02 | Item 1 / Item 2 |
```

Times in the script are `m:ss` for people; the HTML uses seconds (`0:28.4` → `28.4`).

## Correction protocol

The user sends `m:ss → element` (e.g. `1:44 "Price is what you pay"`):
1. Convert to seconds (`1:44` → `104`). If they give `m:ss.s`, keep the decimal.
2. Find that element, change only its `data-cue` (or the slide's `data-start`).
3. Update the matching cue-sheet row in `script.md`.
4. Reply with what changed, one line per correction.

If a correction would make an element appear before its slide starts, or after the next
slide starts, say so instead of applying it.

## Timing without narration

- **Duration given** → split proportionally by word count per slide, minimum 3 s per slide.
- **Reading pace** → ~3 words/s for on-screen text + 1 s hold, min 2.5 s per slide.
- **Music** → ask for BPM or detect beats (`ffmpeg`/`librosa` if available); cue on beats,
  slide changes on bar downbeats.
- **User timestamps** → use them as-is.

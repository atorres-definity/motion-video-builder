# Export

## Which format

| Need | Deliver | Why |
|---|---|---|
| Finished video to publish/upload | **MP4** (H.264 + AAC) | One file, plays everywhere |
| Transparency / alpha (overlays, lower thirds, titles over footage) | **PNG sequence** (RGBA) + WAV | MP4 can't carry alpha; every editor imports PNG sequences |
| Alpha but the editor needs a single file | ProRes 4444 `.mov` (`encode.py prores`) | Only if the user asks; files are very large |
| Editor wants to re-time or grade | PNG sequence without alpha | Lossless frames |

If the user asks for "MP4 with transparency", explain in one sentence that MP4 can't do
it and recommend the PNG sequence.

## Steps

1. **Render frames**
   ```
   python scripts/render_frames.py animation.html --out render/frames [--alpha] [--workers 4]
   ```
   - Duration: `--duration` > `CONFIG.duration` > length of `CONFIG.audio` (ffprobe) > last slide + 4 s.
   - `--start/--end` (seconds) re-render part of the timeline; `--resume` skips existing frames.
   - Aborts if a font in `CONFIG.fonts` didn't load. Fix fonts; never ship fallbacks.
   - Frames are `000000.png`, frame *i* = time *i/fps*.

2. **Encode**
   ```
   python scripts/encode.py mp4 --frames render/frames --audio audio/narration.mp3 --out "export/<name> vN.mp4"
   python scripts/encode.py png --frames render/frames --audio audio/narration.mp3 --out "export/<name> vN PNG.zip"
   python scripts/encode.py prores --frames render/frames --audio audio/narration.mp3 --out "export/<name> vN.mov"
   ```
   fps is read from `render/frames/render.json` (written by the renderer).

3. **Check before delivering**
   - `ffprobe` duration matches the audio (±1 frame) and resolution/fps are right.
   - Pull 3–4 frames at cue times and look at them (fonts, positions, nothing clipped).
   - Audio sync: first cue and last cue land on their words.
   - PNG: first frame is RGBA (`encode.py` reports it) when alpha was requested.

4. **Deliver** the file path + one line. Delete `render/frames` only if the user agrees.

## Settings used

- MP4: libx264, `-crf 18 -preset slow -pix_fmt yuv420p -movflags +faststart`, AAC 192k, 48 kHz.
- PNG zip: frames stored (no recompression), `narration.wav` 48 kHz 16-bit, `README.txt`.
- ProRes: `prores_ks -profile:v 4444 -pix_fmt yuva444p10le`, PCM audio.

## Troubleshooting

- **Text looks different from the preview** → a font fell back; check `missingFonts` in
  `render.json`; load fonts from local files.
- **Frame shows a half-finished state that the preview didn't** → an animation uses CSS
  transitions or timers; rewrite it as a function of time in `window.CUSTOM_ANIMS`.
- **Render is slow** → raise `--workers` (one Chromium page each); with 4 workers expect roughly
  2 minutes of rendering per minute of 1080p30 video (heavier slides take longer).
- **Audio drift** → frames are time-exact; check the narration's real duration with ffprobe
  and that the cue times came from that same file (not the original video).

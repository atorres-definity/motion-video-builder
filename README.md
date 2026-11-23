# motion-video-builder

A Claude skill for building narrated, animated slide and motion-graphics videos from a style guide, synced to a voice-over, and exported as an **MP4** or a **PNG sequence** (with alpha).

## Workflow

1. **Style intake** — design system, brand file, references or a prompt → `style-sheet.md`
2. **Brief** — content, format, slide transitions (multi-select from a live demo), element animation, output type
3. **Narration** — audio or video file → narration track, word-timestamped transcript, script + cue sheet
4. **Static review** — one slide per screen (`animation.html?deck`), approved before any animation
5. **Animated preview** — synced to the narration; corrections as `m:ss → element`
6. **Export** — MP4 (H.264 + narration) or PNG sequence (RGBA + WAV); ProRes 4444 on request

## Contents

```
motion-video-builder/
├── SKILL.md
├── references/   motion-defaults.md · timing.md · export.md
├── scripts/      check_env.py · transcribe.py · render_frames.py · encode.py
└── assets/       engine.html · transitions-demo.html · script-template.md
```

## Requirements

Built for Claude Cowork and Claude Code. Needs ffmpeg, Python 3, Playwright + Chromium, and faster-whisper (optional, for transcription). Run `python motion-video-builder/scripts/check_env.py` to check.

## Install

- **Claude (Cowork / claude.ai):** zip the `motion-video-builder` folder and upload it under Settings → Capabilities → Skills.
- **Claude Code:** copy the `motion-video-builder` folder into `~/.claude/skills/` (personal) or `.claude/skills/` in a project.

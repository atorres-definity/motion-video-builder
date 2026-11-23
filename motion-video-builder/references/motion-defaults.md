# Motion defaults

Use these when the user has no specific animation style. Project style sheets override them.

## Element animation vocabulary (engine names in `code`)

| Name | What it does | Default duration | Use for |
|---|---|---|---|
| `rise` | fade in + move up 28px, ease-out | 0.7 s | Default for every text line, card, list item |
| `fade` | fade in only | 0.7 s | Photos, logos, backgrounds, large images |
| `draw` | SVG stroke draws on (`path`, `line`, `polyline`) | 1.2 s | Chart lines and arrows that exist in the design |
| `reveal` | clip reveal left → right | 0.8 s | Bars or shapes that exist in the design |
| `pop` | fade + scale 0.92 → 1 | 0.5 s | Small badges, pills, icons (use sparingly) |
| `none` | hard cut on | — | Elements that must appear exactly on a word |
| `data-out` | fade out at a time | 0.5 s | Removing something mid-slide |

## Slide transitions

Always chosen by the user in Phase 2 (multi-select). Never default to one silently.

| # | Name (`data-transition`) | What it looks like | Duration | Fits |
|---|---|---|---|---|
| 1 | Cross-fade (`fade`) | New slide fades in over the old | 0.7 s | Almost any brand; calm, neutral |
| 2 | Cut (`cut`) | Instant change | — | Fast, editorial; lets text motion carry it |
| 3 | Push (`push`) | New slide pushes the old one off to the side | 0.8 s | Step-by-step stories, sequences |
| 4 | Slide over (`slide-over`) | New slide slides in on top; old one stays still | 0.8 s | Card-like, app-like looks |
| 5 | Reveal (`reveal`) | New slide uncovered edge to edge | 0.8 s | Clean, graphic brands |
| 6 | Rise (`rise`) | New slide fades in moving up slightly | 0.7 s | Matches text rise-ins; soft |
| 7 | Dip to color (`dip`) | Fade to a solid color, then into the next | 1.0 s | Chapter breaks, serious topics |
| 8 | Color wipe (`wipe`) | Brand-color bar sweeps across | 0.9 s | Energetic; best only at section changes |

- `CONFIG.defaultTransition` = the user's default; `data-transition` on a slide only where the
  brief says so. The first slide is a cut unless it has `data-transition` set.
- Direction for push / slide over / reveal: `data-dir="left|right|up|down"` (default `left`:
  the new slide enters from the right). Per-slide duration: `data-transition-dur`.
- Dip color: `CONFIG.dipColor`; wipe color: `CONFIG.wipeColor` (or `--wipe-color`). Use brand colors.
- The wipe is centered on the slide start (half before, half after); the others start at it.

Element animation durations can be overridden per element with `data-dur="1.2"`.

## Rules

- Animate only elements that exist in the approved design. Never add decorative elements
  (lines over titles, accent bars, dividers, shapes) to have something to animate.
- Text appears **when the narrator says it**, not before.
- No zoom / Ken Burns on slides with text — it makes text shimmer when rendered.
- No "karaoke" dimmed text; quotes and sentences appear whole.
- One idea per slide; max ~2 same-color backgrounds in a row, alternate light/dark for rhythm.
- Minimum text size 24px at 1080p (scale proportionally for other sizes).
- Stagger list items by the narration, not by a fixed interval.
- When an eyebrow/title is the main point of a moment, it may start large and centered, then
  move to its place before the content appears (write it as a custom animation).

## Custom animations

Add to `window.CUSTOM_ANIMS` (block above the engine in `animation.html`). Signature:
`(el, p, t) => {}` where `p` is 0→1 progress (already clamped) and `t` absolute time.
Default durations go in `window.CUSTOM_DURATIONS`. Use with `data-anim="name"`. Animations must be pure functions of time (no CSS transitions,
no setTimeout) or the render will not match the preview.

## Alpha (transparent) output

- No slide backgrounds; the engine renders `?alpha` with a transparent stage.
- Text needs to read on any plate: use shadows/backing shapes from the style guide, or ask.
- Transitions between slides cross-fade both ways (out + in) in alpha mode so nothing
  doubles up.
- Preview on both a light and a dark plate before export (the deck shows a checkerboard
  toggle via `?deck&alpha`).

## Style sheet template

```markdown
# Style sheet — <project>
Source: <files/links the user gave>

## Palette
| Token | Hex | Use |
|---|---|---|

## Type
- Display: <family, weight> — loaded from <assets/fonts/... or URL>
- Body/UI: <family, weights>
- Min size: 24px @1080p

## Logos & recurring elements
- <file> — <where/when>

## Layouts
| Type | Background | Notes |
|---|---|---|

## Motion
- <project rules; or "defaults from motion-defaults.md">

## Never
- <things the brand forbids>
```

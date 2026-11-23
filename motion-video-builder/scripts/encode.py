#!/usr/bin/env python3
"""
Frames -> deliverable.

  python encode.py mp4    --frames render/frames --audio audio/narration.mp3 --out "export/Name v1.mp4"
  python encode.py png    --frames render/frames --audio audio/narration.mp3 --out "export/Name v1 PNG.zip"
  python encode.py prores --frames render/frames --audio audio/narration.mp3 --out "export/Name v1.mov"

fps comes from render.json in the frames folder (override with --fps). --audio is optional.
"""
import argparse, json, subprocess, sys, tempfile, zipfile
from pathlib import Path


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-2500:]}")
    return r.stdout


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration", "-of", "json", str(path)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("format", choices=["mp4", "png", "prores"])
    ap.add_argument("--frames", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float)
    ap.add_argument("--crf", type=int, default=18)
    a = ap.parse_args()

    fr = Path(a.frames)
    files = sorted(fr.glob("[0-9][0-9][0-9][0-9][0-9][0-9].png"))
    if not files:
        sys.exit(f"No frames in {fr}")
    meta = json.loads((fr / "render.json").read_text()) if (fr / "render.json").exists() else {}
    fps = a.fps or meta.get("fps") or 30
    first, last = int(files[0].stem), int(files[-1].stem)
    if last - first + 1 != len(files):
        missing = sorted(set(range(first, last + 1)) - {int(f.stem) for f in files})
        sys.exit(f"Missing frames (e.g. {missing[:10]}). Re-render with --resume.")
    n = len(files)
    dur = n / fps
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)

    pix = probe(files[0])["streams"][0].get("pix_fmt", "?")
    has_alpha = "a" in pix.replace("gray", "")  # rgba, ya8, etc.
    print(f"{n} frames · {fps} fps · {dur:.2f}s · first frame {pix}{' (alpha)' if has_alpha else ''}")

    inp = ["-framerate", str(fps), "-start_number", str(first), "-i", str(fr / "%06d.png")]
    aud = ["-i", a.audio] if a.audio else []
    maps = ["-map", "0:v"] + (["-map", "1:a"] if a.audio else [])

    if a.format == "mp4":
        if has_alpha:
            print("note: MP4 can't hold transparency — alpha is flattened. Use `png` for alpha.")
        run(["ffmpeg", "-y", "-v", "error", *inp, *aud, *maps, "-c:v", "libx264", "-preset", "slow",
             "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-r", str(fps),
             *(["-c:a", "aac", "-b:a", "192k", "-ar", "48000"] if a.audio else []),
             "-t", f"{dur:.4f}", "-movflags", "+faststart", str(out)])

    elif a.format == "prores":
        run(["ffmpeg", "-y", "-v", "error", *inp, *aud, *maps, "-c:v", "prores_ks", "-profile:v", "4444",
             "-pix_fmt", "yuva444p10le" if has_alpha else "yuv444p10le", "-vendor", "apl0",
             *(["-c:a", "pcm_s16le", "-ar", "48000"] if a.audio else []), "-t", f"{dur:.4f}", str(out)])

    else:  # png sequence zip
        stem = out.stem
        with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
            for i, f in enumerate(files):
                z.write(f, f"{stem}/frames/{stem}_{i:06d}.png")
            if a.audio:
                wav = Path(td) / "narration.wav"
                run(["ffmpeg", "-y", "-v", "error", "-i", a.audio, "-t", f"{dur:.4f}", "-ar", "48000",
                     "-ac", "2", "-c:a", "pcm_s16le", str(wav)])
                z.write(wav, f"{stem}/narration.wav")
            w, h = meta.get("width", "?"), meta.get("height", "?")
            z.writestr(f"{stem}/README.txt",
                f"{stem}\n\nPNG sequence · {w}x{h} · {fps} fps · {n} frames · {dur:.2f} s\n"
                f"Pixel format: {pix} ({'transparent background / alpha' if has_alpha else 'no alpha'})\n"
                f"Frames: frames/{stem}_000000.png … (frame 0 = 00:00:00:00)\n"
                + ("Audio: narration.wav (48 kHz, 16-bit), starts at frame 0\n" if a.audio else "")
                + "\nImport as an image sequence at the fps above (Premiere: Import > Image Sequence;\n"
                  "Resolve: select the first frame; After Effects: PNG Sequence, interpret at the fps above).\n")
        print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
        return

    j = probe(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    print(f"Wrote {out} · {v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']} {v.get('pix_fmt')} · "
          f"{float(j['format']['duration']):.2f}s · audio: {'yes' if any(s['codec_type']=='audio' for s in j['streams']) else 'no'}")


if __name__ == "__main__":
    main()

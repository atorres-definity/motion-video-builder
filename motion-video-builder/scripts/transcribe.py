#!/usr/bin/env python3
"""
Narration (audio OR video file, any size) -> audio/narration.mp3 + words.json + transcript.md

  python transcribe.py <input> --out-dir <video-folder> [--model small] [--language en]

Also accepts .srt / .vtt (no word timestamps; segments only).
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration",
               "-of", "json", str(path)])
    j = json.loads(out)
    kinds = {s["codec_type"] for s in j.get("streams", [])}
    return kinds, float(j.get("format", {}).get("duration", 0) or 0)


def fmt(t):
    m = int(t // 60)
    return f"{m}:{t - m * 60:05.2f}"


def parse_subs(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    ts = r"(\d+):(\d{2}):(\d{2})[,.](\d{3})|(\d{1,2}):(\d{2})[,.](\d{3})"
    def sec(m):
        if m.group(1) is not None:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
        return int(m.group(5)) * 60 + int(m.group(6)) + int(m.group(7)) / 1000
    segs = []
    for block in re.split(r"\n\s*\n", text.replace("\r", "")):
        lines = [l for l in block.split("\n") if l.strip()]
        for i, l in enumerate(lines):
            if "-->" in l:
                a, b = l.split("-->")
                ma, mb = re.search(ts, a), re.search(ts, b)
                if ma and mb:
                    body = " ".join(re.sub(r"<[^>]+>", "", x) for x in lines[i + 1:]).strip()
                    if body:
                        segs.append({"start": sec(ma), "end": sec(mb), "text": body})
                break
    return segs


def transcribe(wav, model_name, language):
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="auto", compute_type="int8")
        it, _ = model.transcribe(str(wav), word_timestamps=True, language=language)
        segs, words = [], []
        for s in it:
            segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
            words += [{"start": w.start, "end": w.end, "word": w.word.strip()} for w in (s.words or [])]
            print(f"  {fmt(s.start)}  {s.text.strip()[:70]}", flush=True)
        return segs, words, "faster-whisper " + model_name
    except ImportError:
        pass
    try:
        import whisper
        model = whisper.load_model(model_name)
        r = model.transcribe(str(wav), word_timestamps=True, language=language)
        segs = [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in r["segments"]]
        words = [{"start": w["start"], "end": w["end"], "word": w["word"].strip()}
                 for s in r["segments"] for w in s.get("words", [])]
        return segs, words, "openai-whisper " + model_name
    except ImportError:
        sys.exit("No transcription engine installed. Install faster-whisper, or supply an .srt/.vtt, "
                 "or ask the user for timestamps.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--model", default="small", help="tiny/base/small/medium/large-v3")
    ap.add_argument("--language", default=None, help="e.g. en, es (auto if omitted)")
    ap.add_argument("--audio-only", action="store_true", help="extract narration.mp3 and stop")
    a = ap.parse_args()

    src, out = Path(a.input), Path(a.out_dir)
    (out / "audio").mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() in (".srt", ".vtt"):
        segs, words, engine = parse_subs(src), [], f"subtitles ({src.name})"
        duration = segs[-1]["end"] if segs else 0
    else:
        kinds, duration = probe(src)
        if "audio" not in kinds:
            sys.exit(f"{src} has no audio track.")
        narration = out / "audio" / "narration.mp3"
        if src.suffix.lower() == ".mp3" and "video" not in kinds:
            if src.resolve() != narration.resolve():
                shutil.copyfile(src, narration)
        else:
            print(f"Extracting audio from {src.name} ({'video' if 'video' in kinds else 'audio'}, {fmt(duration)})…")
            run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-map", "0:a:0",
                 "-ar", "48000", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", str(narration)])
        print(f"Narration: {narration}")
        if a.audio_only:
            return
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "a.wav"
            run(["ffmpeg", "-y", "-v", "error", "-i", str(narration), "-ar", "16000", "-ac", "1", str(wav)])
            print("Transcribing…")
            segs, words, engine = transcribe(wav, a.model, a.language)

    (out / "words.json").write_text(json.dumps({"engine": engine, "duration": duration,
                                                "segments": segs, "words": words}, indent=1))
    lines = [f"# Transcript\n", f"Source: `{src.name}` ({fmt(duration)}) · {engine}. "
             "Times are m:ss.ss. Check names and numbers.\n"]
    lines += [f"- {fmt(s['start'])}  {s['text']}" for s in segs]
    (out / "transcript.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {out/'transcript.md'} and {out/'words.json'} ({len(segs)} segments, {len(words)} words)")


if __name__ == "__main__":
    main()

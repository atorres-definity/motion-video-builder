#!/usr/bin/env python3
"""Check the tools this skill needs and print install commands for anything missing."""
import importlib.util, shutil, subprocess, sys

ok = True
def report(name, good, fix=""):
    global ok
    print(f"[{'ok' if good else 'MISSING'}] {name}" + ("" if good else f"\n        fix: {fix}"))
    ok = ok and good

pip = f"{sys.executable} -m pip install"
report("python >= 3.8", sys.version_info >= (3, 8), "install Python 3.8+")
report("ffmpeg", bool(shutil.which("ffmpeg")), "macOS: brew install ffmpeg · Ubuntu: sudo apt install ffmpeg · Windows: winget install ffmpeg")
report("ffprobe", bool(shutil.which("ffprobe")), "comes with ffmpeg")

has_pw = importlib.util.find_spec("playwright") is not None
report("playwright (python)", has_pw, f"{pip} playwright   (add --break-system-packages if pip refuses)")
if has_pw:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        report("chromium for playwright", True)
    except Exception as e:
        report("chromium for playwright", False, f"{sys.executable} -m playwright install chromium   ({str(e).splitlines()[0][:120]})")

fw = importlib.util.find_spec("faster_whisper") is not None
ow = importlib.util.find_spec("whisper") is not None
if fw or ow:
    report(f"transcription ({'faster-whisper' if fw else 'openai-whisper'})", True)
else:
    print(f"[optional] transcription — not installed\n        fix: {pip} faster-whisper"
          "\n        (first run downloads a model from Hugging Face; without it, use an SRT/VTT or user timestamps)")

print("\nAll required tools present." if ok else "\nSome required tools are missing — ask the user before installing.")
sys.exit(0 if ok else 1)

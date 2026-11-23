#!/usr/bin/env python3
"""
Render animation.html frame by frame (time-exact) with headless Chromium.

  python render_frames.py animation.html --out render/frames [--alpha] [--workers 4]
                          [--start S] [--end S] [--duration S] [--fps N] [--resume]
  python render_frames.py animation.html --stills review/          # one PNG per slide (final state)
  python render_frames.py animation.html --times 12.5,104 --out review/   # specific moments

Frames: 000000.png … ; frame i = time i/fps. Writes render.json next to the frames.
"""
import argparse, asyncio, json, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ARGS = ["--allow-file-access-from-files", "--disable-web-security", "--font-render-hinting=none",
        "--force-color-profile=srgb", "--hide-scrollbars"]


def audio_duration(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                              "default=nw=1:nk=1", str(path)], capture_output=True, text=True).stdout
        return float(out.strip())
    except Exception:
        return None


async def open_page(browser, url, w, h):
    page = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    await page.goto(url)
    await page.wait_for_function("window.__ready === true", timeout=120000)
    return page


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", default="render/frames")
    ap.add_argument("--alpha", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--fps", type=float)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--stills", help="folder: one PNG per slide at its final state")
    ap.add_argument("--times", help="comma-separated seconds to capture into --out")
    ap.add_argument("--allow-missing-fonts", action="store_true")
    a = ap.parse_args()

    html = Path(a.html).resolve()
    base = html.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=ARGS)

        if a.stills:
            out = Path(a.stills); out.mkdir(parents=True, exist_ok=True)
            page = await open_page(browser, base + "?render" + ("&alpha" if a.alpha else ""), 1920, 1080)
            info = await page.evaluate("window.__info()")
            await page.set_viewport_size({"width": info["width"], "height": info["height"]})
            for idx, s in enumerate(info["slides"]):
                await page.evaluate(f"window.__still({idx})")
                name = f"{s['n']} {s['name']}".replace("/", "-") + ".png"
                await page.screenshot(path=str(out / name), omit_background=a.alpha)
                print("wrote", out / name)
            await browser.close(); return

        page = await open_page(browser, base + "?render" + ("&alpha" if a.alpha else ""), 1920, 1080)
        info = await page.evaluate("window.__info()")
        w, h = info["width"], info["height"]
        fps = a.fps or info["fps"]
        if info["missingFonts"] and not a.allow_missing_fonts:
            sys.exit(f"Fonts did not load: {info['missingFonts']}. Fix @font-face (local files) "
                     "or rerun with --allow-missing-fonts to test anyway.")
        await page.set_viewport_size({"width": w, "height": h})

        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

        if a.times:
            for t in [float(x) for x in a.times.split(",")]:
                await page.evaluate(f"window.__seek({t})")
                path = out / f"t{t:08.2f}.png"
                await page.screenshot(path=str(path), omit_background=a.alpha)
                print("wrote", path)
            await browser.close(); return

        dur = a.duration or info["duration"]
        if not dur and info["audio"]:
            dur = audio_duration(html.parent / info["audio"])
        if not dur:
            dur = info["lastStart"] + 4
        total = int(round(dur * fps))
        f0 = int(round(a.start * fps))
        f1 = min(total, int(round(a.end * fps)) if a.end else total)
        todo = [i for i in range(f0, f1) if not (a.resume and (out / f"{i:06d}.png").exists())]
        print(f"{w}x{h} @ {fps} fps · {dur:.2f}s · frames {f0}–{f1 - 1} · {len(todo)} to render · "
              f"{'alpha' if a.alpha else 'opaque'} · {a.workers} workers")

        (out / "render.json").write_text(json.dumps({"width": w, "height": h, "fps": fps, "duration": dur,
            "frames": total, "alpha": a.alpha, "missingFonts": info["missingFonts"],
            "source": str(html), "slides": info["slides"]}, indent=1))

        pages = [page] + [await open_page(browser, page.url, w, h) for _ in range(max(0, a.workers - 1))]
        queue = asyncio.Queue()
        for i in todo: queue.put_nowait(i)
        done, t_start = 0, time.time()

        async def worker(pg):
            nonlocal done
            while True:
                try: i = queue.get_nowait()
                except asyncio.QueueEmpty: return
                await pg.evaluate(f"window.__seek({i / fps})")
                await pg.screenshot(path=str(out / f"{i:06d}.png"), omit_background=a.alpha,
                                    clip={"x": 0, "y": 0, "width": w, "height": h})
                done += 1
                if done % 150 == 0 or done == len(todo):
                    el = time.time() - t_start
                    print(f"  {done}/{len(todo)} frames · {el:.0f}s · eta {el / done * (len(todo) - done):.0f}s", flush=True)

        await asyncio.gather(*(worker(pg) for pg in pages))
        await browser.close()
        print(f"Done → {out}")


if __name__ == "__main__":
    asyncio.run(main())

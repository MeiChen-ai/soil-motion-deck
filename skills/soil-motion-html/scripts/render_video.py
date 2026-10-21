"""Product B: render narrated motion slides from a built deck to MP4 (+ SRT subtitles).

usage:
  python render_video.py <deck.html> <out_dir> [--motion g6 --motion g8 | (all)]
                         [--size 1280x720] [--browser msedge] [--burn] [--join name.mp4]

The deck must come from build_motion.py: the narration (base64 MP3) and the caption timings
(<script class="mx-captions">) are read from the deck itself, so the video always matches
the slides.

How: Playwright opens the deck in an installed browser (Edge or Chrome, no download), goes to
the slide, presses Play with the voice muted and records the screen in real time; ffmpeg then
trims the recording to the moment Play was pressed, adds the narration and the subtitles.
Subtitles are soft (a track you can switch on) unless --burn writes them into the picture.
ffmpeg comes from PATH, or from the imageio-ffmpeg package (pip install imageio-ffmpeg).

Writes <out_dir>/<name>.mp4 and <name>.srt per motion slide; --join also writes one MP4
with all of them in deck order.
"""
import argparse, base64, json, pathlib, re, shutil, subprocess, sys, tempfile, time


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("render_video: ffmpeg not found. Install it, or run: pip install imageio-ffmpeg")


def srt_time(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def write_srt(cues, path):
    lines = []
    for i, (a, b, text) in enumerate(cues, 1):
        lines += [str(i), "%s --> %s" % (srt_time(a), srt_time(b)), text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def deck_motions(html):
    """name -> (mp3 bytes, cues) for every motion block, in deck order."""
    out = {}
    for m in re.finditer(r'<div class="motion" data-motion="([^"]+)">(.*?)(?=<div class="motion" data-motion=|</section>)', html, re.S):
        name, body = m.group(1), m.group(2)
        a = re.search(r'<audio[^>]*src="data:audio/mpeg;base64,([^"]+)"', body)
        c = re.search(r'<script type="application/json" class="mx-captions">(.*?)</script>', body, re.S)
        if not a:
            continue
        cues = json.loads(c.group(1).replace("<\\/", "</")) if c else []
        out[name] = (base64.b64decode(a.group(1)), cues)
    return out


HIDE_CHROME = "#footer-shell,#hint,.mx-ctrl{visibility:hidden !important;}"


def record(page, cdp, frames_dir, deck_url, name, w, h):
    """Play one motion slide while capturing frames (CDP screencast).

    Returns (frames, t_play, end): frames is [(timestamp, jpeg path)], t_play the wall-clock
    time Play was pressed. Frames arrive only when the picture changes, so each one is held
    until the next (see encode_frames)."""
    frames = []

    def on_frame(ev):
        path = frames_dir / ("f%05d.jpg" % len(frames))
        path.write_bytes(base64.b64decode(ev["data"]))
        frames.append((ev["metadata"]["timestamp"], path))
        cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

    cdp.on("Page.screencastFrame", on_frame)
    page.goto(deck_url)
    page.wait_for_load_state("load")
    page.evaluate("""name => {
        const root = document.querySelector('[data-motion="' + name + '"]');
        const n = Array.from(document.querySelectorAll('.slide')).indexOf(root.closest('.slide')) + 1;
        goTo(n);
        root.querySelector('audio').muted = true;
    }""", name)
    page.wait_for_timeout(1200)  # slide transition + audio metadata
    end = page.evaluate("name => MOTIONS.find(m => m.root.dataset.motion === name).end", name)
    page.add_style_tag(content=HIDE_CHROME)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": w, "maxHeight": h, "everyNthFrame": 1})
    page.wait_for_timeout(500)
    t_play = time.time()
    page.evaluate("name => document.querySelector('[data-motion=\"' + name + '\"] .mx-play').click()", name)
    page.wait_for_function("name => /Play again/.test(document.querySelector('[data-motion=\"' + name + '\"] .mx-play').textContent)",
                           arg=name, timeout=int((end + 30) * 1000), polling=200)
    page.wait_for_timeout(1000)  # hold the final frame
    cdp.send("Page.stopScreencast")
    return frames, t_play, end


def encode_frames(frames, t_play, length, tmp):
    """ffmpeg concat list: every frame held until the next one, starting at Play."""
    t_end = t_play + length
    before = [p for ts, p in frames if ts <= t_play]
    shown = [(t_play, before[-1] if before else frames[0][1])]  # picture on screen at Play
    shown += [(ts, p) for ts, p in frames if t_play < ts < t_end]
    rows = [(p, (shown[i + 1][0] if i + 1 < len(shown) else t_end) - ts) for i, (ts, p) in enumerate(shown)]
    lst = tmp / "frames.txt"
    lst.write_text("".join("file '%s'\nduration %.4f\n" % (p.as_posix(), d) for p, d in rows) + "file '%s'\n" % rows[-1][0].as_posix(), encoding="utf-8")
    return lst


def main(a):
    deck = pathlib.Path(a.deck).resolve()
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    motions = deck_motions(deck.read_text(encoding="utf-8"))
    names = a.motion or list(motions)
    missing = [n for n in names if n not in motions]
    if missing:
        sys.exit("render_video: no motion slide named %s in %s (found: %s)" % (missing, deck.name, ", ".join(motions)))
    w, h = map(int, a.size.lower().split("x"))
    ff = ffmpeg_exe()
    from playwright.sync_api import sync_playwright

    made = []
    with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        browser = p.chromium.launch(channel=a.browser, args=["--autoplay-policy=no-user-gesture-required"])
        for name in names:
            mp3, cues = motions[name]
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            cdp = ctx.new_cdp_session(page)
            fdir = tmp / name
            fdir.mkdir()
            frames, t_play, end = record(page, cdp, fdir, deck.as_uri(), name, w, h)
            ctx.close()
            if not frames:
                sys.exit("render_video: the browser sent no frames for %s" % name)
            length = end + 0.8
            lst = encode_frames(frames, t_play, length, tmp)
            (tmp / (name + ".mp3")).write_bytes(mp3)
            srt = out / (name + ".srt")
            write_srt(cues, srt)
            shutil.copy(srt, tmp / "subs.srt")
            mp4 = out / (name + ".mp4")
            cmd = [ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", name + ".mp3"]
            vf = ["scale=%d:%d:flags=lanczos,format=yuv420p" % (w, h)]
            if a.burn:
                vf.append("subtitles=subs.srt:force_style='FontName=Segoe UI,FontSize=18,Spacing=0.4,Outline=1.4,Shadow=0,MarginV=26'")
            else:
                cmd += ["-i", "subs.srt"]
            cmd += ["-t", "%.2f" % length, "-map", "0:v", "-map", "1:a"] + ([] if a.burn else ["-map", "2:s", "-c:s", "mov_text"])
            cmd += ["-vf", ",".join(vf), "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(mp4.resolve())]
            subprocess.run(cmd, cwd=tmp, check=True)  # cwd=tmp: subtitles filter cannot take a Windows drive path
            made.append(mp4)
            print("ok %s  %.1f s, %d frames captured, %d KB" % (mp4, length, len(frames), mp4.stat().st_size // 1024))
        browser.close()

    if a.join and len(made) > 1:
        lst = out / "_join.txt"
        lst.write_text("".join("file '%s'\n" % m.resolve().as_posix() for m in made), encoding="utf-8")
        joined = out / a.join
        subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
        lst.unlink()
        print("ok %s (joined %d clips)" % (joined, len(made)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("out_dir")
    ap.add_argument("--motion", action="append")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--browser", default="msedge", help="msedge or chrome (installed browsers)")
    ap.add_argument("--burn", action="store_true", help="burn subtitles into the picture")
    ap.add_argument("--join", help="also write all clips joined into this file name")
    main(ap.parse_args())

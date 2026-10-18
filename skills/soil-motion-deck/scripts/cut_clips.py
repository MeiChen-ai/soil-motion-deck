"""Cut one clip per animated slide out of the silent render, plus a poster PNG for each.

Each storyboard frame is a scene in index.html (id="el-<frame>", data-start, data-duration).
transitions.mjs fades scenes with tl.fromTo("#el-X", {opacity:0}, {opacity:1, duration:d}, t) and
tl.to("#el-X", {opacity:0, duration:d}, t). The clip runs from the end of the fade-in to the start
of the fade-out, so no neighbouring frame bleeds in. Hard cuts need no trimming.

  python cut_clips.py --project <film> --video <film>-silent/renders/silent.mp4 \
      --map p03=02-squares p06=04-proof p09=06-myths --out deck/media [--poster last]

--poster: last (default, the settled conclusion), first, or seconds into the clip (e.g. 2.5).
Writes <name>.mp4 (H.264, yuv420p, no audio, faststart: plays in PowerPoint and Keynote) and
<name>.png, and prints a duration table to paste into the speaker notes.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def scenes(index_html):
    out = {}
    for m in re.finditer(r"<div\b[^>]*>", index_html):
        tag = m.group(0)
        idm = re.search(r'\bid="el-([^"]+)"', tag)
        st = re.search(r'\bdata-start="([\d.]+)"', tag)
        du = re.search(r'\bdata-duration="([\d.]+)"', tag)
        if idm and st and du and "data-composition-src" in tag:
            out[idm.group(1)] = [float(st.group(1)), float(st.group(1)) + float(du.group(1))]
    return out


def fades(index_html):
    fin, fout = {}, {}
    for m in re.finditer(r'tl\.fromTo\("#el-([^"]+)",\s*\{\s*opacity:\s*0\s*\},\s*\{[^}]*?duration:\s*([\d.]+)[^}]*\},\s*([\d.]+)\)', index_html):
        fin[m.group(1)] = float(m.group(3)) + float(m.group(2))
    for m in re.finditer(r'tl\.to\("#el-([^"]+)",\s*\{[^}]*?opacity:\s*0[^}]*\},\s*([\d.]+)\)', index_html):
        fout[m.group(1)] = float(m.group(2))
    return fin, fout


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(r.stderr[-2000:])
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, help="narrated project (its index.html gives the timing)")
    ap.add_argument("--video", required=True, help="silent render of the twin project")
    ap.add_argument("--map", nargs="+", required=True, metavar="NAME=FRAME", help="e.g. p03=02-squares")
    ap.add_argument("--out", required=True, help="output folder, usually <deck>/media")
    ap.add_argument("--poster", default="last")
    ap.add_argument("--crf", type=int, default=20)
    a = ap.parse_args()

    html = (Path(a.project) / "index.html").read_text(encoding="utf-8")
    sc = scenes(html)
    fin, fout = fades(html)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"{'clip':<8}{'frame':<22}{'from':>8}{'to':>8}{'len':>7}")
    for pair in a.map:
        name, frame = pair.split("=", 1)
        if frame not in sc:
            sys.exit(f"frame '{frame}' not in index.html; known: {', '.join(sc)}")
        t0 = fin.get(frame, sc[frame][0])
        t1 = fout.get(frame, sc[frame][1])
        mp4, png = out / f"{name}.mp4", out / f"{name}.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", a.video, "-an",
             "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(mp4)])
        if a.poster == "last":
            seek = ["-sseof", "-0.1"]
        elif a.poster == "first":
            seek = ["-ss", "0"]
        else:
            seek = ["-ss", a.poster]
        run(["ffmpeg", "-v", "error", "-y", *seek, "-i", str(mp4), "-frames:v", "1", "-update", "1", str(png)])
        print(f"{name:<8}{frame:<22}{t0:>8.2f}{t1:>8.2f}{t1 - t0:>6.1f}s")


if __name__ == "__main__":
    main()

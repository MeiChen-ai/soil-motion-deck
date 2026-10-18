"""Export every slide of a .pptx to PNG and tile them into contact sheets for layout review.

  python thumbs.py deck.pptx --out thumbs [--width 960]

Windows with PowerPoint: uses PowerPoint itself (export_thumbs.ps1), so fonts and video posters
look exactly as in class. Elsewhere: LibreOffice (soffice) -> PDF -> pdftoppm. LibreOffice may
substitute fonts; judge layout, not typography, from those images.
Sheets are built with review-loop/scripts/sheet.py when it is installed next to this skill.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def via_powerpoint(pptx, out, width):
    ps = HERE / "export_thumbs.ps1"
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps),
                        "-Pptx", str(pptx), "-OutDir", str(out), "-Width", str(width)])
    return r.returncode == 0


def via_libreoffice(pptx, out, width):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice or not shutil.which("pdftoppm"):
        sys.exit("need PowerPoint (Windows) or LibreOffice + poppler (pdftoppm) to export slides")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx)], check=True)
    pdf = out / (pptx.stem + ".pdf")
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1", str(pdf), str(out / "slide")], check=True)
    for i, f in enumerate(sorted(out.glob("slide-*.png")), 1):
        f.rename(out / f"slide{i:02d}.png")
    pdf.unlink()
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("--out", default="thumbs")
    ap.add_argument("--width", type=int, default=960)
    a = ap.parse_args()
    pptx, out = Path(a.pptx).resolve(), Path(a.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ok = os.name == "nt" and via_powerpoint(pptx, out, a.width)
    if not ok:
        via_libreoffice(pptx, out, a.width)
    slides = sorted(glob.glob(str(out / "slide*.png")))
    print(f"{len(slides)} slides -> {out}")
    sheet = HERE.parent.parent / "review-loop" / "scripts" / "sheet.py"
    if sheet.exists() and slides:
        labels = ",".join(str(i) for i in range(1, len(slides) + 1))
        subprocess.run([sys.executable, str(sheet), "--images", *slides, "--labels", labels,
                        "--width", "480", "--out", str(out), "--name", "deck"], check=True)


if __name__ == "__main__":
    main()

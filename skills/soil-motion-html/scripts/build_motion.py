"""Build a SOIL HTML deck with narrated motion slides.

usage:
  python build_motion.py <spec_dir> <out.html> [--no-captions]

<spec_dir> (kept next to the deck, e.g. "Week 7/slides/motion/gemini-skills-walkthrough/"):
  original.html    the deck WITHOUT motion slides; every build starts from this copy, so a
                   rebuild never stacks a second engine on top of the first
  manifest.json    {"motions": [{"name": "g6", "slide": 6, "end": 47.6, "audio": "s6",
                                  "chips": [["1 Write the prompt", 0], ["2 Send", 37.46]]}, ...]}
  slides.html      one fragment per slide, headed <!--SLIDE n-->; each fragment replaces
                   everything after that slide's </h2> and contains <!--CTRL name--> where
                   the player controls go
  slides.css       styles for this deck's motion slides
  configs.js       one makeMotion(name, {end, acts, tracks}) call per slide
  <audio>/narration.mp3 + narration.json   from make_narration.py

The skill's templates/motion.css and templates/motion_engine.js are added automatically.
Each motion block also gets its caption timings (<script type="application/json"
class="mx-captions">), which render_video.py turns into subtitles.
"""
import argparse, base64, html, json, pathlib, re, sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
CRLF, LF = chr(13) + chr(10), chr(10)


def read(path):
    """Text with LF line ends (a Git checkout on Windows may turn them into CRLF)."""
    return pathlib.Path(path).read_text(encoding="utf-8").replace(CRLF, LF)


def die(msg):
    sys.exit("build_motion: " + msg)


def captions(narr):
    """Caption cues of at most ~12 words, cut at sentence ends where possible."""
    cues = []
    for seg in narr["segments"]:
        text, words = seg["text"], seg["words"]
        end_of_seg = seg["start"] + seg["dur"]
        pos, start, cur = 0, 0, []
        for i, (w, t) in enumerate(words):
            j = text.find(w, pos)
            pos = j + len(w) if j >= 0 else pos
            cur.append(t)
            sentence_end = j >= 0 and text[pos:pos + 1] in (".", "!", "?", ":")
            nxt = words[i + 1][1] if i + 1 < len(words) else end_of_seg
            if len(cur) >= 12 or i + 1 == len(words) or (sentence_end and len(cur) >= 4):
                # the cue shows the narration's own wording (with punctuation) for these words
                piece = text[start:pos + (1 if sentence_end else 0)].strip().lstrip(",;: ") if j >= 0 else " ".join(x for x, _ in words[i + 1 - len(cur):i + 1])
                cues.append([round(cur[0], 2), round(min(nxt, end_of_seg), 2), piece])
                start, cur = pos + (1 if sentence_end else 0), []
    return cues


def main(a):
    spec = pathlib.Path(a.spec_dir)
    s = read(spec / "original.html")
    if "data-motion=" in s:
        die("original.html already contains motion slides; it must be the deck before any motion was added")
    man = json.loads(read(spec / "manifest.json"))
    motions = {m["name"]: m for m in man["motions"]}

    frags = dict(re.findall(r"<!--SLIDE (\d+)-->\n(.*?)(?=<!--SLIDE|\Z)", read(spec / "slides.html"), re.S))
    for n, frag in frags.items():
        m = re.search(r'(<section class="slide[^"]*" data-slide="%s"[^>]*>\s*<div class="slide-inner">.*?</h2>\n)(.*?)(    </div>\n  </section>)' % n, s, re.S)
        if not m:
            die("slide %s: expected <section ... data-slide=\"%s\"> with an <h2> title, closed by '    </div>\\n  </section>'" % (n, n))
        s = s[:m.start(2)] + frag + s[m.end(2):]

    def ctrl(m):
        name, *legacy = m.group(1).split("|")
        mo = motions.get(name) or die("<!--CTRL %s--> has no entry in manifest.json" % name)
        chips = mo.get("chips") or [c.rsplit("@", 1) for c in legacy]
        end = mo["end"]
        adir = spec / mo["audio"]
        mp3 = base64.b64encode((adir / "narration.mp3").read_bytes()).decode()
        chip_html = "".join('<button class="mx-chip" type="button" data-seek="%s">%s</button>' % (c[1], html.escape(str(c[0]))) for c in chips)
        out = ('<div class="mx-ctrl">\n'
               '          <button class="mx-btn mx-play" type="button">&#9654; Play</button>\n'
               '          <button class="mx-btn ghost mx-replay" type="button">&#8634; Replay</button>\n'
               '          <button class="mx-btn ghost mx-narr" type="button" aria-pressed="true">&#128266; Voice on</button>\n'
               '          <span class="mx-chips">%s</span>\n'
               '          <div class="mx-bar"><div></div></div>\n'
               '          <span class="mx-time">0:00 / %d:%02d</span>\n'
               '          <audio preload="auto" src="data:audio/mpeg;base64,%s"></audio>\n'
               '        </div>') % (chip_html, end // 60, end % 60, mp3)
        if not a.no_captions:
            narr = json.loads(read(adir / "narration.json"))
            out += '\n        <script type="application/json" class="mx-captions">%s</script>' % json.dumps(captions(narr), ensure_ascii=False).replace("</", "<\\/")
        return out

    s, n = re.subn(r"<!--CTRL ([^>]+)-->", ctrl, s)
    if n != len(motions):
        die("found %d <!--CTRL--> markers for %d manifest entries" % (n, len(motions)))

    css = read(SKILL / "templates" / "motion.css") + read(spec / "slides.css")
    s, n = re.subn(r"\n</style>", lambda m: "\n" + css + "</style>", s, count=1)
    n or die("no </style> in original.html")
    s, n = re.subn(r"(  document\.getElementById\('nextBtn'\)\.disabled = current === total;\n)(\})", r"\1  if(window.mxOnSlide) mxOnSlide(el);\n\2", s, count=1)
    n or die("goTo() not found: expected the SOIL deck's goTo(n) ending with the nextBtn line")
    s, n = re.subn(r"(document\.addEventListener\('click', e => \{\n  if\()(.*?)\) return;", lambda m: m.group(1) + m.group(2) + " || e.target.closest('.motion')) return;", s, count=1, flags=re.S)
    n or die("click-to-turn handler not found")
    engine = read(SKILL / "templates" / "motion_engine.js") + read(spec / "configs.js")
    s, n = re.subn(r"\ngoTo\(1\);\n</script>", lambda m: "\n" + engine + "\ngoTo(1);\n</script>", s, count=1)
    n or die("'goTo(1);' before </script> not found")

    pathlib.Path(a.out).write_text(s, encoding="utf-8", newline="")
    print("ok %s: %d motion slides, %d KB" % (a.out, len(motions), len(s) // 1024))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_dir")
    ap.add_argument("out")
    ap.add_argument("--no-captions", action="store_true")
    main(ap.parse_args())

"""Generate narration audio + word timings with edge-tts.

usage:
  python make_narration.py <segments.json> <out_dir> [--rate -6%] [--voice en-US-JennyNeural]
                                                      [--app-voice en-GB-RyanNeural]

segments.json is a list of [name, voice, text]. voice is "N" (narrator), "A" (a second
voice, e.g. an app reading a sentence aloud) or a full edge-tts voice name.

Writes into <out_dir>:
  narration.mp3   all segments joined, in order
  narration.json  {"total": s, "segments": [{name, start, dur, text, words: [[word, t], ...]}]}
                  times in seconds from the start of narration.mp3

Then print the word timings and anchor every animation step to a word (see SKILL.md §4).
"""
import argparse, asyncio, json, pathlib, sys

import edge_tts

BYTES_PER_SEC = 48000 / 8  # edge-tts default output: 24 kHz, 48 kbit/s mono MP3 (CBR)


async def one(voice, text, rate):
    audio, words = bytearray(), []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            words.append([chunk["text"], round(chunk["offset"] / 1e7, 3)])
    return bytes(audio), words


async def main(a):
    voices = {"N": a.voice, "A": a.app_voice}
    segments = json.loads(pathlib.Path(a.segments).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    allbytes, segs, t = bytearray(), [], 0.0
    for name, voice, text in segments:
        audio, words = await one(voices.get(voice, voice), text, a.rate)
        dur = len(audio) / BYTES_PER_SEC
        segs.append({"name": name, "start": round(t, 3), "dur": round(dur, 3), "text": text,
                     "words": [[w, round(t + o, 3)] for w, o in words]})
        allbytes += audio
        t += dur
    (out / "narration.mp3").write_bytes(allbytes)
    (out / "narration.json").write_text(json.dumps({"total": round(t, 3), "segments": segs}, indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for s in segs:
        print("%-10s %6.2f-%6.2f  %s" % (s["name"], s["start"], s["start"] + s["dur"], " ".join("%s@%s" % (w, tt) for w, tt in s["words"])))
    print("total %.2f s, %d KB" % (t, len(allbytes) // 1024))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("out_dir")
    ap.add_argument("--rate", default="-6%")
    ap.add_argument("--voice", default="en-US-JennyNeural")
    ap.add_argument("--app-voice", default="en-GB-RyanNeural")
    asyncio.run(main(ap.parse_args()))

"""
Turn the captions of `TravelingWaveTube` into a spoken track.

    # 1. collect the captions (runs construct without rendering)
    TWT_COLLECT=1 manim --dry_run twt.py TravelingWaveTube

    # 2. speak them
    python narrate.py --voice /path/to/en-us-ryan-high.onnx

    # 3. render for real — each caption now holds for as long as it is spoken,
    #    and the render logs when each one started
    manim -r 1600,900 --fps 30 --format png twt.py TravelingWaveTube

    # 4. lay the clips back onto the video at those times
    python narrate.py --mix --video out.mp4

Voice: Piper (https://github.com/rhasspy/piper). The "ryan" model used here
comes from the RyanSpeech dataset, which is CC BY-NC-SA 4.0 — fine for a
personal page, not for anything commercial.

A caption and its narration are the same sentence by default; `overrides.json`
exists for the handful that need to be said differently from how they are
written ("a quarter of c" reads badly out loud).
"""

import argparse
import json
import subprocess
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent / "narration"
AUDIO = HERE / "audio"

LENGTH_SCALE = 1.06      # a touch slower than default; it reads calmer
SENTENCE_SILENCE = 0.35  # breath between sentences
LEAD_IN = 0.25           # start speaking just after the caption has faded in


def wav_seconds(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def speak(voice):
    script = json.loads((HERE / "script.json").read_text())
    overrides = {}
    if (HERE / "overrides.json").exists():
        overrides = json.loads((HERE / "overrides.json").read_text())

    AUDIO.mkdir(parents=True, exist_ok=True)
    durations = {}
    for beat in script:
        key = beat["key"]
        text = overrides.get(key, beat["text"])
        out = AUDIO / f"{key}.wav"
        subprocess.run(
            ["piper", "-m", str(voice), "-f", str(out),
             "--length-scale", str(LENGTH_SCALE),
             "--sentence-silence", str(SENTENCE_SILENCE)],
            input=text, text=True, check=True, capture_output=True)
        durations[key] = round(wav_seconds(out), 3)
        print(f"{key}  {durations[key]:6.2f}s  {text[:60]}")

    (HERE / "durations.json").write_text(json.dumps(durations, indent=2))
    print(f"\n{len(durations)} clips, {sum(durations.values()):.1f}s of speech")


def mix(video, out):
    """Lay each clip onto the finished video at the time its caption appeared."""
    beats = json.loads((HERE / "beats.json").read_text())
    inputs, filters, labels = ["-i", str(video)], [], []
    for i, beat in enumerate(beats, start=1):
        clip = AUDIO / f"{beat['key']}.wav"
        if not clip.exists():
            continue
        inputs += ["-i", str(clip)]
        delay = int(round((beat["t"] + LEAD_IN) * 1000))
        filters.append(f"[{i}:a]adelay={delay}|{delay},volume=0.82[a{i}]")
        labels.append(f"[a{i}]")

    # the clips are already normalised and never overlap, so a plain sum with a
    # little headroom is all that is needed
    graph = ";".join(filters) + ";" + "".join(labels) + \
        f"amix=inputs={len(labels)}:normalize=0[out]"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph,
         "-map", "0:v", "-map", "[out]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)], check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", help="path to the Piper .onnx model")
    ap.add_argument("--mix", action="store_true")
    ap.add_argument("--video")
    ap.add_argument("--out", default="narrated.mp4")
    a = ap.parse_args()
    if a.mix:
        mix(a.video, a.out)
    else:
        speak(a.voice)

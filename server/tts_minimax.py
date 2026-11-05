#!/usr/bin/env python3
"""MiniMax voice adapter for Lemo-Opuscar (drop-in for core/tts/tts_zh.py / tts.py).

Same input/output contract, so mix.py / mux.sh / subtitles keep working unchanged.

Usage:
    python tts_minimax.py lines.json out_dir

lines.json = [{"id": ..., "text": ..., "voice": "...", "rate": 1.0, "pitch": 0, "say": "..."}, ...]
  - "id"    : used for the output filename <id>.wav
  - "text"  : what appears in subtitles
  - "say"   : optional; what is actually spoken (numbers/abbrevs written out), default "text"
  - "voice" : optional MiniMax voice_id, default $MINIMAX_VOICE_ID
  - "rate"  : optional speed multiplier (1.0 = normal), mapped to MiniMax "speed"
  - "pitch" : optional pitch offset, mapped to MiniMax "pitch"

Environment:
    MINIMAX_API_KEY   (required)  - bearer token
    MINIMAX_GROUP_ID  (required)  - MiniMax group id
    MINIMAX_MODEL     (default "speech-02-turbo")
    MINIMAX_VOICE_ID  (default voice; per-line "voice" overrides)
    MINIMAX_BASE_URL  (default "https://api.minimax.chat/v1/t2a_v2")

Output: out_dir/<id>.wav (24 kHz mono, leading/trailing silence trimmed) and out_dir/dur.json.
Audio is cached in out_dir/.cache/ keyed by (say, voice, rate, pitch). Needs ffmpeg on PATH.
Stdlib only (no pip deps), so it runs inside the lemo-opuscar environment.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

API_KEY = os.environ.get("MINIMAX_API_KEY", "")
GROUP_ID = os.environ.get("MINIMAX_GROUP_ID", "")
BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1/t2a_v2")
MODEL = os.environ.get("MINIMAX_MODEL", "speech-02-turbo")
DEFAULT_VOICE = os.environ.get("MINIMAX_VOICE_ID", "")
SR = 24000


def synth(text: str, voice: str, rate: float, pitch: int) -> bytes:
    if not API_KEY or not GROUP_ID:
        sys.exit("tts_minimax.py: set MINIMAX_API_KEY and MINIMAX_GROUP_ID")
    url = f"{BASE_URL}?GroupId={urllib.parse.quote(GROUP_ID)}"
    body = {
        "model": MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": float(rate), "vol": 1.0, "pitch": int(pitch)},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read().decode("utf-8"))
            base = resp.get("base_resp", {})
            if base.get("status_code", 0) != 0:
                raise RuntimeError(f"MiniMax base_resp: {base}")
            audio = (resp.get("data") or {}).get("audio") or ""
            if not audio:
                raise RuntimeError("MiniMax returned empty audio")
            try:
                return bytes.fromhex(audio)          # T2A v2 returns hex-encoded mp3
            except ValueError:
                return base64.b64decode(audio)        # be lenient if it is base64
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def decode_to_wav(raw: bytes, wav_path: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(raw)
        tmp = f.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                "-ar", str(SR), "-ac", "1",
                "-af",
                "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1,"
                "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1,areverse",
                "-f", "wav", wav_path,
            ],
            check=True,
        )
    finally:
        os.remove(tmp)


def wav_duration(wav_path: str) -> float:
    with wave.open(wav_path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    lines_path, out_dir = sys.argv[1], sys.argv[2]

    with open(lines_path, encoding="utf-8") as f:
        lines = json.load(f)

    out = os.path.abspath(out_dir)
    cache = os.path.join(out, ".cache")
    os.makedirs(cache, exist_ok=True)

    dur = {}
    for line in lines:
        lid = line["id"]
        text = line.get("text", "")
        say = line.get("say") or text
        voice = line.get("voice") or DEFAULT_VOICE
        if not voice:
            sys.exit("tts_minimax.py: no voice (set MINIMAX_VOICE_ID or per-line 'voice')")
        rate = line.get("rate")
        if rate is None and "speed" in line:
            rate = float(line["speed"])
        rate = float(rate or 1.0)
        pitch = int(line.get("pitch") or 0)

        key = hashlib.sha1(json.dumps([say, voice, rate, pitch], sort_keys=True).encode()).hexdigest()
        raw_path = os.path.join(cache, key + ".raw")
        wav_path = os.path.join(out, f"{lid}.wav")

        if not os.path.exists(raw_path):
            raw = synth(say, voice, rate, pitch)
            part = raw_path + ".part"
            with open(part, "wb") as f:
                f.write(raw)
            os.replace(part, raw_path)
        with open(raw_path, "rb") as f:
            raw = f.read()

        part = wav_path + ".part"
        decode_to_wav(raw, part)
        os.replace(part, wav_path)
        dur[lid] = round(wav_duration(wav_path), 3)
        print(f"  {lid}: {dur[lid]}s")

    with open(os.path.join(out, "dur.json"), "w", encoding="utf-8") as f:
        json.dump(dur, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(lines)} lines -> {out}")


if __name__ == "__main__":
    main()

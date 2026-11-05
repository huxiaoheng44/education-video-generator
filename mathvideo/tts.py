# -*- coding: utf-8 -*-
"""MiniMax 同步语音合成（逐句）。用标准库 urllib，避免外部依赖。"""
import json
import urllib.request
import urllib.error
import config


def _post(payload, key):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(config.MINIMAX_URL, data=data, headers={
        'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        raise RuntimeError(f"MiniMax HTTP {e.code}: {body[:600]}")


def synthesize(text, out_mp3, key, speed=None):
    """合成一段文本，写 mp3 到 out_mp3，返回时长（秒）。"""
    payload = {
        "model": config.MODEL,
        "text": text,
        "stream": False,
        "language_boost": config.LANGUAGE_BOOST,
        "output_format": "hex",
        "voice_setting": {"voice_id": config.VOICE_ID,
                          "speed": speed or config.TTS_SPEED, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": config.SAMPLE_RATE,
                          "bitrate": 128000, "format": config.TTS_FORMAT, "channel": 1},
    }
    resp = _post(payload, key)
    base = resp.get('base_resp', {})
    if base.get('status_code') != 0:
        raise RuntimeError(f"MiniMax error {base.get('status_code')} {base.get('status_msg')}")
    audio_hex = (resp.get('data') or {}).get('audio')
    if not audio_hex:
        raise RuntimeError("no audio in response")
    raw = bytes.fromhex(audio_hex)
    with open(out_mp3, 'wb') as f:
        f.write(raw)
    dur_ms = (resp.get('extra_info') or {}).get('audio_length')
    return (dur_ms / 1000.0) if dur_ms else None

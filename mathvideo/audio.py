# -*- coding: utf-8 -*-
"""音频组装：逐句 mp3 → wav（ffmpeg 文件转文件），numpy 拼接 + 合成配乐 + 主混音。"""
import os
import subprocess
import wave
import numpy as np
import config


def run_quiet(cmd):
    # 不捕获 stdout/stderr（沙箱禁止通过命名管道捕获），重定向到空设备
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def mp3_to_wav(mp3, wav, sr=24000):
    run_quiet([config.FFMPEG, '-y', '-i', mp3, '-ar', str(sr), '-ac', '1', '-f', 'wav', wav])


def read_wav_mono(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        data = w.readframes(n)
    x = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def synth_bed(n, sr, seed=11):
    """合成一段轻柔的合成配乐底垫（A-F-G-E 和弦进行）。"""
    rng = np.random.default_rng(seed)
    roots = [220.0, 174.61, 196.0, 164.81]   # A3 F3 G3 E3
    bed = np.zeros(n, dtype=np.float32)
    seg = n // len(roots)
    for i, root in enumerate(roots):
        s = i * seg
        e = min(s + seg, n)
        L = e - s
        if L <= 0:
            continue
        tt = np.arange(L) / sr
        env = np.minimum(tt / 0.6, 1.0) * np.minimum((L / sr - tt) / 0.6, 1.0)
        env = np.clip(env, 0, 1)
        sig = np.zeros(L, dtype=np.float32)
        for mult, amp in [(1.0, 0.5), (1.5, 0.28), (2.0, 0.18)]:
            ph = rng.uniform(0, 2 * np.pi)
            sig += amp * np.sin(2 * np.pi * root * mult * tt + ph).astype(np.float32)
        sig += 0.18 * np.sin(2 * np.pi * root * 1.004 * tt).astype(np.float32)
        bed[s:e] += (sig * env * 0.5).astype(np.float32)
    m = np.abs(bed).max()
    if m > 1e-6:
        bed = bed / m
    return bed


def assemble(story, mp3_paths, out_wav, sr=24000, with_music=True):
    wavs = []
    for mp3 in mp3_paths:
        w = os.path.splitext(mp3)[0] + '.wav'
        mp3_to_wav(mp3, w, sr)
        wavs.append(w)

    total = int(round((story.duration + 0.5) * sr))
    narr = np.zeros(total, dtype=np.float32)
    for sc, w in zip(story.scenes, wavs):
        x, s = read_wav_mono(w)
        if s != sr:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * sr / s)),
                          np.arange(len(x)), x).astype(np.float32)
        start = int(round(sc.t0 * sr))
        end = min(start + len(x), total)
        if end > start:
            narr[start:end] += x[:end - start]

    peak = np.abs(narr).max()
    if peak > 1e-6:
        narr = narr / peak * 0.88

    if with_music:
        mix = narr + synth_bed(total, sr) * 0.13
    else:
        mix = narr

    mix = np.clip(mix, -0.98, 0.98)
    fade = int(0.3 * sr)
    if fade > 0 and len(mix) > 2 * fade:
        mix[:fade] *= np.linspace(0, 1, fade)
        mix[-fade:] *= np.linspace(1, 0, fade)

    pcm = (mix * 32767.0).astype(np.int16)
    with wave.open(out_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav

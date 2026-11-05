# -*- coding: utf-8 -*-
"""编排：加载示例 → TTS（可缓存）→ 布局时间轴 → 逐帧渲染 → 音频组装 → ffmpeg 合成。"""
import os
import sys
import json
import math
import time
import importlib.util

import config
from engine import Engine
import tts
import audio


def load_sample(name):
    path = os.path.join(config.ROOT, 'samples', name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_frames(story, eng, fdir):
    total_frames = int(math.ceil(story.duration * story.fps))
    t0 = time.time()
    for f in range(total_frames):
        t = f / story.fps
        img = story.render(eng, t)
        img.save(os.path.join(fdir, f'f_{f:05d}.jpg'), quality=88)
        if f % 120 == 0 or f == total_frames - 1:
            el = time.time() - t0
            print(f"  帧 {f + 1}/{total_frames}  ({el:.1f}s)")
    return total_frames


def mux(fdir, master_wav, out_mp4, fps):
    cmd = [config.FFMPEG, '-y',
           '-framerate', str(fps), '-i', os.path.join(fdir, 'f_%05d.jpg'),
           '-i', master_wav,
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '160k',
           '-shortest', out_mp4]
    audio.run_quiet(cmd)


def build(sample_name, force_tts=False):
    mod = load_sample(sample_name)
    story, theme = mod.build_story()
    eng = Engine(theme)
    key = config.load_api_key()

    out_dir = os.path.join(config.ROOT, 'output', sample_name)
    adir = os.path.join(out_dir, 'audio')
    fdir = os.path.join(out_dir, 'frames')
    os.makedirs(adir, exist_ok=True)
    os.makedirs(fdir, exist_ok=True)

    timing_path = os.path.join(out_dir, 'timing.json')
    mp3s = [os.path.join(adir, f'scene_{i:02d}.mp3') for i in range(len(story.scenes))]

    # 1. TTS（缓存：mp3 与 timing.json 齐备则跳过，避免重复调用 API）
    if (not force_tts) and os.path.exists(timing_path) and all(os.path.exists(m) for m in mp3s):
        with open(timing_path, encoding='utf-8') as f:
            durations = json.load(f)
        print('使用缓存配音 + 时间轴')
    else:
        durations = []
        for i, sc in enumerate(story.scenes):
            print(f'TTS [{i + 1}/{len(story.scenes)}] {sc.narration[:22]}...')
            d = tts.synthesize(sc.narration, mp3s[i], key)
            if d is None:
                d = max(1.5, len(sc.narration) * 0.22)
            durations.append(d)
        with open(timing_path, 'w', encoding='utf-8') as f:
            json.dump(durations, f, ensure_ascii=False)

    story.layout(durations)
    print(f'总时长 {story.duration:.1f}s / {int(math.ceil(story.duration * story.fps))} 帧')

    # 2. 渲染
    print('渲染帧 ...')
    render_frames(story, eng, fdir)

    # 3. 音频
    print('合成音频 ...')
    master = os.path.join(out_dir, 'master.wav')
    audio.assemble(story, mp3s, master, with_music=True)

    # 4. mux
    out_mp4 = os.path.join(out_dir, f'{sample_name}.mp4')
    print('合成视频 ...')
    mux(fdir, master, out_mp4, story.fps)
    print(f'完成: {out_mp4}')
    return out_mp4


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'ji_tu'
    force = '--force-tts' in sys.argv
    build(name, force_tts=force)

# -*- coding: utf-8 -*-
"""预览：用假时长布局并渲染若干静帧，快速检查画面。"""
import os
import sys
import config
from engine import Engine
from build import load_sample


def main(name='ji_tu', n=12):
    story, theme = load_sample(name).build_story()
    eng = Engine(theme)
    story.layout([7.0] * len(story.scenes))
    out = os.path.join(config.ROOT, 'output', name, 'preview')
    os.makedirs(out, exist_ok=True)
    for k in range(n):
        t = k * story.duration / n
        img = story.render(eng, t)
        path = os.path.join(out, f'p_{k:02d}_{t:.1f}s.jpg')
        img.save(path, quality=90)
        print('saved', path)
    print('preview duration:', round(story.duration, 1), 's')


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'ji_tu'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    main(name, n)

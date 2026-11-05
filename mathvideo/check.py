# -*- coding: utf-8 -*-
"""程序化校验：统计关键颜色像素，确认标题/动物/文字确实被绘制。"""
import os
import glob
import numpy as np
from PIL import Image

COLORS = {
    'coral_title': (242, 112, 75),
    'mustard': (242, 184, 75),
    'chick': (245, 201, 92),
    'rabbit': (185, 168, 201),
    'ink_text': (74, 59, 42),
    'teal': (58, 167, 163),
}


def count_near(a, target, tol=24):
    t = np.array(target, dtype=np.int16)
    d = np.abs(a.astype(np.int16) - t).sum(axis=2)
    return int((d <= tol * 3).sum())


def main():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'ji_tu', 'preview')
    frames = sorted(glob.glob(os.path.join(base, '*.jpg')))
    for f in frames:
        a = np.array(Image.open(f).convert('RGB'))
        counts = {k: count_near(a, c) for k, c in COLORS.items()}
        non_bg = int(((a.astype(np.int16) - np.array([250, 247, 237])).sum(axis=2).__abs__() > 60).sum())
        print(os.path.basename(f),
              f"nonbg={non_bg:>6}",
              ' '.join(f"{k}={v}" for k, v in counts.items()))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""确定性逐帧渲染引擎：Pillow 实现 render(t)。

核心思想（源自 lemo-opuscar）：画面是时间的函数，任意一帧都能独立、按任意顺序渲染。
本引擎用「场景 Scene → 步骤 Step」组织：每个 Step 在场景内的相对时间 [r0, r1] 内被调用，
绘图函数收到场景进度 q ∈ [0,1]，自行用 clamp01((q-a)/d) 计算揭示进度并保持显示。
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import config

# ---- 缓动 ----
def clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def linear(p):
    return p


def ease_out(p):
    return 1.0 - (1.0 - p) ** 3


def ease_in_out(p):
    return p * p * (3.0 - 2.0 * p)


ANCHORS = {
    'tl': (0, 0), 'tc': (0.5, 0), 'tr': (1, 0),
    'ml': (0, 0.5), 'mc': (0.5, 0.5), 'mr': (1, 0.5),
    'bl': (0, 1), 'bc': (0.5, 1), 'br': (1, 1), 'mm': (0.5, 0.5),
}


def lerp_color(c1, c2, p):
    p = clamp01(p)
    return tuple(int(round(a + (b - a) * p)) for a, b in zip(c1, c2))


class Engine:
    def __init__(self, theme, width=None, height=None, fps=None):
        self.theme = theme
        self.W = width or config.WIDTH
        self.H = height or config.HEIGHT
        self.fps = fps or config.FPS
        self._fc = {}
        self.base = self._build_base()

    # ---------- 字体 ----------
    def font(self, size, kind='hand'):
        key = (kind, size)
        if key not in self._fc:
            path = {
                'hand': self.theme.font_hand,
                'heading': self.theme.font_heading,
                'sans': self.theme.font_sans,
            }[kind]
            self._fc[key] = ImageFont.truetype(path, size)
        return self._fc[key]

    # ---------- 底层 ----------
    def _layer(self):
        return Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))

    def _blit(self, img, layer):
        img.alpha_composite(layer, (0, 0))

    @staticmethod
    def _set_alpha(layer, alpha):
        if alpha >= 0.999:
            return layer
        a = np.array(layer)
        a[..., 3] = (a[..., 3].astype(np.float32) * alpha).astype(np.uint8)
        return Image.fromarray(a, 'RGBA')

    @staticmethod
    def _reveal_h(layer, p):
        p = clamp01(p)
        if p >= 1.0:
            return layer
        if p <= 0.0:
            return None
        a = np.array(layer)
        cut = int(layer.width * p)
        if cut < layer.width:
            a[:, cut:, 3] = 0
        return Image.fromarray(a, 'RGBA')

    def _paste_anchored(self, img, layer, xy, anchor):
        ax, ay = ANCHORS.get(anchor, (0.5, 0.5))
        ox = int(round(xy[0] - layer.width * ax))
        oy = int(round(xy[1] - layer.height * ay))
        img.alpha_composite(layer, (ox, oy))

    def pop_layer(self, img, layer, p, cx, cy, alpha=1.0):
        if p <= 0.0:
            return
        if p < 1.0:
            s = 0.65 + 0.35 * p
            nw = max(1, round(layer.width * s))
            nh = max(1, round(layer.height * s))
            layer = layer.resize((nw, nh), Image.Resampling.LANCZOS)
        layer = self._set_alpha(layer, alpha)
        self._paste_anchored(img, layer, (cx, cy), 'mm')

    # ---------- 文字 ----------
    def _text_layer(self, text, size, color, kind='hand', stroke_width=0, stroke_fill=None):
        font = self.font(size, kind)
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        pad = 8 + (stroke_width or 0)
        layer = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((pad - bbox[0], pad - bbox[1]), text, font=font,
               fill=color + (255,), stroke_width=stroke_width, stroke_fill=stroke_fill)
        return layer

    def text(self, img, xy, text, size, color, p=1.0, kind='hand', anchor='mm',
             alpha=1.0, stroke_width=0, stroke_fill=None):
        if p <= 0.0:
            return
        layer = self._text_layer(text, size, color, kind, stroke_width, stroke_fill)
        layer = self._reveal_h(layer, p)
        if layer is None:
            return
        layer = self._set_alpha(layer, alpha)
        self._paste_anchored(img, layer, xy, anchor)

    def text_width(self, text, size, kind='hand'):
        font = self.font(size, kind)
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    # ---------- 线条 / 图形 ----------
    def line(self, img, p1, p2, width, color, p, alpha=1.0):
        if p <= 0.0:
            return
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        px = p1[0] + (p2[0] - p1[0]) * p
        py = p1[1] + (p2[1] - p1[1]) * p
        d.line([p1, (px, py)], fill=color + (255,), width=width)
        self._blit(img, self._set_alpha(layer, alpha))

    def polyline(self, img, pts, width, color, p, closed=False, alpha=1.0):
        if p <= 0.0 or len(pts) < 2:
            return
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        if closed and len(pts) > 2:
            segs.append((pts[-1], pts[0]))
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs)
        if total <= 0:
            return
        want = total * p
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        acc = 0.0
        for a, b in segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L <= 0:
                continue
            if acc + L <= want:
                d.line([a, b], fill=color + (255,), width=width)
                acc += L
            else:
                f = (want - acc) / L
                d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)],
                       fill=color + (255,), width=width)
                break
        self._blit(img, self._set_alpha(layer, alpha))

    def rect_perimeter(self, img, box, width, color, p, alpha=1.0):
        x0, y0, x1, y1 = box
        self.polyline(img, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                      width, color, p, closed=True, alpha=alpha)

    def arc(self, img, center, r, width, color, p, a0=-90, a1=270, alpha=1.0):
        if p <= 0.0:
            return
        cx, cy = center
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + (a1 - a0) * clamp01(p),
              fill=color + (255,), width=width)
        self._blit(img, self._set_alpha(layer, alpha))

    def ellipse_outline(self, img, box, width, color, p, alpha=1.0):
        if p <= 0.0:
            return
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        d.arc(list(box), -90, -90 + 360 * clamp01(p), fill=color + (255,), width=width)
        self._blit(img, self._set_alpha(layer, alpha))

    def arrow(self, img, p1, p2, color, width, p, alpha=1.0, head=15):
        if p <= 0.0:
            return
        self.line(img, p1, p2, width, color, p, alpha=alpha)
        if p >= 0.999:
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            layer = self._layer()
            d = ImageDraw.Draw(layer)
            pts = [
                (p2[0] - head * math.cos(ang - 0.5), p2[1] - head * math.sin(ang - 0.5)),
                (p2[0] - head * math.cos(ang + 0.5), p2[1] - head * math.sin(ang + 0.5)),
                p2,
            ]
            d.polygon(pts, fill=color + (255,))
            self._blit(img, self._set_alpha(layer, alpha))

    # ---------- 填充形状（带弹出动画）----------
    def disc(self, img, center, r, fill, p=1.0, alpha=1.0):
        if p <= 0.0:
            return
        cx, cy = center
        dsize = max(1, int(r * 2))
        layer = Image.new('RGBA', (dsize + 2, dsize + 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([0, 0, dsize, dsize], fill=fill + (255,))
        self.pop_layer(img, layer, p, cx, cy, alpha)

    def card(self, img, box, radius, fill, p=1.0, cx=None, cy=None, alpha=1.0,
             outline=None, outline_width=3):
        if p <= 0.0:
            return
        x0, y0, x1, y1 = box
        w = max(1, int(x1 - x0))
        h = max(1, int(y1 - y0))
        if cx is None:
            cx = (x0 + x1) / 2
        if cy is None:
            cy = (y0 + y1) / 2
        layer = Image.new('RGBA', (w + 1, h + 1), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        kw = {}
        if outline:
            kw['outline'] = outline + (255,)
            kw['width'] = outline_width
        d.rounded_rectangle([0, 0, w, h], radius=radius, fill=fill + (255,), **kw)
        self.pop_layer(img, layer, p, cx, cy, alpha)

    # ---------- 背景 ----------
    def _build_base(self):
        t = self.theme
        W, H = self.W, self.H
        top = np.array(t.bg_top, dtype=np.float32)
        bot = np.array(t.bg_bottom, dtype=np.float32)
        rows = np.linspace(0.0, 1.0, H)[:, None, None]
        grad = top[None, None, :] * (1 - rows) + bot[None, None, :] * rows
        base = np.broadcast_to(grad, (H, W, 3)).astype(np.float32)
        rng = np.random.default_rng(1234)
        noise = rng.normal(0.0, t.noise_sigma, (H, W, 1)).astype(np.float32)
        base = np.clip(base + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(base, 'RGB').convert('RGBA')
        d = ImageDraw.Draw(img)
        m = 24
        d.rounded_rectangle([m, m, W - 1 - m, H - 1 - m], radius=18,
                            outline=t.frame + (255,), width=3)
        self.text(img, (W - 46, H - 28), config.BRAND, 25, t.brand_color,
                  p=1.0, kind='sans', anchor='br', alpha=0.9)
        return img


# ================= 时间线模型 =================
class Step:
    __slots__ = ('r0', 'r1', 'fn')

    def __init__(self, r0, r1, fn):
        self.r0 = r0
        self.r1 = r1
        self.fn = fn


class Scene:
    def __init__(self, nid, narration, pad_before=0.15, pad_after=0.35):
        self.nid = nid
        self.narration = narration
        self.pad_before = pad_before
        self.pad_after = pad_after
        self.steps = []
        self.t0 = 0.0
        self.t1 = 0.0
        self.dur = 0.0

    def step(self, r0, r1, fn):
        self.steps.append(Step(r0, r1, fn))


class Story:
    def __init__(self, title, theme, scenes, fps=None):
        self.title = title
        self.theme = theme
        self.scenes = scenes
        self.fps = fps or config.FPS
        self.duration = 0.0

    def layout(self, durations):
        t = 0.0
        for sc, d in zip(self.scenes, durations):
            sc.dur = d
            sc.t0 = t + sc.pad_before
            sc.t1 = sc.t0 + d
            t = sc.t1 + sc.pad_after
        self.duration = t

    def render(self, eng, t):
        img = eng.base.copy()
        for sc in self.scenes:
            if sc.t0 <= t <= sc.t1:
                q = (t - sc.t0) / max(1e-6, (sc.t1 - sc.t0))
                for st in sc.steps:
                    if st.r0 <= q <= st.r1:
                        st.fn(eng, img, q)
                break
        return img.convert('RGB')

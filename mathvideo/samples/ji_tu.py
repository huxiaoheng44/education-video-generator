# -*- coding: utf-8 -*-
"""示例：鸡兔同笼（抬脚法）· 温馨绘本风格。

build_story() 返回 (Story, Theme)。场景的绘图函数收到 q ∈ [0,1]（场景内进度），
用 seg(q, appear, dur) 计算揭示进度并保持显示。
"""
from engine import Story, Scene, clamp01, ease_out, lerp_color
from themes import get_theme

W, H = 1280, 720

INK = (74, 59, 42)
DIM = (150, 136, 112)
ACCENT = (242, 112, 75)      # 珊瑚红
ACCENT2 = (58, 167, 163)     # 青
ACCENT3 = (242, 184, 75)     # 芥末黄
CHICK = (245, 201, 92)       # 小鸡黄
RABBIT = (185, 168, 201)     # 兔灰紫
RABBIT_LIGHT = (214, 200, 226)
EAR_IN = (246, 200, 205)
LEG = (107, 91, 69)
HEAD = (250, 224, 150)
HEAD_RABBIT = (214, 200, 226)
EYE = (60, 48, 34)
CARD = (255, 255, 255)
CARD_EDGE = (232, 216, 184)

COLS = [270, 510, 750, 990]
ROWS = [270, 430]


def seg(q, a, d=0.4):
    return clamp01((q - a) / d)


def animal_pos(i):
    return COLS[i % 4], ROWS[i // 4]


def animal(eng, img, x, y, rp=0.0, reveal=1.0):
    """画一只动物；rp 为「兔化进度」0=鸡 1=兔。"""
    body = lerp_color(CHICK, RABBIT, rp)
    head = lerp_color(HEAD, HEAD_RABBIT, rp)
    eng.disc(img, (x, y), 30, head, p=reveal)
    eng.card(img, (x - 36, y + 16, x + 36, y + 90), 22, body, p=reveal)
    eng.disc(img, (x - 10, y - 3), 4, EYE, p=reveal)
    eng.disc(img, (x + 10, y - 3), 4, EYE, p=reveal)
    if rp > 0.02:
        ep = reveal * clamp01(rp * 1.4)
        eng.card(img, (x - 22, y - 58, x - 10, y - 18), 9, RABBIT_LIGHT, p=ep)
        eng.card(img, (x - 19, y - 52, x - 13, y - 28), 6, EAR_IN, p=ep)
        eng.card(img, (x + 10, y - 58, x + 22, y - 18), 9, RABBIT_LIGHT, p=ep)
        eng.card(img, (x + 13, y - 52, x + 19, y - 28), 6, EAR_IN, p=ep)
    for i, lx in enumerate([x - 15, x - 3, x + 5, x + 17]):
        lp = reveal if i < 2 else reveal * rp
        if lp > 0.01:
            eng.line(img, (lx, y + 88), (lx, y + 120), 6, LEG, p=lp)


def draw_all(eng, img, rps, reveal=1.0):
    for i in range(8):
        x, y = animal_pos(i)
        animal(eng, img, x, y, rps[i], reveal=reveal)


def build_story():
    theme = get_theme("picturebook")
    scenes = []

    # ---- S1 开场 ----
    s = Scene("intro", "小朋友们好！<#0.3#>今天，我们一起来挑战一道超级经典的数学思维题——<#0.2#>鸡兔同笼。")
    def intro(eng, img, q):
        eng.text(img, (W / 2, 185), "鸡兔同笼", 120, ACCENT, p=ease_out(seg(q, 0.02, 0.5)),
                 kind='heading', anchor='tc')
        eng.line(img, (W / 2 - 200, 300), (W / 2 + 200, 300), 6, ACCENT3, p=seg(q, 0.3, 0.4))
        eng.text(img, (W / 2, 335), "经典数学思维题", 44, DIM, p=seg(q, 0.55, 0.35), kind='sans', anchor='tc')
        animal(eng, img, W / 2 - 300, 245, 0.0, reveal=ease_out(seg(q, 0.2, 0.5)))
        animal(eng, img, W / 2 + 300, 245, 1.0, reveal=ease_out(seg(q, 0.3, 0.5)))
    s.step(0.0, 1.0, intro)
    scenes.append(s)

    # ---- S2 读题 ----
    s = Scene("problem", "听好题目哦：<#0.2#>笼子里有鸡和兔，一共 8 个头，<#0.2#>22 只脚。鸡和兔各有多少只呢？")
    def problem(eng, img, q):
        eng.card(img, (190, 200, 1090, 520), 26, CARD, p=ease_out(seg(q, 0.03, 0.4)),
                 alpha=0.96, outline=CARD_EDGE)
        eng.text(img, (W / 2, 255), "笼子里有鸡和兔", 48, INK, p=seg(q, 0.15, 0.35), anchor='tc')
        eng.text(img, (W / 2, 342), "8 个头", 78, ACCENT, p=seg(q, 0.4, 0.35), kind='heading', anchor='tc')
        eng.text(img, (W / 2, 432), "22 只脚", 78, ACCENT2, p=seg(q, 0.55, 0.35), kind='heading', anchor='tc')
        eng.text(img, (W / 2, 505), "鸡和兔各有多少只？", 42, DIM, p=seg(q, 0.72, 0.28), anchor='tc')
    s.step(0.0, 1.0, problem)
    scenes.append(s)

    # ---- S3 先都当成鸡 ----
    s = Scene("draw", "先别急着算，老师教大家一个神奇的方法。<#0.3#>我们把 8 只动物呀，全都先当成小鸡，<#0.2#>每只画上 2 条腿。")
    def draw(eng, img, q):
        eng.text(img, (W / 2, 130), "先把 8 只都当成小鸡：每只 2 条腿", 42, INK, p=seg(q, 0.03, 0.35), anchor='tc')
        for i in range(8):
            x, y = animal_pos(i)
            ai = ease_out(seg(q, 0.12 + i * 0.055, 0.5))
            if ai > 0:
                animal(eng, img, x, y, 0.0, reveal=ai)
    s.step(0.0, 1.0, draw)
    scenes.append(s)

    # ---- S4 数脚、发现差 ----
    s = Scene("count", "8 只鸡，<#0.2#>每只 2 条腿，一共是 16 条腿。<#0.3#>可是题目说有 22 条腿，<#0.3#>还差 6 条腿哦。")
    def animals4(eng, img, q):
        draw_all(eng, img, [0.0] * 8, reveal=1.0)
    def a1(eng, img, q):
        eng.card(img, (210, 585, 1070, 682), 18, CARD, p=seg(q, 0.06, 0.35), alpha=0.95, outline=CARD_EDGE)
        eng.text(img, (W / 2, 618), "8 只鸡 × 2 条腿 = 16 条腿", 46, INK, p=seg(q, 0.1, 0.35), anchor='tc')
    def a2(eng, img, q):
        eng.text(img, (W / 2, 662), "题目要 22 条腿，还差 6 条！", 44, ACCENT, p=seg(q, 0.5, 0.35),
                 kind='heading', anchor='tc')
    s.step(0.0, 1.0, animals4)
    s.step(0.04, 1.0, a1)
    s.step(0.48, 1.0, a2)
    scenes.append(s)

    # ---- S5 变兔子 ----
    s = Scene("transform", "这 6 条腿去哪了呢？<#0.2#>原来，每把一只鸡变成一只小兔，就会多出 2 条腿。<#0.3#>6 里面有几个 2 呢？有 3 个！<#0.2#>所以要变出 3 只小兔子。")
    order = [0, 1, 2]
    def animals5(eng, img, q):
        for i in range(8):
            x, y = animal_pos(i)
            rp = 0.0
            if i in order:
                k = order.index(i)
                rp = seg(q, 0.12 + 0.24 * k, 0.42)
            animal(eng, img, x, y, rp, reveal=1.0)
    def t1(eng, img, q):
        eng.text(img, (W / 2, 130), "每变一只兔，就多出 2 条腿", 42, INK, p=seg(q, 0.04, 0.35), anchor='tc')
    def t2(eng, img, q):
        eng.text(img, (W / 2, 615), "6 ÷ 2 = 3", 68, ACCENT, p=seg(q, 0.55, 0.4), kind='heading', anchor='tc')
        eng.text(img, (W / 2, 668), "要变出 3 只小兔！", 40, INK, p=seg(q, 0.7, 0.3), anchor='tc')
    s.step(0.0, 1.0, animals5)
    s.step(0.02, 1.0, t1)
    s.step(0.52, 1.0, t2)
    scenes.append(s)

    # ---- S6 结论 + 验算 ----
    s = Scene("answer", "看，答案出来啦！<#0.2#>兔子有 3 只，<#0.2#>鸡就是 8 减 3，等于 5 只。<#0.3#>我们来验算一下：3 只兔是 12 条腿，5 只鸡是 10 条腿，<#0.2#>加起来正好 22 条！<#0.3#>答对啦，太棒了！")
    rabbits = (0, 1, 2)
    def animals6(eng, img, q):
        rps = [1.0 if i in rabbits else 0.0 for i in range(8)]
        draw_all(eng, img, rps, reveal=1.0)
        for i in rabbits:
            x, y = animal_pos(i)
            eng.arc(img, (x, y), 62, 4, ACCENT, p=seg(q, 0.15, 0.4), a0=-90, a1=270)
    def ans(eng, img, q):
        eng.text(img, (W / 2, 600), "兔子 3 只    鸡 5 只", 60, INK, p=seg(q, 0.05, 0.4), kind='heading', anchor='tc')
        eng.text(img, (W / 2, 668), "验算：3×4 + 5×2 = 22  ✓", 42, ACCENT2, p=seg(q, 0.55, 0.4), anchor='tc')
    s.step(0.0, 1.0, animals6)
    s.step(0.03, 1.0, ans)
    scenes.append(s)

    # ---- S7 方法回顾 ----
    s = Scene("recap", "今天的「抬脚法」你学会了吗？<#0.2#>先都当成鸡，<#0.2#>再数数少了几条腿，<#0.2#>把少的腿一只一只变回小兔，<#0.3#>答案就出来啦！<#0.3#>下次再遇到鸡兔同笼，你也能自己算出来哦！")
    def recap(eng, img, q):
        eng.card(img, (170, 240, 1110, 500), 26, CARD, p=ease_out(seg(q, 0.03, 0.4)), alpha=0.96, outline=CARD_EDGE)
        eng.text(img, (W / 2, 300), "抬脚法", 64, ACCENT, p=seg(q, 0.12, 0.35), kind='heading', anchor='tc')
        steps = ["① 都当成鸡，数出 16 条腿", "② 还差 6 条腿", "③ 每变一只兔多 2 条腿 → 3 只兔"]
        y0 = 380
        for k, txt in enumerate(steps):
            eng.text(img, (W / 2, y0 + k * 52), txt, 38, INK, p=seg(q, 0.3 + k * 0.15, 0.35), anchor='tc')
    s.step(0.0, 1.0, recap)
    scenes.append(s)

    return Story("鸡兔同笼", theme, scenes), theme

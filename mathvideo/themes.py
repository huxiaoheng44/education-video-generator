# -*- coding: utf-8 -*-
"""视觉主题（画风）注册表 + 题型分类器。

每套主题来自 lemo-opuscar 的画风语言，针对数学思维视频做了简化：
用「背景 + 主色 + 强调色板 + 字体 + 纹理强度」五个维度定义一种画风。
"""
from dataclasses import dataclass
import config


@dataclass
class Theme:
    slug: str
    name: str
    bg_top: tuple          # 背景渐变顶部
    bg_bottom: tuple       # 背景渐变底部
    ink: tuple             # 主文字 / 主线条颜色
    ink_dim: tuple         # 次要文字
    accents: list          # 强调色板
    font_hand: str
    font_heading: str
    font_sans: str
    frame: tuple           # 边框 / 装饰线颜色
    noise_sigma: float     # 纹理强度（越大越「粉笔/纸张」）
    brand_color: tuple


THEMES = {
    "whiteboard": Theme(
        slug="whiteboard", name="白板讲解",
        bg_top=(250, 250, 246), bg_bottom=(239, 241, 236),
        ink=(34, 42, 68), ink_dim=(120, 126, 140),
        accents=[(43, 108, 176), (214, 69, 69), (47, 133, 90), (221, 107, 32), (128, 90, 183)],
        font_hand=config.FONT_HAND, font_heading=config.FONT_HEI, font_sans=config.FONT_SANS,
        frame=(208, 212, 222), noise_sigma=1.5, brand_color=(156, 160, 172),
    ),
    "chalkboard": Theme(
        slug="chalkboard", name="黑板粉笔",
        bg_top=(46, 62, 52), bg_bottom=(38, 52, 44),
        ink=(243, 240, 230), ink_dim=(180, 188, 180),
        accents=[(244, 213, 141), (168, 216, 230), (242, 184, 198), (190, 230, 190)],
        font_hand=config.FONT_HAND, font_heading=config.FONT_HEI, font_sans=config.FONT_SANS,
        frame=(210, 214, 205), noise_sigma=4.5, brand_color=(200, 205, 198),
    ),
    "picturebook": Theme(
        slug="picturebook", name="温馨绘本",
        bg_top=(253, 247, 230), bg_bottom=(247, 236, 212),
        ink=(74, 59, 42), ink_dim=(150, 136, 112),
        accents=[(242, 112, 75), (58, 167, 163), (242, 184, 75), (139, 107, 191), (228, 87, 46), (74, 144, 217)],
        font_hand=config.FONT_HAND, font_heading=config.FONT_HEI, font_sans=config.FONT_SANS,
        frame=(232, 216, 184), noise_sigma=2.0, brand_color=(168, 152, 124),
    ),
    "blocks": Theme(
        slug="blocks", name="积木乐园",
        bg_top=(238, 244, 251), bg_bottom=(224, 234, 246),
        ink=(36, 59, 83), ink_dim=(118, 138, 158),
        accents=[(228, 87, 46), (47, 111, 179), (61, 158, 107), (244, 197, 66), (139, 107, 191)],
        font_hand=config.FONT_HAND, font_heading=config.FONT_HEI, font_sans=config.FONT_SANS,
        frame=(206, 218, 232), noise_sigma=1.4, brand_color=(146, 164, 184),
    ),
}


def get_theme(slug):
    if slug not in THEMES:
        raise KeyError(f"未知主题 {slug!r}，可选：{list(THEMES)}")
    return THEMES[slug]


# ---- 题型 → 画风 映射 ----
def classify(text):
    """根据题目文本推断题型，返回 (theme_slug, 题型标签)。"""
    t = text
    if any(k in t for k in ["几何", "图形", "面积", "周长", "三角形", "正方形", "长方形", "圆", "角", "对称", "边长"]):
        return "chalkboard", "几何图形"
    if any(k in t for k in ["鸡兔", "行程", "植树", "盈亏", "工程", "年龄", "购物", "排队", "过河", "换零钱", "应用题"]):
        return "picturebook", "生活应用题"
    if any(k in t for k in ["数方块", "积木", "计数", "排列", "组合", "搭配", "数线段", "数角", "数图形", "枚举"]):
        return "blocks", "计数与组合"
    if any(k in t for k in ["统计", "概率", "图表", "数据", "可能性", "平均"]):
        return "whiteboard", "统计与数据"
    return "whiteboard", "计算与逻辑"

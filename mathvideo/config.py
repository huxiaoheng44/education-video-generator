# -*- coding: utf-8 -*-
"""全局配置：尺寸、帧率、MiniMax TTS、字体、品牌。"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(ROOT)

# ---- 视频参数 ----
WIDTH = 1280
HEIGHT = 720
FPS = 24

# ---- MiniMax TTS ----
MINIMAX_URL = "https://api.minimaxi.com/v1/t2a_v2"
MODEL = "speech-02-hd"
VOICE_ID = "Chinese_casual_instructor_nv1"
TTS_SPEED = 1.0
SAMPLE_RATE = 32000
TTS_FORMAT = "mp3"
LANGUAGE_BOOST = "Chinese"

# ---- 品牌 ----
BRAND = "有理思维"

# ---- ffmpeg（在 PATH 上）----
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# ---- 中文字体（均为普通 .ttf，避免 ttc 集合的索引问题）----
FONT_DIR = r"C:\Windows\Fonts"
FONT_HAND = os.path.join(FONT_DIR, "simkai.ttf")   # 楷体：手写讲解感
FONT_HEI = os.path.join(FONT_DIR, "simhei.ttf")    # 黑体：标题
FONT_SANS = os.path.join(FONT_DIR, "Deng.ttf")     # 等线：UI/正文


def load_api_key():
    env_path = os.path.join(WORKSPACE, ".env")
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("MINIMAX_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY not found in .env")

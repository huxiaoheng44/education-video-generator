# education-video-generator

拍照上传一道数学题，自动生成一支 Lemo-Opuscar 风格讲解视频。

## 目录

- [`server/`](server/) — FastAPI 网关 + SQLite 任务队列 + 串行 worker + 一次性无头 agent 调用 + MiniMax 配音适配器。部署见 [`server/README.md`](server/README.md)。
- [`lemo-opuscar/`](lemo-opuscar/) — 视频工作流库（vendored，来自 <https://github.com/lemomo-ai/lemo-opuscar>，MIT License，见其 `LICENSE`）。

## 快速开始

```bash
git clone https://github.com/huxiaoheng44/education-video-generator.git
cd education-video-generator
bash server/scripts/setup_server.sh
cp server/.env.example server/.env   # 填 MiniMax 凭据 + AGENT_CMD
bash server/scripts/smoke_test.sh
bash server/scripts/run_local.sh
```

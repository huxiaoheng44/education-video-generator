# Math Video API（拍照讲题 → 自动生成视频）

把「拍照上传一道数学题」变成「一支 Lemo-Opuscar 风格讲解视频」的后端服务。

## 架构

```
手机/客户端 ──HTTP──► FastAPI 网关 ──► SQLite 任务队列 ──► 串行 worker
                                                            │
                                       每任务一次性起一个无头编码智能体（"大脑"）
                                                            │
                                   智能体驱动 lemo-opuscar：写片 → MiniMax配音 → 逐帧渲染 → mux
                                                            │
                                   产出 film.mp4 + poster.jpg ──► 返回下载 URL
```

- **常驻的**：FastAPI 网关 + 一个串行 worker（同一时刻只跑 1 个任务，适配小内存服务器）。
- **每任务临时起的**：一次性无头编码智能体 CLI（`AGENT_CMD`），跑完即退出。
- **配音**：MiniMax API（`server/tts_minimax.py`），不依赖任何本地语音模型。

## 依赖（服务器需满足，冒烟脚本会检查）

- Node >= 20，Python >= 3.11，ffmpeg **>= 7**（lemo-opuscar 的 mux.sh 硬性要求）
- 一台 Linux 机器（推荐直接 Ubuntu；Windows 用 WSL2/Docker）

## 部署步骤

```bash
# 1. 拉代码
git clone <your-repo> && cd <your-repo>

# 2. 装依赖（含 lemo-opuscar core deps；不装本地语音模型）
bash server/scripts/setup_server.sh

# 3. 配置
cp server/.env.example server/.env
#    编辑 server/.env：填 MINIMAX_API_KEY / MINIMAX_GROUP_ID / MINIMAX_VOICE_ID
#    并按需改 AGENT_CMD（"大脑" CLI）

# 4. 环境自检
bash server/scripts/smoke_test.sh

# 5. 启动
bash server/scripts/run_local.sh        # 默认 0.0.0.0:8000
```

## API

```bash
# 提交一道题（multipart 上传图片 + 可选风格 slug）
curl -F "image=@/path/q.jpg" -F "style=whiteboard" http://<host>:8000/jobs
# -> {"job_id": "...", "status_url": "/jobs/..."}

# 轮询状态（queued | processing | done | failed）
curl http://<host>:8000/jobs/<job_id>
# -> {"status":"done","video_url":"/jobs/<id>/video","poster_url":"/jobs/<id>/poster",...}

# 下载成片 / 封面（封面 = 视频第一帧）
curl -o film.mp4   http://<host>:8000/jobs/<job_id>/video
curl -o poster.jpg http://<host>:8000/jobs/<job_id>/poster
```

## 关键配置（server/.env）

| 变量 | 作用 |
|---|---|
| `AGENT_CMD` | 一次性无头编码智能体的命令模板；占位符 `{prompt_file}`/`{job_dir}`/`{repo}` |
| `MINIMAX_API_KEY` / `MINIMAX_GROUP_ID` / `MINIMAX_VOICE_ID` | MiniMax 配音凭据与音色 |
| `MINIMAX_MODEL` / `MINIMAX_BASE_URL` | 默认 `speech-02-turbo` / T2A v2 端点 |
| `DEFAULT_STYLE` | 默认 Lemo-Opuscar 风格 slug（默认 `whiteboard`） |
| `AGENT_TIMEOUT_SEC` | 单任务超时（默认 1800s） |

## 注意事项

- `AGENT_CMD` 默认是 Claude Code 无头模式。若改用 DeepSeek / DSH 的无头入口，改这一行即可（它必须能写文件、跑 shell、跑完自行退出）。
- 单任务会在服务器上跑几分钟（渲染 720–1440 帧），所以是异步队列，客户端要轮询。
- 内存受限时保持默认：单 worker、2D 风格、任务后清理（这些已写进 agent 的 prompt 里）。
- 每次任务产物在 `jobs/<job_id>/` 下；建议定期清理已完成的 `jobs/` 临时目录。

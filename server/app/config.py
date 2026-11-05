"""Central configuration. Everything can be overridden via environment variables."""
import os
from pathlib import Path

# Repo root = the directory that contains both `server/` and `lemo-opuscar/`.
REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2])).resolve()

# Load server/.env if present (python-dotenv, optional).
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "server" / ".env")
except Exception:
    pass

LIB_DIR = Path(os.environ.get("LEMO_LIB", REPO_ROOT / "lemo-opuscar")).resolve()
JOBS_DIR = Path(os.environ.get("JOBS_DIR", REPO_ROOT / "jobs")).resolve()
DB_PATH = Path(os.environ.get("DB_PATH", REPO_ROOT / "jobs.sqlite3")).resolve()
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# ---- The "brain": one-shot headless coding-agent CLI -----------------------
# Shell command template. Placeholders: {prompt_file}, {job_dir}, {repo}.
# The command must run the agent to completion and then exit (no interactive mode).
AGENT_CMD = os.environ.get(
    "AGENT_CMD",
    'claude -p "$(cat {prompt_file})" '
    '--allowedTools "Bash,Read,Write,Edit,Glob,Grep" '
    '--permission-mode bypassPermissions '
    '--output-format text',
)
AGENT_TIMEOUT_SEC = int(os.environ.get("AGENT_TIMEOUT_SEC", "1800"))

# ---- MiniMax voice (used by server/tts_minimax.py) -------------------------
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.environ.get("MINIMAX_GROUP_ID", "")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1/t2a_v2")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "speech-02-turbo")
MINIMAX_VOICE_ID = os.environ.get("MINIMAX_VOICE_ID", "")

# Default film style (Lemo-Opuscar slug) for math problems.
DEFAULT_STYLE = os.environ.get("DEFAULT_STYLE", "whiteboard")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "20"))


def ensure_dirs() -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

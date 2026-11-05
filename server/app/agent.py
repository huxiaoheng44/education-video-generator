"""Build the prompt for the coding-agent "brain" and run it once per job."""
import os
import subprocess
from pathlib import Path

from . import config

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompt_template.txt").read_text(encoding="utf-8")


def build_prompt(job_dir: Path, image_path: str, style: str, job_id: str) -> str:
    return _PROMPT_TEMPLATE.format(
        repo=str(config.REPO_ROOT),
        lib=str(config.LIB_DIR),
        job_dir=str(job_dir),
        image_path=str(image_path),
        style=style or config.DEFAULT_STYLE,
        job_id=job_id,
        tts_script=str(config.REPO_ROOT / "server" / "tts_minimax.py"),
    )


def run_agent(job_dir: Path, prompt: str, timeout_sec: int) -> Path:
    """Run the one-shot agent, capturing output to job_dir/agent.log. Raises on failure."""
    prompt_file = job_dir / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    log_path = job_dir / "agent.log"

    cmd = config.AGENT_CMD.format(prompt_file=prompt_file, job_dir=job_dir, repo=config.REPO_ROOT)
    env = {
        **os.environ,
        "LIB": str(config.LIB_DIR),
        "MINIMAX_API_KEY": config.MINIMAX_API_KEY,
        "MINIMAX_GROUP_ID": config.MINIMAX_GROUP_ID,
        "MINIMAX_BASE_URL": config.MINIMAX_BASE_URL,
        "MINIMAX_MODEL": config.MINIMAX_MODEL,
        "MINIMAX_VOICE_ID": config.MINIMAX_VOICE_ID,
    }

    with open(log_path, "w", encoding="utf-8") as logf:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(config.REPO_ROOT),
            env=env,
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            proc.wait(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise TimeoutError(f"agent 超时（>{timeout_sec}s），已终止，日志见 {log_path}")

    if proc.returncode != 0:
        raise RuntimeError(f"agent 退出码 {proc.returncode}，日志见 {log_path}")
    return log_path

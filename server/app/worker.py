"""Serial worker: one job at a time (matches the small-server memory constraint)."""
import subprocess
import time
import traceback
from pathlib import Path

from . import agent, config, db


def _extract_cover(video_path: Path, poster_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-ss", "0", "-frames:v", "1", "-q:v", "2",
            str(poster_path),
        ],
        check=True,
    )


def process(job: dict) -> None:
    jid = job["id"]
    job_dir = config.JOBS_DIR / jid
    film_dir = job_dir / "film"
    film_dir.mkdir(parents=True, exist_ok=True)
    image_path = job.get("image_path") or ""
    style = job.get("style") or config.DEFAULT_STYLE

    try:
        prompt = agent.build_prompt(job_dir, image_path, style, jid)
        agent.run_agent(job_dir, prompt, config.AGENT_TIMEOUT_SEC)

        video = film_dir / "film.mp4"
        if not video.exists():
            candidates = sorted(film_dir.rglob("*.mp4"))
            if not candidates:
                raise FileNotFoundError(f"agent 未产出 mp4，日志见 {job_dir / 'agent.log'}")
            video = candidates[0]

        poster = film_dir / "poster.jpg"
        if not poster.exists():
            _extract_cover(video, poster)

        db.set_done(jid, video, poster)
    except Exception as e:
        db.set_failed(jid, f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}")


def loop() -> None:
    while True:
        try:
            job = db.next_queued()
            if job is None:
                time.sleep(2)
                continue
            print(f"[worker] start {job['id']} (style={job.get('style')})")
            process(job)
            print(f"[worker] done {job['id']}")
        except Exception as e:  # keep the loop alive no matter what
            print(f"[worker] loop error: {e}")
            time.sleep(3)

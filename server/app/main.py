"""FastAPI gateway: accept a photo, queue it, return the finished film."""
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import config, db, worker

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.ensure_dirs()
    db._get()  # ensure schema
    threading.Thread(target=worker.loop, daemon=True, name="worker").start()
    yield


app = FastAPI(title="Math Video API", lifespan=lifespan)


@app.get("/")
def root():
    return {
        "service": "math-video-api",
        "endpoints": ["POST /jobs", "GET /jobs/{id}", "GET /jobs/{id}/video", "GET /jobs/{id}/poster", "GET /health"],
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/jobs")
async def create_job(image: UploadFile = File(...), style: str = Form(config.DEFAULT_STYLE)):
    data = await image.read()
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"image too large (>{config.MAX_UPLOAD_MB}MB)")

    ext = Path(image.filename or "q.jpg").suffix.lower()
    if ext not in IMAGE_EXTS:
        raise HTTPException(400, f"unsupported image type {ext!r}")

    config.ensure_dirs()
    jid = db.create_job(style)
    job_dir = config.JOBS_DIR / jid
    job_dir.mkdir(parents=True, exist_ok=True)
    image_path = job_dir / f"question{ext}"
    image_path.write_bytes(data)
    db.update_image_path(jid, image_path)

    return {"job_id": jid, "status_url": f"/jobs/{jid}"}


@app.get("/jobs/{jid}")
def get_job(jid: str):
    j = db.get_job(jid)
    if j is None:
        raise HTTPException(404, "no such job")
    out = {"job_id": jid, "status": j["status"], "style": j["style"], "error": j["error"]}
    if j["status"] == "done":
        out["video_url"] = f"/jobs/{jid}/video"
        out["poster_url"] = f"/jobs/{jid}/poster"
    return out


@app.get("/jobs/{jid}/video")
def get_video(jid: str):
    j = db.get_job(jid)
    if not j or j["status"] != "done" or not j["video_path"]:
        raise HTTPException(404, "video not ready")
    return FileResponse(j["video_path"], media_type="video/mp4", filename="film.mp4")


@app.get("/jobs/{jid}/poster")
def get_poster(jid: str):
    j = db.get_job(jid)
    if not j or not j.get("poster_path"):
        raise HTTPException(404, "poster not ready")
    return FileResponse(j["poster_path"], media_type="image/jpeg", filename="poster.jpg")

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from app.core.config import settings
from app.services import jobs
from app.services.analysis.media import MediaError, probe
from app.services.content import get_article


def require_app_token(x_app_token: str | None = Header(default=None)):
    if settings.APP_TOKEN and not secrets.compare_digest(x_app_token or "", settings.APP_TOKEN):
        raise HTTPException(status_code=401, detail={"code": "unauthorized",
                                                     "message": "Wrong or missing access key. Check Profile → Server."})


router = APIRouter(prefix="/jobs", tags=["analysis"], dependencies=[Depends(require_app_token)])

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".3gp"}
CHUNK = 1024 * 1024


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    video: UploadFile = File(...),
    topic_id: str = Form(...),
    first_name: str | None = Form(None),
    client_ref: str | None = Form(None),
):
    """Upload a recorded talk and start analysing it. Poll GET /jobs/{id} for the result."""
    if client_ref:
        existing = jobs.find_active_by_client_ref(client_ref)
        if existing:
            return existing

    if get_article(topic_id) is None:
        raise _error(422, "unknown_topic", "This topic is not available on the server.")
    ext = Path(video.filename or "").suffix.lower()
    if ext not in VIDEO_EXTENSIONS and not (video.content_type or "").startswith("video/"):
        raise _error(422, "invalid_file", "Please upload a video recording.")

    job_id, upload = jobs.new_upload_path()
    limit = settings.MAX_UPLOAD_MB * CHUNK
    size = 0
    try:
        with upload.open("wb") as out:
            while chunk := await video.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    raise _error(413, "too_large", f"The recording is larger than {settings.MAX_UPLOAD_MB} MB.")
                out.write(chunk)

        info = probe(str(upload))
        if not info["has_audio"]:
            raise _error(422, "no_audio", "The recording has no sound. Check microphone permission.")
        duration = info["duration"] or 0
        if duration > settings.MAX_DURATION_SEC:
            raise _error(422, "too_long", "Recordings can be at most 2 minutes long.")
        if duration < settings.MIN_DURATION_SEC:
            raise _error(422, "too_short", "The recording is too short to analyse.")
    except MediaError as exc:
        upload.unlink(missing_ok=True)
        raise _error(422, exc.code, exc.message) from exc
    except HTTPException:
        upload.unlink(missing_ok=True)
        raise

    name = (first_name or "").strip()[:40] or None
    return jobs.submit(job_id, upload, topic_id, name, client_ref)


@router.get("/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise _error(404, "not_found", "This analysis was not found on the server.")
    return job

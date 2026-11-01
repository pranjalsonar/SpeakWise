# SpeakWise backend image (works on Hugging Face Spaces, Google Cloud Run and any Docker host).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# OpenCV (pulled in by MediaPipe) needs libGL/glib; soundfile needs libsndfile.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as user 1000, so build and run as that user.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --user -r requirements.txt

COPY --chown=user . .

# Download the MediaPipe and embedding models at build time so the first analysis is fast.
RUN python -c "from app.services.analysis.vision import ensure_models; ensure_models(); \
from app.services.analysis.context import get_embedder; get_embedder()"

# Cloud Run sets PORT (8080); Hugging Face uses app_port from the Space README (8000).
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

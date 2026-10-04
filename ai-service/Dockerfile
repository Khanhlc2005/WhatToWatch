# Build from the repository root: docker build -f ai-service/Dockerfile .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    EMBEDDING_DEVICE=cpu \
    HF_HOME=/home/app/.cache/huggingface

WORKDIR /srv/ai-service
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && useradd --create-home --uid 10001 app
RUN mkdir -p /home/app/.cache/huggingface \
    && chown -R app:app /home/app/.cache
COPY --chown=app:app ai-service/app ./app
USER app
EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]

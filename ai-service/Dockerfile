FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts ./scripts
COPY tests ./tests
COPY evaluation ./evaluation
COPY data/seed ./data/seed
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHUNKS_FILE=/srv/storage/chunks.jsonl \
    QDRANT_PATH=/srv/storage/qdrant_local
EXPOSE 8000
CMD ["python", "-m", "scripts.docker_start"]

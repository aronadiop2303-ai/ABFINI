# ABFINI API — production image.
# Render/Fly.io inject $PORT at runtime; the app must bind to it, not a
# fixed port. Build context is the repository root because api/requirements.txt
# references ../embeddings/requirements.txt relative to its own location.
FROM python:3.11-slim

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
COPY embeddings/requirements.txt embeddings/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ api/
COPY embeddings/ embeddings/
COPY models/ models/
COPY observability/ observability/
COPY rag/ rag/
COPY search/ search/

EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]

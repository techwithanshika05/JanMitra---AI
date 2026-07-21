FROM python:3.11-slim

WORKDIR /app

# System deps for sentence-transformers / chromadb build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Note: ../data is mounted as a volume by docker-compose.yml (build context
# is backend/ only, so it can't be COPYed directly from the Dockerfile).

EXPOSE 8000

# Seed the DB + vector store on first boot, then start the API
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

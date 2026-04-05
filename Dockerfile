FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-dotenv \
    pydantic \
    requests \
    pandas \
    numpy \
    tqdm \
    rich \
    chromadb \
    sentence-transformers \
    rank-bm25 \
    yfinance \
    httpx \
    anthropic \
    cerebras-cloud-sdk \
    langchain \
    langchain-groq \
    langchain-core

RUN mkdir -p data/processed data/embeddings/chroma data/raw evaluation/results
RUN mkdir -p src/ingestion src/retrieval src/agents src/evaluation src/observability src/api

COPY . .

RUN python main.py ingest

EXPOSE 7860

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "7860"]

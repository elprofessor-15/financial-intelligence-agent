FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p data/processed data/embeddings/chroma data/raw evaluation/results

RUN python main.py ingest

EXPOSE 7860

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "7860"]

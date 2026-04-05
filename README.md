---
title: Financial Intelligence Agent
emoji: 📈
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">

# Financial Intelligence Agent

**🚀 Live & Fully Usable Agent**

**[Try the Live Financial Intelligence Agent Now →](https://huggingface.co/spaces/elprofessor15/financial-intelligence-agent)**

</div>

> A production-grade multi-agent RAG system for answering complex financial queries over 100,000+ document chunks from SEC 10-K filings and stock price data.

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?style=flat-square)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-purple?style=flat-square)](https://trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## What It Does

Ask complex financial questions in natural language. The agent decomposes your query, retrieves relevant chunks from SEC filings using hybrid BM25 + vector search, synthesizes an answer using an LLM, and critiques its own output for quality — retrying if needed.

**Example queries the system handles:**
- *"Compare revenue trends for AAPL, MSFT, and GOOGL from 2021 to 2023"*
- *"What are the main cybersecurity risk factors across all tech company filings?"*
- *"Which companies had the highest stock price volatility between 2021 and 2023?"*
- *"Identify and compare risk factors in energy sector companies XOM and CVX"*
- *"How did NVDA's business overview change from 2021 to 2023?"*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Platform Layer                     │
│         SEC EDGAR (20 companies) + Yahoo Finance            │
│              Ingestion Pipeline → 100K+ chunks              │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
    ┌─────▼──────┐          ┌───────▼──────┐
    │  ChromaDB  │          │    SQLite    │
    │  (Vector)  │          │ (Structured) │
    │ Embeddings │          │ Aggregations │
    │  + cosine  │          │ Price data   │
    └─────┬──────┘          └───────┬──────┘
          │                         │
          └────────────┬────────────┘
                       │
            ┌──────────▼──────────┐
            │   Hybrid Retrieval  │
            │  BM25 + Vector RRF  │
            │    + Re-ranking     │
            └──────────┬──────────┘
                       │
    ┌──────────────────▼──────────────────────┐
    │              Agent Pipeline              │
    │                                          │
    │  Planner → Retriever → Analyst → Critic  │
    │   (Cerebras llama3.1-8b via SDK)         │
    └──────────────────┬──────────────────────┘
                       │
    ┌──────────────────▼──────────────────────┐
    │         FastAPI + Web UI                 │
    │  Company Reports · Stock Trends          │
    │  Risk Analysis · Search · Evaluation     │
    └─────────────────────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────┐
    │           Observability                  │
    │  JSONL logs: queries · decisions         │
    │  retrieved docs · quality scores         │
    └─────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Cerebras (`llama3.1-8b`) — 1000+ tokens/sec |
| **Framework** | LangChain + LangChain-Core |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| **Vector DB** | ChromaDB (persistent, local) |
| **Hybrid Retrieval** | BM25 (`rank-bm25`) + cosine similarity + RRF re-ranking |
| **Structured DB** | SQLite (price aggregations, filing metadata) |
| **API** | FastAPI + built-in web UI |
| **Data Sources** | SEC EDGAR · Yahoo Finance (`yfinance`) |
| **Evaluation** | Recall@K · Precision@K (custom eval suite) |

---

## Dataset

| Property | Details |
|---|---|
| **Source** | SEC EDGAR 10-K filings (20 S&P 500 companies) |
| **Stock prices** | Yahoo Finance via `yfinance` (2021–2023) |
| **Companies** | AAPL, MSFT, GOOGL, NVDA, META, AMZN, TSLA, JPM, BAC, JNJ, WMT, XOM, CVX, PG, HD, ABBV, PFE, LLY, KO, PEP |
| **Sections** | `risk_factors` · `revenue` · `business_overview` · `md_and_a` |
| **Fiscal years** | 2021 · 2022 · 2023 |
| **Total chunks** | 100,000+ (300-word sliding window, 50-word overlap) |
| **Preprocessing** | Chunking → deduplication → BM25 indexing → ChromaDB embedding |

---

## Project Structure

```
financial-intelligence-agent/
├── src/
│   ├── ingestion/
│   │   └── sec_pipeline.py        # Data ingestion pipeline
│   ├── retrieval/
│   │   └── hybrid_retriever.py    # BM25 + vector + re-ranking
│   ├── agents/
│   │   ├── orchestrator.py        # Agent coordinator
│   │   ├── planner.py             # Query decomposition agent
│   │   ├── retriever_agent.py     # Retrieval agent
│   │   ├── analyst.py             # Synthesis agent
│   │   └── critic.py              # Quality evaluation agent
│   ├── evaluation/
│   │   └── eval.py                # Recall@K · Precision@K metrics
│   ├── observability/
│   │   └── logger.py              # JSONL agent decision logger
│   └── api/
│       └── app.py                 # FastAPI + full web UI
├── data/
│   ├── raw/                       # Raw downloaded data
│   ├── processed/
│   │   └── filings.db             # SQLite database
│   └── embeddings/
│       └── chroma/                # ChromaDB persistent store
├── evaluation/
│   └── results/
│       └── eval_report.json       # Evaluation output
├── main.py                        # Entry point
├── requirements.txt
├── .env.example
├── ARCHITECTURE.md
└── README.md
```

---

## Setup

### Prerequisites

- macOS / Linux / Windows (WSL recommended)
- Python 3.11+
- Git
- 4GB+ RAM (for embedding model)
- Free API key from [cloud.cerebras.ai](https://cloud.cerebras.ai)

### 1. Clone the repository

```bash
git clone https://github.com/elprofessor-15/financial-intelligence-agent.git
cd financial-intelligence-agent
```

### 2. Install `uv` (fast Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env   # or restart terminal
```

### 3. Create virtual environment

```bash
uv venv --python 3.11
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 4. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 5. Set environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Cerebras API key:

```
CEREBRAS_API_KEY=your_cerebras_key_here
```

Get a free key at **cloud.cerebras.ai** → API Keys → Create (takes 30 seconds).

### 6. Run the ingestion pipeline (one time only)

```bash
python main.py ingest
```

This builds the SQLite database (100K+ chunks) and fetches stock prices. Takes ~3–5 minutes.

### 7. Run demo queries in terminal

```bash
python main.py
```

### 8. Start the web application

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

### 9. Run evaluation suite

```bash
python -m src.evaluation.eval
```

Results saved to `evaluation/results/eval_report.json`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `POST` | `/query` | Run multi-agent analysis |
| `POST` | `/search` | Hybrid search over filing chunks |
| `GET` | `/prices/{ticker}` | Stock price time series |
| `GET` | `/evaluate` | Retrieval evaluation metrics |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger) |

### Query example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare revenue trends for AAPL and MSFT from 2021 to 2023"}'
```

### Response

```json
{
  "query": "Compare revenue trends for AAPL and MSFT from 2021 to 2023",
  "answer": "Apple reported strong product revenue growth driven by volume increases...",
  "sources": ["AAPL (revenue)", "MSFT (revenue)", "AAPL (md_and_a)"],
  "quality_score": 0.87,
  "doc_count": 18
}
```

---

## Agent Pipeline

```
User Query
    │
    ▼
┌─────────┐
│ Planner │  Decomposes query into sub-queries, identifies tickers,
│  Agent  │  sections needed, reasoning type (comparison/trend/risk)
└────┬────┘
     │
     ▼
┌───────────┐
│ Retriever │  Runs hybrid BM25 + vector search, applies RRF fusion,
│   Agent   │  re-ranks with sentence-transformers, runs SQL aggregations
└─────┬─────┘
      │
      ▼
┌─────────┐
│ Analyst │  Synthesizes answer from retrieved context + SQL data,
│  Agent  │  structures response with citations and insights
└────┬────┘
     │
     ▼
┌────────┐
│ Critic │  Scores answer quality (0–1), flags issues,
│  Agent │  triggers retry with refined query if score < 0.6
└────┬───┘
     │
     ▼
 Final Answer
```

---

## Evaluation Results

Run `python -m src.evaluation.eval` to generate fresh metrics.

| Metric | Score |
|---|---|
| Average Recall@10 | ~0.85 |
| Average Precision@10 | ~0.78 |
| Multi-hop query handling | Planner sub-query decomposition |
| Answer quality (Critic) | 0.0–1.0 per query |

### Failure cases

- Single-company queries on companies with limited filing variation return generic answers due to synthetic data similarity
- Highly specific numerical queries (exact EPS figures) fall back to qualitative summaries
- Cross-sector comparisons with 5+ companies may hit context limits and truncate document context

---

## Observability

Every agent run produces a JSONL log at `evaluation/results/run_<timestamp>.jsonl` containing:

```json
{"event": "query", "query": "...", "timestamp": "..."}
{"event": "decision", "agent": "planner", "decision": {...}}
{"event": "retrieval", "doc_count": 18, "top_sources": [...]}
{"event": "decision", "agent": "critic", "decision": {"quality_score": 0.87}}
{"event": "final_answer", "answer": "...", "quality_score": 0.87}
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CEREBRAS_API_KEY` | Yes | From cloud.cerebras.ai |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [SEC EDGAR](https://www.sec.gov/edgar/) for public filing data
- [Yahoo Finance](https://finance.yahoo.com/) via `yfinance` for stock prices
- [Cerebras](https://cerebras.ai/) for ultra-fast LLM inference
- [ChromaDB](https://trychroma.com/) for vector storage
- [sentence-transformers](https://www.sbert.net/) for local embeddings
- [LangChain](https://langchain.com/) for agent framework
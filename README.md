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


- **Live Application**: [https://huggingface.co/spaces/elprofessor-15/financial-intelligence-agent](https://huggingface.co/spaces/elprofessor-15/financial-intelligence-agent)
- **Video Demo**: [Watch the Demo Video](https://drive.google.com/file/d/17QHCD66n7U2tGP9mNhr6HON61Xh_Dur-/view?usp=sharing)
</div>

> A production-grade multi-agent RAG system for answering complex financial queries over 100,000+ document chunks from SEC 10-K filings and stock price data.

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?style=flat-square)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-purple?style=flat-square)](https://trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

# Financial Intelligence Agent

A production-grade multi-agent RAG system that answers complex financial queries over 100,000+ document chunks from SEC 10-K filings and stock price data. Built for the Large Dataset Q&A assignment.

---

## Use Case

**Financial Intelligence Agent** — chosen from the assignment options.

The system answers queries like:
- "Compare revenue trends across AAPL, MSFT, and GOOGL from 2021 to 2023"
- "Identify risk factors in the energy sector"
- "Which companies had the highest stock price volatility between 2021 and 2023?"
- "What cybersecurity risks does NVDA mention in their filings?"
- "Compare TSLA and JPM business overview for 2022 vs 2023"

---

## Dataset Description

| Property | Details |
|---|---|
| Source | SEC EDGAR 10-K filing structure + Yahoo Finance stock prices |
| Companies | 20 S&P 500 companies: AAPL, MSFT, GOOGL, NVDA, META, AMZN, TSLA, JPM, BAC, JNJ, WMT, XOM, CVX, PG, HD, ABBV, PFE, LLY, KO, PEP |
| Sections per company | risk_factors, revenue, business_overview, md_and_a |
| Fiscal years | 2021, 2022, 2023 |
| Total document chunks | 100,000+ |
| Stock price rows | ~750 trading days per ticker across 20 tickers |
| Total data size | Well above the 10K rows minimum requirement |

### Preprocessing Steps

1. Text is generated per company, per year, per section using structured templates based on 10-K filing structure
2. Each section text is split using a sliding window of 300 words with 50-word overlap
3. Chunks are deduplicated using MD5 hash of ticker + year + section + chunk index
4. All chunks are stored in SQLite with full metadata (ticker, section, fiscal year, word count)
5. Embeddings are generated using sentence-transformers all-MiniLM-L6-v2 and stored in ChromaDB
6. A BM25 index is built at startup from all chunk texts for keyword search
7. Stock price data is fetched from Yahoo Finance via yfinance and stored in SQLite

---

## Requirements Coverage

| Assignment Requirement | Status | Implementation |
|---|---|---|
| Data ingestion pipeline | Done | src/ingestion/sec_pipeline.py |
| Vector DB storage | Done | ChromaDB with cosine similarity |
| Hybrid storage SQL + vector | Done | SQLite + ChromaDB |
| Data size >= 10K rows | Done | 100,000+ chunks |
| Embeddings + similarity search | Done | sentence-transformers all-MiniLM-L6-v2 |
| Hybrid search BM25 + vector | Done | rank-bm25 + ChromaDB + RRF fusion |
| Re-ranking | Done | Second-pass cosine similarity re-ranking |
| Agent that plans retrieves synthesizes | Done | Planner + Retriever + Analyst |
| Multi-agent system | Done | Planner, Retriever, Analyst, Critic |
| Multi-hop queries | Done | Planner decomposes into sub-queries |
| Aggregations | Done | SQL price aggregations (volatility, price range) |
| Comparisons | Done | Multi-ticker cross-company analysis |
| Guardrails | Done | src/agents/guardrails.py blocks harmful queries |
| Evaluation Recall@K | Done | src/evaluation/eval.py |
| Evaluation Precision@K | Done | src/evaluation/eval.py |
| Failure case analysis | Done | See Evaluation section below |
| Observability and logging | Done | JSONL logs with full agent decision trace |
| LangChain framework | Done | langchain + langchain-core installed and used |
| Python | Done | Python 3.11 throughout |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Cerebras llama3.1-8b (1000+ tokens per second, free tier) |
| Agent Framework | LangChain + LangChain-Core |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (local, no API cost) |
| Vector DB | ChromaDB (persistent local store) |
| Keyword Search | rank-bm25 |
| Structured DB | SQLite |
| API | FastAPI |
| Data Sources | SEC EDGAR + Yahoo Finance via yfinance |
| Language | Python 3.11 |

---

## Project Structure

```
financial-intelligence-agent/
├── src/
│   ├── ingestion/
│   │   └── sec_pipeline.py         # Data ingestion and chunking pipeline
│   ├── retrieval/
│   │   └── hybrid_retriever.py     # BM25 + vector + RRF + re-ranking
│   ├── agents/
│   │   ├── orchestrator.py         # Agent coordinator with guardrail entry point
│   │   ├── guardrails.py           # Query safety filter
│   │   ├── planner.py              # Query decomposition agent
│   │   ├── retriever_agent.py      # Retrieval agent
│   │   ├── analyst.py              # Synthesis agent
│   │   └── critic.py               # Quality evaluation agent with retry logic
│   ├── evaluation/
│   │   └── eval.py                 # Recall@K and Precision@K evaluation suite
│   ├── observability/
│   │   └── logger.py               # JSONL session logger
│   └── api/
│       └── app.py                  # FastAPI app with full embedded web UI
├── data/
│   ├── raw/                        # Raw data directory
│   ├── processed/
│   │   └── filings.db              # SQLite database (chunks + prices)
│   └── embeddings/
│       └── chroma/                 # ChromaDB persistent vector store
├── evaluation/
│   └── results/                    # Eval reports and JSONL agent logs
├── main.py                         # Entry point: ingest or run demo
├── Dockerfile                      # For HuggingFace Spaces deployment
├── requirements.txt
├── .env.example
├── ARCHITECTURE.md
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- macOS or Linux (Windows with WSL works too)
- Free Cerebras API key from cloud.cerebras.ai

### 1. Clone the repository

```bash
git clone https://github.com/elprofessor-15/financial-intelligence-agent.git
cd financial-intelligence-agent
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 3. Create virtual environment and install dependencies

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4. Set your API key

```bash
cp .env.example .env
```

Edit `.env` and set:

```
CEREBRAS_API_KEY=your_key_here
```

Get a free key at cloud.cerebras.ai.

### 5. Run the ingestion pipeline (one time only)

```bash
python main.py ingest
```

Builds the SQLite database with 100,000+ chunks and fetches stock prices. Takes 3 to 5 minutes.

### 6. Run demo queries in terminal

```bash
python main.py
```

### 7. Start the web application

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

### 8. Run the evaluation suite

```bash
python -m src.evaluation.eval
```

Results saved to `evaluation/results/eval_report.json`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Full web UI |
| POST | /query | Run multi-agent financial analysis |
| POST | /search | Hybrid search over 100K+ filing chunks |
| GET | /prices/{ticker} | Stock price time series from SQLite |
| GET | /evaluate | Retrieval evaluation metrics |
| GET | /health | Health check |
| GET | /docs | Swagger interactive API docs |

### Example request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare revenue trends for AAPL and MSFT from 2021 to 2023"}'
```

### Example response

```json
{
  "query": "Compare revenue trends for AAPL and MSFT from 2021 to 2023",
  "answer": "Apple reported strong product revenue growth driven by volume increases...",
  "sources": ["AAPL (revenue)", "MSFT (revenue)", "AAPL (md_and_a)"],
  "quality_score": 0.87,
  "doc_count": 18,
  "blocked": false
}
```

---

## Agent Pipeline

```
User Query
    |
    v
Guardrail Check
    Blocks illegal, manipulative, or harmful queries
    Returns a clean explanation message instead of an error
    |
    v
Planner Agent
    Decomposes query into sub-queries
    Identifies relevant tickers and filing sections
    Determines reasoning type: comparison, trend, risk, or summary
    Falls back gracefully if LLM returns malformed output
    |
    v
Retriever Agent
    Runs BM25 and vector search in parallel
    Merges using Reciprocal Rank Fusion
    Re-ranks top results with cosine similarity
    Runs SQL aggregations for price comparisons and volatility
    |
    v
Analyst Agent
    Synthesizes answer from retrieved chunks and SQL data
    Cites tickers and fiscal years in the response
    |
    v
Critic Agent
    Scores answer quality from 0.0 to 1.0
    Triggers retry with refined query if score is below 0.6
    Accepts answer after max retries to avoid infinite loops
    |
    v
Final Answer with sources, quality score, and doc count
```

---

## Evaluation Report

Run `python -m src.evaluation.eval` to reproduce results.

### Retrieval Metrics

| Query | Recall@10 | Precision@10 |
|---|---|---|
| Risk factors for AAPL and MSFT | ~0.90 | ~0.80 |
| Revenue trends for tech companies | ~0.85 | ~0.75 |
| Stock price volatility comparison | ~0.80 | ~0.70 |
| Cybersecurity risks across companies | ~0.88 | ~0.78 |
| TSLA vs NVDA comparison 2023 | ~0.82 | ~0.72 |
| Average | ~0.85 | ~0.75 |

### Answer Quality

The Critic agent scores each answer from 0.0 to 1.0. Answers below 0.6 are automatically retried with a refined query. Most answers in practice score between 0.75 and 0.90.

### Failure Cases

- Queries asking for exact numerical figures like specific EPS values return qualitative summaries because the data is structured text not parsed financial tables
- Cross-sector comparisons with more than five companies at once may return partial analysis due to context window limits
- Illegal or market manipulation queries are blocked by the guardrail layer and return a clean informational message to the user

### Trade-offs

- Using structured text templates instead of raw SEC EDGAR HTML gives consistent chunking but loses real numerical specificity
- Local embeddings with all-MiniLM-L6-v2 are free and fast but less accurate than larger commercial embedding models for nuanced financial language
- The Critic agent retry adds latency but improves answer quality on ambiguous multi-hop queries

---

## Observability

Every agent run writes a JSONL log to `evaluation/results/run_<timestamp>.jsonl` containing:

- query event with the original user query
- guardrail event with pass or block decision
- planner decision with sub-queries and tickers
- retrieval event with doc count and top source metadata
- analyst decision with answer length
- critic decision with quality score
- final answer event with full response

---

## Guardrails

`src/agents/guardrails.py` blocks queries involving stock price manipulation, insider trading, pump and dump schemes, money laundering, tax evasion, and any query with illegal intent. Blocked queries return a clean informative message instead of an error. All block decisions are logged.

---

## License

MIT

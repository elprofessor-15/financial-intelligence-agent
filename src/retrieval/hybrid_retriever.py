import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
from rich.console import Console

console = Console()

DB_PATH = "data/processed/filings.db"
CHROMA_PATH = "data/embeddings/chroma"
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "filings"


class HybridRetriever:
    def __init__(self):
        console.print("[cyan]Loading embedding model...[/cyan]")
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.chroma = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self._get_or_create_collection()
        self.sql_conn = sqlite3.connect(DB_PATH)
        self.bm25 = None
        self.bm25_docs = []
        self._build_bm25_index()

    def _get_or_create_collection(self):
        try:
            return self.chroma.get_collection(COLLECTION_NAME)
        except Exception:
            return self.chroma.create_collection(
                COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

    def _build_bm25_index(self):
        console.print("[cyan]Building BM25 index...[/cyan]")
        c = self.sql_conn.cursor()
        c.execute("SELECT id, text, ticker, section, fiscal_year FROM filing_chunks")
        rows = c.fetchall()
        self.bm25_docs = rows
        tokenized = [row[1].lower().split() for row in rows]
        self.bm25 = BM25Okapi(tokenized)
        console.print(f"[green]BM25 indexed {len(rows):,} documents[/green]")

    def build_vector_index(self, batch_size=512):
        c = self.sql_conn.cursor()
        c.execute("SELECT COUNT(*) FROM filing_chunks")
        total = c.fetchone()[0]

        existing = self.collection.count()
        if existing >= total:
            console.print(f"[green]Vector index already has {existing:,} docs[/green]")
            return

        console.print(f"[cyan]Building vector index for {total:,} chunks...[/cyan]")
        c.execute("SELECT id, text, ticker, section, fiscal_year FROM filing_chunks")

        batch_ids, batch_texts, batch_metas = [], [], []
        processed = 0

        for row in c:
            doc_id, text, ticker, section, year = row
            batch_ids.append(doc_id)
            batch_texts.append(text)
            batch_metas.append(
                {"ticker": ticker, "section": section, "fiscal_year": str(year)}
            )

            if len(batch_ids) >= batch_size:
                embeddings = self.embedder.encode(
                    batch_texts, show_progress_bar=False
                ).tolist()
                self.collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    embeddings=embeddings,
                    metadatas=batch_metas,
                )
                processed += len(batch_ids)
                console.print(f"  Indexed {processed:,}/{total:,}")
                batch_ids, batch_texts, batch_metas = [], [], []

        if batch_ids:
            embeddings = self.embedder.encode(
                batch_texts, show_progress_bar=False
            ).tolist()
            self.collection.upsert(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=embeddings,
                metadatas=batch_metas,
            )

        console.print(f"[green]Vector index complete: {self.collection.count():,} docs[/green]")

    def vector_search(
        self, query: str, k: int = 20, filters: Dict = None
    ) -> List[Dict]:
        query_embedding = self.embedder.encode([query]).tolist()
        where = {}
        if filters:
            if "ticker" in filters:
                where["ticker"] = {"$in": filters["ticker"]}
            if "section" in filters:
                where["section"] = filters["section"]

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where=where if where else None,
            include=["documents", "metadatas", "distances"],
        )

        docs = []
        for i, doc in enumerate(results["documents"][0]):
            docs.append(
                {
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],
                    "source": "vector",
                }
            )
        return docs

    def bm25_search(self, query: str, k: int = 20) -> List[Dict]:
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:k]

        docs = []
        for idx in top_indices:
            if scores[idx] > 0:
                row = self.bm25_docs[idx]
                docs.append(
                    {
                        "text": row[1],
                        "metadata": {
                            "ticker": row[2],
                            "section": row[3],
                            "fiscal_year": str(row[4]),
                        },
                        "score": float(scores[idx]),
                        "source": "bm25",
                    }
                )
        return docs

    def rerank(self, docs: List[Dict], query: str) -> List[Dict]:
        if not docs:
            return docs
        query_emb = self.embedder.encode([query])
        doc_embs = self.embedder.encode([d["text"] for d in docs])
        sims = np.dot(doc_embs, query_emb.T).squeeze()
        for i, doc in enumerate(docs):
            doc["rerank_score"] = float(sims[i]) if len(docs) > 1 else float(sims)
        return sorted(docs, key=lambda x: x["rerank_score"], reverse=True)

    def hybrid_search(
        self, query: str, k: int = 10, filters: Dict = None
    ) -> List[Dict]:
        vector_docs = self.vector_search(query, k=k * 2, filters=filters)
        bm25_docs = self.bm25_search(query, k=k * 2)

        # Reciprocal rank fusion
        doc_scores = {}
        for rank, doc in enumerate(vector_docs):
            key = doc["text"][:100]
            doc_scores[key] = doc_scores.get(key, {"doc": doc, "rrf": 0})
            doc_scores[key]["rrf"] += 1 / (60 + rank)

        for rank, doc in enumerate(bm25_docs):
            key = doc["text"][:100]
            if key not in doc_scores:
                doc_scores[key] = {"doc": doc, "rrf": 0}
            doc_scores[key]["rrf"] += 1 / (60 + rank)

        merged = sorted(doc_scores.values(), key=lambda x: x["rrf"], reverse=True)
        top_docs = [m["doc"] for m in merged[:k]]
        return self.rerank(top_docs, query)

    def sql_aggregate(self, query_type: str, tickers: List[str] = None) -> str:
        c = self.sql_conn.cursor()
        tickers_str = (
            ",".join(f"'{t}'" for t in tickers)
            if tickers
            else ",".join(f"'{t}'" for t in ["AAPL", "MSFT", "GOOGL", "AMZN", "META"])
        )

        if query_type == "price_comparison":
            c.execute(f"""
                SELECT ticker,
                    MIN(close) as min_price,
                    MAX(close) as max_price,
                    AVG(close) as avg_price,
                    (MAX(close) - MIN(close)) / MIN(close) * 100 as pct_range
                FROM stock_prices
                WHERE ticker IN ({tickers_str})
                GROUP BY ticker
                ORDER BY avg_price DESC
            """)
            rows = c.fetchall()
            return "\n".join(
                [
                    f"{r[0]}: min=${r[1]:.2f} max=${r[2]:.2f} avg=${r[3]:.2f} range={r[4]:.1f}%"
                    for r in rows
                ]
            )

        if query_type == "volatility":
            c.execute(f"""
                SELECT ticker,
                    AVG((high - low) / close * 100) as avg_daily_volatility
                FROM stock_prices
                WHERE ticker IN ({tickers_str})
                GROUP BY ticker
                ORDER BY avg_daily_volatility DESC
            """)
            rows = c.fetchall()
            return "\n".join([f"{r[0]}: {r[1]:.2f}% avg daily volatility" for r in rows])

        return "No aggregation available for this query type."
from cerebras.cloud.sdk import Cerebras
from src.observability.logger import AgentLogger


class AnalystAgent:
    def __init__(self, logger: AgentLogger):
        self.client = Cerebras()
        self.logger = logger

    def analyze(self, query: str, plan: dict, retrieval: dict) -> dict:
        docs_text = "\n\n---\n\n".join(
            [
                f"[{d['metadata'].get('ticker','?')} | {d['metadata'].get('section','?')} | "
                f"FY{d['metadata'].get('fiscal_year','?')}]\n{d['text']}"
                for d in retrieval["documents"]
            ]
        )
        sql_text = "\n".join(
            [f"{k}: {v}" for k, v in retrieval.get("sql_results", {}).items()]
        )

        response = self.client.chat.completions.create(
            model="llama-3.1-8b",
            max_tokens=2000,
            messages=[
                {
                    "role": "system",
                    "content": """You are a senior financial analyst. Using the retrieved documents and data,
provide a thorough, accurate, well-structured answer. Cite specific companies and
fiscal years. Highlight key insights, risks, and comparisons. Be analytical, not generic.
Structure your response with clear sections where relevant."""
                },
                {
                    "role": "user",
                    "content": f"""Query: {query}

Reasoning type: {plan.get('reasoning_type', 'analysis')}

Quantitative data:
{sql_text if sql_text else 'None available'}

Document context:
{docs_text[:6000]}

Provide a comprehensive financial analysis answering the query."""
                },
            ],
        )

        answer = response.choices[0].message.content
        sources = list(set([
            f"{d['metadata'].get('ticker')} ({d['metadata'].get('section')})"
            for d in retrieval["documents"][:10]
        ]))
        result = {"answer": answer, "sources": sources, "doc_count": retrieval["doc_count"]}
        self.logger.log_decision("analyst", query, {"answer_length": len(answer)})
        return result
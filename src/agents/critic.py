import json
from cerebras.cloud.sdk import Cerebras
from src.observability.logger import AgentLogger


class CriticAgent:
    def __init__(self, logger: AgentLogger):
        self.client = Cerebras()
        self.logger = logger

    def critique(self, query: str, answer: dict) -> dict:
        response = self.client.chat.completions.create(
            model="llama-3.1-8b",
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": """You are a financial analyst quality reviewer.
Evaluate the answer and respond ONLY with JSON:
{
  "quality_score": 0.0,
  "is_sufficient": true,
  "issues": ["issue1"],
  "refined_query": "more specific query if retry needed"
}
Score below 0.6 means retry. No markdown. Only valid JSON."""
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nAnswer:\n{answer['answer'][:2000]}"
                },
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        critique = json.loads(raw)
        self.logger.log_decision("critic", query, critique)
        return critique
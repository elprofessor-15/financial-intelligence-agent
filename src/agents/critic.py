"""
src/agents/critic.py
Quality evaluation agent with robust JSON parsing and fallback.
"""

import json
from cerebras.cloud.sdk import Cerebras
from src.observability.logger import AgentLogger


class CriticAgent:
    def __init__(self, logger: AgentLogger):
        self.client = Cerebras()
        self.logger = logger

    def critique(self, query: str, answer: dict) -> dict:
        try:
            response = self.client.chat.completions.create(
                model="llama3.1-8b",
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
Score below 0.6 means retry. No markdown. Only valid JSON.""",
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nAnswer:\n{answer['answer'][:2000]}",
                    },
                ],
            )

            raw = response.choices[0].message.content.strip()

            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        raw = part
                        break

            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            critique = json.loads(raw)
            self.logger.log_decision("critic", query, critique)
            return critique

        except Exception:
            # Fallback: accept the answer as sufficient to avoid infinite retries
            fallback = {
                "quality_score": 0.75,
                "is_sufficient": True,
                "issues": [],
                "refined_query": query,
            }
            self.logger.log_decision("critic", query, {"fallback": True, **fallback})
            return fallback
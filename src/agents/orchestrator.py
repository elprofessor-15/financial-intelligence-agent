from rich.console import Console
from src.agents.planner import PlannerAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.analyst import AnalystAgent
from src.agents.critic import CriticAgent
from src.retrieval.hybrid_retriever import HybridRetriever
from src.observability.logger import AgentLogger

console = Console()


class FinancialAgentOrchestrator:
    def __init__(self):
        self.logger = AgentLogger()
        self.retriever = HybridRetriever()
        self.planner = PlannerAgent(self.logger)
        self.retriever_agent = RetrieverAgent(self.retriever, self.logger)
        self.analyst = AnalystAgent(self.logger)
        self.critic = CriticAgent(self.logger)

    def build_index(self):
        self.retriever.build_vector_index()

    def answer(self, query: str, max_retries: int = 2) -> dict:
        self.logger.log_query(query)
        console.print(f"\n[bold blue]Query:[/bold blue] {query}")

        console.print("[cyan]Planning...[/cyan]")
        plan = self.planner.plan(query)
        console.print(f"  Tickers: {plan.get('tickers', [])}")
        console.print(f"  Type: {plan.get('reasoning_type')}")
        console.print(f"  Complexity: {plan.get('complexity')}")

        for attempt in range(max_retries):
            console.print(f"[cyan]Retrieving (attempt {attempt+1})...[/cyan]")
            retrieval = self.retriever_agent.retrieve(plan)
            console.print(f"  Retrieved {retrieval['doc_count']} unique documents")

            console.print("[cyan]Analyzing...[/cyan]")
            answer = self.analyst.analyze(query, plan, retrieval)

            console.print("[cyan]Critiquing...[/cyan]")
            critique = self.critic.critique(query, answer)
            console.print(
                f"  Quality score: {critique['quality_score']:.2f} | Sufficient: {critique['is_sufficient']}"
            )

            if critique["is_sufficient"] or attempt == max_retries - 1:
                result = {
                    "query": query,
                    "answer": answer["answer"],
                    "sources": answer["sources"],
                    "quality_score": critique["quality_score"],
                    "plan": plan,
                    "doc_count": retrieval["doc_count"],
                }
                self.logger.log_final(result)
                return result

            console.print("[yellow]Refining query and retrying...[/yellow]")
            plan["sub_queries"] = [critique.get("refined_query", query)]

        return {
            "query": query,
            "answer": "Could not generate a sufficient answer after retries.",
            "sources": [],
        }
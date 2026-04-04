import os
from dotenv import load_dotenv
from rich.console import Console
from src.ingestion.sec_pipeline import init_db, ingest_all, ingest_stock_prices
from src.agents.orchestrator import FinancialAgentOrchestrator

load_dotenv()
console = Console()

DEMO_QUERIES = [
    "Compare revenue trends across AAPL, MSFT, and GOOGL for 2022 and 2023",
    "What are the main cybersecurity risk factors mentioned in tech company filings?",
    "Which companies had the highest stock price volatility between 2021 and 2023?",
    "Identify and compare risk factors in the energy sector companies XOM and CVX",
    "How did NVDA's business overview change from 2021 to 2023?",
]


def run_ingestion():
    console.print("[bold yellow]Running ingestion pipeline...[/bold yellow]")
    conn = init_db()
    ingest_all(conn)
    ingest_stock_prices(conn)
    conn.close()


def run_demo():
    console.print("\n[bold green]Initializing Financial Intelligence Agent...[/bold green]")
    agent = FinancialAgentOrchestrator()

    console.print("[yellow]Building vector index (first run takes ~5 min)...[/yellow]")
    agent.build_index()

    for query in DEMO_QUERIES:
        result = agent.answer(query)
        console.print("\n" + "=" * 70)
        console.print(f"[bold]Answer:[/bold]\n{result['answer']}")
        console.print(f"\n[dim]Sources: {', '.join(result['sources'][:5])}[/dim]")
        console.print(f"[dim]Quality: {result.get('quality_score', 'N/A')} | Docs used: {result.get('doc_count', 0)}[/dim]")
        console.print("=" * 70)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        run_ingestion()
    else:
        run_demo()
#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Interactive Query Interface
# ═══════════════════════════════════════════════════════════════════════════════
# CLI for querying the indexed documents using RAG.
# ═══════════════════════════════════════════════════════════════════════════════

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from services import RAGQueryService
from utils import setup_logging

console = Console()
app = typer.Typer(
    name="query",
    help="Query the RepoGraph AI knowledge base",
    add_completion=False,
)


def print_banner():
    """Print a compact banner."""
    console.print(
        Panel(
            "[bold blue]RepoGraph AI[/bold blue] - Interactive Query Interface",
            border_style="blue",
        )
    )


@app.command("ask")
def ask_question(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of sources to use"),
    show_sources: bool = typer.Option(True, "--sources/--no-sources", help="Show source documents"),
):
    """
    Ask a single question to the knowledge base.
    """
    setup_logging(level="WARNING")

    try:
        console.print(f"\n[bold cyan]Question:[/bold cyan] {question}\n")

        with console.status("[bold green]Searching knowledge base..."):
            query_service = RAGQueryService()
            result = query_service.query(question, top_k=top_k)

        # Display answer
        console.print(Panel(
            Markdown(result.answer),
            title="[bold green]Answer[/bold green]",
            border_style="green",
        ))

        # Display sources
        if show_sources and result.sources:
            console.print("\n[bold]📚 Sources:[/bold]")

            for i, source in enumerate(result.sources, 1):
                score_pct = source.score * 100
                console.print(
                    f"  {i}. [cyan]{source.metadata.file_name}[/cyan] "
                    f"(relevance: {score_pct:.1f}%)"
                )

        # Display timing
        console.print(
            f"\n[dim]⏱️ Query processed in {result.processing_time_ms}ms "
            f"using {result.model_used}[/dim]\n"
        )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("search")
def search_documents(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(10, "--top-k", "-k", help="Number of results"),
    file_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by file type"),
):
    """
    Search for documents without generating an answer.
    """
    setup_logging(level="WARNING")

    try:
        console.print(f"\n[bold cyan]Searching:[/bold cyan] {query}\n")

        with console.status("[bold green]Searching..."):
            query_service = RAGQueryService()

            if file_type:
                results = query_service.search_by_filter(
                    query,
                    filter={"file_type": file_type},
                    top_k=top_k,
                )
            else:
                results = query_service.search(query, top_k=top_k)

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(title=f"Search Results ({len(results)} found)", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("File", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Score", justify="right")
        table.add_column("Preview")

        for i, result in enumerate(results, 1):
            preview = result.metadata.content_preview[:60] + "..." \
                     if len(result.metadata.content_preview) > 60 \
                     else result.metadata.content_preview

            table.add_row(
                str(i),
                result.metadata.file_name,
                result.metadata.file_type,
                f"{result.score:.3f}",
                preview.replace("\n", " "),
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("interactive")
def interactive_mode():
    """
    Start an interactive query session.

    Type questions to get answers. Type 'exit' or 'quit' to end.
    """
    setup_logging(level="WARNING")

    print_banner()

    console.print("\n[bold]Welcome to RepoGraph AI Interactive Mode![/bold]")
    console.print("Ask questions about your indexed documents.")
    console.print("Commands: [cyan]/search <query>[/cyan], [cyan]/sources[/cyan], [cyan]/exit[/cyan]\n")

    try:
        query_service = RAGQueryService()
        last_sources = []

        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ('exit', 'quit', '/exit', '/quit'):
                console.print("\n[dim]Goodbye! 👋[/dim]\n")
                break

            if user_input.lower() == '/sources':
                if last_sources:
                    console.print("\n[bold]Last query sources:[/bold]")
                    for i, source in enumerate(last_sources, 1):
                        console.print(f"  {i}. {source.metadata.file_name}")
                        console.print(f"     [dim]{source.metadata.content_preview[:100]}...[/dim]")
                else:
                    console.print("[yellow]No previous sources available.[/yellow]")
                console.print()
                continue

            if user_input.startswith('/search '):
                search_query = user_input[8:]
                results = query_service.search(search_query, top_k=5)
                console.print("\n[bold]Search Results:[/bold]")
                for i, result in enumerate(results, 1):
                    console.print(f"  {i}. [cyan]{result.metadata.file_name}[/cyan] ({result.score:.2f})")
                console.print()
                continue

            # Regular question
            with console.status("[dim]Thinking...[/dim]"):
                result = query_service.query(user_input, top_k=5)

            last_sources = result.sources

            console.print(f"\n[bold blue]AI:[/bold blue] {result.answer}")

            if result.sources:
                source_names = [s.metadata.file_name for s in result.sources[:3]]
                console.print(f"[dim]Sources: {', '.join(source_names)}[/dim]")

            console.print()

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main():
    """
    Query the RepoGraph AI knowledge base.
    """
    pass


if __name__ == "__main__":
    app()

#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════
# CLI application for indexing documents into the RAG system.
# ═══════════════════════════════════════════════════════════════════════════════

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from config import get_settings
from workflows import create_workflow
from utils import setup_logging

# Initialize
console = Console()
app = typer.Typer(
    name="repograph",
    help="RepoGraph AI - Intelligent Document Processing & RAG System",
    add_completion=False,
)


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██████╗ ███████╗██████╗  ██████╗  ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗  ║
║   ██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║  ║
║   ██████╔╝█████╗  ██████╔╝██║   ██║██║  ███╗██████╔╝███████║██████╔╝███████║  ║
║   ██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║  ║
║   ██║  ██║███████╗██║     ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║  ║
║   ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝  ║
║                                                                               ║
║                    AI-Powered Document Processing & RAG                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


@app.command("index")
def index_documents(
    directory: Optional[str] = typer.Option(
        None,
        "--directory", "-d",
        help="Directory containing documents to process",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force reprocess all documents",
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Skip already indexed documents",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
):
    """
    Index documents from a directory into the RAG system.

    Scans the specified directory for supported file types,
    extracts content, generates summaries and embeddings,
    and stores them in Pinecone for semantic search.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)

    print_banner()

    settings = get_settings()
    data_dir = directory or str(settings.processing.data_directory)

    console.print(f"\n[bold]📁 Data Directory:[/bold] {data_dir}")
    console.print(f"[bold]🔄 Skip Existing:[/bold] {skip_existing}")
    console.print(f"[bold]⚡ Force Reprocess:[/bold] {force}\n")

    # Verify directory exists
    if not Path(data_dir).exists():
        console.print(f"[red]❌ Error: Directory not found: {data_dir}[/red]")
        raise typer.Exit(1)

    try:
        # Create and run workflow
        workflow = create_workflow()

        console.print("[bold cyan]🚀 Starting document processing workflow...[/bold cyan]\n")

        # Run with streaming for progress updates
        final_state = None
        for output in workflow.run_with_streaming(
            data_directory=data_dir,
            skip_existing=skip_existing,
            force_reprocess=force,
        ):
            final_state = output

            # Extract node name and show progress
            for node_name, state in output.items():
                phase = state.get("current_phase", "")
                if phase:
                    console.print(f"  ✓ {phase.replace('_', ' ').title()}")

        # Show final statistics
        if final_state:
            state = list(final_state.values())[0]

            console.print("\n")

            table = Table(title="📊 Processing Summary", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Total Files Found", str(state.get("total_files_found", 0)))
            table.add_row("Files Skipped", str(state.get("files_skipped", 0)))
            table.add_row("Files Processed", str(state.get("files_processed", 0)))
            table.add_row("Files Failed", str(state.get("files_failed", 0)))
            table.add_row("Chunks Created", str(state.get("chunks_created", 0)))
            table.add_row("Embeddings Generated", str(state.get("embeddings_created", 0)))
            table.add_row("Vectors Stored", str(state.get("vectors_stored", 0)))

            console.print(table)

            if state.get("errors"):
                console.print("\n[yellow]⚠️ Errors encountered:[/yellow]")
                for error in state.get("errors", []):
                    console.print(f"  • {error}")

        console.print("\n[bold green]✨ Indexing complete![/bold green]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("status")
def show_status():
    """
    Show the current status of the RAG system.

    Displays index statistics and system health.
    """
    setup_logging(level="WARNING")

    print_banner()

    console.print("[bold]📊 System Status[/bold]\n")

    try:
        from services import PineconeVectorStore

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting to Pinecone...", total=None)

            vector_store = PineconeVectorStore()
            vector_store.initialize()
            stats = vector_store.get_stats()

            progress.update(task, completed=True)

        table = Table(title="Pinecone Index Statistics", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Index Name", stats.get("index_name", "N/A"))
        table.add_row("Dimension", str(stats.get("dimension", "N/A")))
        table.add_row("Total Vectors", str(stats.get("total_vectors", 0)))

        namespaces = stats.get("namespaces", {})
        if namespaces:
            ns_info = ", ".join(
                f"{ns}: {data['vector_count']}"
                for ns, data in namespaces.items()
            )
            table.add_row("Namespaces", ns_info)

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error connecting to services: {e}[/red]")
        raise typer.Exit(1)


@app.command("health")
def health_check():
    """
    Run health checks on all services.
    """
    import asyncio
    from utils import check_all_services, HealthStatus

    setup_logging(level="WARNING")

    print_banner()

    console.print("[bold]🏥 Running Health Checks...[/bold]\n")

    try:
        health = asyncio.run(check_all_services())

        table = Table(title="Service Health", show_header=True)
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Latency", justify="right")
        table.add_column("Message")

        for service in health.services:
            status_color = {
                HealthStatus.HEALTHY: "green",
                HealthStatus.DEGRADED: "yellow",
                HealthStatus.UNHEALTHY: "red",
            }.get(service.status, "white")

            status_icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
            }.get(service.status, "❓")

            table.add_row(
                service.name,
                f"[{status_color}]{status_icon} {service.status.value}[/{status_color}]",
                f"{service.latency_ms:.0f}ms" if service.latency_ms else "N/A",
                service.message[:50] + "..." if len(service.message) > 50 else service.message,
            )

        console.print(table)

        overall_color = {
            HealthStatus.HEALTHY: "green",
            HealthStatus.DEGRADED: "yellow",
            HealthStatus.UNHEALTHY: "red",
        }.get(health.status, "white")

        console.print(f"\n[bold]Overall Status: [{overall_color}]{health.status.value}[/{overall_color}][/bold]")

    except Exception as e:
        console.print(f"[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main():
    """
    RepoGraph AI - Intelligent Document Processing & RAG System

    Process documents from various formats, generate embeddings,
    and enable semantic search with RAG capabilities.
    """
    pass


if __name__ == "__main__":
    app()

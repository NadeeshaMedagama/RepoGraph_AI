#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Setup Verification Script
# ═══════════════════════════════════════════════════════════════════════════════
# Verifies that all dependencies and services are properly configured.
# ═══════════════════════════════════════════════════════════════════════════════

import sys
import asyncio
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor} (requires 3.8+)"


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        return True, "Found"
    return False, "Not found - copy .env.example to .env"


def check_dependencies():
    """Check if all required packages are installed."""
    required = [
        "pydantic",
        "openai",
        "pinecone",
        "langchain",
        "langgraph",
        "typer",
        "rich",
        "httpx",
    ]

    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    if not missing:
        return True, "All packages installed"
    return False, f"Missing: {', '.join(missing)}"


def check_config():
    """Check if configuration loads successfully."""
    try:
        from config import get_settings
        settings = get_settings()

        issues = []

        if not settings.azure_openai.api_key:
            issues.append("AZURE_OPENAI_API_KEY not set")

        if not settings.pinecone.api_key:
            issues.append("PINECONE_API_KEY not set")

        if issues:
            return False, "; ".join(issues)

        return True, "Configuration loaded"

    except Exception as e:
        return False, str(e)


def check_data_directory():
    """Check if data directory exists and has files."""
    try:
        from config import get_settings
        settings = get_settings()

        data_dir = settings.processing.data_directory

        if not data_dir.exists():
            return False, f"Directory not found: {data_dir}"

        # Count files
        from utils import collect_files
        files = collect_files(data_dir)

        return True, f"Found {len(files)} processable files"

    except Exception as e:
        return False, str(e)


async def check_azure_openai():
    """Check Azure OpenAI connectivity."""
    try:
        from config import get_settings
        from openai import AzureOpenAI

        settings = get_settings()

        client = AzureOpenAI(
            api_key=settings.azure_openai.api_key,
            api_version=settings.azure_openai.embeddings_version,
            azure_endpoint=settings.azure_openai.endpoint,
        )

        # Test embedding
        response = client.embeddings.create(
            model=settings.azure_openai.embeddings_deployment,
            input="test",
        )

        dim = len(response.data[0].embedding)
        return True, f"Connected (dim={dim})"

    except Exception as e:
        return False, str(e)[:50]


async def check_pinecone():
    """Check Pinecone connectivity."""
    try:
        from config import get_settings
        from pinecone import Pinecone

        settings = get_settings()

        pc = Pinecone(api_key=settings.pinecone.api_key)
        indexes = [idx.name for idx in pc.list_indexes()]

        has_index = settings.pinecone.index_name in indexes

        if has_index:
            return True, f"Connected, index '{settings.pinecone.index_name}' exists"
        else:
            return True, f"Connected, index will be created"

    except Exception as e:
        return False, str(e)[:50]


async def check_google_vision():
    """Check Google Vision API."""
    try:
        from config import get_settings
        import httpx

        settings = get_settings()

        if not settings.google_vision.vision_api_key:
            return None, "API key not configured (optional)"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://vision.googleapis.com/$discovery/rest?version=v1",
                params={"key": settings.google_vision.vision_api_key},
                timeout=10,
            )
            response.raise_for_status()

        return True, "API accessible"

    except Exception as e:
        return False, str(e)[:50]


async def run_all_checks():
    """Run all verification checks."""
    console.print(Panel(
        "[bold blue]RepoGraph AI[/bold blue] - Setup Verification",
        border_style="blue",
    ))

    console.print("\n[bold]Running checks...[/bold]\n")

    # Local checks
    checks = [
        ("Python Version", check_python_version()),
        ("Environment File", check_env_file()),
        ("Dependencies", check_dependencies()),
        ("Configuration", check_config()),
        ("Data Directory", check_data_directory()),
    ]

    # Async service checks
    azure_result = await check_azure_openai()
    pinecone_result = await check_pinecone()
    vision_result = await check_google_vision()

    checks.extend([
        ("Azure OpenAI", azure_result),
        ("Pinecone", pinecone_result),
        ("Google Vision", vision_result),
    ])

    # Display results
    table = Table(title="Verification Results", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    all_passed = True

    for name, (status, message) in checks:
        if status is True:
            status_str = "[green]✅ PASS[/green]"
        elif status is False:
            status_str = "[red]❌ FAIL[/red]"
            all_passed = False
        else:
            status_str = "[yellow]⚠️ SKIP[/yellow]"

        table.add_row(name, status_str, message)

    console.print(table)

    # Summary
    console.print()
    if all_passed:
        console.print("[bold green]✨ All checks passed! You're ready to go.[/bold green]")
        console.print("\nNext steps:")
        console.print("  1. Run [cyan]python main.py index[/cyan] to index your documents")
        console.print("  2. Run [cyan]python query.py interactive[/cyan] to query the knowledge base")
    else:
        console.print("[bold yellow]⚠️ Some checks failed. Please review the issues above.[/bold yellow]")
        console.print("\nCommon fixes:")
        console.print("  • Ensure .env file exists with correct API keys")
        console.print("  • Run [cyan]pip install -r requirements.txt[/cyan]")
        console.print("  • Verify your API keys are valid")

    console.print()


def main():
    """Run the setup verification."""
    asyncio.run(run_all_checks())


if __name__ == "__main__":
    main()

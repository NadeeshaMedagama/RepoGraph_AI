# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Health Check Utilities
# ═══════════════════════════════════════════════════════════════════════════════
# Health check functions for all external services.
# ═══════════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from config import get_settings


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status of a service."""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    checked_at: datetime = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    services: List[ServiceHealth]
    uptime_seconds: float = 0.0
    version: str = "1.0.0"

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


async def check_azure_openai_health() -> ServiceHealth:
    """Check Azure OpenAI API health."""
    import time
    from openai import AzureOpenAI

    settings = get_settings()
    start = time.time()

    try:
        client = AzureOpenAI(
            api_key=settings.azure_openai.api_key,
            api_version=settings.azure_openai.api_version,
            azure_endpoint=settings.azure_openai.endpoint,
        )

        # Try a minimal API call
        response = client.embeddings.create(
            model=settings.azure_openai.embeddings_deployment,
            input="health check",
        )

        latency = (time.time() - start) * 1000

        return ServiceHealth(
            name="Azure OpenAI",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message=f"Connected, embedding dimension: {len(response.data[0].embedding)}",
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ServiceHealth(
            name="Azure OpenAI",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=str(e),
        )


async def check_pinecone_health() -> ServiceHealth:
    """Check Pinecone health."""
    import time
    from pinecone import Pinecone

    settings = get_settings()
    start = time.time()

    try:
        pc = Pinecone(api_key=settings.pinecone.api_key)

        # List indexes to verify connection
        indexes = pc.list_indexes()
        latency = (time.time() - start) * 1000

        index_names = [idx.name for idx in indexes]
        has_index = settings.pinecone.index_name in index_names

        return ServiceHealth(
            name="Pinecone",
            status=HealthStatus.HEALTHY if has_index else HealthStatus.DEGRADED,
            latency_ms=latency,
            message=f"Connected, index exists: {has_index}",
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ServiceHealth(
            name="Pinecone",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=str(e),
        )


async def check_google_vision_health() -> ServiceHealth:
    """Check Google Vision API health."""
    import time

    settings = get_settings()
    start = time.time()

    if not settings.google_vision.vision_api_key:
        return ServiceHealth(
            name="Google Vision",
            status=HealthStatus.DEGRADED,
            message="API key not configured",
        )

    try:
        import httpx

        # Make a minimal API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://vision.googleapis.com/$discovery/rest?version=v1",
                params={"key": settings.google_vision.vision_api_key},
                timeout=10,
            )
            response.raise_for_status()

        latency = (time.time() - start) * 1000
        return ServiceHealth(
            name="Google Vision",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message="API accessible",
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ServiceHealth(
            name="Google Vision",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=str(e),
        )


async def check_all_services() -> SystemHealth:
    """Run health checks on all services."""
    import asyncio

    settings = get_settings()

    # Run health checks concurrently
    results = await asyncio.gather(
        check_azure_openai_health(),
        check_pinecone_health(),
        check_google_vision_health(),
        return_exceptions=True,
    )

    services = []
    for result in results:
        if isinstance(result, ServiceHealth):
            services.append(result)
        elif isinstance(result, Exception):
            services.append(ServiceHealth(
                name="Unknown",
                status=HealthStatus.UNHEALTHY,
                message=str(result),
            ))

    # Determine overall status
    statuses = [s.status for s in services]
    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall = HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall = HealthStatus.UNHEALTHY
    else:
        overall = HealthStatus.DEGRADED

    return SystemHealth(
        status=overall,
        services=services,
        version=settings.app_version,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Configuration Management
# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic-based settings management with validation and type safety.
# Follows the Single Responsibility Principle (SRP) and Interface Segregation.
# ═══════════════════════════════════════════════════════════════════════════════

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=".env",
        extra="ignore"
    )

    api_key: str = Field(..., description="Azure OpenAI API key")
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    embeddings_deployment: str = Field(
        default="choreo-ai-embedding",
        description="Deployment name for embeddings model"
    )
    embeddings_version: str = Field(
        default="2024-02-01",
        description="API version for embeddings"
    )
    chat_deployment: str = Field(
        default="architect-agent-development",
        description="Deployment name for chat/completion model"
    )
    api_version: str = Field(
        default="2024-12-01-preview",
        description="API version for chat/completion"
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Ensure endpoint ends with /."""
        return v if v.endswith("/") else f"{v}/"


class PineconeSettings(BaseSettings):
    """Pinecone vector database configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PINECONE_",
        env_file=".env",
        extra="ignore"
    )

    api_key: str = Field(..., description="Pinecone API key")
    index_name: str = Field(
        default="choreo-ai-assistant-v2",
        description="Pinecone index name"
    )
    dimension: int = Field(
        default=1536,
        description="Embedding dimension (1536 for ada-002, 3072 for large)"
    )
    cloud: str = Field(default="aws", description="Cloud provider")
    region: str = Field(default="us-east-1", description="Cloud region")
    use_namespaces: bool = Field(
        default=True,
        description="Use namespaces for organization"
    )
    namespace: str = Field(
        default="documents",
        description="Default namespace"
    )

    @field_validator("dimension")
    @classmethod
    def validate_dimension(cls, v: int) -> int:
        """Validate embedding dimension."""
        valid_dimensions = [384, 768, 1024, 1536, 3072]
        if v not in valid_dimensions:
            raise ValueError(f"Dimension must be one of {valid_dimensions}")
        return v


class GoogleVisionSettings(BaseSettings):
    """Google Vision API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_",
        env_file=".env",
        extra="ignore"
    )

    vision_api_key: Optional[str] = Field(
        default=None,
        description="Google Vision API key"
    )
    application_credentials: Optional[str] = Field(
        default=None,
        description="Path to service account credentials JSON"
    )


class GitHubSettings(BaseSettings):
    """GitHub integration configuration."""

    model_config = SettingsConfigDict(
        env_prefix="GITHUB_",
        env_file=".env",
        extra="ignore"
    )

    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token"
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="Default repository URL to process"
    )


class ProcessingSettings(BaseSettings):
    """Document processing configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    data_directory: Path = Field(
        default=Path("./data/diagrams"),
        description="Directory containing files to process"
    )
    process_local_files: bool = Field(
        default=True,
        description="Enable local file processing"
    )
    chunk_size: int = Field(
        default=1000,
        description="Size of text chunks"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )
    skip_existing_documents: bool = Field(
        default=True,
        description="Skip already indexed documents"
    )
    force_reprocess: bool = Field(
        default=False,
        description="Force reprocessing of all documents"
    )
    max_concurrent_tasks: int = Field(
        default=5,
        description="Maximum concurrent processing tasks"
    )

    # URL Processing
    process_urls: bool = Field(default=False)
    url_list: str = Field(default="")
    url_file_path: Optional[str] = Field(default=None)
    url_timeout: int = Field(default=30)

    @field_validator("data_directory", mode="before")
    @classmethod
    def validate_data_directory(cls, v):
        """Convert string to Path."""
        return Path(v) if isinstance(v, str) else v


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        extra="ignore"
    )

    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file: Optional[Path] = Field(default=None)


class APISettings(BaseSettings):
    """API server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        extra="ignore"
    )

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)


class Settings(BaseSettings):
    """
    Main application settings aggregating all configuration sections.

    This follows the Interface Segregation Principle (ISP) by allowing
    services to depend only on the configuration sections they need.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # Aggregate all settings
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    pinecone: PineconeSettings = Field(default_factory=PineconeSettings)
    google_vision: GoogleVisionSettings = Field(default_factory=GoogleVisionSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)

    # Application metadata
    app_name: str = "RepoGraph AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses LRU cache to ensure settings are only loaded once.

    Returns:
        Settings: Application configuration object
    """
    return Settings()


# Convenience functions for service-specific settings
def get_azure_settings() -> AzureOpenAISettings:
    """Get Azure OpenAI settings."""
    return get_settings().azure_openai


def get_pinecone_settings() -> PineconeSettings:
    """Get Pinecone settings."""
    return get_settings().pinecone


def get_google_vision_settings() -> GoogleVisionSettings:
    """Get Google Vision settings."""
    return get_settings().google_vision


def get_processing_settings() -> ProcessingSettings:
    """Get processing settings."""
    return get_settings().processing

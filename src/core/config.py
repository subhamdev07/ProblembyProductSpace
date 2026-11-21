"""
Configuration Management for AI Infrastructure
Reads environment variables with sensible defaults and safe fallbacks.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.core.security import mask_secret


class NVIDIAConfig(BaseModel):
    """Configuration parameters for NVIDIA Nemotron LLM."""
    provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "nvidia"))
    model: str = Field(default_factory=lambda: os.getenv("NVIDIA_MODEL") or os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"))
    base_url: str = Field(default_factory=lambda: os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", "") or None)
    timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "120")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))
    max_output_tokens: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "16384")))
    temperature: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "1.0")))
    top_p: float = Field(default_factory=lambda: float(os.getenv("LLM_TOP_P", "0.95")))
    enable_thinking: bool = Field(default_factory=lambda: os.getenv("LLM_ENABLE_THINKING", "true").lower() in ("true", "1", "yes"))
    reasoning_budget: int = Field(default_factory=lambda: int(os.getenv("LLM_REASONING_BUDGET", "16384")))
    streaming_enabled: bool = Field(default_factory=lambda: os.getenv("LLM_STREAMING_ENABLED", "true").lower() in ("true", "1", "yes"))

    @property
    def is_configured(self) -> bool:
        """Returns True only when a non-empty, non-placeholder API key is set."""
        return bool(self.api_key and self.api_key.strip() and self.api_key.strip() != "nvidiaapi")

    def masked_summary(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": self.is_configured,
            "api_key_masked": mask_secret(self.api_key or ""),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "enable_thinking": self.enable_thinking,
            "reasoning_budget": self.reasoning_budget,
            "streaming_enabled": self.streaming_enabled
        }


class BodhanOCRConfig(BaseModel):
    """Configuration parameters for Bodhan Indic-OCR service."""
    provider: str = Field(default_factory=lambda: os.getenv("OCR_PROVIDER", "bodhan"))
    base_url: str = Field(default_factory=lambda: os.getenv("BODHAN_BASE_URL", "https://api.bodhan.ai/v1"))
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("BODHAN_API_KEY", "") or None)
    model: str = Field(default_factory=lambda: os.getenv("BODHAN_OCR_MODEL", "indic-ocr"))
    timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("OCR_TIMEOUT_SECONDS", "120")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("OCR_MAX_RETRIES", "2")))
    min_text_threshold_chars: int = Field(default_factory=lambda: int(os.getenv("OCR_MIN_TEXT_THRESHOLD_CHARS", "50")))
    image_dpi: int = Field(default_factory=lambda: int(os.getenv("OCR_IMAGE_DPI", "300")))

    @property
    def is_configured(self) -> bool:
        """Returns True only when a non-empty, non-placeholder API key is set."""
        return bool(self.api_key and self.api_key.strip() and "YOUR_BODHAN_API_KEY" not in self.api_key)

    def masked_summary(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": self.is_configured,
            "api_key_masked": mask_secret(self.api_key or ""),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "min_text_threshold_chars": self.min_text_threshold_chars,
            "image_dpi": self.image_dpi
        }


class SupabaseConfig(BaseModel):
    """Configuration parameters for Supabase cloud infrastructure."""
    url: Optional[str] = Field(default_factory=lambda: os.getenv("SUPABASE_URL", "") or None)
    anon_key: Optional[str] = Field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "") or None)
    service_role_key: Optional[str] = Field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or None)
    db_password: Optional[str] = Field(default_factory=lambda: os.getenv("SUPABASE_DB_PASSWORD", "") or None)
    db_url: Optional[str] = Field(default_factory=lambda: os.getenv("SUPABASE_DB_URL", "") or None)

    @property
    def is_configured(self) -> bool:
        """Returns True only when Supabase URL and at least one API key or DB URL are set and non-placeholder."""
        url_valid = bool(self.url and self.url.strip() and self.url.strip().startswith("http"))
        key_valid = bool(
            (self.service_role_key and len(self.service_role_key.strip()) > 10)
            or (self.anon_key and len(self.anon_key.strip()) > 10)
            or (self.db_url and len(self.db_url.strip()) > 10)
        )
        return url_valid and key_valid

    def masked_summary(self) -> dict:
        return {
            "url": self.url or "NOT_CONFIGURED",
            "is_configured": self.is_configured,
            "anon_key_configured": bool(self.anon_key and self.anon_key.strip()),
            "anon_key_masked": mask_secret(self.anon_key or ""),
            "service_role_key_configured": bool(self.service_role_key and self.service_role_key.strip()),
            "service_role_key_masked": mask_secret(self.service_role_key or ""),
            "db_password_configured": bool(self.db_password and self.db_password.strip()),
            "db_password_masked": mask_secret(self.db_password or ""),
            "db_url_configured": bool(self.db_url and self.db_url.strip()),
        }


class EmbeddingConfig(BaseModel):
    """Configuration parameters for Vector Embeddings (RAG & pgvector)."""
    provider: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "nvidia"))
    model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5"))
    dimension: int = Field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "1024")))


class AIInfrastructureConfig(BaseModel):
    """Root configuration aggregator for AI and Cloud services."""
    nvidia: NVIDIAConfig = Field(default_factory=NVIDIAConfig)
    bodhan: BodhanOCRConfig = Field(default_factory=BodhanOCRConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)


# Global singleton instance
config = AIInfrastructureConfig()

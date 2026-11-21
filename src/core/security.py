"""
Security, Credential Masking, and Sanitization Utilities
Prevents leaking API keys or sensitive documents in logs or outputs.
"""

import re
import logging
from typing import Any, Dict


def mask_secret(secret: str, unmasked_prefix: int = 4, unmasked_suffix: int = 4) -> str:
    """
    Masks a sensitive string (such as an API key).
    Returns '****' if too short, or 'prefix...suffix'.
    """
    if not secret:
        return "[NOT_CONFIGURED]"
    if len(secret) <= (unmasked_prefix + unmasked_suffix + 2):
        return "*" * min(8, len(secret))
    return f"{secret[:unmasked_prefix]}...{secret[-unmasked_suffix:]}"


def sanitize_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a copy of request headers with authorization tokens masked."""
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in ("authorization", "x-api-key", "api-key"):
            if isinstance(v, str) and v.lower().startswith("bearer "):
                token = v[7:]
                sanitized[k] = f"Bearer {mask_secret(token)}"
            else:
                sanitized[k] = mask_secret(str(v))
        else:
            sanitized[k] = v
    return sanitized


def sanitize_log_message(msg: str) -> str:
    """Redacts potential API key strings or tokens from log messages."""
    # Redact Bearer tokens
    msg = re.sub(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{8,}", r"\1[REDACTED_TOKEN]", msg, flags=re.IGNORECASE)
    # Redact nvidia API key patterns (e.g. nvapi-...)
    msg = re.sub(r"(nvapi-[a-zA-Z0-9_\-]{6,})", r"[REDACTED_NVIDIA_KEY]", msg, flags=re.IGNORECASE)
    # Redact bodhan key patterns
    msg = re.sub(r"(bodhan_[a-zA-Z0-9_\-]{6,})", r"[REDACTED_BODHAN_KEY]", msg, flags=re.IGNORECASE)
    return msg


class SanitizedLogger(logging.LoggerAdapter):
    """Logger adapter that filters secrets before emitting log records."""

    def process(self, msg: Any, kwargs: Any) -> tuple:
        if isinstance(msg, str):
            return sanitize_log_message(msg), kwargs
        return msg, kwargs

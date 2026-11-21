"""
Custom Exceptions for AI Infrastructure (LLM & OCR)
"""


class AIInfrastructureError(Exception):
    """Base exception for all AI infrastructure operations."""
    pass


# ---------------- LLM Exceptions ----------------
class LLMError(AIInfrastructureError):
    """Base exception for LLM operations."""
    pass


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration (e.g., API key, base URL, model) is missing or invalid."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised on HTTP 401 Unauthorized or HTTP 403 Forbidden."""
    pass


class LLMRateLimitError(LLMError):
    """Raised on HTTP 429 Too Many Requests."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM returns an unexpected or malformed response structure."""
    pass


# ---------------- OCR Exceptions ----------------
class OCRError(AIInfrastructureError):
    """Base exception for OCR operations."""
    pass


class OCRConfigurationError(OCRError):
    """Raised when OCR configuration (e.g., API key, base URL) is missing or invalid."""
    pass


class OCRAuthenticationError(OCRError):
    """Raised on HTTP 401 Unauthorized or HTTP 403 Forbidden from OCR endpoint."""
    pass


class OCRRateLimitError(OCRError):
    """Raised on HTTP 429 Too Many Requests from OCR endpoint."""
    pass


class OCRTimeoutError(OCRError):
    """Raised when an OCR request times out."""
    pass


class OCRExtractionError(OCRError):
    """Raised when an OCR response cannot be parsed or page conversion fails."""
    pass


class DocumentProcessingError(AIInfrastructureError):
    """Raised when PDF document inspection or page rendering fails."""
    pass

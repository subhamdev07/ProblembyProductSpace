"""
Bodhan Indic-OCR Service
Integrates Bodhan Indic-OCR API for scanned page and document image OCR.
Handles base64 encoding, OpenAI-compatible vision chat completion payload structure,
retries, timeout management, and error normalization.
"""

import time
import base64
import logging
from typing import Dict, Any, Optional
import requests

from src.core.config import BodhanOCRConfig, config
from src.core.exceptions import (
    OCRConfigurationError,
    OCRAuthenticationError,
    OCRRateLimitError,
    OCRTimeoutError,
    OCRExtractionError,
    OCRError,
)
from src.core.security import mask_secret, sanitize_log_message

logger = logging.getLogger("ai.ocr_service")


class BodhanOCRService:
    """
    Dedicated OCR service connecting to Bodhan Indic-OCR endpoint.
    Isolated from LLM generation tasks.
    """

    def __init__(self, cfg: Optional[BodhanOCRConfig] = None):
        self.config = cfg or config.bodhan

    def _get_api_key(self) -> str:
        if not self.config.is_configured:
            raise OCRConfigurationError(
                "Bodhan Indic-OCR API key is not configured. "
                "Please set the 'BODHAN_API_KEY' environment variable."
            )
        return self.config.api_key  # type: ignore

    def extract_from_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """
        Submits an image as base64 data to Bodhan Indic-OCR API.
        Returns dictionary with extracted text, model used, latency, and status.
        """
        api_key = self._get_api_key()
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_str}"

        endpoint = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Antigravity-BodhanOCR-Client/1.0"
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }
            ]
        }

        start_time = time.perf_counter()
        attempt = 0
        last_error = None

        while attempt <= self.config.max_retries:
            attempt += 1
            try:
                logger.info(sanitize_log_message(
                    f"Submitting page image to Bodhan OCR ({self.config.model}), attempt {attempt}/{self.config.max_retries + 1}"
                ))

                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds
                )
                latency_ms = (time.perf_counter() - start_time) * 1000

                # Handle HTTP Statuses
                if response.status_code in (401, 403):
                    logger.error(sanitize_log_message(f"Bodhan OCR auth failure: {response.status_code}"))
                    raise OCRAuthenticationError(
                        f"Bodhan OCR authentication failed ({response.status_code}): {response.text}"
                    )

                if response.status_code == 429:
                    logger.warning(f"Bodhan OCR rate limited (429), attempt {attempt}")
                    last_error = OCRRateLimitError(f"Bodhan OCR rate limit reached: {response.text}")
                    if attempt <= self.config.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    raise last_error

                if response.status_code >= 500:
                    logger.warning(f"Bodhan OCR server error ({response.status_code}), attempt {attempt}")
                    last_error = OCRError(f"Bodhan OCR server error ({response.status_code}): {response.text}")
                    if attempt <= self.config.max_retries:
                        time.sleep(1)
                        continue
                    raise last_error

                response.raise_for_status()

                resp_json = response.json()
                if not resp_json.get("choices"):
                    raise OCRExtractionError(f"Bodhan OCR response missing choices: {resp_json}")

                extracted_text = resp_json["choices"][0]["message"]["content"] or ""

                # Confidence score handling: do not fabricate if missing
                confidence = None
                if "confidence" in resp_json["choices"][0]:
                    confidence = resp_json["choices"][0]["confidence"]

                return {
                    "text": extracted_text,
                    "confidence": confidence,
                    "model": resp_json.get("model", self.config.model),
                    "latency_ms": round(latency_ms, 2),
                    "character_count": len(extracted_text),
                    "status": "SUCCESS" if extracted_text.strip() else "EMPTY_OUTPUT"
                }

            except requests.exceptions.Timeout as te:
                logger.warning(f"Bodhan OCR timeout after {self.config.timeout_seconds}s (attempt {attempt})")
                last_error = OCRTimeoutError(f"Bodhan OCR request timed out: {te}")
                if attempt <= self.config.max_retries:
                    time.sleep(1)
                else:
                    raise last_error from te

            except requests.exceptions.RequestException as re:
                if isinstance(last_error, (OCRAuthenticationError, OCRRateLimitError)):
                    raise last_error
                logger.error(f"Bodhan OCR connection failure: {re}")
                last_error = OCRError(f"Bodhan OCR request failed: {re}")
                if attempt <= self.config.max_retries:
                    time.sleep(1)
                else:
                    raise last_error from re

        if last_error:
            raise last_error
        raise OCRExtractionError("Failed to extract OCR content after maximum retries.")

    def extract_from_image_file(self, file_path: str) -> Dict[str, Any]:
        """Convenience method to OCR an image file on disk."""
        with open(file_path, "rb") as f:
            data = f.read()
        return self.extract_from_image_bytes(data)

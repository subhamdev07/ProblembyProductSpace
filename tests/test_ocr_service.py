"""
Unit and Integration Tests for Bodhan Indic-OCR Service (Mocked)
Tests client initialization, missing credentials, image encoding, request payload structure,
response parsing, retries, and error handling.
"""

import pytest
import base64
from unittest.mock import MagicMock, patch
import requests

from src.core.config import BodhanOCRConfig
from src.core.exceptions import (
    OCRConfigurationError,
    OCRAuthenticationError,
    OCRRateLimitError,
    OCRTimeoutError,
    OCRExtractionError,
    OCRError,
)
from src.ai.ocr_service import BodhanOCRService


def test_ocr_missing_key():
    cfg = BodhanOCRConfig(api_key=None)
    service = BodhanOCRService(cfg)
    with pytest.raises(OCRConfigurationError) as exc_info:
        service.extract_from_image_bytes(b"dummy_bytes")
    assert "BODHAN_API_KEY" in str(exc_info.value)


def test_ocr_placeholder_key():
    cfg = BodhanOCRConfig(api_key="YOUR_BODHAN_API_KEY")
    service = BodhanOCRService(cfg)
    with pytest.raises(OCRConfigurationError) as exc_info:
        service.extract_from_image_bytes(b"dummy_bytes")
    assert "BODHAN_API_KEY" in str(exc_info.value)


def test_ocr_successful_extraction():
    cfg = BodhanOCRConfig(api_key="bodhan_test_secret_key")
    service = BodhanOCRService(cfg)

    dummy_image = b"FAKE_PNG_BINARY_DATA"
    expected_b64 = base64.b64encode(dummy_image).decode()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "indic-ocr",
        "choices": [
            {
                "message": {
                    "content": "Chapter 1: Chemical Reactions and Equations\nActivity 1.1: Heating Magnesium Ribbon"
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = service.extract_from_image_bytes(dummy_image)

        assert "Chemical Reactions" in result["text"]
        assert result["model"] == "indic-ocr"
        assert result["status"] == "SUCCESS"
        assert result["confidence"] is None  # Not fabricated

        # Verify request structure
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.bodhan.ai/v1/chat/completions"
        payload = call_args[1]["json"]
        assert payload["model"] == "indic-ocr"
        assert "data:image/png;base64," + expected_b64 in payload["messages"][0]["content"][0]["image_url"]["url"]


def test_ocr_authentication_failure():
    cfg = BodhanOCRConfig(api_key="bodhan_invalid_key", max_retries=2)
    service = BodhanOCRService(cfg)

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized: Invalid API Key"

    with patch("requests.post", return_value=mock_resp) as mock_post:
        with pytest.raises(OCRAuthenticationError):
            service.extract_from_image_bytes(b"image_bytes")

        # Must not retry auth errors
        assert mock_post.call_count == 1


def test_ocr_rate_limit_and_retry():
    cfg = BodhanOCRConfig(api_key="bodhan_valid_key", max_retries=1)
    service = BodhanOCRService(cfg)

    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Too many requests"

    with patch("requests.post", return_value=mock_resp_429) as mock_post:
        with patch("time.sleep", return_value=None):
            with pytest.raises(OCRRateLimitError):
                service.extract_from_image_bytes(b"image_bytes")

        assert mock_post.call_count == 2


def test_ocr_empty_response():
    cfg = BodhanOCRConfig(api_key="bodhan_valid_key", max_retries=0)
    service = BodhanOCRService(cfg)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"model": "indic-ocr", "choices": []}

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(OCRExtractionError):
            service.extract_from_image_bytes(b"image_bytes")

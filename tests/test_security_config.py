"""
Unit Tests for Security, Secret Masking, and Configuration
"""

from src.core.security import mask_secret, sanitize_headers, sanitize_log_message
from src.core.config import NVIDIAConfig, BodhanOCRConfig


def test_mask_secret():
    assert mask_secret("") == "[NOT_CONFIGURED]"
    assert mask_secret("123") == "***"
    assert mask_secret("nvapi-1234567890abcdef") == "nvap...cdef"
    assert mask_secret("bodhan_secret_api_key_xyz") == "bodh..._xyz"


def test_sanitize_headers():
    headers = {
        "Authorization": "Bearer nvapi-1234567890abcdef",
        "Content-Type": "application/json",
        "X-Custom-Header": "public-value"
    }
    sanitized = sanitize_headers(headers)
    assert "1234567890" not in sanitized["Authorization"]
    assert "Bearer nvap...cdef" in sanitized["Authorization"]
    assert sanitized["Content-Type"] == "application/json"


def test_sanitize_log_message():
    msg = "Sending request to NVIDIA with token nvapi-998877665544 and Bearer my_secret_token_12345"
    sanitized = sanitize_log_message(msg)
    assert "nvapi-998877665544" not in sanitized
    assert "[REDACTED_NVIDIA_KEY]" in sanitized
    assert "my_secret_token_12345" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized


def test_config_masked_summary():
    cfg = NVIDIAConfig(api_key="nvapi-super-secret-key-1234")
    summary = cfg.masked_summary()
    assert summary["api_key_configured"] is True
    assert "super-secret" not in summary["api_key_masked"]
    assert "nvap...1234" in summary["api_key_masked"]


def test_bodhan_config_masked_summary():
    cfg = BodhanOCRConfig(api_key="bodhan_test_api_key_9999")
    summary = cfg.masked_summary()
    assert summary["api_key_configured"] is True
    assert "bodh...9999" in summary["api_key_masked"]


def test_zero_api_keys_leaked_in_workspace():
    from scripts.audit_api_leaks import audit_workspace_for_leaks
    leaks = audit_workspace_for_leaks(".")
    assert len(leaks) == 0, f"Critical security alert: API key leak detected in workspace: {leaks}"


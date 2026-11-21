"""
Unit and Integration Tests for NVIDIA Nemotron LLM Service (Mocked)
Tests client initialization, missing credentials, reasoning separation,
streaming/non-streaming, error handling, retries, and secret masking.
"""

import pytest
from unittest.mock import MagicMock, patch
from openai import AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError

from src.core.config import NVIDIAConfig
from src.core.exceptions import (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    LLMError,
)
from src.ai.llm_service import NVIDIANemotronService


def test_nvidia_client_missing_key():
    cfg = NVIDIAConfig(api_key=None)
    service = NVIDIANemotronService(cfg)
    with pytest.raises(LLMConfigurationError) as exc_info:
        service.generate([{"role": "user", "content": "Hello"}])
    assert "NVIDIA_API_KEY" in str(exc_info.value)


def test_nvidia_client_placeholder_key():
    cfg = NVIDIAConfig(api_key="nvidiaapi")
    service = NVIDIANemotronService(cfg)
    with pytest.raises(LLMConfigurationError) as exc_info:
        service.generate([{"role": "user", "content": "Hello"}])
    assert "NVIDIA_API_KEY" in str(exc_info.value)


def test_nvidia_successful_non_streaming():
    cfg = NVIDIAConfig(api_key="nvapi-test-key-123456789")
    service = NVIDIANemotronService(cfg)

    # Mock completion object
    mock_choice = MagicMock()
    mock_choice.message.content = "Energy is conserved according to the First Law of Thermodynamics."
    mock_choice.message.reasoning_content = "Thinking through physics principles..."
    mock_choice.finish_reason = "stop"

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    mock_completion.usage.prompt_tokens = 25
    mock_completion.usage.completion_tokens = 15
    mock_completion.usage.total_tokens = 40

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client

        response = service.generate([{"role": "user", "content": "State law of conservation of energy"}])

        assert response.content == "Energy is conserved according to the First Law of Thermodynamics."
        assert response.reasoning_content == "Thinking through physics principles..."
        assert response.model == "nvidia/nemotron-3.5-lightning-30b-a3b"
        assert response.usage["total_tokens"] == 40
        assert response.latency_ms > 0
        assert response.finish_reason == "stop"


def test_nvidia_reasoning_content_isolation():
    """Ensure user-facing content does not accidentally expose reasoning tokens."""
    cfg = NVIDIAConfig(api_key="nvapi-test-key-123456789")
    service = NVIDIANemotronService(cfg)

    mock_choice = MagicMock()
    mock_choice.message.content = "Answer for the student."
    mock_choice.message.reasoning_content = "SECRET_TEACHER_LOGIC_DO_NOT_EXPOSE"
    mock_choice.message.model_extra = None
    mock_choice.finish_reason = "stop"

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    mock_completion.usage = None

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client

        response = service.generate([{"role": "user", "content": "Query"}])
        assert "SECRET_TEACHER_LOGIC" not in response.content
        assert response.reasoning_content == "SECRET_TEACHER_LOGIC_DO_NOT_EXPOSE"


def test_nvidia_successful_streaming():
    cfg = NVIDIAConfig(api_key="nvapi-test-key-123456789")
    service = NVIDIANemotronService(cfg)

    # Mock chunk stream
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.reasoning_content = "Analyzing question..."
    chunk1.choices[0].delta.content = None

    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.reasoning_content = None
    chunk2.choices[0].delta.content = "Ohm's law states that "

    chunk3 = MagicMock()
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta.reasoning_content = None
    chunk3.choices[0].delta.content = "V = IR."

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2, chunk3]
        mock_get_client.return_value = mock_client

        chunks = list(service.stream_generate([{"role": "user", "content": "Explain Ohm's Law"}]))

        assert chunks == [
            ("reasoning", "Analyzing question..."),
            ("content", "Ohm's law states that "),
            ("content", "V = IR."),
        ]


def test_nvidia_json_mode_validation():
    cfg = NVIDIAConfig(api_key="nvapi-test-key-123456789")
    service = NVIDIANemotronService(cfg)

    mock_choice = MagicMock()
    mock_choice.message.content = '{"concept": "Photosynthesis", "status": "VERIFIED"}'
    mock_choice.message.reasoning_content = None
    mock_choice.message.model_extra = None
    mock_choice.finish_reason = "stop"

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    mock_completion.usage = None

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client

        resp = service.generate([{"role": "user", "content": "json query"}], json_mode=True)
        assert "Photosynthesis" in resp.content


def test_nvidia_json_mode_malformed_raises_error():
    cfg = NVIDIAConfig(api_key="nvapi-test-key-123456789")
    service = NVIDIANemotronService(cfg)

    mock_choice = MagicMock()
    mock_choice.message.content = 'NOT VALID JSON'
    mock_choice.message.reasoning_content = None

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    mock_completion.usage = None

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMResponseError):
            service.generate([{"role": "user", "content": "json query"}], json_mode=True)


def test_nvidia_auth_failure_no_infinite_retry():
    cfg = NVIDIAConfig(api_key="nvapi-invalid-key", max_retries=2)
    service = NVIDIANemotronService(cfg)

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        # AuthenticationError should raise immediately without 3 retry loops
        mock_client.chat.completions.create.side_effect = AuthenticationError("Invalid API key", response=MagicMock(status_code=401), body={})
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMAuthenticationError):
            service.generate([{"role": "user", "content": "Test"}])

        assert mock_client.chat.completions.create.call_count == 1


def test_nvidia_rate_limit_and_retry():
    cfg = NVIDIAConfig(api_key="nvapi-valid-key", max_retries=1)
    service = NVIDIANemotronService(cfg)

    with patch.object(service, "_get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded", response=MagicMock(status_code=429), body={})
        mock_get_client.return_value = mock_client

        with patch("time.sleep", return_value=None):
            with pytest.raises(LLMRateLimitError):
                service.generate([{"role": "user", "content": "Test"}])

        # Initial try + 1 retry = 2 calls
        assert mock_client.chat.completions.create.call_count == 2

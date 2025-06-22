import logging
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from openrouter_utils import DEFAULT_EMBEDDING_MODEL, OpenRouter
from openrouter_utils import DEFAULT_OPENROUTER_MODEL

# Configure logging for tests
logger = logging.getLogger("OpenRouterTest")
logging.basicConfig(level=logging.INFO)


@pytest.fixture(scope="module")
def openrouter_instance():

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY environment variable not set. Skipping tests.")

    try:
        openrouter = OpenRouter(api_key=api_key)
        return openrouter
    except Exception as e:
        logger.error(f"Failed to initialize OpenRouter for tests: {str(e)}")
        pytest.fail(f"Failed to initialize OpenRouter: {str(e)}")


def test_openrouter_initialization(openrouter_instance):
    """
    Tests the OpenRouter initialization and basic getters.
    """
    assert openrouter_instance is not None
    assert openrouter_instance.get_url() == "https://openrouter.ai/api/v1/chat/completions"
    assert openrouter_instance.get_model_name() == DEFAULT_OPENROUTER_MODEL
    assert openrouter_instance.get_temperature() == 0.3
    assert openrouter_instance.get_system_prompt() is not None
    logger.info("OpenRouter initialization test passed")


def test_openrouter_getters(openrouter_instance):
    """
    Tests all the getter methods of OpenRouter.
    """
    url = openrouter_instance.get_url()
    model_name = openrouter_instance.get_model_name()
    max_tokens = openrouter_instance.get_max_tokens()
    system_prompt = openrouter_instance.get_system_prompt()
    temperature = openrouter_instance.get_temperature()

    assert isinstance(url, str)
    assert isinstance(model_name, str)
    assert isinstance(system_prompt, str)
    assert isinstance(temperature, float)
    assert max_tokens is None or isinstance(max_tokens, int)

    logger.info(f"URL: {url}")
    logger.info(f"Model: {model_name}")
    logger.info(f"Temperature: {temperature}")
    logger.info(f"Max tokens: {max_tokens}")


@patch('openrouter_utils.requests.post')
def test_get_llm_response_success(mock_post, openrouter_instance):
    """
    Tests successful LLM response using mocked requests.
    """
    # Mock successful response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"response": {"answer": {"body": "Test response", "confidence": "0.9"}}, "status": "success"}'
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    test_prompt = "How is a model context protocol server helpful to an LLM?"
    success, result = openrouter_instance.get_llm_response(prompt=test_prompt)

    assert success is True
    assert isinstance(result, dict)
    assert "response" in result
    logger.info(f"Successful response test passed with result: {result}")


@patch('openrouter_utils.requests.post')
def test_get_llm_response_http_error(mock_post, openrouter_instance):
    """
    Tests LLM response with HTTP error using mocked requests.
    """
    # Mock HTTP error response
    from requests.exceptions import HTTPError
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.json.return_value = {"error": "Invalid API key"}

    http_error = HTTPError()
    http_error.response = mock_response
    mock_post.side_effect = http_error

    test_prompt = "Test prompt"
    success, result = openrouter_instance.get_llm_response(prompt=test_prompt)

    assert success is False
    assert isinstance(result, dict)
    assert "response" in result
    assert "answer" in result["response"]
    assert "error" in result["status"]
    logger.info(f"HTTP error test passed with result: {result}")


@patch('openrouter_utils.requests.post')
def test_get_llm_response_no_choices(mock_post, openrouter_instance):
    """
    Tests LLM response when API returns no choices.
    """
    # Mock response with no choices
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"choices": []}
    mock_post.return_value = mock_response

    test_prompt = "Test prompt"
    success, result = openrouter_instance.get_llm_response(prompt=test_prompt)

    assert success is False
    assert isinstance(result, dict)
    assert "response" in result
    assert "status" in result
    assert result["status"] == "error"
    logger.info(f"No choices test passed with result: {result}")


@patch('openrouter_utils.requests.post')
def test_get_llm_response_json_decode_error(mock_post, openrouter_instance):
    """
    Tests LLM response when JSON decoding fails.
    """
    # Mock response that raises JSONDecodeError
    from json import JSONDecodeError
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
    mock_post.return_value = mock_response

    test_prompt = "Test prompt"
    success, result = openrouter_instance.get_llm_response(prompt=test_prompt)

    assert success is False
    assert isinstance(result, dict)
    assert "response" in result
    assert "status" in result
    assert result["status"] == "error"
    logger.info(f"JSON decode error test passed with result: {result}")

def test_clean_json_str_invalid_json(openrouter_instance):
    """
    Tests the _clean_json_str method with invalid JSON.
    """
    invalid_json_str = '{"test": "value", "invalid": }'
    result = openrouter_instance._clean_json_str(invalid_json_str)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "Invalid JSON format"
    logger.info(f"Invalid JSON cleaning test passed: {result}")


def test_missing_response_format(openrouter_instance):
    """
    Tests the _missing_response method format.
    """
    error_message = "Test error message"
    result = openrouter_instance._missing_response(error_message)

    assert isinstance(result, dict)
    assert "response" in result
    assert "answer" in result["response"]
    assert "body" in result["response"]["answer"]
    assert result["response"]["answer"]["body"] == error_message
    assert result["response"]["answer"]["confidence"] == "0"
    assert result["status"] == "error"
    logger.info(f"Missing response format test passed: {result}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])

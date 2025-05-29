import os
import requests
import json
import logging
from typing import Tuple, Dict, Any, Optional, List

_logger: logging.Logger = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-3.5-turbo" # A common default, can be changed

class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass

def get_openrouter_response(
    api_key: str,
    model_name: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    site_url: Optional[str] = "http://localhost:3000", # Recommended by OpenRouter
    site_name: Optional[str] = "MCPClient" # Recommended by OpenRouter
) -> Tuple[bool, Any]:
    """
    Contacts the OpenRouter.ai API to get a response from a specified model.

    :param api_key: Your OpenRouter.ai API key.
    :param model_name: The name of the model to use (e.g., "openai/gpt-3.5-turbo").
    :param prompt: The user's prompt.
    :param system_prompt: An optional system message to guide the model's behavior.
    :param temperature: Sampling temperature, between 0 and 2.
    :param max_tokens: Optional maximum number of tokens to generate.
    :param site_url: Your app's site URL for OpenRouter to identify your app.
    :param site_name: Your app's name for OpenRouter to identify your app.
    :return: A tuple (success: bool, response_content: Any).
             If success is True, response_content is the parsed JSON response from the API.
             If success is False, response_content is an error message string.
    """
    if not api_key:
        _logger.error("OpenRouter API key is missing.")
        return False, "Error: OpenRouter API key is required."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-Title"] = site_name

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    url = f"{OPENROUTER_API_BASE_URL}/chat/completions"

    try:
        _logger.debug(f"Sending request to OpenRouter: URL='{url}', Model='{model_name}', Payload='{json.dumps(payload, indent=2)}'")
        response = requests.post(url, headers=headers, json=payload, timeout=120) # 120s timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        _logger.debug(f"Received response from OpenRouter: {json.dumps(response_data, indent=2)}")

        if response_data.get("choices") and len(response_data["choices"]) > 0:
            # Typically, the main content is in the first choice's message
            message_content = response_data["choices"][0].get("message", {}).get("content")
            if message_content:
                return True, message_content # Return the string content directly
            else: # If content is missing for some reason
                return True, response_data # Fallback to returning the whole data
        else: # If no choices or choices array is empty
            _logger.warning(f"OpenRouter response did not contain expected choices: {response_data}")
            return False, f"Error: OpenRouter response format unexpected - no choices. Full response: {response_data}"


    except requests.exceptions.HTTPError as http_err:
        error_content = "Unknown error"
        try:
            error_content = http_err.response.json()
        except json.JSONDecodeError:
            error_content = http_err.response.text
        _logger.error(f"OpenRouter HTTP error: {http_err.response.status_code} - {error_content}")
        return False, f"Error: OpenRouter API request failed with status {http_err.response.status_code} - {error_content}"
    except requests.exceptions.RequestException as req_err:
        _logger.error(f"OpenRouter request exception: {req_err}")
        return False, f"Error: Failed to connect to OpenRouter: {req_err}"
    except json.JSONDecodeError:
        _logger.error("Failed to decode JSON response from OpenRouter.")
        return False, "Error: Invalid JSON response from OpenRouter."
    except KeyError as key_err:
        _logger.error(f"Unexpected response format from OpenRouter (KeyError): {key_err}")
        return False, f"Error: Unexpected response format from OpenRouter (missing key: {key_err})."
    except Exception as e:
        _logger.exception(f"An unexpected error occurred while calling OpenRouter: {e}")
        return False, f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    # Example usage:
    # Ensure you have OPENROUTER_API_KEY environment variable set or pass it directly.
    api_key_env = os.environ.get("OPENROUTER_API_KEY")
    if not api_key_env:
        print("Please set the OPENROUTER_API_KEY environment variable to run the example.")
    else:
        print("Testing OpenRouter API call...")
        test_prompt = "What is the capital of France?"
        test_model = "openai/gpt-3.5-turbo" # You can change this to other models supported by OpenRouter

        success, result = get_openrouter_response(
            api_key=api_key_env,
            model_name=test_model,
            prompt=test_prompt,
            system_prompt="You are a helpful assistant."
        )

        if success:
            print(f"\nModel: {test_model}")
            print(f"Prompt: {test_prompt}")
            print("Response:")
            # If result is a string (the message content)
            if isinstance(result, str):
                print(result)
            # If result is the full JSON (fallback or if you change the return)
            else:
                print(json.dumps(result, indent=2))
        else:
            print(f"\nFailed to get response from OpenRouter.")
            print(f"Error: {result}")

        print("\nTesting with a non-existent model (expecting failure):")
        success_fail, result_fail = get_openrouter_response(
            api_key=api_key_env,
            model_name="nonexistent/model-v1",
            prompt="This should fail."
        )
        if not success_fail:
            print(f"Correctly failed for non-existent model.")
            print(f"Error: {result_fail}")
        else:
            print("Test with non-existent model did not fail as expected.")
            print(f"Response: {result_fail}")
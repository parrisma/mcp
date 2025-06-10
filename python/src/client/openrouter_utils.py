import os
import requests
import json
import logging
import re
from typing import Tuple, Dict, Any, Optional, List

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-pro-preview"


class OpenRouter:

    class OpenRouterError(Exception):
        pass

    def __init__(self,
                 api_key: str,
                 openrouter_url: Optional[str] = None,
                 model_name: Optional[str] = None,
                 max_tokens: Optional[int] = None,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.3,) -> None:

        self._log: logging.Logger = logging.getLogger(__name__)
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        if openrouter_url is None:
            openrouter_url = OPENROUTER_API_BASE_URL
        else:
            self._openrouter_url: str = openrouter_url
        self._api_key: str = api_key
        if not model_name:
            self._model_name = DEFAULT_OPENROUTER_MODEL
        else:
            self._model_name: str = model_name
        self._temperature: float = temperature
        self._max_tokens: int | None = max_tokens
        self._url: str = f"{OPENROUTER_API_BASE_URL}/chat/completions"
        if system_prompt is not None:
            self._system_prompt: str = system_prompt
        else:
            self._system_prompt: str = "you are an expert assistant that answers questions directly and concisely, without any additional information or disclaimers. You are very helpful and friendly, but you do not provide any additional information or disclaimers. You answer questions directly and concisely"

    def get_url(self) -> str:
        """Returns the OpenRouter API URL."""
        return self._url

    def get_model_name(self) -> str:
        """Returns the model name being used."""
        return self._model_name

    def get_max_tokens(self) -> Optional[int]:
        """Returns the maximum number of tokens for the response."""
        return self._max_tokens

    def get_system_prompt(self) -> str:
        """Returns the system prompt being used."""
        return self._system_prompt

    def get_temperature(self) -> float:
        """Returns the temperature setting for the API call."""
        return self._temperature

    def _clean_json_str(self,
                         jason_str: str) -> Dict[str, Any]:
        jason_str = re.sub(r"[\n\t`']", "", jason_str, flags=re.MULTILINE)
        jason_str = re.sub(r"^json", "", jason_str, flags=re.IGNORECASE)
        response: Dict[str, str] = {}
        try:
            response = json.loads(jason_str)
        except json.JSONDecodeError as je:
            msg: str = f"JSON Decode Error: {je.msg} at line {je.lineno}, column {je.colno}"
            self._log.error(msg=msg)
            response = {
                "error": "Invalid JSON format",
                "details": msg
            }
        except Exception as e:
            msg: str = f"Unexpected error while parsing JSON: {str(e)}"
            self._log.error(msg=msg)
            response = {
                "error": "Unexpected error while parsing JSON",
                "details": msg
            }
        # Normalize the JSON string to ensure it's a valid JSON object
        return json.loads(json.dumps(response, ensure_ascii=False, indent=2))

    def _missing_response(self,
                          error_message: str) -> Dict[str, Any]:
        return {
            "response": {
                "answer": {
                    "body": f"{error_message}",
                    "confidence": "0"
                },
                "clarifications": [],
                "mcp_server_calls": [],
                "thinking": {
                }
            },
            "status": "error"
        }

    def get_llm_response(self,
                         prompt: str
                         ) -> Tuple[bool, Any]:
        """
        Contacts the OpenRouter.ai API to get a response to the given prompt.

        :param prompt: The user's prompt.
        :return: A tuple (success: bool, response_content: Any).
                 If success is True, response_content is formatted JSON response from the API.
                 If success is False, response_content is formatted JSON with error in answer field.
        """

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        headers["X-Title"] = "MCP Client Web Server"

        messages: List[Dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": self._temperature,
        }
        if self._max_tokens is not None:
            payload["max_tokens"] = self._max_tokens

        try:
            self._log.debug(
                f"Sending request to OpenRouter: URL='{self._url}', Model='{self._model_name}', Payload='{json.dumps(payload, indent=2)}'")
            response: requests.Response = requests.post(self._url, 
                                                        headers=headers,
                                                        json=payload, 
                                                        timeout=120) 
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            response_data = response.json()
            self._log.debug(
                f"Received response from OpenRouter: {json.dumps(response_data, indent=2)}")

            if response_data.get("choices") and len(response_data["choices"]) > 0:
                # Typically, the main content is in the first choice's message
                message_content = self._clean_json_str(
                    response_data["choices"][0].get("message", {}).get("content"))
                if message_content:
                    # Return response as Response JSON object expected by the client
                    return True, message_content
                else:
                    msg = "Error, content could not be located in the llm response"
                    self._log.error(msg)
                    return False, self._missing_response(msg)
            else:  # If no choices or choices array is empty
                msg = f"Error, OpenRouter response did not contain expected choices: {response_data}"
                self._log.error(msg)
                return False, self._missing_response(msg)

        except requests.exceptions.HTTPError as http_err:
            error_content = "Unknown error"
            try:
                error_content = http_err.response.json()
            except json.JSONDecodeError:
                error_content = http_err.response.text
                msg = f"Error, OpenRouter HTTP error: {http_err.response.status_code} - {error_content}"
                self._log.error(msg)
                return False, self._missing_response(msg)
        except requests.exceptions.RequestException as req_err:
            msg = f"Error, OpenRouter request exception: {req_err}"
            self._log.error(msg)
            return False, self._missing_response(msg)
        except json.JSONDecodeError:
            msg = "Error, failed to decode JSON response from OpenRouter."
            self._log.error(msg)
            return False, self._missing_response(msg)
        except KeyError as key_err:
            msg = f"Error, unexpected response format from OpenRouter (KeyError): {key_err}"
            self._log.error(msg)
            return False, self._missing_response(msg)
        except Exception as e:
            msg = f"Error, an unexpected error occurred while calling OpenRouter: {e}"
            self._log.exception(msg)
            return False, self._missing_response(msg)
        return False, self._missing_response("Unknown error occurred in get_llm_response.")


if __name__ == "__main__":
    # Example usage:
    # Ensure you have OPENROUTER_API_KEY environment variable set or pass it directly.
    api_key_env = os.environ.get("OPENROUTER_API_KEY")
    if not api_key_env:
        print("Please set the OPENROUTER_API_KEY environment variable to run the example.")
    else:
        print("Testing OpenRouter API call...")

        openrouter = OpenRouter(api_key=api_key_env)

        test_prompt_path = os.path.join(
            os.path.dirname(__file__), "test_prompt.txt")
        if os.path.isfile(test_prompt_path):
            with open(test_prompt_path, "r", encoding="utf-8") as f:
                test_prompt = f.read().strip()
        else:
            test_prompt = "How a model context protocol server helpful to an LLM ?"

        success, result = openrouter.get_llm_response(
            prompt=test_prompt
        )

        if success:
            print(f"Prompt: {test_prompt}")
            print("Response:")
            if isinstance(result, str):
                print(result)
            else:
                print(json.dumps(result, indent=2))
        else:
            print(f"\nFailed to get response from OpenRouter.")
            print(f"Error: {result}")

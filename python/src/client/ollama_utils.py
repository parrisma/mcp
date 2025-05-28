import os
import mcp
import requests
import json
import logging
from typing import Tuple, Dict
from enum import Enum
from ollama import EmbeddingsResponse, embeddings
from datetime import datetime
from yarl import URL
from .prompts import get_initial_prompt

_logger: logging.Logger = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,  # Default to INFO, can be overridden by application
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


class OllamaModel(Enum):
    LLAMA2_7B = "llama2:7b"
    LLAMA3_3_LATEST = "llama3.3:latest"
    QWEN2_5_72B = "qwen2.5:72b"


ollama_model = OllamaModel.QWEN2_5_72B.value
ollama_host = "http://localhost:11434"


def ollama_running_and_model_loaded(host_url: URL,
                                    model_name: str) -> bool:
    try:
        response: requests.Response = requests.get(
            str(host_url.joinpath("api/tags")))
        response.raise_for_status()
        models = [m["name"] for m in response.json()["models"]]
        loaded_ok: bool = model_name in models
        if loaded_ok:
            _logger.debug(f"Ollama - model is loaded OK [{model_name}]")
        else:
            _logger.debug(f"Ollama - model is not loaded [{model_name}]")
        return loaded_ok
    except requests.exceptions.RequestException as e:
        _logger.debug(
            f"Ollama - An error occurred, getting model [{model_name}] status: {e}")
        return False


def clean_json_str(jason_str: str) -> str:
    jason_str = jason_str.replace('\n', '')
    jason_str = jason_str.replace('`', '')
    jason_str = jason_str.replace('\'', '')

    first_bracket_index = jason_str.find('[')
    last_bracket_index = jason_str.rfind(']')

    if first_bracket_index == -1 and last_bracket_index == -1:
        return jason_str

    if first_bracket_index != -1 and last_bracket_index != -1:
        return jason_str[first_bracket_index+1:last_bracket_index]

    jason_str = jason_str.replace('[', '')
    jason_str = jason_str.replace(']', '')
    return jason_str


def get_ollama_response(prompt: str,
                        model: str,
                        host: str,
                        temperature: float) -> Tuple[bool, str]:
    try:
        start_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _logger.debug(f"Model request starts: {start_time}")

        ollama_host: str = os.environ.get('OLLAMA_HOST', host)
        url: str = f"{ollama_host}/api/chat"
        headers: Dict[str, str] = {'Content-Type': 'application/json'}
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            'options': {'temperature': temperature}
        }

        response: requests.Response = requests.post(url, headers=headers,
                                                    data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()
        json_str: str = clean_json_str(data['message']['content'])

        end_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _logger.debug(f"Model request ends: {end_time}")
        _logger.debug(f"Model request duration: {(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')).seconds // 60} mins and {(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')).seconds % 60} seconds")

        return (True, json.loads(json_str))

    except requests.exceptions.RequestException as e:
        return (False, f"Error: Failed to connect to Ollama: {e}")
    except json.JSONDecodeError:
        return (False, "Error: Invalid JSON response from Ollama.")
    except KeyError:
        return (False, "Error: Unexpected response format from Ollama.")
    except Exception as e:
        return (False, f"An unexpected error occurred: {e}")


def get_initial_response(user_goal: str,
                         mcp_server_descriptions: str,
                         model: str,
                         host: str,
                         temperature) -> Tuple[bool, Dict]:
    try:
        prompt: str = get_initial_prompt(
            mcp_server_descriptions=mcp_server_descriptions,
            goal=user_goal
        )

        res, reply = get_ollama_response(
            prompt, model=model, host=host, temperature=temperature)
        return res, reply
    except Exception as e:
        msg: str = f"Error in get_initial_response: {e}"
        _logger.error(msg)
        return False, {"error": msg}

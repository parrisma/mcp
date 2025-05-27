import os
import requests
import json
import logging
from typing import Tuple, List, Dict
from enum import Enum
from ollama import EmbeddingsResponse, embeddings
from datetime import datetime
from yarl import URL

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

# Create embedding and load files into Chroma
#


def generate_ollama_embedding(text: str,
                              model: str,
                              host: str) -> List[float]:
    try:
        if os.environ.get("OLLAMA_HOST") != host:
            os.environ["OLLAMA_HOST"] = host
        response: EmbeddingsResponse = embeddings(model=model, prompt=text)
        return response['embedding']
    except Exception as e:
        _logger.debug(f"Ollama - Error generating embedding: {e}")
        return []


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
    jason_str = jason_str.replace('\`', '')
    jason_str = jason_str.replace('\'', '')

    first_bracket_index = jason_str.find('[')
    last_bracket_index = jason_str.rfind(']')

    if first_bracket_index == -1 or last_bracket_index == -1:
        return None  # No brackets found

    if first_bracket_index == last_bracket_index:
        return None  # only one bracket found

    if first_bracket_index > last_bracket_index:
        return None  # first bracket after last bracket

    return jason_str[first_bracket_index+1:last_bracket_index]


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

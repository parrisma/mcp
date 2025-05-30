import os
import mcp
import requests
import json
import logging
import re
import uuid
from typing import Tuple, Dict, Any, List
from enum import Enum
from datetime import datetime
from yarl import URL
from .prompts import get_llm_prompt

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
    jason_str = re.sub(r"[\n\t`']", "", jason_str, flags=re.MULTILINE)
    jason_str = re.sub(r"^json", "", jason_str, flags=re.IGNORECASE)
    response: Dict[str, str] = {}
    try:
        response = json.loads(jason_str)
    except json.JSONDecodeError as je:
        msg: str = f"JSON Decode Error: {je.msg} at line {je.lineno}, column {je.colno}"
        _logger.error(msg=msg)
        response = {
            "error": "Invalid JSON format",
            "details": msg
        }
    except Exception as e:
        msg: str = f"Unexpected error while parsing JSON: {str(e)}"
        _logger.error(msg=msg)
        response = {
            "error": "Unexpected error while parsing JSON",
            "details": msg
        }
    return json.dumps(response, ensure_ascii=False, indent=2)


def get_ollama_response(prompt: str,
                        model: str,
                        host_and_port_url: str,
                        temperature: float) -> Tuple[bool, Dict]:
    try:
        start_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _logger.debug(f"Model request starts: {start_time}")

        ollama_host: str = os.environ.get('OLLAMA_HOST', host_and_port_url)
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
        return (False, {"error": f"Failed to connect to Ollama: {e}"})
    except json.JSONDecodeError:
        return (False, {"error": "Invalid JSON response from Ollama."})
    except KeyError:
        return (False, {"error": "Unexpected response format from Ollama."})
    except Exception as e:
        return (False, {"error": f"An unexpected error occurred: {e}"})


def _log_prompt(prompt: str) -> None:
    try:
        with open("prompt_log.txt", "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n\n")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\n\n")
            f.write(prompt + "\n")
            f.write("=" * 80 + "\n\n")
    except Exception as e:
        _logger.error(f"Failed to log prompt: {e}")


def get_llm_response(user_goal: str,
                     session_id: uuid.UUID,
                     mcp_server_descriptions: Dict[str, Any],
                     mcp_responses: List[Dict[str, Any]],
                     clarifications: List[Dict[str, Any]],
                     model: str,
                     host: str,
                     temperature) -> Tuple[bool, Dict]:
    try:
        prompt: str = get_llm_prompt(
            goal=user_goal,
            session_id=str(session_id),
            mcp_server_descriptions=json.dumps(mcp_server_descriptions),
            mcp_responses=json.dumps(
                mcp_responses, ensure_ascii=False, indent=2),
            clarifications=json.dumps(
                clarifications, ensure_ascii=False, indent=2),
        )

        _log_prompt(prompt)

        res, reply = get_ollama_response(
            prompt, model=model, host_and_port_url=host, temperature=temperature)
        # No change needed here now, as reply will always be a Dict
        return res, reply
    except Exception as e:
        msg: str = f"Error in get_llm_response: {e}"
        _logger.error(msg)
        return False, {"error": msg}

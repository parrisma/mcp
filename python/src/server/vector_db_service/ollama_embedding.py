import os
import requests
import json
import logging
from typing import Optional, Tuple, List, Dict
from enum import Enum
from ollama import EmbeddingsResponse, embeddings
from datetime import datetime

from sympy import E


class OllamaEmbedding:

    class OllamaModel(Enum):
        LLAMA2_7B = "llama2:7b"
        LLAMA3_3_LATEST = "llama3.3:latest"
        QWEN2_5_72B = "qwen2.5:72b"

    ollama_model = OllamaModel.QWEN2_5_72B.value
    # running inside container so ollama_gpu is host name of the ollama container
    # To access this outside of the dev container use localhost:11434
    ollama_host = "http://ollama-gpu:11434"

    class OllamaGenerationError(Exception):
        pass

    def __init__(self,
                 model: str = ollama_model,
                 host: str = ollama_host) -> None:
        self._model = model
        self._host = host
        self._log: logging.Logger = self._configure_logging()
        self._log.debug(
            f"OllamaUtils initialized with model: {self._model}, host: {self._host}")

    def _configure_logging(self) -> logging.Logger:
        log: logging.Logger = logging.getLogger("mcp-client-runner")
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        return log

    def generate_embedding(self,
                           text: str) -> Optional[List[float]]:
        try:
            # Ollama expects the host to be set in the environment variable OLLAMA_HOST
            response: EmbeddingsResponse = embeddings(
                model=self._model, prompt=text)
            embedding = response['embedding']
            if embedding is None or not isinstance(embedding, list) or not isinstance(embedding[0], float) or len(embedding) <= 0:
                msg = f"Invalid embedding response: {embedding}"
                self._log.error(msg)
                raise self.OllamaGenerationError(msg)
            return embedding
        except Exception as e:
            msg = f"Ollama - Error generating embedding: {str(e)}"
            self._log.error(msg)
            raise self.OllamaGenerationError(msg)

    def ollama_running_and_model_loaded(self) -> bool:
        try:
            response = requests.get(f"{self._host}/api/tags")
            response.raise_for_status()
            models = [m["name"] for m in response.json()["models"]]
            loaded_ok = self._model in models
            if loaded_ok:
                self._log.debug(f"Ollama - model is loaded OK [{self._model}]")
            else:
                self._log.debug(
                    f"Ollama - model is not loaded [{self._model}]")
            return loaded_ok
        except requests.exceptions.RequestException as e:
            self._log.debug(
                f"Ollama - An error occurred, getting model [{self._model}] status: {e}")
            return False


if __name__ == "__main__":
    ollama_embedding = OllamaEmbedding()
    if ollama_embedding.ollama_running_and_model_loaded():
        try:
            response = ollama_embedding.generate_embedding(
                "Some text to embed")
            print("Embedding:", response)
        except OllamaEmbedding.OllamaGenerationError as oe:
            print("Error generating embedding:", str(oe))
        except Exception as re:
            print("Unexpected error:", str(re))
    else:
        print("Ollama is not running or model is not loaded.")

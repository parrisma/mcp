from abc import ABC, abstractmethod
from ast import Str
from typing import Callable, List, Tuple, Dict, Any
from enum import Enum


class IMCPServer(ABC):

    def _raise_not_implemented(self, method_name: str) -> None:
        raise NotImplementedError(
            f"IMCPServer method [{method_name}] must be implemented in a subclass."
        )

    class ConfigFields(Enum):
        DATA_PATH = "data_path"

    @abstractmethod
    def __init__(self,
                 logger,
                 json_config: Dict[str, Any]) -> None:
        self._raise_not_implemented("__init__")

    @property
    @abstractmethod
    def server_name(self) -> str:
        self._raise_not_implemented("server_name")

    @property
    @abstractmethod
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        self._raise_not_implemented("supported_tools")

    @property
    @abstractmethod
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        self._raise_not_implemented("supported_resources")

    @property
    @abstractmethod
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        self._raise_not_implemented("supported_prompts")

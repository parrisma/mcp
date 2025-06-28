from enum import Enum
from typing import Any, Callable, Dict, Optional
import os
from httpx import get
from ollama import Message
from mcp_client_web_server import MCPClientWebServer

DEFAULT_PORT = 6000
DEFAULT_HOST = '0.0.0.0'


class VectorDBWeb:

    class WebMessageKeys(Enum):
        DOCUMENT = "document"
        DOCUMENT_GUID = "document_guid"
        STATUS = "status"
        ERROR = "error"
        OK = "ok"

    class DocumentType(Enum):
        NEWS = "news"
        RESEARCH = "research"
        MESSAGE = "message"
        TRADE = "trade"
        GENERAL = "general"

    class handlerFunctions(Enum):
        ADD_DOCUMENT = "_add_document"
        GET_DOCUMENT = "_get_document"

    def __init__(self,
                 handlers: Dict[handlerFunctions, Callable],
                 host: Optional[str] = DEFAULT_HOST,
                 port: Optional[int] = DEFAULT_PORT,
                 ) -> None:

        if host is None:
            raise ValueError(
                "Host must be provided to vector_db_web or via command line argument.")
        else:
            self._host = host

        if port is None:
            raise ValueError(
                "Port must be provided to vector_db_web or via command line argument.")
        else:
            self._port = port

        self._web_server = MCPClientWebServer(host=self._host, port=self._port)

        if handlers is None:
            raise ValueError("Handlers must be provided to vgector_db_web.")

        add_handler: Callable | None = handlers.get(
            self.handlerFunctions.ADD_DOCUMENT, None)
        if add_handler is None:
            raise ValueError(
                "Add document handler must be provided to vector_db_web.")

        get_handler: Callable | None = handlers.get(
            self.handlerFunctions.GET_DOCUMENT, None)
        if get_handler is None:
            raise ValueError(
                "Get document handler must be provided to vector_db_web.")

        self._web_server.add_route(route='/add_document',
                                   methods=['POST'],
                                   handler=add_handler)

        self._web_server.add_route(route='/get_document',
                                   methods=['GET'],
                                   handler=get_handler)

        self._messages: Dict[str, Any] = {}

    def run(self) -> None:
        self._web_server.run()


if __name__ == '__main__':

    def test_add_document(document: str) -> Dict[str, Any]:
        return {
            VectorDBWeb.WebMessageKeys.STATUS.value: VectorDBWeb.WebMessageKeys.OK.value,
            VectorDBWeb.WebMessageKeys.DOCUMENT.value: document
        }

    def test_get_document(request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            VectorDBWeb.WebMessageKeys.STATUS.value: VectorDBWeb.WebMessageKeys.OK.value,
            "response": "Test response for document search"
        }

    handlers: Dict[VectorDBWeb.handlerFunctions, Callable[..., Dict[str, Any]]] = {
        VectorDBWeb.handlerFunctions.ADD_DOCUMENT: test_add_document,
        VectorDBWeb.handlerFunctions.GET_DOCUMENT: test_get_document}

    vector_db_web_service = VectorDBWeb(host='0.0.0.0',
                                        port=6000,
                                        handlers=handlers)
    vector_db_web_service.run()

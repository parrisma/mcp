from email import message
from math import e
from re import A
from tkinter import ALL
from tkinter.tix import STATUS
from typing import Dict, Any, Callable, Optional
from functools import partial, update_wrapper
import json
from enum import Enum
import argparse
from unittest.mock import DEFAULT
from xml.sax import handler

from numpy import add
import test
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

    class handlerFunctions(Enum):
        ADD_DOCUMENT = "_add_document"

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

        self._web_server.add_route(route='/add_document',
                                   methods=['POST'],
                                   handler=add_handler)

        self._messages: Dict[str, Any] = {}

    def _add_document(self,
                      document: str) -> Dict[str, Any]:
        return {
            self.WebMessageKeys.STATUS.value: self.WebMessageKeys.OK.value,
        }

    def run(self) -> None:
        self._web_server.run()


if __name__ == '__main__':

    def test_add_document(document: str) -> Dict[str, Any]:
        return {
            VectorDBWeb.WebMessageKeys.STATUS.value: VectorDBWeb.WebMessageKeys.OK.value,
            VectorDBWeb.WebMessageKeys.DOCUMENT.value: document
        }

    handlers: Dict[VectorDBWeb.handlerFunctions, Callable[..., Dict[str, Any]]] = {
        VectorDBWeb.handlerFunctions.ADD_DOCUMENT: test_add_document}

    vector_db_web_service = VectorDBWeb(host='0.0.0.0',
                                        port=6000,
                                        handlers=handlers)
    vector_db_web_service.run()

from curses import meta
from re import M
from tkinter.tix import STATUS
from typing import Dict, Any, Callable, List, Tuple, Annotated
from urllib import response
from xml.sax import handler
from flask.cli import F
from pydantic import Field
from enum import Enum
import random
import logging
import uuid
import json
import os
from i_mcp_server import IMCPServer
from chroma_util import ChromaDBUtils
from vector_db_web import VectorDBWeb
import threading


class VectorDBService(IMCPServer):

    class ErrorLoadingVectorDBConfig(RuntimeError):
        pass

    class VectorDBField(Enum):
        OK = "OK"
        ERROR = "error"
        DOCUMENT = "document"
        DOCUMENT_GUID = "document_guid"
        SIMILARITY = "similarity"
        UUID = "uuid"
        DOC_TYPE = "type"
        RESPONSE = "response"
        STATUS = "status"

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = IMCPServer.ConfigFields.DATA_PATH.value
        DB_NAME = "db_name"

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            VectorDBService.ConfigField.DB_NAME.value, "-VectorDBService")

        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"

        self._db_path: str = json_config.get(
            VectorDBService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingVectorDBConfig(
                f"Config path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            VectorDBService.ConfigField.DB_NAME.value, "vector_db_config.json")
        if not self._db_name:
            raise self.ErrorLoadingVectorDBConfig(
                "VectorDB Config path name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            msg = f"VectorDB config file {self._full_db_path} does not exist. Please ensure the path is correct."
            self._log.error(msg)
            raise self.ErrorLoadingVectorDBConfig(msg)

        self._log.info(
            f"VectorDB Service initialized name: {self._server_name} db: {self._full_db_path}")

        self._chroma = chroma_util = ChromaDBUtils()  # Default host and port.
        self._chroma_running = False
        if chroma_util.test_chroma_connection():
            self._chroma_running = True
            self._log.info("ChromaDB is running and accessible.")
        else:
            self._log.error("Vedtopr DB connot function, ChromaDB is not running or not accessible. "
                            "Ensure that the ChromaDB service is up and running.")

        self._vectordb_config: Dict[str, Any] = self._load_vectordb_config()
        if not self._vectordb_config:
            raise self.ErrorLoadingVectorDBConfig(
                "VectorDB config is empty or could not be loaded.")

        # Expose Web interface for VectorDB for document add.
        handlers: Dict[VectorDBWeb.handlerFunctions, Callable] = {
            VectorDBWeb.handlerFunctions.ADD_DOCUMENT: self.put_doc_web_call,
        }
        self._vector_db_web = VectorDBWeb(handlers=handlers)
        # Start the Vector DB Web interface in a separate thread
        web_thread = threading.Thread(
            target=self._vector_db_web.run, daemon=True)
        web_thread.start()
        self._log.info(f"Started VectorDB Web interface in background thread")

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("put_doc", self.put_doc),
                ("get_related_docs", self.get_related_docs),
                ]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return []

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return []

    def handle_request(self, request):
        # Implement this method as required by IMCPServer
        raise NotImplementedError("handle_request must be implemented.")

    def _load_vectordb_config(self) -> Dict[str, Any]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingVectorDBConfig(
                        "VectorDB config file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingVectorDBConfig(
                        "Malformed JSON in VectorDB config.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingVectorDBConfig(
                f"Error loading VectorDB config: {str(e)}") from e

    def put_doc_web_call(self,
                         document: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(document, dict):
            if "args" in document and isinstance(document["args"], dict):
                document = document["args"]
            else:
                msg = "Document is not a valid dictionary."
                self._log.error(msg=msg)
                return {self.VectorDBField.ERROR.value: msg}                
                
            if self._vector_db_web.WebMessageKeys.DOCUMENT.value in document:
                document = document[self._vector_db_web.WebMessageKeys.DOCUMENT.value]
                res = self.put_doc(document=document)
                if res and self.VectorDBField.OK.value in res:
                    return {self.VectorDBField.OK.value: res[self.VectorDBField.OK.value]}
                else:
                    msg = "Failed to add document to vector DB."
                    self._log.error(msg=msg)
                    return {self.VectorDBField.ERROR.value: msg}
            else:
                msg = "Document is not a valid dictionary."
                self._log.error(msg=msg)
                return {self.VectorDBField.ERROR.value: msg}
        return {self.VectorDBField.ERROR.value: "Invalid document format"}

    def put_doc(self,
                document: Annotated[str, Field(description="Document to add to vector DB for later semantic search")]) -> Dict[str, Any]:
        if self._chroma_running:
            try:
                if not document or not isinstance(document, str) or len(document) == 0:
                    msg = "Document is empty or not a valid string."
                    self._log.error(msg=msg)
                    raise ValueError(msg)

                meta = {
                    ChromaDBUtils.ChromaMeta.TYPE.value: ChromaDBUtils.ChromaMeta.TYPE_GENERAL.value
                }
                res = self._chroma.add_document(document=document,
                                                metadata=meta)
                if res:
                    msg = f"Document added to ChromaDB: {document[:25]}..."
                    self._log.info(msg=msg)
                    return {self.VectorDBField.OK.value: msg}
                else:
                    msg = f"Failed to add document to ChromaDB: {document[:25]}..."
                    self._log.error(msg=msg)
                    return {self.VectorDBField.ERROR.value: msg}
            except Exception as e:
                msg = f"Error adding document to ChromaDB: {str(e)}"
                self._log.error(msg=msg)
                return {self.VectorDBField.ERROR.value: msg}
        else:
            msg = "ChromaDB is not running. Cannot add document."
            self._log.error(msg=msg)
            return {self.VectorDBField.ERROR.value: "ChromaDB is not running, cannot add document."}
        return {self.VectorDBField.OK.value: "Document added successfully"}

    def get_related_docs(self,
                         document_fragment: Annotated[str, Field(description="A document fragment to do a semantic (embedding) search for related documents")],
                         num_results: Annotated[int, Field(description="Number of related documents to return", ge=1, le=100)] = 5) -> Dict[str, Any]:

        try:
            res: List[List[str]] | Dict[str, Any] = self._chroma.get_similar_docs(
                doc_to_match=document_fragment,
                num_similar=num_results)
            response = []
            if res and len(res) > 0:
                for doc in res:
                    if isinstance(doc, list) and len(doc) >= 3:
                        if self.VectorDBField.UUID.value in doc[2] and self.VectorDBField.DOC_TYPE.value in doc[2]:
                            meta: Dict[str, Any] = doc[2]  # type: ignore
                            response.append({self.VectorDBField.DOCUMENT_GUID.value: meta[self.VectorDBField.UUID.value],
                                             self.VectorDBField.DOCUMENT_GUID.value: meta[self.VectorDBField.DOC_TYPE.value],
                                             self.VectorDBField.SIMILARITY.value: doc[1],
                                             self.VectorDBField.DOCUMENT.value: doc[0]}
                                            )
                if len(response) > 0:
                    msg = f"Found {len(response)} related documents for fragment: {document_fragment[:25]}..."
                    self._log.info(msg=msg)
                    response = sorted(
                        response, key=lambda x: x[self.VectorDBField.SIMILARITY.value], reverse=True)
                    response = {self.VectorDBField.RESPONSE.value: response,
                                self.VectorDBField.STATUS.value: msg}
                else:
                    msg = "No related documents found for the given fragment."
                    self._log.info(msg=msg)
                    return {self.VectorDBField.ERROR.value: msg}
            else:
                msg = "Sorry, no related documents found."
                self._log.info(msg=msg)
                return {self.VectorDBField.ERROR.value: msg}
        except Exception as e:
            msg = f"Error retrieving related documents: {str(e)}"
            self._log.error(msg=msg)
            return {self.VectorDBField.ERROR.value: msg}

        return response

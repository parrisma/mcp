from curses import meta
from typing import Optional, Tuple, List, Callable, Dict, Any
import logging
import numpy as np
import json
import uuid
import requests
import time
import chromadb
from enum import Enum
from chromadb.config import Settings
from .ollama_embedding import OllamaEmbedding

# Chroma settings
#

chroma_host = "chromadb"  # This should be the hostname of your ChromaDB *container*
chroma_port = 8000


class ChromaDBUtils:

    class ChromaDocumentGetError(Exception):
        pass

    class ChromaManagementError(Exception):
        pass

    class ChromaDocumentPutError(Exception):
        pass

    class ChromaConfig(Enum):
        COLLECTION_NAME = "mcp-collection"

    class ChromaMeta(Enum):
        UUID = "uuid"
        TYPE = "type"
        TYPE_GENERAL = "general"
        TYPE_NEWS = "news"
        TYPE_RESEARCH = "research"
        TYPE_CHAT = "chat"
        TYPE_TRADE = "trade"

    def __init__(self,
                 host: str = chroma_host,
                 port: int = chroma_port) -> None:
        self._collection_name = self.ChromaConfig.COLLECTION_NAME.value
        self._log: logging.Logger = self._configure_logging()
        self._host = host
        self._port = port
        self._log.debug(
            f"ChromaDBUtils initialized with host: {self._host}, port: {self._port}")
        self._persistent_client = self._create_persistent_client()
        self._collection: chromadb.Collection = self._create_collection()
        self._embedding_generator = OllamaEmbedding()

    def _create_persistent_client(self):
        client_settings = Settings(
            chroma_api_impl="chromadb.api.fastapi.FastAPI",
            chroma_server_host=self._host,
            chroma_server_http_port=self._port)
        return chromadb.PersistentClient(settings=client_settings)

    def _configure_logging(self) -> logging.Logger:
        log: logging.Logger = logging.getLogger(self._collection_name)
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        return log

    def _create_collection(self) -> chromadb.Collection:

        try:
            collections = self._persistent_client.list_collections()
            collection = None
            for col in collections:
                self._log.debug(f"Chroma - Found collection: {col.name}")
                if col.name == self._collection_name:
                    collection = col
                    self._log.debug(
                        f"Chroma - Collection {self._collection_name} already exists, reusing it.")
                    break
            if collection is None:
                collection = self._persistent_client.create_collection(
                    self._collection_name, metadata={"created_at": time.time()})
                self._log.debug(
                    f"Chroma - created new collection: {collection.name}")

            collections = self._persistent_client.list_collections()
            if collection.name in [col.name for col in collections]:
                self._log.debug(
                    f"Chroma - New collection created & visible in Chroma: {collection.name}")
            else:
                msg = f"Chroma - Collection {collection.name} not found after creation."
                self._log.debug(msg)
                raise self.ChromaManagementError(msg)
        except Exception as e:
            self._log.debug(
                f"Chroma - Error creating or getting collections: {e}")
            raise

        return collection

    def _flatten_dict(self,
                      nested_dict: Dict,
                      flat_dict: Optional[Dict] = None,
                      key: str = '') -> Dict:
        if not isinstance(nested_dict, dict):
            raise TypeError(
                f"input, nested dicts must be a dictionary but given : {type(nested_dict)}")

        if flat_dict is None:
            flat_dict = {}

        for k, v in nested_dict.items():
            new_key = f"{key}.{k}" if key else k

            if isinstance(v, dict):
                self._flatten_dict(v, flat_dict, new_key)
            else:
                flat_dict[new_key] = v

        return flat_dict

    def add_document(self,
                     document: str,
                     metadata: dict) -> bool:

        try:
            docs = [document]
            guid = str(uuid.uuid4())
            guids = [guid]
            metadata[self.ChromaMeta.UUID.value] = guid
            metas = [self._flatten_dict(metadata)]

            embedding_values: List[List[float] | None] = [
                self._embedding_generator.generate_embedding(document)]
            if embedding_values is None or len(embedding_values) == 0:
                msg = "Chroma - Error generating embedding for document"
                self._log.error(msg)
                raise self.ChromaDocumentPutError(msg)
            self._collection.add(ids=guids,
                                 embeddings=embedding_values,
                                 documents=docs,
                                 metadatas=metas)
            self._log.debug("Document added to ChromaDB\n")
        except Exception as e:
            self._log.error(f"Error adding document to Chroma: {str(e)}")
            raise
        return True

    def get_similar_docs(self,
                         doc_to_match: str,
                         num_similar: int = 5,
                         source_type_hint: Optional[str] = None) -> List[List[str]] | Dict[str, Any]:
        search_embedding = self._embedding_generator.generate_embedding(
            doc_to_match)
        if search_embedding is None or len(search_embedding) == 0:
            msg = "Chroma - Error generating embedding for search document"
            self._log.error(msg)
            raise self.ChromaDocumentGetError(msg)

        if source_type_hint is not None and len(source_type_hint) > 0:
            similar_docs = self._collection.query(
                query_embeddings=[search_embedding],
                n_results=num_similar,
                where={"type": source_type_hint},
                include=["distances", "documents", "metadatas"])
        else:
            similar_docs = self._collection.query(
                query_embeddings=[search_embedding],
                n_results=num_similar,
                include=["distances", "documents", "metadatas"])
        sdst = np.array(similar_docs["distances"]).T
        sdoc = np.array(similar_docs["documents"]).T
        smet = np.array(similar_docs["metadatas"]).T
        suid = np.array([itm[0]["uuid"] for itm in smet]
                        ).reshape(np.shape(smet)[0], 1)
        res = np.hstack((sdst, sdoc, smet, suid)).tolist()
        return res

    def delete_collection_contents(self) -> None:
        self._log.debug(
            "\n############ D E L E T E  C O L L E C T I O N #########")
        self._persistent_client.delete_collection(name=self._collection.name)
        self._log.debug(f"Collection {self._collection.name} deleted")
        self._create_collection()

    def test_chroma_connection(self) -> bool:
        try:
            url = f"http://{self._host}:{self._port}/api/v2/heartbeat"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            heartbeat_data = response.json()
            self._log.debug(
                f"Chroma - connection successful. Heartbeat: {heartbeat_data}")
            return True
        except requests.exceptions.RequestException as e:
            self._log.debug(f"Chroma - connection failed: {e}")
            return False


if __name__ == "__main__":
    chroma_util = ChromaDBUtils(host=chroma_host,
                                port=chroma_port)
    if chroma_util.test_chroma_connection():
        print(f"Test connected OK to ChromaDB at {chroma_host}:{chroma_port}")
        metadata = {
            "type": "general"
        }
        test_doc = "This is a test document for ChromaDB."
        chroma_util.add_document(
            document=test_doc,
            metadata=metadata)
        res = chroma_util.get_similar_docs(
            doc_to_match=test_doc,
            source_type_hint=None,
            num_similar=5)
        print(res)
    else:
        print(
            f"Test connection to ChromaDB failed at {chroma_host}:{chroma_port}")

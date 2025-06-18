from typing import Dict, Any, Callable, List, Tuple, Annotated
from h11 import CLIENT
from pydantic import Field
import logging
import re
import uuid
import json
import os
import random
from i_mcp_server import IMCPServer
from enum import Enum
from static_data_service.static_data_service import StaticDataService


class ClientService(IMCPServer):

    class ErrorLoadingClientDatabase(RuntimeError):
        pass

    class ClientField(Enum):
        CLIENT_ID = "client_id"
        CLIENT_NAME = "client_name"
        COUNTRY_OF_RESIDENCE = "country_of_residence"
        TRADING_ACCOUNT_ID = "trading_account_id"

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = IMCPServer.ConfigFields.DATA_PATH.value
        DB_NAME = "db_name"

    _client_ids = [
        "e1b7c8a2-1f2a-4e7b-9c3d-1a2b3c4d5e6f",
        "f2c8d9b3-2e3b-5f8c-0d4e-2b3c4d5e6f7a",
        "a3d9e0c4-3f4c-6a9d-1e5f-3c4d5e6f7a8b",
        "b4e0f1d5-4a5d-7b0e-2f6a-4d5e6f7a8b9c",
        "c5f1a2e6-5b6e-8c1f-3a7b-5e6f7a8b9c0d",
        "d6a2b3f7-6c7f-9d2a-4b8c-6f7a8b9c0d1e",
        "e7b3c4a8-7d8a-0e3b-5c9d-7a8b9c0d1e2f",
        "f8c4d5b9-8e9b-1f4c-6d0a-8b9c0d1e2f3a",
        "a9d5e6c0-9f0c-2a5d-7e1b-9c0d1e2f3a4b",
        "b0e6f7d1-0a1d-3b6e-8f2c-0d1e2f3a4b5c",
        "c1f7a8e2-1b2e-4c7f-9a3d-1e2f3a4b5c6d",
        "d2a8b9f3-2c3f-5d8a-0b4e-2f3a4b5c6d7e",
        "e3b9c0a4-3d4a-6e9b-1c5f-3a4b5c6d7e8f",
        "f4c0d1b5-4e5b-7f0c-2d6a-4b5c6d7e8f9a",
        "a5d1e2c6-5f6c-8a1d-3e7b-5c6d7e8f9a0b",
        "b6e2f3d7-6a7d-9b2e-4f8c-6d7e8f9a0b1c",
        "c7f3a4e8-7b8e-0c3f-5a9d-7e8f9a0b1c2d",
        "d8a4b5f9-8c9f-1d4a-6b0e-8f9a0b1c2d3e",
        "e9b5c6a0-9d0a-2e5b-7c1f-9a0b1c2d3e4f",
        "f0c6d7b1-0e1b-3f6c-8d2a-0b1c2d3e4f5a",
        "a1d7e8c2-1f2c-4a7d-9b3e-1c2d3e4f5a6b",
        "b2e8f9d3-2a3d-5b8e-0c4f-2d3e4f5a6b7c",
        "c3f9a0e4-3b4e-6c9f-1d5a-3e4f5a6b7c8d",
        "d4a0b1f5-4c5f-7d0a-2e6b-4f5a6b7c8d9e",
        "e5b1c2a6-5d6a-8e1f-3b7c-5a6b7c8d9e0f",
        "f6c2d3b7-6e7b-9f2c-4a8d-6b7c8d9e0f1a",
        "a7d3e4c8-7f8c-0a3d-5b9e-7c8d9e0f1a2b",
        "b8e4f5d9-8a9d-1b4e-6c0f-8d9e0f1a2b3c",
        "c9f5a6e0-9b0e-2c5f-7d1a-9e0f1a2b3c4d",
        "d0a6b7f1-0c1f-3d6a-8e2b-0f1a2b3c4d5e"
    ]

    _trading_account_ids = [
        "A1B2C3D4E",
        "F5G6H7J8K",
        "L9M0N1P2Q",
        "R3S4T5U6V",
        "W7X8Y9Z0A",
        "B2C3D4E5F",
        "G6H7J8K9L",
        "M0N1P2Q3R",
        "S4T5U6V7W",
        "X8Y9Z0A1B",
        "C3D4E5F6G",
        "H7J8K9L0M",
        "N1P2Q3R4S",
        "T5U6V7W8X",
        "Y9Z0A1B2C",
        "D4E5F6G7H",
        "J8K9L0M1N",
        "P2Q3R4S5T",
        "U6V7W8X9Y",
        "Z0A1B2C3D",
        "E5F6G7H8J",
        "K9L0M1N2P",
        "Q3R4S5T6U",
        "V7W8X9Y0Z"
    ]

    @staticmethod
    def get_trading_account_ids() -> List[str]:
        return ClientService._trading_account_ids

    @staticmethod
    def get_client_ids() -> List[str]:
        return ClientService._client_ids

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            ClientService.ConfigField.DB_NAME.value, "ClientService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"

        self._staticDataService: StaticDataService = StaticDataService(
            logger, json_config)

        self._db_path: str = json_config.get(
            ClientService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingClientDatabase(
                f"Database path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            ClientService.ConfigField.DB_NAME.value, "client.json")
        if not self._db_name:
            raise self.ErrorLoadingClientDatabase(
                "Database name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            msg = f"Client database file {self._full_db_path} does not exist. Please ensure the path is correct."
            self._log.error(msg)
            raise self.ErrorLoadingClientDatabase(msg)

        self._log.info(
            f"ClientService initialized name: {self._server_name} db: {self._full_db_path}")

        self._client_db: List[Dict[str, Any]
                              ] = self._load_client_database()
        if not self._client_db:
            raise self.ErrorLoadingClientDatabase(
                "Client database is empty or could not be loaded.")

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_client_field_names", self.get_all_client_field_names),
                ("get_clients", self.get_clients)
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

    def _load_client_database(self) -> List[Dict[str, Any]]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingClientDatabase(
                        "Client database file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingClientDatabase(
                        "Malformed JSON in client database.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingClientDatabase(
                f"Error loading client database: {str(e)}") from e

    def get_all_client_field_names(self) -> Dict[str, Any]:
        try:
            return {"client_fields": [field.value for field in self.ClientField.__members__.values()]}
        except Exception as e:
            msg = f"Error retrieving client field names: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_clients(self,
                    field_name: Annotated[str, Field(description="The client field name to search for")],
                    regular_expression: Annotated[str, Field(description="Pattern to match field name against")]) -> Dict[str, Any]:
        try:
            regex = re.compile(regular_expression)
            return {"clients": [entry for entry in self._client_db if field_name in entry and regex.search(entry[field_name])]}
        except Exception as e:
            msg = f"Error searching for clients with key field [{field_name}] and matching expression [{regular_expression}]: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ClientServiceExample")

    config = {}
    config[ClientService.ConfigField.DB_NAME.value] = "client.json"
    config[ClientService.ConfigField.DB_PATH.value] = "python/src/server/client_service"
    config[ClientService.ConfigField.SERVER_NAME.value] = "ClientService"

    try:
        service = ClientService(logger,
                                config)

        print(service.get_all_client_field_names()
              )
        print(service.get_clients(
            ClientService.ClientField.CLIENT_NAME.value, r".*Holdings.*"))
        print(service.get_clients(
            ClientService.ClientField.CLIENT_NAME.value, r"*"))

    except ClientService.ErrorLoadingClientDatabase as e:
        logger.error(f"Failed to load Client database: {str(e)}")

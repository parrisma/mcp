import logging
import time
from tkinter.tix import STATUS
from urllib import response
import uuid
import json
import os
from enum import Enum
from typing import Callable, List, Tuple, Annotated, Dict, Any
from anyio import Path
from flask.config import T
from i_mcp_server import IMCPServer
from pydantic import Field
from langchain.prompts import PromptTemplate
import requests


class MessageService(IMCPServer):

    class JsonMessageKeys(Enum):
        MESSAGE_PORT = "message_port"
        MESSAGE_HOST = "message_host"
        CHANNELS = "channels"
        CHANNEL_ID = "channel_id"
        CHANNEL_DESCRIPTION = "channel_description"
        STATUS = "status"
        ERROR = "error"

    class WebMessageServerParams(Enum):
        CHANNEL_ID_GUID = "channel_id"
        MESSAGE = "message"
        SEND_MESSAGE = "send_message"

    class ErrorLoadingMessageServiceSettings(RuntimeError):
        pass

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = IMCPServer.ConfigFields.DATA_PATH.value
        DB_NAME = "db_name"

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config
        self._server_name: str = f"MessageServer_{str(uuid.uuid4()).upper()}"

        self._db_path: str = json_config.get(
            MessageService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingMessageServiceSettings(
                f"Config path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            MessageService.ConfigField.DB_NAME.value, "message_settings.json")
        if not self._db_name:
            raise self.ErrorLoadingMessageServiceSettings(
                "Config file name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            raise self.ErrorLoadingMessageServiceSettings(
                f"Config file {self._full_db_path} does not exist.")

        self._message_host, self._message_port, self._channels = self.initialize_from_config(
            Path(self._full_db_path))

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("post_message", self._post_message),
                ("get_message_channels", self._get_message_channels)]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return []

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return []

    def _form_message_url(self,
                          channel_id: str,
                          message: str) -> str:
        base_url = f"http://{self._message_host}:{self._message_port}/{self.WebMessageServerParams.SEND_MESSAGE.value}"
        # URL encode the message to handle special characters
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        return f"{base_url}?{self.WebMessageServerParams.CHANNEL_ID_GUID.value}={channel_id}&{self.WebMessageServerParams.MESSAGE.value}={encoded_message}"

    def initialize_from_config(self,
                               config_path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
        try:
            with open(config_path, 'r') as config_file:
                message_config = json.load(config_file)

            # Extract configuration values
            message_host = message_config.get(
                self.JsonMessageKeys.MESSAGE_HOST.value, None)
            if message_host is None:
                raise ValueError(
                    f"message host missing in configuration [{config_path}]")

            message_port = message_config.get(
                self.JsonMessageKeys.MESSAGE_PORT.value, None)
            if message_host is None:
                raise ValueError(
                    f"message port missing in configuration [{config_path}]")

            channels = message_config.get(
                self.JsonMessageKeys.CHANNELS.value, None)
            if channels is None:
                raise ValueError(
                    f"message channels are missing in configuration [{config_path}]")

            if not isinstance(channels, list):
                raise ValueError(
                    f"message channels should be a list in configuration [{config_path}]")

            self._log.info(
                f"Initialized message service with host: {message_host}, port: {message_port}")
            for channel in channels:
                if not isinstance(channel, dict):
                    raise ValueError(
                        f"Each channel should be a dictionary in configuration [{config_path}]")
                k = channel.get(self.JsonMessageKeys.CHANNEL_ID.value, None)
                v = channel.get(
                    self.JsonMessageKeys.CHANNEL_DESCRIPTION.value, None)
                if k is None or v is None:
                    raise ValueError(
                        f"Each channel must have 'channel_id' and 'channel_description' in configuration [{config_path}]")
                if not isinstance(k, str) or not isinstance(v, str):
                    raise ValueError(
                        f"'channel_id' and 'channel_description' must be strings in configuration [{config_path}]")
                self._log.info(f"Channel ID: {k}, Description: {v}")
            return message_host, message_port, channels

        except Exception as e:
            msg = f"Failed to load message configuration: {str(e)}"
            self._log.error(msg=msg)
            raise RuntimeError(msg) from e
    #
    # Tool implementions
    #

    def _invoke_message_url(self, url: str) -> bool:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self._log.info(f"Message sent successfully: {url}")
                return True
            else:
                self._log.error(
                    f"Failed to send message. Status code: {response.status_code}, URL: {url}")
                return False
        except Exception as e:
            self._log.error(
                f"Error invoking message URL: {url}, Error: {str(e)}")
            return False

    def _post_message(self,
                      message: Annotated[str, Field(description="A message to post to the chat channel")],
                      channel_id: Annotated[str, Field(description="The GUID of the channel to post the message to")]) -> Dict[str, Any]:
        self._log.info(f"Posting message: {message} to channel: {channel_id}")
        response = {}
        if self._invoke_message_url(self._form_message_url(channel_id, message)):
            self._log.info(
                f"Message posted successfully to channel {channel_id}")
            response = {
                self.JsonMessageKeys.STATUS.value: "OK",
                self.JsonMessageKeys.CHANNEL_ID.value: channel_id,
            }
        else:
            self._log.error(f"Failed to post message to channel {channel_id}")
            response = {
                self.JsonMessageKeys.STATUS.value: "ERROR",
                self.JsonMessageKeys.CHANNEL_ID.value: channel_id,
            }
        return response

    def _get_message_channels(self) -> List[Dict[str, Any]]:
        self._log.info("Retrieving message channels")
        return self._channels

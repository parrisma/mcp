import argparse
import json
import logging
import random
import threading
import time
import uuid
from enum import Enum
from typing import Any, Dict, List

import requests

from mcp_client_web_server import MCPClientWebServer


# Only works for single subscriber, multiple subscribers will need a more complex solution
# and we are not trying to demo message service with multiple subscribers at this time.

class MessageService:

    class JsonMessageKeys(Enum):
        CHANNEL_ID_GUID = "channel_id"
        MESSAGES = "messages"
        MESSAGE = "message"
        ERROR = "error"
        OK = "ok"
        STATUS = "status"
        ALL = "all"
        TIMESTAMP = "timestamp"

        def __str__(self) -> str:
            return self.value

    def __init__(self,
                 host: str,
                 port: int) -> None:

        self._log: logging.Logger = self._configure_logging()
        self._log.debug(f"MessageService starting")

        self._args: argparse.Namespace = self._parse_args()

        self._host: str = self._args.host
        if not self._host:
            self._host = host

        self._port: int = self._args.port
        if not self._port:
            self._port = port

        self._log.debug(
            f"MessageService initialized with host: {host}, port: {port}")

        # Initialize document storage settings with defaults
        self._document_storage_host: str = "0.0.0.0"
        self._document_storage_port: int = 6000

        self._web_server = MCPClientWebServer(host=self._host, port=self._port)

        self._web_server.add_route(route='/send_message',
                                   methods=['POST'],
                                   handler=self._post_message)
        self._web_server.add_route(route='/get_message',
                                   methods=['GET'],
                                   handler=self._get_messages)

        self._messages: Dict[str, Any] = {}
        self._messages_lock = threading.Lock()

        self._log.info(f"Started Message Web interface in background thread")

    def _configure_logging(self) -> logging.Logger:
        log: logging.Logger = logging.getLogger("MessageWebServer")
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        return log

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Message Service')
        parser.add_argument('--host', default='0.0.0.0',
                            help='Host to bind the server to')
        parser.add_argument('--port', type=int, default=5000,
                            help='Port to bind the server to')
        args: argparse.Namespace = parser.parse_args()
        return args

    def _post_message(self,
                      params: Dict) -> Dict:
        # Check if the required parameters are present
        if 'args' in params:
            params = params['args']
        else:
            return {self.JsonMessageKeys.ERROR.value: "Missing 'args' in parameters."}

        if not isinstance(params, dict):
            return {self.JsonMessageKeys.ERROR.value: "Invalid parameters format. Expected a dictionary."}

        if self.JsonMessageKeys.CHANNEL_ID_GUID.value not in params:
            return {self.JsonMessageKeys.ERROR.value: f"Missing required parameter: {self.JsonMessageKeys.CHANNEL_ID_GUID.value}"}

        if self.JsonMessageKeys.MESSAGE.value not in params:
            return {self.JsonMessageKeys.ERROR.value: f"Missing required parameter: {self.JsonMessageKeys.MESSAGE.value}"}

        channel_id_guid = params[self.JsonMessageKeys.CHANNEL_ID_GUID.value]
        message = params[self.JsonMessageKeys.MESSAGE.value]

        # Validate that channel_id_guid is a valid UUID
        try:
            _ = uuid.UUID(channel_id_guid)
        except ValueError:
            return {self.JsonMessageKeys.ERROR.value: f"Invalid UUID format for {self.JsonMessageKeys.CHANNEL_ID_GUID.value}"}

        # Add the message to our internal storage
        self._add_message(channel_id_guid, message)

        # Additionally, try to post to document storage (don't fail if this fails)
        try:
            self._post_message_to_document_storage(message, channel_id_guid)
        except Exception as e:
            self._log.warning(
                f"Failed to post message to document storage, but continuing: {str(e)}")

        # Return success response
        return {
            self.JsonMessageKeys.STATUS.value: self.JsonMessageKeys.OK.value,
        }

    def _add_message(self,
                     channel_id_guid: str,
                     message: Dict[str, Any]) -> None:
        """Adds a message to the internal message list."""
        with self._messages_lock:
            if channel_id_guid not in self._messages:
                self._messages[channel_id_guid] = [message]
            else:
                self._messages[channel_id_guid].append(message)

    def _get_messages(self,
                      params: Dict) -> Dict[str, Any]:
        # Check if the required parameters are present
        if 'args' in params:
            params = params['args']
        else:
            return {self.JsonMessageKeys.ERROR.value: "Missing 'args' in parameters."}

        if not isinstance(params, dict):
            return {self.JsonMessageKeys.ERROR.value: "Invalid parameters format. Expected a dictionary."}

        if self.JsonMessageKeys.CHANNEL_ID_GUID.value not in params:
            return {self.JsonMessageKeys.ERROR.value: f"Missing required parameter: {self.JsonMessageKeys.CHANNEL_ID_GUID.value}"}

        if self.JsonMessageKeys.ALL.value in params:
            all = True
        else:
            all = False

        channel_id_guid = params[self.JsonMessageKeys.CHANNEL_ID_GUID.value]
        try:
            _ = uuid.UUID(channel_id_guid)
        except ValueError:
            return {self.JsonMessageKeys.ERROR.value: f"Invalid UUID format for {self.JsonMessageKeys.CHANNEL_ID_GUID.value}",
                    self.JsonMessageKeys.CHANNEL_ID_GUID.value: channel_id_guid}

        messages: List[str] = self._wait_for_message_with_channel_id(
            channel_id_as_guid=channel_id_guid)
        # Add timestamps to messages if they don't already have them
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if messages:
            if all:
                return {self.JsonMessageKeys.MESSAGES.value: messages,
                        self.JsonMessageKeys.TIMESTAMP.value: timestamp,
                        self.JsonMessageKeys.CHANNEL_ID_GUID.value: channel_id_guid}
            else:
                return {self.JsonMessageKeys.MESSAGE.value: messages[-1],
                        self.JsonMessageKeys.TIMESTAMP.value: timestamp,
                        self.JsonMessageKeys.CHANNEL_ID_GUID.value: channel_id_guid}
        else:
            return {self.JsonMessageKeys.ERROR.value: [f"Failed to retrieve messages for channel ID: {channel_id_guid}"],
                    self.JsonMessageKeys.TIMESTAMP.value: timestamp,
                    self.JsonMessageKeys.CHANNEL_ID_GUID.value: channel_id_guid}

    def _wait_for_message_with_channel_id(self,
                                          channel_id_as_guid: str,
                                          timeout: int = 60*60) -> List[str]:
        """
        Blocks until a NEW message with the specified channel ID is found in the internal message list.
        Returns the message if found within the timeout, otherwise returns None.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._messages_lock:
                if channel_id_as_guid in self._messages and self._messages[channel_id_as_guid]:
                    messages = self._messages[channel_id_as_guid]
                    # Clear the messages after retrieving them so we only get new messages on subsequent calls
                    self._messages[channel_id_as_guid] = []
                    return messages
            time.sleep(0.1)
        return [f"Timed out, no messages arrived on channel id {channel_id_as_guid}"]

    def _debug_messages(self, params: Dict) -> Dict[str, Any]:
        """Debug endpoint to see current message state"""
        with self._messages_lock:
            return {
                "message_count_by_channel": {k: len(v) for k, v in self._messages.items()},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }

    def _post_message_to_document_storage(self,
                                          message: str,
                                          channel_id: str) -> bool:
        try:
            # Create document combining message, channel_id and timestamp
            timestamp = int(time.time())
            document = {
                "message": message,
                "channel_id": channel_id,
                "timestamp": timestamp
            }
            document_json = json.dumps(document)

            # URL encode the document
            import urllib.parse
            encoded_document = urllib.parse.quote(document_json)

            # 10% chance to include a random desk
            desk_param = ""
            if random.random() < 0.1:  # 10% chance
                desk_number = random.randint(1, 9)
                desk_param = f"&desk=Desk{desk_number:03d}"

            # Form the URL
            url = f"http://{self._document_storage_host}:{self._document_storage_port}/add_document?document={encoded_document}&document_type=message{desk_param}"

            # Make the request
            response = requests.get(url, timeout=5)  # 5 second timeout
            if response.status_code == 200:
                self._log.debug(
                    f"Message document posted successfully to storage: {url}")
                return True
            else:
                self._log.warning(
                    f"Failed to post message document to storage. Status code: {response.status_code}")
                return False

        except Exception as e:
            self._log.warning(
                f"Error posting message document to storage: {str(e)}")
            return False

    def run(self) -> None:
        self._web_server.run()


if __name__ == '__main__':

    message_service = MessageService(host='0.0.0.0',
                                     port=5000)
    message_service.run()

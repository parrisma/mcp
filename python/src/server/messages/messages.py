from email import message
from math import e
from re import A
from tkinter import ALL
from typing import Dict, Protocol, Any, Literal, List
from functools import partial, update_wrapper
import json
from enum import Enum
import argparse
import threading
import time
from typing import Optional
import uuid

from sqlalchemy import TIMESTAMP
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

        self._args = self._parse_args()

        self._host: str = self._args.host
        if not self._host:
            self._host = host

        self._port: int = self._args.port
        if not self._port:
            self._port = port

        self._web_server = MCPClientWebServer(host=self._host, port=self._port)

        self._web_server.add_route(route='/send_message',
                                   methods=['POST'],
                                   handler=self._post_message)
        self._web_server.add_route(route='/get_message',
                                   methods=['GET'],
                                   handler=self._get_messages)

        self._messages: Dict[str, Any] = {}
        self._messages_lock = threading.Lock()

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

        # Return success response
        return {
            self.JsonMessageKeys.STATUS.value: self.JsonMessageKeys.OK.value,
        }

    def _add_message(self,
                     channel_id_guid: str,
                     message: Dict[str, Any]) -> None:
        """Adds a message to the internal message list."""
        with self._messages_lock:
            if channel_id_guid not in message:
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
                                          timeout: int = 10*60) -> List[str]:
        """
        Blocks until a message with the specified channel ID is found in the internal message list.
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

    def run(self) -> None:
        self._web_server.run()


if __name__ == '__main__':

    message_service = MessageService(host='0.0.0.0',
                                     port=5000)
    message_service.run()

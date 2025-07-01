import argparse
import json
import logging
import random
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Type

import requests

from json_message_keys import JsonMessageKeys
from mcp_client_web_server import MCPClientWebServer


# Only works for single subscriber, multiple subscribers will need a more complex solution
# and we are not trying to demo message service with multiple subscribers at this time.

class MessageService:

    class MessageServiceFailure(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

        def __str__(self) -> str:
            return self.message

    class MessageGetFailure(MessageServiceFailure):
        def __init__(self, message):
            super().__init__(f"Failed to get message: {message}")

    class MessagePostFailure(MessageServiceFailure):
        def __init__(self, message):
            super().__init__(f"Failed to post message: {message}")

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

        self._messages: Dict[uuid.UUID, Any] = {}
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
        if JsonMessageKeys.ARGS.value in params:
            params = params['args']
        else:
            return {JsonMessageKeys.ERROR.value: "Missing 'args' in parameters."}

        if not isinstance(params, dict):
            return {JsonMessageKeys.ERROR.value: "Invalid parameters format. Expected a dictionary."}

        if JsonMessageKeys.CHANNEL_ID_GUID.value not in params:
            return {JsonMessageKeys.ERROR.value: f"Missing required parameter: {JsonMessageKeys.CHANNEL_ID_GUID.value}"}

        if JsonMessageKeys.MESSAGE.value not in params:
            return {JsonMessageKeys.ERROR.value: f"Missing required parameter: {JsonMessageKeys.MESSAGE.value}"}

        channel_id_guid = params[JsonMessageKeys.CHANNEL_ID_GUID.value]
        message = params[JsonMessageKeys.MESSAGE.value]

        # Validate that channel_id_guid is a valid UUID
        try:
            channel_id_guid = uuid.UUID(channel_id_guid)
        except ValueError:
            return {JsonMessageKeys.ERROR.value: f"Invalid UUID format for {JsonMessageKeys.CHANNEL_ID_GUID.value}"}

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
            JsonMessageKeys.STATUS.value: JsonMessageKeys.OK.value,
        }

    def _create_channel(self,
                        channel_id_guid: uuid.UUID) -> None:
        with self._messages_lock:
            if channel_id_guid not in self._messages:
                self._messages[channel_id_guid] = []
        self._add_message(channel_id_guid, "Channel created")

    def _add_message(self,
                     channel_id_guid: uuid.UUID,
                     message: Any) -> None:

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # If message is already a dict with proper structure, use it
        if isinstance(message, dict) and (JsonMessageKeys.MESSAGE.value in message):
            structured_message = message
            if JsonMessageKeys.TIMESTAMP.value not in structured_message:
                structured_message[JsonMessageKeys.TIMESTAMP.value] = timestamp
            structured_message[JsonMessageKeys.MESSAGE_UUID.value] = str(
                uuid.uuid4()).upper()
        else:
            try:
                if not isinstance(message, str):
                    message = str(message).strip()
            except Exception as e:
                message = f"Error converting message: {str(e)}"

            structured_message: Dict[str, str] = {
                JsonMessageKeys.MESSAGE.value: str(message),
                JsonMessageKeys.TIMESTAMP.value: timestamp,
                JsonMessageKeys.MESSAGE_UUID.value: str(
                    uuid.uuid4()).upper()
            }

        with self._messages_lock:
            if channel_id_guid not in self._messages:
                self._messages[channel_id_guid] = [structured_message]
            else:
                self._messages[channel_id_guid].append(structured_message)

    def _extract_param(self,
                       params: Dict,
                       key: str,
                       type_cast: Callable,
                       exception_class: Type[Exception],
                       optional: bool = False,
                       default: None | Any = None) -> Any:

        res = params.get(key, None)
        error_msg: str = ""
        if res is None:
            if not optional:
                error_msg = f"Missing required parameter: {key}"
            res = default
        else:
            try:
                res = type_cast(res)
            except Exception as e:
                error_msg = f"Parameter '{key}' could not be extracted as required type: {str(e)}"
                res = None
        if not error_msg:
            return res

        raise exception_class(error_msg)

    def _extract_params_from_payload(self,
                                     params: Dict) -> Dict[str, Any]:
        if JsonMessageKeys.ARGS.value in params:
            params = params[JsonMessageKeys.ARGS.value]
        else:
            raise self.MessageGetFailure(
                f"Unexpected payload, expected to level element key [{JsonMessageKeys.ARGS.value}]")

        if not isinstance(params, dict):
            raise self.MessageGetFailure(
                f"Invalid parameters format. Expected a dictionary, got {type(params).__name__}")

        if JsonMessageKeys.CHANNEL_ID_GUID.value not in params:
            raise self.MessageGetFailure(
                f"Missing required parameter: {JsonMessageKeys.CHANNEL_ID_GUID.value}")
        return params

    def _get_messages(self,
                      params: Dict) -> Dict[str, Any]:

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        try:
            params = self._extract_params_from_payload(params)

            message_uuid: uuid.UUID = self._extract_param(
                params,
                JsonMessageKeys.MESSAGE_UUID.value,
                uuid.UUID,
                self.MessageGetFailure,
                True,)

            all: bool = self._extract_param(
                params,
                JsonMessageKeys.ALL.value,
                lambda x: str(x).lower() in ('true', 't', 'yes', 'y', '1'),
                self.MessageGetFailure,
                True,
                False)

            channel_id_guid: uuid.UUID = self._extract_param(
                params,
                JsonMessageKeys.CHANNEL_ID_GUID.value,
                uuid.UUID,
                self.MessageGetFailure)

            messages: List = self._wait_for_message_with_channel_id(channel_id_as_guid=channel_id_guid,
                                                                    message_uuid=message_uuid,
                                                                    all=all)

            return {JsonMessageKeys.MESSAGES.value: messages,
                    JsonMessageKeys.TIMESTAMP.value: timestamp}
        except Exception as e:
            return {JsonMessageKeys.MESSAGES.value: [{JsonMessageKeys.ERROR.value: [f"Failed to retrieve messages, payload [{json.dumps(params)}] with error: {str(e)}"],
                                                      JsonMessageKeys.CHANNEL_ID_GUID.value: "Unkown_or_Missing", }],
                    JsonMessageKeys.TIMESTAMP.value: timestamp}

    def _get_message_after_uuid(self,
                                message_uuid: uuid.UUID,
                                channel_messages: List[Dict[str, Any]],
                                message_cap: int) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        included_message: bool = False
        for message in channel_messages:
            if included_message:
                messages.append(message)
            else:
                if str(message.get(JsonMessageKeys.MESSAGE_UUID.value)).upper() == str(message_uuid).upper():
                    included_message = True

        if len(messages) >= message_cap:
            messages = messages[-message_cap:]

        return messages

    def _wait_for_message_with_channel_id(self,
                                          channel_id_as_guid: uuid.UUID,
                                          message_uuid: uuid.UUID | None = None,
                                          all: bool = False,
                                          timeout: int = 60*60,
                                          message_cap: int = 100) -> List[Dict[str, Any]]:
        """
        Blocks until a NEW message with the specified channel ID is found in the internal message list.
        Returns the message if found within the timeout, otherwise returns None.
        """
        if channel_id_as_guid not in self._messages:
            self._create_channel(channel_id_as_guid)
            self._log.info(
                f"Created new message channel with ID {channel_id_as_guid}")

        if all or message_uuid is None:
            cap: int = min(
                len(self._messages[channel_id_as_guid]), message_cap)
            return self._messages[channel_id_as_guid][-cap:]

        # yes, but this is just a demo ..
        message_uuid_list: List[str] = [
            x[JsonMessageKeys.MESSAGE_UUID.value] for x in self._messages[channel_id_as_guid]]
        if str(message_uuid).upper() not in [uuid_str.upper() for uuid_str in message_uuid_list]:
            raise self.MessageServiceFailure(
                f"Message UUID {message_uuid} not found in channel ID {channel_id_as_guid}.")

        if str(message_uuid).upper() == message_uuid_list[-1].upper():
            start_time = time.time()
            while time.time() - start_time < timeout:
                with self._messages_lock:
                    channel_messages = self._messages[channel_id_as_guid]
                    messages = self._get_message_after_uuid(message_uuid=message_uuid,
                                                            channel_messages=channel_messages,
                                                            message_cap=message_cap)
                    # If we found new messages, return them
                    if messages:
                        return messages
                time.sleep(0.2)
        else:
            return self._get_message_after_uuid(message_uuid=message_uuid,
                                                channel_messages=self._messages[channel_id_as_guid],
                                                message_cap=message_cap)
        return [{
            JsonMessageKeys.MESSAGE.value: f"Timed out, no messages arrived on channel id {channel_id_as_guid}",
            JsonMessageKeys.TIMESTAMP.value: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            JsonMessageKeys.MESSAGE_UUID.value: str(uuid.uuid4()).upper()
        }]

    def _post_message_to_document_storage(self,
                                          message: str,
                                          channel_id: uuid.UUID) -> bool:
        try:
            # Create document combining message, channel_id and timestamp
            timestamp = int(time.time())
            channel_id_as_str = str(channel_id).upper()

            document = {
                "message": message,
                "channel_id": str(channel_id_as_str).upper(),
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

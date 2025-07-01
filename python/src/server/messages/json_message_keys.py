from enum import Enum


class JsonMessageKeys(Enum):
    """Enum containing all JSON message keys used in the message service."""
    CHANNEL_ID_GUID = "channel_id"
    MESSAGES = "messages"
    MESSAGE = "message"
    ERROR = "error"
    OK = "ok"
    STATUS = "status"
    ALL = "all"
    TIMESTAMP = "timestamp"
    MESSAGE_UUID = "message_uuid"
    ARGS = "args"


class JsonMessageKeysProvider:
    """Class that provides access to the JsonMessageKeys enum."""
    
    @staticmethod
    def get_keys() -> type[JsonMessageKeys]:
        """Return the current JsonMessageKeys enum class."""
        return JsonMessageKeys
    
    @classmethod
    def get_instance(cls) -> 'JsonMessageKeysProvider':
        """Return an instance of the JsonMessageKeysProvider."""
        return cls()
    
    def keys(self) -> type[JsonMessageKeys]:
        """Instance method to get the JsonMessageKeys enum."""
        return JsonMessageKeys
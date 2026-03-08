from enum import Enum, auto


class Event(Enum):
    START = auto()
    DEVICE_FOUND = auto()
    CONNECT_OK = auto()
    CONNECT_FAIL = auto()
    SERVICES_OK = auto()
    SUBSCRIBE_OK = auto()
    DISCONNECTED = auto()
    TIMEOUT = auto()

from enum import Enum, auto


class Event(Enum):

    DEVICE_SELECTED = auto()

    CONNECT_OK = auto()

    CONNECT_FAIL = auto()

    SERVICES_OK = auto()

    SUBSCRIBE_OK = auto()

    DISCONNECTED = auto()
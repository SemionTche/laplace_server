# libraries
import logging

# project
from server_lhc.protocol import (
    AVAILABLE_DEVICES, LOGGER_NAME, PROTOCOL_VERSION
)

log = logging.getLogger(LOGGER_NAME)


# checking formats
def validate_device(device: str) -> str | None:
    """Check if device is among AVAILABLE_DEVICES."""
    if device not in AVAILABLE_DEVICES:
        msg = (f"Invalid device: '{device}'. "
               f"Choose among {AVAILABLE_DEVICES}.")
        log.warning(msg)
        return msg
    return None

def validate_freedom(freedom: int) -> str | None:
    """Check if freedom is an int."""
    if not isinstance(freedom, int):
        msg = f"'freedom' must be int, not {type(freedom).__name__}."
        log.warning(msg)
        return msg
    if not freedom >=0:
        msg = f"'freedom' must be positive (>=0), not {freedom}."
        log.warning(msg)
        return msg
    return None


def validate_address(address: str) -> str | None:
    """Check address format."""
    if not isinstance(address, str):
        msg = f"'address' must be str, not {type(address).__name__}."
        log.warning(msg)
        return msg
    if not address.startswith("tcp://"):
        msg = f"Address must start with 'tcp://', got '{address}'."
        log.warning(msg)
        return msg
    return None


def validate_message(message: dict) -> str | None:
    """Check message structure and version."""
    if not isinstance(message, dict):
        msg = f"Message must be dict, got {type(message).__name__}."
        log.warning(msg)
        return msg

    if message.get("version") != PROTOCOL_VERSION:
        msg = f"Protocol version mismatch: expected {PROTOCOL_VERSION}, got {message.get('version')}."
        log.warning(msg)
        return msg

    if not message.get("cmd"):
        msg = "'message' must contain 'cmd' field."
        log.warning(msg)
        return msg

    if not message.get("from"):
        msg = "'message' must contain 'from' field."
        log.warning(msg)
        return msg
    
    if "payload" not in message:
        msg = "'message' must contain 'payload' field."
        log.warning(msg)
        return msg

    return None

def validate_payload(message: dict, expected_keys: list[str]) -> str | None:
    """Check payload contains expected keys."""
    payload = message.get("payload")
    if not isinstance(payload, dict):
        msg = "'payload' must be a dict."
        log.warning(msg)
        return msg

    missing = [k for k in expected_keys if k not in payload]
    if missing:
        msg = f"Payload missing keys: {missing}."
        log.warning(msg)
        return msg

    return None
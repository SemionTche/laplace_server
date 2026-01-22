'''
Validation utilities for LAPLACE-LHC server inputs and messages.

This module provides lightweight validation functions used to verify
server configuration parameters and incoming protocol messages.
Each function returns a human-readable error message or None if the
validation succeeds.
'''

# libraries
import logging

# project
from server_lhc.protocol import (
    AVAILABLE_DEVICES, LOGGER_NAME, PROTOCOL_VERSION
)

log = logging.getLogger(LOGGER_NAME)


def validate_address(address: str) -> None:
    '''Check address format.'''
    if not isinstance(address, str):
        msg = f"'address' must be str, not {type(address).__name__}."
        log.error(msg)
        raise TypeError(msg)

    if not address.startswith("tcp://"):
        msg = f"Address must start with 'tcp://', got '{address}'."
        log.error(msg)
        raise ValueError(msg)


def validate_freedom(freedom: int) -> None:
    '''Check if freedom is a positive int.'''
    if not isinstance(freedom, int):
        msg = f"'freedom' must be int, not {type(freedom).__name__}."
        log.error(msg)
        raise TypeError(msg)
    if freedom < 0:
        msg = f"'freedom' must be positive (>=0), not {freedom}."
        log.error(msg)
        raise ValueError(msg)


def validate_device(device: str) -> None:
    '''Check if device is among AVAILABLE_DEVICES.'''
    if device not in AVAILABLE_DEVICES:
        msg = (f"Invalid device: '{device}'. "
               f"Choose among {AVAILABLE_DEVICES}.")
        log.error(msg)
        raise ValueError(msg)


def validate_message(message: dict) -> str | None:
    '''Check message structure and version.'''
    if not isinstance(message, dict):
        return f"Message must be dict, got {type(message).__name__}."

    if not message.get("version"):
        return "'message' must contain 'version' field."
    
    if not message.get("cmd"):
        return "'message' must contain 'cmd' field."

    if not message.get("from"):
        return "'message' must contain 'from' field."

    if message.get("version") != PROTOCOL_VERSION:
        return f"Protocol version mismatch: expected {PROTOCOL_VERSION}, got {message.get('version')}."
    
    if "payload" not in message:
        return "'message' must contain a 'payload' dictionary, even if empty."

    return None


def validate_payload(message: dict, expected_keys: list[str]) -> str | None:
    '''Check payload contains expected keys.'''
    payload = message.get("payload")
    if not isinstance(payload, dict):
        msg = "'payload' must be a dict."
        log.error(msg)
        return msg

    missing = [k for k in expected_keys if k not in payload]
    if missing:
        msg = f"Payload missing keys: {missing}."
        log.error(msg)
        return msg

    return None
# libraries
import logging

# project
from server_lhc.protocol import AVAILABLE_DEVICES, LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)


# checking formats
def format_device(device: str) -> None:
    '''Check if the device argument is among the 'AVAILABLE_DEVICES'.'''
    if device not in AVAILABLE_DEVICES:
        log.error(f"Error: 'device' argument provided: '{device}' is invalid.\n" + 
                    f"The device must be choosen among the available devices: {AVAILABLE_DEVICES}.")
        raise ValueError(f"Error: 'device' argument provided: '{device}' is invalid.\n" + 
                    f"The device must be choosen among the available devices: {AVAILABLE_DEVICES}.")


def format_freedom(freedom: int) -> None:
    '''Check if the freedom argument is an integer.'''
    if not isinstance(freedom, int):
        log.error(f"Error: 'freedom' argument must be an '{int.__name__}' not: '{type(freedom).__name__}'.")
        raise TypeError(f"Error: 'freedom' argument must be an '{int.__name__}' not: '{type(freedom).__name__}'.")


def format_address(address: str) -> None:
    '''Check if the address argument is a string and use the right protocol.'''
    if not isinstance(address, str):
        log.error(f"Error: 'address' argument must be a '{str.__name__}' not: '{type(address).__name__}'.")
        raise TypeError(f"Error: 'address' argument must be a '{str.__name__}' not: '{type(address).__name__}'.")

    if not address.startswith("tcp://"):
        log.error(f"Error: server address must use 'tcp' protocol, meaning starting by 'tcp://', not: '{address}'.")
        raise ValueError(f"Error: server address must use 'tcp' protocol, meaning starting by 'tcp://', not: '{address}'.")


def format_message(message: dict) -> None:
    '''Check if the message argument is a dictionary and its contant.'''
    if not isinstance(message, dict):
        log.error(f"Error: 'message' argument must be an '{dict.__name__}' not: '{type(message).__name__}'.")
        raise TypeError(f"Error: 'message' argument must be an '{dict.__name__}' not: '{type(message).__name__}'.")
    
    if not message.get("cmd"):
        log.error(f"Error: 'message' dictionary must contain a 'cmd' field.")
        raise ValueError(f"Error: 'message' dictionary must contain a 'cmd' field.")

    if not message.get("from"):
        log.error(f"Error: 'message' dictionary must contain a 'from' field.")
        raise ValueError(f"Error: 'message' dictionary must contain a 'from' field.")

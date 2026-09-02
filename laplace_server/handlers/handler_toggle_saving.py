# libraries
import logging

# project
from ..protocol import (
    CMD_TOGGLE_SAVING, LOGGER_NAME,
    make_toggle_saving_status_reply, make_error, 
)
from ..validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_toggle_saving_status(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_TOGGLE_SAVING}' from '{target}'.")
    err = validate_payload(message, expected_keys=["saving status"])
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_TOGGLE_SAVING, 
                error_msg=err
            )
        )
        return
    
    saving_status = message["payload"]["saving status"]
    server.emit("on_saving_status_toggled", saving_status)
    server.socket.send_json(
        make_toggle_saving_status_reply(
            sender=server.name, 
            target=target
        )
    )
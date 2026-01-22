# libraries
import logging

# project
from server_lhc.protocol import (
    CMD_SET, LOGGER_NAME,
    make_set_reply, make_error, 
)
from server_lhc.validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_set(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_SET}' from '{target}'.")

    err = validate_payload(message, expected_keys=["positions"])
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_SET, 
                error_msg=err
            )
        )
        return
    
    positions = message["payload"]["positions"]
    server.emit("on_position_changed", positions)
    
    server.socket.send_json(
        make_set_reply(
            sender=server.name, 
            target=target
        )
    )
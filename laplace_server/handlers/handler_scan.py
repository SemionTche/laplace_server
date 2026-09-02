# libraries
import logging

# project
from ..protocol import (
    CMD_SCAN, LOGGER_NAME,
    make_scan_reply, make_error, 
)
from ..validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_scan(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_SCAN}' from '{target}'.")
    err = validate_payload(message, expected_keys=["data"])
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_SCAN, 
                error_msg=err
            )
        )
        return
    
    data = message["payload"]["data"]
    server.emit("on_opt", data)
    
    server.socket.send_json(
        make_scan_reply(
            sender=server.name, 
            target=target
        )
    )
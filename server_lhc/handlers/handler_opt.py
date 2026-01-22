# libraries
import logging

# project
from server_lhc.protocol import (
    CMD_OPT, LOGGER_NAME,
    make_opt_reply, make_error, 
)
from server_lhc.validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_opt(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_OPT}' from '{target}'.")
    err = validate_payload(message, expected_keys=["data"])
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_OPT, 
                error_msg=err
            )
        )
        return
    
    data = message["payload"]["data"]
    server.emit("on_opt", data)
    
    server.socket.send_json(
        make_opt_reply(
            sender=server.name, 
            target=target
        )
    )
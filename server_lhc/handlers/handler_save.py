# libraries
import logging

# project
from server_lhc.protocol import (
    CMD_SAVE, LOGGER_NAME,
    make_save_reply, make_error, 
)
from server_lhc.validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_save(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_SAVE}' from '{target}'.")
    err = validate_payload(message, expected_keys=["path"])
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_SAVE, 
                error_msg=err
            )
        )
        return
    
    path = message["payload"]["path"]
    server.emit("on_saving_path_changed", path)
    server.socket.send_json(
        make_save_reply(
            sender=server.name, 
            target=target
        )
    )
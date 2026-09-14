# libraries
import logging

# project
from ..protocol import (
    CMD_SET_DIAG, LOGGER_NAME,
    make_scan_reply, make_error, 
)
from ..validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_set_diagnostics(server, message: dict, target: str) -> None:
    log.debug(f"[Server {server.name}] Received: '{CMD_SET_DIAG}' from '{target}'")
    err = validate_payload(message, expected_keys=["diagnostics"])
    if err:
        log.info(f'Invalid payload')
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_SET_DIAG, 
                error_msg=err
            )
        )
        return
    
    diagnostics = message["payload"]["diagnostics"]
    server.emit("on_set_diagnostics", diagnostics)
    
    server.socket.send_json(
        make_scan_reply(
            sender=server.name, 
            target=target
        )
    )
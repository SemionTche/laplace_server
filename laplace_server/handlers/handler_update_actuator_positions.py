# libraries
import logging

# project
from ..protocol import (
    CMD_UPDATE_ACTUATORS_POS, LOGGER_NAME,
    make_scan_reply, make_error, 
)
# from ..validations import validate_payload

log = logging.getLogger(LOGGER_NAME)


def handle_update_actuator_positions(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_UPDATE_ACTUATORS_POS}' from '{target}'")
    #err = validate_payload(message, expected_keys=["actuators"])
    err = False
    if err:
        server.socket.send_json(
            make_error(
                sender=server.name, 
                target=target, 
                cmd=CMD_UPDATE_ACTUATORS_POS, 
                error_msg=err
            )
        )
        return
    
    # actuators = message["payload"]["actuators"]
    # server.emit("on_set_actuators", actuators)
    server.emit("on_set_actuators", message)
    
    server.socket.send_json(
        make_scan_reply(
            sender=server.name, 
            target=target
        )
    )
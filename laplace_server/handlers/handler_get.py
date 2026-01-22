# libraries
import logging

# project
from protocol import make_get_reply, CMD_GET, LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)


def handle_get(server, message: dict, target: str) -> None:
    log.debug(f"[Server {server.name}] Received: '{CMD_GET}' from '{target}'.")
    server.socket.send_json(
        make_get_reply(
            sender=server.name, 
            target=target, 
            data=server.data
        )
    )
    server.emit("on_get")
    if server.empty_data_after_get:
        server.empty_data()
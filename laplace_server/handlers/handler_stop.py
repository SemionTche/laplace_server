# libraries
import logging

# project
from protocol import make_stop_reply, CMD_STOP, LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)


def handle_stop(server, message: dict, target: str) -> None:
    log.info(f"[Server {server.name}] Received: '{CMD_STOP}' from '{target}'.")
    server._running.clear()     # stop the thread
    server.socket.send_json(
        make_stop_reply(
            sender=server.name, 
            target=target
        )
    )
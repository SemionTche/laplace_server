# libraries
import logging

# project
from server_lhc.protocol import make_info_reply, CMD_INFO, LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)


def handle_info(server, message, target):
    log.info(f"[Server {server.name}] Received: '{CMD_INFO}' from '{target}'.")
    response = make_info_reply(
        sender=server.name,
        target=target,
        device=server.device,
        freedom=server.freedom,
        name=server.name,
        capabilities=server.capabilities
    )
    server.socket.send_json(response)

PROTOCOL_VERSION = "1.0"

CMD_INFO = "INFO"
CMD_PING = "PING"
CMD_GET  = "GET"
CMD_SAVE = "SAVE"
CMD_STOP = "STOP"
CMD_ERROR = "ERROR"

def make_message( *,
                 cmd: str,
                 sender: str,
                 target: str,
                 payload: dict | None = None,
                 error_msg: str | None = None,
                 msg: str | None = None,
                 version: str = PROTOCOL_VERSION, ) -> dict:
    message = {
        "from": sender,
        "to": target,
        "cmd": cmd,
        "payload": payload or {},
        "version": version,
        "error_msg": error_msg,
        "msg": msg,
    }
    return message

def make_ping(sender: str, target: str):
    return make_message(
        cmd=CMD_PING,
        sender=sender,
        target=target,
        payload={"PING": None},
        msg="Alive?"
    )

def make_pong(sender: str, target: str):
    return make_message(
        cmd=CMD_PING,
        sender=sender,
        target=target,
        payload={"PING": "PONG"},
        msg="Still alive."
    )

def make_info_request(sender: str, target: str):
    return make_message(
        cmd=CMD_INFO,
        sender=sender,
        target=target,
        msg="Informations required."
    )

def make_info_reply(sender: str, target: str, *, device, freedom, name, capabilities):
    return make_message(
        cmd=CMD_INFO,
        sender=sender,
        target=target,
        payload={
            "device": device,
            "freedom": freedom,
            "name": name,
            "capabilities": capabilities,
        },
        msg="Informations transmitted."
    )

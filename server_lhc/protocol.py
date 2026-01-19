# libraries
import logging
log = logging.getLogger("laplace.server.protocol")

# protocol version
PROTOCOL_VERSION = "1.5"

# commands
CMD_INFO = "INFO"
CMD_PING = "PING"
CMD_GET  = "GET"
CMD_SAVE = "SAVE"
CMD_SET = "SET"
CMD_STOP = "STOP"
CMD_ERROR = "ERROR"
CMD_OPT = "INFO_OPT"

# devices
DEVICE_MOTOR = "MOTOR"
DEVICE_CAMERA = "CAMERA"
DEVICE_GAS = "GAS"
DEVICE_OPT = "OPT"

AVAILABLE_DEVICES = [DEVICE_MOTOR, DEVICE_CAMERA, DEVICE_GAS, DEVICE_OPT]


def make_message(*,
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

def make_get_request(sender: str, target: str):
    return make_message(
        cmd=CMD_GET,
        sender=sender,
        target=target,
        msg="Get values."
    )

def make_get_reply(sender: str, target: str, *, data: dict):
    return make_message(
        cmd=CMD_GET,
        sender=sender,
        target=target,
        payload={"data": data},
        msg="Data sent."
    )

def make_save_request(sender: str, target: str, *, path: str):
    return make_message(
        cmd=CMD_SAVE,
        sender=sender,
        target=target,
        payload={"path": path},
        msg="Save path request."
    )

def make_save_reply(sender: str, target: str):
    return make_message(
        cmd=CMD_SAVE,
        sender=sender,
        target=target,
        msg="Saving path changed."
    )

def make_error(sender: str, target: str, *, cmd: str, error_msg: str):
    return make_message(
        cmd=cmd,
        sender=sender,
        target=target,
        error_msg=error_msg,
        msg="Error encountered."
    )

def make_stop(sender: str, target: str):
    return make_message(
        cmd=CMD_STOP,
        sender=sender,
        target=target,
        msg="Shutdown request."
    )

def make_stop_reply(sender: str, target: str):
    return make_message(
        cmd=CMD_STOP,
        sender=sender,
        target=target,
        msg="Server stopping."
    )

def make_set_request(sender: str, target: str, *, positions: list):
    return make_message(
        cmd=CMD_SET,
        sender=sender,
        target=target,
        payload={
            "positions": positions,
        },
        msg="Set request."
    )

def make_set_reply(sender: str, target: str):
    return make_message(
        cmd=CMD_SET,
        sender=sender,
        target=target,
        msg="Positions updated."
    )

def make_opt_update(sender: str, target: str, *, data: dict):
    return make_message(
        cmd=CMD_OPT,
        sender=sender,
        target=target,
        payload={"data": data},
        msg="Opt informations."
    )

def make_opt_reply(sender: str, target: str):
    return make_message(
        cmd=CMD_OPT,
        sender=sender,
        target=target,
        msg="Updating opt."
    )
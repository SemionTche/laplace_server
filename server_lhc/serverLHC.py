# libraries
from typing import Callable
import zmq
import socket as sock  # rename to avoid conflict with zmq socket
import threading
import time
import json
import logging


# project
from server_lhc.protocol import (
    # available commands
    CMD_INFO, CMD_PING, CMD_GET, CMD_SET, CMD_SAVE, CMD_STOP, CMD_OPT, 
    
    # available messages
    make_info_reply, make_pong, make_get_reply,
    make_save_reply, make_set_reply, make_opt_reply, 
    make_error, make_stop_reply, make_stop,
    
    # available devices
    AVAILABLE_DEVICES,

    # the name of the logger instance
    LOGGER_NAME
)
from server_lhc.check_format import(
    # format checkers
    format_device, format_freedom, format_address, format_message
)

log = logging.getLogger(LOGGER_NAME)


class ServerLHC(threading.Thread):
    '''
    Server made for the LAPLACE-LHC project.

    To start the server, create an instance of the server and use the 'start' 
    method to assing its own thread:
        serv = ServerLHC(name, ...)
        serv.start()

    To update the dictionary stored in the server, use 'set_data' method:
        serv.set_data(new_data: dict)

    To close the server, use the 'stop' method:
        serv.stop()
    
    Some methods might be implemented to be used in the appropriate situation,
    for example: using 'set_on_get' define the callable use when a 'CMD_GET'
    is received. The ServerController class provide useful functions making
    PyQt6 signal:
        serv = ServerLHC(name, ...)
        server_controller = ServerController()
        serv.set_on_get(server_controller.on_get)
    (This was made to avoid making the server a QObject)
    
    Warning:
        Since the server has its own thread, stopping the main process will not
        necessarily stop the server. The user must close the server himself.
    '''

    def __init__(
            self,
            name: str,
            address: str,
            freedom: int,
            device: str,
            data: dict,
            empty_data_after_get: bool = False,
            time_poll_ms: int = 100,
            time_sleep_ms: float = 10
        ):
        f'''
            Args:
                name: (str)
                    the server name.
                
                address: (str)
                    the server address. 
                    The format must be "tcp://'IP to listen':'port'", with:
                        'tcp://' beeing the imposed protocol, 
                        'IP to listen' the IP address the server should listen 
                        or '*' (equivalent to 0.0.0.0) to listen every IP.
                
                freedom: (int)
                    the degree of freedom of the associated device.
                    (Number of motors the server should drive, 0 for camera)
                
                device: (str)
                    The device associated to the server.
                    Among: {AVAILABLE_DEVICES}.

                data: (dict)
                    the dictionary stored by the server. Transmited by 'CMD_GET'. 
                    Must be set using 'set_data' method.
                
                empty_data_after_get: (bool)
                    whether to empty the data dictionary stored in the server
                    after transmission through 'CMD_GET'. (default {False})
                
                time_poll_ms: (int)
                    The timeout (in milliseconds) to wait for an event. 
                    If unspecified (or specified None), will wait forever for an event.
                
                time_sleep_ms: (float)
                    Delay execution (between 2 server polling) for a given number of milliseconds. 
                    The argument may be a floating point number for subsecond precision.
        '''
        
        super().__init__() # heritage from Thread
        
        # checking format
        format_address(address)
        format_freedom(freedom)
        format_device(device)

        # set attributes
        self.name = name
        self._address = address
        self.freedom = freedom
        self.device = device
        self.set_data(data)
        self.empty_data_after_get = empty_data_after_get
        self.time_poll_ms = time_poll_ms
        self.time_sleep_ms = time_sleep_ms

        # server context
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self._address)

        self._server_ip = self.get_ip() # get the server IP

        self.capabilities = [
            CMD_INFO, CMD_PING, CMD_GET, CMD_SET, CMD_SAVE, CMD_STOP, CMD_OPT
        ]
        self._handlers = {
            CMD_INFO: self._handle_info,
            CMD_PING: self._handle_ping,
            CMD_GET:  self._handle_get,
            CMD_SAVE: self._handle_save,
            CMD_SET:  self._handle_set,
            CMD_OPT:  self._handle_opt,
            CMD_STOP: self._handle_stop,
        }

        # creating the server Thread
        self._running = threading.Event()
        self._running.set()

        # callable to emit a signal when corresponding messages are 
        # received. Need to be set by the user when deploying the server
        self.on_saving_path_changed = None
        self.on_position_changed = None
        self.on_get = None
        self.on_opt = None


    def get_ip(self) -> str:
        '''Helper returning the IPV4 address of the running process.'''
        s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))  # No traffic is actually sent
            log.debug(f"[Server {self.name}] IPV4 address of the running process: {s.getsockname()[0]}")
            return s.getsockname()[0]
        finally:
            s.close()
    
    
    def set_data(self, new_data: dict) -> None:
        '''Set a new dictionary.'''
        self._data = new_data
        log.debug(f"[Server {self.name}] Server new dictionary setted.")
        
        d = json.dumps(self.data, indent=4, sort_keys=True, default=str) # making a json
        log.debug(f"[Server {self.name}] Current dictionary:\n" + d )

    
    def empty_data(self) -> None:
        '''Reset the server dictionary.'''
        self.set_data(new_data={})
        log.debug("Server dictionary emptied.")


    @property
    def data(self) -> dict:
        '''Helper to avoid 'data' direct modification.
            To modify 'data', use 'set_data'.'''
        return self._data
    
    @property
    def address(self) -> str:
        '''Helper to avoid 'address' direct modification. 
           Format 'protocol'://'IP to listen':'port'.'''
        return self._address
    
    @property
    def server_ip(self) -> str:
        '''Helper to avoid 'server_ip' direct modification.'''
        return self._server_ip
    
    @property
    def server_port(self):
        '''Helper to get the server port.'''
        _, rest = self.address.split("://")
        _, port = rest.split(":")
        return port
    
    @property
    def running(self):
        '''Helper to avoid 'running' direct modifications.'''
        return self._running

    @property
    def address_for_client(self):
        '''Helper that return the 'address' the client should use.
           'protocol'://'server IP':'port'.'''
        protocol, rest = self.address.split("://")
        _, port = rest.split(":")

        address_for_client = f"{protocol}://{self.server_ip}:{port}"

        return address_for_client


    def run(self) -> None:
        '''
        Function used while the server is 'running'.
        The server is waiting to receive messages from client.
        '''
        log.info(f"[Server {self.name}] Running on: {self.address}")
        log.info(f"[Server {self.name}] To connect with, use: {self.address_for_client}")

        while self._running.is_set():

            try:
                
                if self.socket.poll(self.time_poll_ms):  # poll for 100 ms
                    message = self.socket.recv_json()

                    format_message(message)       # message checking

                    cmd = message.get("cmd")      # get the 'CMD'
                    target = message.get("from")  # get the sender

                    handler = self._handlers.get(cmd)

                    if handler:
                        handler(message, target)
                    else:
                        self.socket.send_json(
                            make_error(
                                sender=self.name,
                                target=target,
                                cmd=cmd,
                                error_msg="Unknown command"
                            )
                        )

                else:
                    time.sleep(self.time_sleep_ms * 1e-3)  # wait time_sleep ms (convert to second for sleep function)

            except zmq.error.ContextTerminated:
                break
        
        # closing
        log.debug(f"[Server {self.name}] Closing socket...")
        self.socket.close(0) # close the server
        self.context.term()  # close the context
        log.info(f"[Server {self.name}] Stopped.")


    ### handlers
    def _handle_stop(self, message: dict, target: str) -> None:
        log.info(f"[Server {self.name}] Received: '{CMD_STOP}' from '{target}'.")
        self.socket.send_json(
            make_stop_reply(sender=self.name, target=target)
        )
        self._running.clear()

    def _handle_info(self, message: dict, target: str) -> None:
        log.info(f"[Server {self.name}] Received: '{CMD_INFO}' from '{target}'.")
        response = make_info_reply(
            sender=self.name,
            target=target,
            device=self.device,
            freedom=self.freedom,
            name=self.name,
            capabilities=self.capabilities
        )
        self.socket.send_json(response)
    
    def _handle_ping(self, message: dict, target: str) -> None:
        log.debug(f"[Server {self.name}] Received: '{CMD_PING}' from '{target}'.")
        self.socket.send_json(
            make_pong(self.name, target)
        )
    
    def _handle_get(self, message: dict, target: str) -> None:
        log.debug(f"[Server {self.name}] Received: '{CMD_GET}' from '{target}'.")
        self.socket.send_json(
            make_get_reply(sender=self.name, target=target, data=self.data)
        )
        self.emit_get()
        if self.empty_data_after_get:
            self.empty_data()
    
    def _handle_save(self, message: dict, target: str) -> None:
        log.info(f"[Server {self.name}] Received: '{CMD_SAVE}' from '{target}'.")
        path = message.get("payload", {}).get("path")

        if not path:
            self.socket.send_json(
                make_error(
                    sender=self.name,
                    target=target,
                    cmd=CMD_SAVE,
                    error_msg="Missing path"
                )
            )
            return

        self.emit_save(path)
        self.socket.send_json(
            make_save_reply(sender=self.name, target=target)
        )

    def _handle_set(self, message: dict, target: str) -> None:
        log.info(f"[Server {self.name}] Received: '{CMD_SET}' from '{target}'.")
        positions = message.get("payload", {}).get("positions")

        if not positions:
            self.socket.send_json(
                make_error(
                    sender=self.name,
                    target=target,
                    cmd=CMD_SET,
                    error_msg="Missing positions"
                )
            )
            return

        self.emit_positions(positions)
        self.socket.send_json(
            make_set_reply(sender=self.name, target=target)
        )
    
    def _handle_opt(self, message: dict, target: str) -> None:
        log.info(f"[Server {self.name}] Received: '{CMD_OPT}' from '{target}'.")
        data = message.get("payload", {}).get("data")

        if not data:
            self.socket.send_json(
                make_error(
                    sender=self.name,
                    target=target,
                    cmd=CMD_OPT,
                    error_msg="Missing data"
                )
            )
            return

        self.emit_opt(data)
        self.socket.send_json(
            make_opt_reply(sender=self.name, target=target)
        )


    ### emit
    def emit_save(self, path):
        if self.on_saving_path_changed:
            log.debug("'on_saving_path_changed' function used.")
            try:
                self.on_saving_path_changed(path)
            except Exception:
                log.exception("Error in 'on_saving_path_changed' callback.")
    
    def emit_positions(self, positions):
        if self.on_position_changed:
            log.debug("'on_position_changed' function used.")
            try:
                self.on_position_changed(positions)
            except Exception:
                log.exception("Error in 'on_position_changed' callback.")
    
    def emit_get(self):
        if self.on_get:
            log.debug("'on_get' function used.")
            try:
                self.on_get()
            except Exception:
                log.exception("Error in 'on_get' callback.")
    
    def emit_opt(self, data):
        if self.on_opt:
            log.debug("'on_opt' function used.")
            try:
                self.on_opt(data)
            except Exception:
                log.exception("Error in 'on_opt' callback.")


    ### setters
    def set_on_saving_path_changed(self, func: Callable[[str], None]) -> None:
        '''Set the function to use when a path is received inside a 'CMD_SAVE'.'''
        self.on_saving_path_changed = func
        log.debug("'on_saving_path_changed' function set.")
    
    def set_on_position_changed(self, func: Callable[[list], None]) -> None:
        '''Set the function to use when a position is received inside a 'CMD_SET'.'''
        self.on_position_changed = func
        log.debug("'on_position_changed' function set.")
    
    def set_on_get(self, func: Callable[[], None]) -> None:
        '''Set the function to use when a 'CMD_GET' is received.'''
        self.on_get = func
        log.debug("'on_get' function set.")
    
    def set_on_opt(self, func: Callable[[dict], None]) -> None:
        '''Set the function to use when a 'CMD_OPT' is received.'''
        self.on_opt = func
        log.debug("'on_opt' function set.")


    ### stop
    def stop(self) -> None:
        '''
        Proper way to stop the thread where the server is running.
        The function send a 'CMD_STOP' message to the server,
        which then close itself. 
        
        To do so, the function create a client that will send the message, 
        wait for the server to stop and then close itself.
        '''
        if self.is_alive():  # if the thread is alive

            log.info(f"[Server {self.name}] Stopping...")

            self._running.clear() # update the flag

            # create a client ZMQ
            ctx = zmq.Context()
            socket = ctx.socket(zmq.REQ)

            socket.connect(self.address_for_client)

            try:
                # try to send 'CMD_STOP' to the server
                socket.send_json( make_stop(sender="local", target=self.name) )
                socket.recv_json()  # response is mandatory in REP
            except Exception as e:
                log.error(f"[Server {self.name}] Stop error:", e)

            socket.close(0) # close the client
            ctx.term()      # close the client context

            self.join()     # wait until the thread terminates


if __name__ == "__main__":
    serv = ServerLHC("test", "tcp://*:1", 0, AVAILABLE_DEVICES[0], {}, False)
    # serv.start()
    serv.stop()

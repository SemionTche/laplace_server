'''
ZMQ-based server implementation for the LAPLACE-LHC project.

This module defines the ServerLHC class, which runs a command-driven server
in its own thread. The server listens for protocol-compliant messages,
validates them, dispatches command handlers, and optionally triggers
user-defined callbacks.

The server is designed to remain independent from GUI frameworks
(e.g. PyQt), while still allowing integration through callback-based
controllers.
'''

# libraries
import json
import logging
import socket as sock  # rename to avoid conflict with zmq socket
import threading
import time
from typing import Callable

import zmq

# project
from .protocol import (
    CMD_INFO, CMD_PING, CMD_GET,
    CMD_SET, CMD_SAVE, CMD_OPT, CMD_STOP, 
    make_error, make_stop,
    AVAILABLE_DEVICES,
    LOGGER_NAME
)
from .validations import(
    validate_device, validate_freedom, 
    validate_address, validate_message
)
from . import handlers


log = logging.getLogger(LOGGER_NAME)


class ServerLHC(threading.Thread):
    f'''
    Server made for the LAPLACE-LHC project.

    The server runs in its own thread and communicates using the ZMQ REP/REQ
    pattern.

    Basic usage:
        serv = ServerLHC(name, ...)
        serv.start()          # start the server thread
        serv.set_data(data)   # update server data
        serv.stop()           # stop the server gracefully

    Callbacks can be registered to react to incoming commands (e.g. 'CMD_GET').
    The 'ServerController' class provides helper methods that emit PyQt6 signals,
    allowing integration with Qt applications without making the server a QObject.

    Warning:
        The server runs in a non-daemon thread and must be stopped explicitly
        using 'stop()' to allow the Python process to exit cleanly.

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
                        'tcp://' being the imposed protocol, 
                        'IP to listen' the IP address the server should listen 
                        or '*' (equivalent to 0.0.0.0) to listen every IP.
                
                freedom: (int)
                    the degree of freedom of the associated device.
                    (Number of motors the server should drive, 0 for camera)
                
                device: (str)
                    the device associated to the server.
                    Among: {AVAILABLE_DEVICES}.

                data: (dict)
                    Initial dictionary stored by the server and transmitted on 'CMD_GET'.
                    The data can be updated later using the 'set_data()' method.
                
                empty_data_after_get: (bool)
                    whether to empty the data dictionary stored in the server
                    after transmission through 'CMD_GET'. (default {False})
                
                time_poll_ms: (int)
                    The timeout (in milliseconds) to wait for an event. 
                
                time_sleep_ms: (float)
                    Delay execution between 2 polling cylces for a given number of milliseconds. 
                    The argument may be a floating point number for subsecond precision.
        '''
        
        super().__init__() # heritage from Thread
        
        # checking format
        validate_address(address)
        validate_freedom(freedom)
        validate_device(device)
        
        # creating the server Thread
        self._running = threading.Event()
        self._running.set()

        # ensure only one thread can access the value at the same time
        self._data_lock = threading.Lock()

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
            CMD_INFO, CMD_PING, CMD_GET, 
            CMD_SET, CMD_SAVE, CMD_STOP, CMD_OPT
        ]
        self._handlers = {
            CMD_INFO: handlers.handle_info,
            CMD_PING: handlers.handle_ping,
            CMD_GET:  handlers.handle_get,
            CMD_SAVE: handlers.handle_save,
            CMD_SET:  handlers.handle_set,
            CMD_OPT:  handlers.handle_opt,
            CMD_STOP: handlers.handle_stop,
        }

        # callable to emit a signal when corresponding messages are 
        # received. Need to be set by the user when deploying the server
        self.on_saving_path_changed = None
        self.on_position_changed = None
        self.on_get = None
        self.on_opt = None

        self.callable_list = [
            self.on_saving_path_changed,
            self.on_position_changed,
            self.on_get,
            self.on_opt
        ]


    ### helpers
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
        with self._data_lock:     # if the thread can access the data
            self._data = new_data
            log.debug(f"[Server {self.name}] Server new dictionary setted.")
        
            d = json.dumps(dict(self._data), indent=4, sort_keys=True, default=str) # making a json
            log.debug(f"[Server {self.name}] Current dictionary:\n" + d )

    
    def empty_data(self) -> None:
        '''Reset the server dictionary.'''
        self.set_data(new_data={})
        log.debug("Server dictionary emptied.")


    @property
    def data(self) -> dict:
        '''Thread-safe read-only access to data'''
        with self._data_lock:       # if the thread can access the data
            return dict(self._data)
    
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

                    err = validate_message(message)  # message checking
                    if err:
                        target = message.get("from", "UNKNOWN") if isinstance(message, dict) else "UNKNOWN"
                        cmd = message.get("cmd", "UNKNOWN") if isinstance(message, dict) else "UNKNOWN"
                        log.error(f"Malformed message from {target}: {err}")
                        self.socket.send_json(
                            make_error(sender=self.name, target=target, cmd=cmd, error_msg=err)
                        )
                        continue     

                    cmd = message.get("cmd")      # get the 'CMD'
                    target = message.get("from")  # get the sender

                    handler = self._handlers.get(cmd) # get the corresponding handler

                    if handler:
                        handler(self, message, target)  # use the handler
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


    ### emit
    def emit(self, callback_name: str, *args):
        '''
        Call a registered callback safely, if it exists.

        The callback is invoked with the provided arguments and any exception
        raised by the callback is caught and logged.
        '''
        callback = getattr(self, callback_name, None)
        if callback:
            log.debug(f"'{callback_name}' function used.")
            try:
                callback(*args)
            except Exception:
                log.exception(f"Error in '{callback_name}' callback.")


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
        if not self.is_alive():  # if the thread is not alive
            return               # there is nothing to do
        
        log.info(f"[Server {self.name}] Stopping...")

        # create a client ZMQ
        ctx = zmq.Context()
        socket = ctx.socket(zmq.REQ)
        socket.connect(self.address_for_client)

        try:
            # try to send 'CMD_STOP' to the server
            socket.send_json( make_stop(sender="local", target=self.name) )
            socket.recv_json()  # response is mandatory in REP
        finally:
            socket.close(0)  # close the client
            ctx.term()       # close the client context

        self.join(timeout=2)     # wait until the thread terminates

# libraries
import zmq
import socket as sock  # rename to avoid conflict with zmq socket
import threading
import time

import logging
logger = logging.getLogger("laplace_server")


# project
from server_lhc.protocol import (
    CMD_INFO, CMD_PING, CMD_GET, CMD_SET, CMD_SAVE, CMD_STOP, CMD_OPT, 
    AVAILABLE_DEVICES,
    make_info_reply, make_pong, make_set_reply, make_opt_reply,
    make_get_reply, make_save_reply, make_error, make_stop_reply, make_stop
)

class ServerLHC(threading.Thread):
    '''
    '''
    def __init__(self,
                 name: str, 
                 address: str,
                 freedom: int,
                 device: str,
                 data: dict,
                 empty_data_after_get: bool = False):
        '''
        Visu server made to transmit a dictionnay 'data' to any client sending '__GET__'
        to the server.

        To start the server, create an instance of the server and use the 'start' method
        to assing its own thread:
            serv = ServerLHC()
            serv.start()

        To update the dictionnary, use 'setData' method:
            serv.setData(newData)

        To close the server, use the 'stop' method:
            serv.stop()

        Args:
            address: (str)
                the server adress. format 'tcp://<listen to>:<port>'
            
            host: (str)
                the host adress.

            data: (dict)
                the dictionnary to transmit.
            
            name: (str)
                the name gave to the server, default 'Unknown'.
        '''
        
        super().__init__() # heritage from Thread
        
        self._address = address
        self._data = data or {}
        self.freedom = freedom
        self.device = device
        self.name = name
        # self.reset_data = False

        # format
        self.device_format()
        self.freedom_format()
        self.set_data(data)

        # server context
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self._address)

        self._server_ip = self.get_my_ip()

        self.capabilities = [CMD_INFO, CMD_PING, CMD_GET, CMD_SET, CMD_SAVE, CMD_STOP, CMD_OPT]

        self.empty_data_after_get = empty_data_after_get

        # creating the Thread of the server
        self._running = threading.Event()
        self._running.set()

        # callable to emit a signal when save message is received
        # need to be set by the user when deploying the server
        self.on_saving_path_changed = None
        self.on_position_changed = None
        self.on_get = None
        self.on_opt = None


    def get_my_ip(self) -> str:
        '''
        Helper returning the IPV4 address of the process running.
        '''
        s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        try:
            # No traffic is actually sent
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    @property
    def address(self) -> str:
        '''
        Helper to avoid 'address' direct modification.
        '''
        return self._address
    
    @property
    def data(self) -> dict:
        '''
        Helper to avoid 'data' direct modification.
        To modify 'data', use 'set_data'.
        '''
        return self._data
    
    @property
    def server_ip(self) -> str:
        '''
        Helper to avoid 'server_ip' direct modification.
        '''
        return self._server_ip
    
    @property
    def running(self):
        '''
        Helper to avoid 'running' direct modification.
        '''
        return self._running

    @property
    def address_for_client(self):
        '''
        Helper that return the 'address' for the client.
        '<protocol>://<IP server>:<port>'
        '''
        proto, rest = self.address.split("://")
        _, port = rest.split(":")

        address_for_client = f"{proto}://{self.server_ip}:{port}"

        return address_for_client

    def set_data(self, new_data: dict) -> None:
        '''
        Set a new dictionary to transmit.
        '''
        self.dictionary_format(new_data)
        self._data = new_data
        # self.reset_data = False


    def dictionary_format(self, data):
        required_keys = []
        pass

    def device_format(self) -> None:
        if self.device not in AVAILABLE_DEVICES:
            raise ValueError(f"Error: 'device' argument must be choosen among the availabel devices: {AVAILABLE_DEVICES}")

    def freedom_format(self) -> None:
        if not isinstance(self.freedom, int):
            raise ValueError(f"Error: 'freedom' argument must be an interger not: {type(self.freedom)}")

    def empty_data(self) -> None:
        self.set_data(new_data={})

    def run(self) -> None:
        '''
        Function used while the server is running.
        The server is waiting to receive messages from clients.
        '''
        logger.info("test info")
        logger.debug("test debug")
        print(f"[Server {self.name}] Running on {self.address}")
        print(f"[Server {self.name}] To connect with, use {self.address_for_client}")

        while self._running.is_set():
            
            try:
                
                if self.socket.poll(100): # poll for 100 ms
                    message = self.socket.recv_json()
                    cmd = message.get("cmd")
                    target = message.get("from")
                    print(f"[Server {self.name}] Received: '{cmd}' from '{target}'.")
                    
                    # stop the thread on message 'STOP'
                    if cmd == CMD_STOP:
                        self.socket.send_json(
                            make_stop_reply(
                                sender=self.name,
                                target=target
                            )
                        )
                        break             # interrupt the loop
                    
                    elif cmd == CMD_INFO:
                        response = make_info_reply(
                            sender = self.name,
                            target = target,
                            device = self.device,
                            freedom = self.freedom,
                            name = self.name,
                            capabilities = self.capabilities
                            )
                        self.socket.send_json(response)

                    # send the dictionnary on message 'GET'
                    elif cmd == CMD_GET:
                        self.socket.send_json(
                            make_get_reply(
                                sender=self.name,
                                target=target,
                                data=self.data
                            )
                        )
                        self.emit_get()
                        if self.empty_data_after_get:
                            self.empty_data()
                            # self.reset_data = True
                    
                    elif cmd == CMD_PING:
                        self.socket.send_json(make_pong(self.name, target))
                    
                    elif cmd == CMD_SAVE:
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
                        else:
                            self.emit_saving_path_changed(path)
                            self.socket.send_json(
                                make_save_reply(
                                    sender=self.name,
                                    target=target
                                )
                            )
                    
                    elif cmd == CMD_SET:
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
                        else:
                            self.emit_position_changed(positions)
                            self.socket.send_json(
                                make_set_reply(
                                    sender=self.name,
                                    target=target,
                                )
                            )
                    
                    elif cmd == CMD_OPT:
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
                        else:
                            self.emit_opt_changed(data)
                            self.socket.send_json(
                                make_opt_reply(
                                    sender=self.name,
                                    target=target
                                )
                            )
                    
                    else :
                        self.socket.send_json(
                            make_error(
                                sender=self.name,
                                target=target,
                                cmd=cmd,
                                error_msg="Unknown command"
                            )
                        )

                else:
                    time.sleep(0.01) # wait 10 ms

            except zmq.error.ContextTerminated:
                break

        print(f"[Server {self.name}] Closing socket...")
        self.socket.close(0) # close the server
        self.context.term()  # close the context
        print(f"[Server {self.name}] Stopped")

    ### emit
    def emit_saving_path_changed(self, path):
        if self.on_saving_path_changed:
            self.on_saving_path_changed(path)
    
    def emit_position_changed(self, positions):
        if self.on_position_changed:
            self.on_position_changed(positions)
    
    def emit_opt_changed(self, data):
        if self.on_opt:
            self.on_opt(data)
    
    def emit_get(self):
        if self.on_get:
            self.on_get()

    ### set
    def set_on_saving_path_changed(self, func: callable) -> None:
        '''Set the function to use when a path is received.'''
        self.on_saving_path_changed = func
    
    def set_on_position_changed(self, func: callable) -> None:
        '''Set the function to use when a position is received.'''
        self.on_position_changed = func
    
    def set_on_get(self, func: callable) -> None:
        '''Set the function to use when a get is received.'''
        self.on_get = func
    
    def set_on_opt(self, func: callable) -> None:
        '''Set the function to use when a cmd opt is received.'''
        self.on_opt = func

    ### stop
    def stop(self) -> None:
        """
        Proper way to stop the thread where the server is running.
        The function send a '__STOP__' message to the server,
        which then close itself. To do so, the function create
        a client that will send the message, wait for the server to
        stop and then close itself.
        """
        print(f"[Server {self.name}] Stopping...")

        # create a client ZMQ
        ctx = zmq.Context()
        socket = ctx.socket(zmq.REQ)

        socket.connect(self.address_for_client)

        try:
            # try to send 'STOP' to the server
            socket.send_json(
                make_stop(
                    sender="local",
                    target=self.name
                )
            )
            socket.recv_json()  # response is mandatory in REP
        except Exception as e:
            print(f"[Server {self.name}] Stop error:", e)

        socket.close(0) # close the client
        ctx.term()    # close the client context

        self._running.clear() # update the flag
        self.join() # wait until the thrad terminates


if __name__ == "__main__":

    address = f"tcp://*:1234"
    data = {"hello": "world", "positions": [42.], "unit": "bar"}

    server = ServerLHC(address=address, freedom=1, device="GAS", data=data, name="gas")
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()

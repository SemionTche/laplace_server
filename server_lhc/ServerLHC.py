# libraries
import json
import zmq
import socket as sock  # rename to avoid conflict with zmq socket
import threading
import time
from PyQt6.QtCore import pyqtSignal

class ServerLHC(threading.Thread):
    '''
    '''
    saving_path_changed = pyqtSignal(str)
    
    def __init__(self, 
                 address: str,
                 freedom: int,
                 device: str,
                 data: dict,
                 name: str = "Unknown"):
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
        
        # format
        self.device_format()
        self.freedom_format()
        self.set_data(data)

        # server context
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self._address)

        self._server_ip = self.get_my_ip()

        # creating the Thread of the server
        self._running = threading.Event()
        self._running.set()


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


    def dictionary_format(self, data):
        required_keys = []
        pass

    def device_format(self) -> None:
        available_devices = ["__GAS__", "__MOTORS__", "__CAMERA__", "__OPT__"]
        if self.device not in available_devices:
            raise ValueError(f"Error: 'device' argument must be choosen among the availabel devices: {available_devices}")

    def freedom_format(self) -> None:
        if not isinstance(self.freedom, int):
            raise ValueError(f"Error: 'freedom' argument must be an interger not: {type(self.freedom)}")


    def run(self) -> None:
        '''
        Function used while the server is running.
        The server is waiting to receive messages from clients.
        keywords are:
            '__GET__': transmit the dictionary
            '__STOP__': stop the server
            '__NAME'__: transmit the name attribute
            '__PING__': answer '__PONG__'
            '__DEVICE__': answer  'diagnostics'
            '__FREEDOM__' : degree of freedom. 1 for a gas controler.
        '''
        print(f"[Server {self.name}] Running on {self.address}")
        print(f"[Server {self.name}] To connect with, use {self.address_for_client}")

        while self._running.is_set():
            
            try:
                
                if self.socket.poll(100): # poll for 100 ms
                    # message = self.socket.recv_json()
                    # cmd = message.get("cmd")
                    message = self.socket.recv_string()
                    print(f"[Server {self.name}] Received: '{message}'")
                    
                    # stop the thread on message '__STOP__'
                    if message == "__STOP__":
                        self.socket.send_string("stopping...")
                        break                                       # interrupt the loop
                    
                    # send the dictionnary on message '__GET__'
                    elif message == "__GET__":
                        response = json.dumps(self.data)
                        self.socket.send_string(response)
                    
                    elif message == "__NAME__":
                        self.socket.send_string(self.name)
                    
                    elif message == "__DEVICE__":
                        self.socket.send_string(f"{self.device}")
                    
                    elif message == "__FREEDOM__":
                        self.socket.send_string(f"{self.freedom}")
                    
                    elif message == "__PING__":
                        self.socket.send_string("__PONG__")
                    
                    elif message == "SAVE":
                        path = message.get("path")
                        if not path:
                            self.socket.send_string("Error: missing path")
                        else:
                            self.emit_saving_path_changed(path)
                            self.socket.send_string("Saving path changed")
                    
                    else :
                        self.socket.send_string("Error: unable to understand the demande")

                else:
                    time.sleep(0.01) # wait 10 ms

            except zmq.error.ContextTerminated:
                break

        print(f"[Server {self.name}] Closing socket...")
        self.socket.close(0) # close the server
        self.context.term()  # close the context
        print(f"[Server {self.name}] Stopped")

    def emit_saving_path_changed(self, path):
        self.saving_path_changed.emit(path)

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
            # try to send '__STOP__' to the server
            socket.send_string("__STOP__")
            socket.recv_string()  # response is mandatory in REP
        except Exception as e:
            print(f"[Server {self.name}] Stop error:", e)

        socket.close(0) # close the client
        ctx.term()    # close the client context

        self._running.clear() # update the flag
        self.join() # wait until the thrad terminates


if __name__ == "__main__":

    address = f"tcp://*:1234"
    data = {"hello": "world", "positions": [42.], "unit": "bar"}

    server = ServerLHC(address=address, freedom=1, device="__GAS__", data=data, name="gas")
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()

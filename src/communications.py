import socket
import json
import cv2
import numpy as np
from typing import *
def recvlen(sock:socket.socket,n: int):
    data = b""
    while len(data)<n:
        bytesrecieved = sock.recv(n-len(data))
        if not bytesrecieved:
            print("No data was recieved.")
            return False
        data += bytesrecieved
    return data

def msghead(message:bytes,prefix:bytes = b"HEAD"):
    return prefix + len(message).to_bytes(10,"big") + message

def recieve_livestream_frame(sock: socket.socket,addr: str) -> Tuple[Iterable,bool]:
    """Upon the failure of this function, here are the error codes:
    * 0: Prefix not recieved
    * 1: Invalid packet prefix
    * 2: Didn't recieve data
    """
    prefix:bytes = sock.recv(4)
    if not prefix:
        print("Prefix not recieved")
        return (0,False)
    elif prefix != b"LVST":
        print(f"Invalid packet prefix: {prefix}")
        return (1,False)
    length:bytes = int.from_bytes(sock.recv(10))
    data: bytes = recvlen(sock,length)
    if not data:
        print("Didn't recieve data")
        return (2,False)
    data = np.frombuffer(data,dtype=np.uint8)
    image = cv2.imdecode(data,cv2.IMREAD_COLOR)
    return (image,True)

class Server:
    server_socket: socket.socket = None
    client_socket: socket.socket = None
    client_address: str = None
    server_address: str = None
    server_port: int = None
    client_mainloops: List[Callable] = []
    stop_client_mainloops: List[Callable] = []
    mainloop_running = False

    def __init__(self,ip:str=None,port:int=None):
        if ip and port:
            self.server_address = ip
            self.server_port = int(port)
        else:
            config_file = open("../config/communications.json")
            config = json.load(config_file)
            config_file.close()
            self.server_address = config["server_address"]
            self.server_port = config["server_port"]

    def begin_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_address,self.server_port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(10)
    
    def add_client(self):
        try:
            client = self.server_socket.accept()
            self.client_socket = client[0]
            self.client_address = client[1]
            return True
        except socket.timeout:
            print("Connection had failed: Attempt to connect to client had timed out.")
        return False
    def begin_client_mainloop(self):
        self.mainloop_running = True
        while self.mainloop_running:
            for mainloop in self.client_mainloops:
                mainloop(self.client_socket,self.client_address,self)
    def stop_client_mainloop(self):
        self.mainloop_running = False

    def bind_client_mainloop(self,func):
        self.client_mainloops.append(func)

    def bind_stop_client_mainloop(self):
        pass

    def send_handshake(self) -> bool:
        self.client_socket.sendall(b"HNDS")
        response: bytes = self.client_socket.recv(4)
        if (not response) or (response != b"HSAC"):
            print("No response" if not response else f"Invalid handshake: {str(response)}")
            return False
        return True
    
    def disconnect(self):
        self.client_socket.close()

    def order_shutdown(self):
        try:
            while True:
                self.client_socket.sendall(b"STDN")
        except:
            return

    def __del__(self):
        self.destroy()

    def destroy(self):
        self.server_socket.close()
        self.client_socket.close()

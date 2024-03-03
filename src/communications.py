import socket
import json
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

class Server:

    server_socket: socket.socket = None
    client_socket: socket.socket = None
    client_address: str = None
    server_address: str = None
    server_port: int = None
    client_mainloops: Dict[int,None] = {}
    mainloop_running = False

    def __init__(self):
        config_file = open("../config/communications.json")
        config = json.load(config_file)
        config_file.close()
        self.server_address = config["server_address"]
        self.server_port = config["server_port"]

    def begin_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_address,self.server_port))
        self.server_socket.listen(1)
    
    def add_client(self):
        client = self.server_socket.accept()
        self.client_socket = client[0]
        self.client_address = client[1]
    
    def begin_client_mainloop(self):
        self.mainloop_running = True
        while self.mainloop_running:
            for id in self.client_mainloops:
                self.client_mainloops[id](self.client_socket,self.client_address,self)
    def stop_client_mainloop(self):
        self.mainloop_running = False

    def add_client_mainloop(self,func):
        id = len(self.client_mainloops)
        self.client_mainloops[id] = func
        return id


    def remove_client_mainloop(self,id):
        try:
            del self.client_mainloops[id]
            return True
        except:
            return False

    def __del__(self):
        self.destroy()

    def destroy(self):
        self.server_socket.close()
        self.client_socket.close()

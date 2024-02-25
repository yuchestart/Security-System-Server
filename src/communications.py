import socket
import json
from typing import *
class Server:

    server: socket.socket = None
    clients: List[Tuple[socket.socket,str]] = []
    server_address: str = None
    server_port: str = None

    def __init__(self):
        config_file = open("../config/communication.json")
        config = json.load(config_file)
        self.server_address = config["adapter_address"]
        self.server_port = config["server_port"]
    
    def create_server(self):
        self.server.bind((self.server_address,self.server_port))
        self.server.listen(1) #Only listen to one socket for now
        client,addr = self.server.accept()
        self.clients.append((client,addr))
        self.process_client(0)

    def process_client(self,client):
        pass

    def destroy(self):
        if self.server == socket.socket:
            self.server.close()
        for sock in self.clients:
            if type(sock) == socket.socket:
                sock.close()

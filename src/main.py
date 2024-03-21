"""
The real Main
"""
#Import modules
from communications import Server,recvlen,msghead,recieve_livestream_frame
from facerec import Face,Person
from uilogic import GUI,notify_user_clear,notify_user_hostile,notify_user_stranger
from typing import *
import atexit
import socket
import numpy as np
import cv2
import time
import sys
from stoppablethread import Thread

#Define cleanup code
def cleanup():
    global server,app,running
    serverthread.terminate()
    server.client_socket.sendall(b"STDN")
    server.destroy()
    app.destroy()
    running = False

#Declare variables
server: Server = None
serverthread: Thread = None
app: GUI = None
hostile_faces: List[Face] = []
faces_detected: List[Face] = []
detect_this_frame: bool = False
displaying_video: bool = True
last_threat: Dict[str,Any] = {
    "detected":False,
    "time":-1,
    "changed":False,
    "number":0
}
notifications: Dict[str,Any] = {
    "hostile":False,
    "stranger":False,
    "clear":False
}
running:bool = True

def start_connection():
    global serverthread,server
    server.add_client()

    print("Client Accepted")

    handshake = server.send_handshake()
    if not handshake:
        quit()

    print("Handshake accepted; Beginning mainloop")
    server.add_client_mainloop(client_mainloop)
    serverthread = Thread(target=server.begin_client_mainloop)
    serverthread.start()
    

def client_mainloop(sock:socket.socket,addr:str,server:Server):
    global detect_this_frame, faces_detected, displaying_video, app, running
    if not running:
        server.stop_client_mainloop()
    sock.sendall(b"CTLS")

    frame,ret = recieve_livestream_frame(sock,addr)

    if not ret:
        print("error code: ",frame)
        if frame == 1:
            print("Invalid packet prefix!")
        server.stop_client_mainloop()
        server.disconnect()
        app.update_connection_status(False)
        return
    
    if detect_this_frame:
        detected = app.recognition.detect_faces(frame)
        labels,hostility = app.recognition.label_persons(detected)
        number_of_hostiles = sum(hostility)
        last_threat["detected"] = not not number_of_hostiles
        last_threat["changed"] = last_threat["number"] < number_of_hostiles and number_of_hostiles != 0
        last_threat["number"] = number_of_hostiles
        if last_threat["detected"]:
            last_threat["time"] = time.time()
        faces_detected = labels
    app.update_stream(frame,faces_detected)

    if last_threat["detected"] and last_threat["changed"]:
        pass

print("Begin program")

server = Server()
print(server.server_address,server.server_port)

server.begin_server()

print("Server Created")

start_connection()

app = GUI(["mainpage","stream","personslist","settings"],title="Security System",names={
    "mainpage":"Home",
    "personslist":"Persons List",
    "stream":"Livestream",
    "settings":"Settings"
},icon="../assets/icon.png")

app.begin()
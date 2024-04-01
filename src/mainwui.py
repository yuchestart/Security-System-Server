"""
The old Main
"""

from communications import Server,recvlen,msghead,recieve_livestream_frame
from facerec import FaceRecognition,Face
from uilogic import GUI,notify_user_clear,notify_user_hostile,notify_user_stranger
from typing import *
import atexit
import socket
import numpy as np
import cv2
import time
import threading

server: Server = None
recognition: FaceRecognition = None
app:GUI = None
hostile_faces: List[Face] = []
faces_detected: List[Face] = []
detect_this_frame: bool = Face
displaying_video: bool = True
last_threat: Dict[str,Any] = {
    "detected":False,
    "time":-1,
    "changed":False,
    "number":0
}
server_mainloop:threading.Thread = None
running: bool = True

@atexit.register
def cleanup():
    global server,app,running
    server.destroy()
    app.destroy()
    running = False
    print("Program Terminated")

def client_mainloop(sock:socket.socket,addr:str,server:Server):
    global detect_this_frame, faces_detected, displaying_video, app, running

    if not running:
        server.stop_client_mainloop()
        return

    #Allow client to continue
    sock.sendall(b"CTLS")

    frame,ret = recieve_livestream_frame(sock,addr)
    
    if not ret:
        print("Error code: ",frame)
        if frame == 1:
            print("Idk man")
        server.stop_client_mainloop()
        return

    if detect_this_frame:
        faces_detected = app.recognition.detect_faces(frame)
        labels,hostility = app.recognition.label_faces(faces_detected,threshold=0.4)
        number_of_hostiles = sum(hostility)
        last_threat["detected"] = not not number_of_hostiles
        last_threat["changed"] = last_threat["number"] < number_of_hostiles and number_of_hostiles != 0
        last_threat["number"] = number_of_hostiles
        if last_threat["detected"]:
            last_threat["time"] = time.time()
        for i,face in enumerate(faces_detected):
            newface = face
            newface.name = labels[i]
            newface.known = True
            faces_detected[i] = newface
    
    app.update_stream(frame,faces_detected)
    
    if last_threat["detected"] and last_threat["changed"]:
        pass

print("Begin Program")

server = Server()
print(server.server_address,server.server_port)

server.begin_server()

print("Server Created")

server.add_client()

print("Client Accepted")

handshake = server.send_handshake()
if not handshake:
    quit()

print("Handshake accepted; Beginning mainloop")
server.bind_client_mainloop(client_mainloop)
server_mainloop = threading.Thread(target=server.begin_client_mainloop)
server_mainloop.start()

app = GUI(["mainpage","stream","personslist","settings"],title="Security System",names={
    "mainpage":"Home",
    "personslist":"Persons List",
    "stream":"Livestream",
    "settings":"Settings"
},icon="../assets/icon.png")

app.begin()
"""
The real Main
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
    global server,recognition,running
    server.destroy()
    recognition.destroy()
    running = False
    print("Program Terminated")

def client_mainloop(sock:socket.socket,addr:str,server:Server):
    global detect_this_frame, faces_detected, displaying_video, app, running

    if not running:
        server.stop_client_mainloop()

    #Allow client to continue
    sock.sendall(b"CTLS")

    frame,ret = recieve_livestream_frame()
    if not ret:
        print("Error code: ",frame)
        if frame == 1:
            print("Idk man")
        server.stop_client_mainloop()
    display_image = cv2.resize(frame,(0,0),fx=4,fy=4)

    if detect_this_frame:
        faces_detected = recognition.detect_faces(frame)
        labels,hostility = recognition.label_faces(faces_detected,threshold=0.4)
        number_of_hostiles = sum(hostility)
        last_threat["detected"] = not not number_of_hostiles
        last_threat["changed"] = last_threat["number"] < number_of_hostiles and number_of_hostiles != 0
        last_threat["number"] = number_of_hostiles
        if last_threat["detected"]:
            last_threat["time"] = time.time()
        for i,face in enumerate(faces_detected):
            newface = face
            newface.name = labels[i]
            faces_detected[i] = newface
    
    app.update_stream(display_image,faces_detected)



print("Begin Program")

server = Server()
recognition = FaceRecognition()

print(server.server_address,server.server_port)

server.begin_server()

print("Server Created")

server.add_client()

print("Client Accepted")

handshake = server.send_handshake()
if not handshake:
    quit()

print("Handshake accepted; Beginning mainloop")
server.add_client_mainloop(client_mainloop)
server_mainloop = threading.Thread(target=server.begin_client_mainloop)
server_mainloop.start()

while True:
    app.begin()
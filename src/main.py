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
from utilities import Thread

customconnectionparams: Dict[str,Any] = {
    "ip":None,
    "port":None
}

for argument in sys.argv:
    arg = argument.split("=")
    if arg[0] in customconnectionparams:
        customconnectionparams[arg[0]] = arg[1]

#Define cleanup code
def cleanup():
    global server,app,running,serverthread
    serverthread.terminate()
    server.order_shutdown()
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
    "number":0,
    "strangers":0
}
notifications: Dict[str,Any] = {
    "hostile":False,
    "stranger":False,
    "clear":False
}
running:bool = True

def start_connection():
    global serverthread,server,app
    server.add_client()

    print("Client Accepted")

    handshake = server.send_handshake()
    if not handshake:
        quit()
    app.update_connection_status(True)
    print("Handshake accepted; Beginning mainloop")
    server.bind_client_mainloop(client_mainloop)
    serverthread = Thread(target=server.begin_client_mainloop)
    serverthread.start()
    

def client_mainloop(sock:socket.socket,addr:str,server:Server):
    global detect_this_frame, faces_detected, displaying_video, app, running
    if not running:
        server.stop_client_mainloop()
        return
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
    strangers = last_threat["strangers"]
    if detect_this_frame and app.configuration["face_detection_enabled"].get():
        detected = app.recognition.detect_faces(frame)
        if app.configuration["face_labeling_enabled"].get():
            labels,hostility,strangers = app.recognition.label_persons(detected,frame)
            number_of_hostiles = sum(hostility)
            last_threat["detected"] = not not number_of_hostiles
            last_threat["changed"] = (last_threat["number"] < number_of_hostiles) and number_of_hostiles != 0
            last_threat["number"] = number_of_hostiles
            if last_threat["detected"]:
                last_threat["time"] = time.time()
            faces_detected = labels
            last_threat["strangers"] = strangers
        else:
            last_threat["strangers"] = len(detected)
    else:
        detected = []
    app.update_stream(frame,faces_detected)

    if last_threat["detected"] and last_threat["changed"] and app.configuration["face_labeling_enabled"].get():
        last_threat["changed"] = False
        notify_user_hostile(last_threat["number"])
    if time.time() - last_threat["time"] > 600 and app.configuration["face_labeling_enabled"].get():
        notify_user_clear()
    if last_threat["strangers"] != strangers and app.configuration["face_detection_enabled"].get():
        last_threat["strangers"] = strangers
        notify_user_stranger(last_threat["strangers"])


    detect_this_frame = not detect_this_frame

print("Begin program")

server = Server(**customconnectionparams)
print(server.server_address,server.server_port)

server.begin_server()

print("Server Created")


app = GUI(["mainpage","stream","personslist","settings"],title="Security System",names={
    "mainpage":"Home",
    "personslist":"Persons List",
    "stream":"Livestream",
    "settings":"Settings"
},icon="../assets/icon.png")

start_connection()

app.begin()
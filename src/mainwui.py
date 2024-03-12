'''

MAIN WITH UI


Yeah I'm not done with this so bye bye.

'''

#region
from communications import Server,recvlen
from facerec import FaceRecognition,Face
from uilogic import GUI,notify_user_hostile,notify_user_clear
from ui import getWidgetByName,image_cv2tk,image_file2tk
from typing import *
import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import Dialog
import atexit
import socket
import numpy as np
import cv2
import threading
import time


server: Server = None
recognition:FaceRecognition = None

app = GUI(["mainpage","stream","personslist","settings"],names={
    "mainpage":"Home",
    "personslist":"Persons List",
    "stream":"Livestream",
    "settings":"Settings"
},title="Security System",icon="../assets/icon.png")
detect_this_frame: bool = False
working: bool = False
faces_detected:List[Face] = []
last_frame: tk.PhotoImage = image_file2tk("../assets/nosignal.png")
hostile_faces:List[Face] = []
last_threat:float = time.time()
threat_changed:bool = False
threat_here:bool = False
variables:Dict[str,tk.Variable] = {
    "livestream_clicked":tk.BooleanVar(),
    "livestream_click_position":(0,0),
    "livestream_identifying":False
}


@atexit.register
def cleanup():
    global server,recognition
    server.destroy()
    recognition.destroy()
    print("Program terminated.")

#endregion

def client_mainloop(sock: socket.socket,addr: str,server: Server):
    global detect_this_frame,faces_detected,app,last_frame,threat_changed,last_threat,threat_here

    if app.closed:
        print("Window closed.")
        return
    #region
    #Allow client to continue.
    sock.sendall(b"CONTINUE")
    
    #Recieve header and handle problems
    header: bytes = sock.recv(10).decode("utf-8")
    if not header:
        print("Header not recieved")
        server.stop_client_mainloop()
    length:int = int(header)
    
    #Recieve data and handle problems
    data: bytes = recvlen(sock,length)
    if not data:
        print("Didn't recieve data.")
        server.stop_client_mainloop()

    #Deserialize image
    data = np.frombuffer(data,dtype=np.uint8)
    image = cv2.imdecode(data,cv2.IMREAD_COLOR)

    
    if detect_this_frame:
        faces = recognition.detect_faces(image)
        labels,hostility = recognition.label_faces(faces,threshold=0.4)
        #print(labels)
        for i in range(len(faces)):
            newface = faces[i]
            newface.name = labels[i]
            faces[i] = newface
            if hostility[i]:
                threat_here = True
                if not faces[i] in hostile_faces:
                    hostile_faces.append(faces[i])
                    threat_changed = True
                elif faces[i] in hostile_faces:
                    hostile_faces.append(faces[i])
        faces_detected = faces
        for i,face in enumerate(hostile_faces):
            if face not in faces_detected:
                del hostile_faces[i]
        if len(hostile_faces) > 0:
            last_threat = time.time()
        #endregion
    if time.time()-last_threat > 600 and threat_here:
        threat_here = False
        notify_user_clear()
    elif threat_changed:
        notify_user_hostile(len(hostile_faces))
        threat_changed = False
    if app.current_screen == "stream":
        app.update_stream(image=image,faces_detected=faces_detected)
    

    
    detect_this_frame = not detect_this_frame

    threat_changed = False

#Setup UI
#region



def setupui():
    global app
    def canvas_clicked(e):
        global variables
        variables["livestream_clicked"].set(True)
        variables["livestream_click_position"] = (e.x,e.y)
    def identifyface():
        btn:tk.Button = getWidgetByName("stream.livestream.identifyface",app.root)
        btn.configure(text="Click here to cancel.")
        if variables["livestream_identifying"]:
            btn.configure(text="Identify Face")
            variables["livestream_identifying"] = False
            variables["livestream_clicked"].set(True)
        if len(faces_detected) == 0:
            return
        variables["livestream_identifying"] = True
        label:tk.Label = getWidgetByName("stream.controls.action",app.root)
        canvas:tk.Canvas = getWidgetByName("stream.livestream",app.root)
        btn:tk.Button = getWidgetByName("stream.livestream.identifyface",app.root)
        btn.configure(text="Click here to cancel.")
        label.configure(text="Click on a face to label it.")
        label.pack(side="left")
        canvas.bind("<Button-1>",canvas_clicked)
        e = True
        face_id = -1
        while e:
            app.root.wait_variable(variables["livestream_clicked"])
            variables["livestream_clicked"].set(False)
            if not variables["livestream_identifying"]:
                return
            for i,face in enumerate(faces_detected):
                x,y = variables["livestream_click_position"][0]/3,variables["livestream_click_position"][1]/3
                if face.location[1] < x and face.location[3] > x:
                    if face.location[0] < y and face.location[2] > y:
                        e = False
                        face_id = i
        d = CategorizeFace(app.root,"Identify Face")
        result = d.result
        if result:
            recognition.add_face()
        label.pack_forget()

    identifyfacebutton:tk.Button = getWidgetByName("stream.controls.identifyface",app.root)
    identifyfacebutton.configure(command = identifyface)
#setupui()
#endregion

print("Begin Program")

server = Server()

print(server.server_address,server.server_port)

server.begin_server()
recognition = FaceRecognition()

print("Server created")

server.add_client()

print("Client accepted")

#Handshake and handle problems
client: socket.socket = server.client_socket
client.sendall(b"HANDSHAKE")
response: bytes = client.recv(18)
if (not response) or (response != b"HANDSHAKE_ACCEPTED"):
    print("Invalid handshake.")
    quit()

#Begin mainloop
print("Handshake accepted; Beginning mainloop")

server.add_client_mainloop(client_mainloop)
recognition_mainloop:  threading.Thread = threading.Thread(target=server.begin_client_mainloop)
recognition_mainloop.start()

while True:
    input("Press Enter to open the window")
    app.begin()
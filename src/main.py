#region
from communications import Server,recvlen
from facerec import FaceRecognition,Face
from uilogic import GUI
from ui import getWidgetByName,image_cv2tk
from typing import *
import tkinter as tk
import atexit
import socket
import numpy as np
import cv2
import threading


server: Server = None
recognition:FaceRecognition = None
app = GUI(["mainpage","stream","personslist","settings"],names={
    "mainpage":"Home",
    "personslist":"Persons List",
    "stream":"Livestream",
    "settings":"Settings"
})
detectThisFrame: bool = False
working: bool = False
facesDetected:List[Face] = []
last_frame: tk.PhotoImage = None


@atexit.register
def cleanup():
    global server,recognition
    server.destroy()
    recognition.destroy()
    print("Program terminated.")

#endregion

def client_mainloop(sock: socket.socket,addr: str,server: Server):
    global detectThisFrame,facesDetected,app,last_frame

    if app.closed:
        server.stop_client_mainloop()
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

    
    if detectThisFrame:
        faces = recognition.detect_faces(image)
        labels,hostility = recognition.label_faces(faces,threshold=0.4)
        #print(labels)
        for i in range(len(faces)):
            newface = faces[i]
            newface.name = labels[i]
            faces[i] = newface
        facesDetected = faces

        #print("I worked!",locations)
        
        for i,face in enumerate(facesDetected): #Top left bottom right
            location = face.location
            image = cv2.rectangle(
                image,
                (location[1],location[0]),
                (location[3],location[2]),
                (0,0,255),
                3
            )
            image = cv2.putText(image,face.name,(location[3],location[2]),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,255))

        streamlabel = getWidgetByName("stream.livestream",app.root)
        last_frame = image_cv2tk(image)
        streamlabel.configure(image=last_frame)
        app.root.update()
    #endregion

    
    detectThisFrame = not detectThisFrame



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

pi = tk.PhotoImage(file='../assets/nosignal.gif')
e = getWidgetByName("stream.livestream",app.root)
e.configure(image = pi)
recognition_mainloop:  threading.Thread = threading.Thread(target=server.begin_client_mainloop)
recognition_mainloop.start()
app.begin()
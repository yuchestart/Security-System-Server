"""
Main without UI
"""

from communications import Server,recvlen
from facerec import FaceRecognition,Face
from typing import *
from uilogic import notify_user_clear,notify_user_hostile
import atexit
import socket
import numpy as np
import cv2
import time

server: Server = None
recognition:FaceRecognition = None
hostile_faces: List[Face] = []
faces_detected: List[Face] = []
detect_this_frame: bool = False
displaying_video: bool = True
last_threat: Dict[str,Any] = {
    "detected":False,
    "time":-1,
    "changed":False,
    "number":0,
}

@atexit.register
def cleanup():
    global server,recognition
    server.destroy()
    recognition.destroy()
    print("Program terminated.")

def client_mainloop(sock: socket.socket, addr: str,server: Server):
    global detect_this_frame,faces_detected,displaying_video
    #Allow client to continue
    sock.sendall(b"CONTINUE")

    ## DATA RECIEVING
    #region
    #Recieve header and handle problems
    header: bytes = sock.recv(14).decode("utf-8")
    if not header:
        print("Header not recieved")
        server.stop_client_mainloop()
    elif not header.startswith("HEAD"):
        print("Header is invalid")
        server.stop_client_mainloop()
    length:int = int(header[4:])

    #Recieve data and handle problems
    data: bytes = recvlen(sock,length)
    if not data:
        print("Didn't recieve data.")
        server.stop_client_mainloop()
    
    #Deserialize image
    data = np.frombuffer(data,dtype=np.uint8)
    image = cv2.imdecode(data,cv2.IMREAD_COLOR)
    display_image = cv2.resize(image,(0,0),fx=4,fy=4)
    #endregion

    ## FACE RECOGNITION
    #region
    if detect_this_frame:
        #Detect faces
        faces_detected = recognition.detect_faces(image)
        #Obtain face labels
        labels,hostility = recognition.label_faces(faces_detected,threshold = 0.4)

        nofhostile = sum(hostility)
        last_threat["detected"] = bool(nofhostile)
        last_threat["changed"] = last_threat["number"] < nofhostile and nofhostile != 0
        last_threat["number"] = nofhostile
        if last_threat["detected"]:
            last_threat["time"] = time.time()
        #Add labels to faces
        for i,face in enumerate(faces_detected):
            newface = face
            newface.name = labels[i]
            faces_detected[i] = newface
    #endregion
            
    ## DISPLAY
    #region
    for i,face in enumerate(faces_detected):
        top,right,bottom,left = face.location
        top*=4
        right*=4
        bottom*=4
        left*=4
        cv2.rectangle(
            display_image,
            (left,top),
            (right,bottom),
            (0,0,255),2
        )
        cv2.putText(
            display_image,
            f"{i}: {face.name}",
            (left+10,bottom-10),
            cv2.FONT_HERSHEY_COMPLEX,
            1,
            (0,0,255)
        )


    cv2.imshow("Security System Display: Doorbell",display_image)
    #endregion
    
    ## NOTIFICATION
    if last_threat["detected"] and last_threat["changed"]:
        print(last_threat["changed"])
        last_threat["changed"] = False
        notify_user_hostile(last_threat["number"])
    #elif not last_threat["detected"] and (time.time() - last_threat["time"]) > 600:
    #
    #    notify_user_clear()

    ## INTERACTION
    #region
    key = cv2.waitKey(10)
    if key == 27:
        print("Program was terminated by user.")
        server.stop_client_mainloop()
    elif key == 13:
        print("EXECUTE COMMAND")
        while True:
            command = input("Execute command (I)dentify faces, (S)ave faces, (L)oad faces, (C)lear faces, (E)xit: ").upper()
            if not command:
                print("No command. Try again")
            elif "I" == command[0]:
                n = int(input("How many faces(or not specify)? "))
                for i in range(n):
                    print(faces_detected)
                    face_id = int(input("Give a number or C to cancel: "))
                    face_name = input("Give a name: ")
                    face_cat = "nonhostile" if input("Give a category: (N)on-hostile or (H)ostile: ").upper() == "N" else "hostile"
                    newface:Face = faces_detected[face_id]
                    newface.name = face_name
                    recognition.add_face(newface,face_cat)
                break
            elif "S" == command[0]:
                recognition.save_faces()
                break
            elif "L" == command[0]:
                recognition.load_faces()
                break
            elif "E" == command[0]:
                server.stop_client_mainloop()
                break
            elif "C" == command[0]:
                recognition.clear_faces()
                break
            else:
                break

    elif key >= 0:
        print(f"Keycode {key} was pressed. Idk how to handle so here you go.")
    #endregion
    detect_this_frame = not detect_this_frame

print("Begin Program")

server = Server()

print("SERVER INFORMATION",server.server_address,server.server_port)

server.begin_server()
recognition = FaceRecognition()

print("Server created")

server.add_client()

print("Client accepted",server.client_address)

client: socket.socket = server.client_socket
client.sendall(b"HANDSHAKE")
response: bytes = client.recv(18)
if (not response) or (response != b"HANDSHAKE_ACCEPTED"):
    print("Invalid handshake.")
    quit()

print("Handshake accepted; Beginning mainloop")

server.add_client_mainloop(client_mainloop)
server.begin_client_mainloop()
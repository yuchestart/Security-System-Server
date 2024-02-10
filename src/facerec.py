import cv2
import face_recognition

class FaceRecognition():
    known_face_encodings = {
        "hostile":[],
        "neutral":[],
        "friendly":[]
    }
    def __init__(self):
        pass
    def detect_faces(self,image_bgr,scale=0.25):
        image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
        small = cv2.resize(image_rgb,fx=scale,fy=scale)
        face_encoding = face_recognition.face_encodings(image_bgr)
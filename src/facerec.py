import cv2
import face_recognition
import numpy as np
from typing import *
class Face():
    name:str = None
    encoding:list = None
    location:list = None
    def __init__(self,encoding,location=None,name='Stranger'):
        self.encoding = encoding
        self.location = location
        self.name = name

class FaceRecognition():
    known_faces: Dict[str, List[Face]] = {
        "hostile":[],
        "neutral":[],
        "friendly":[]
    }
    camera:cv2.VideoCapture = None
    camera_ID:int = None
    def __init__(self):
        pass
        #self.camera = cv2.VideoCapture(camera)
    def detect_faces(self,image_bgr,scale=0.25) -> List[Face]:

        image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
        small = cv2.resize(image_rgb,(0,0),fx=scale,fy=scale)
        face_locations = face_recognition.face_locations(small)
        face_encodings = face_recognition.face_encodings(small,face_locations)
        

        #There should be the same number of face encodings and locations
        faces = []
        for i in range(len(face_encodings)):
            faces.append(
                Face(
                    face_encodings[i],
                    face_locations[i]
                )
            )

        return faces
    
    def label_faces(self,faces: List[Face],threshold = 0.6) -> List[str]:
        labels: List[str] = []
        encodings = []
        for face in faces:
            encodings.append(face.encoding)
        face_categories = ["hostile","neutral","friendly"]
        for encoding in encodings:
            #First check hostile
            face_distances:Dict[str,List[float]] = {"hostile":None,"neutral":None,"friendly":None}
            face_matches:Dict[str,str] = {"hostile":"Stranger","neutral":"Stranger","friendly":"Stranger"}
            for category in face_categories:
                face_distances[category] = face_recognition.face_distance(
                    list(map(lambda x: x.encoding,self.known_faces[category])),
                    encoding
                )
                min_distance = np.argmin(face_distances[category])
                if face_distances[min_distance] < threshold:
                    face_matches[category] = self.known_faces[category][min_distance].name
            labels.append(face_matches[min(face_distances,key=lambda x: face_distances[x])])
        return labels

    def switch_camera(self,camera):
        if self.camera != None:
            self.camera.release()
        self.camera = cv2.VideoCapture(camera)

    def destroy(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def capture(self):
        return self.camera.read()
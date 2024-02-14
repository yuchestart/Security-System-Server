import cv2
import face_recognition
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
    def detect_faces(self,image_bgr,scale=0.25):

        image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
        small = cv2.resize(image_rgb,fx=scale,fy=scale)

        face_encodings = face_recognition.face_encodings(small)
        face_locations = face_recognition.face_locations(small)

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
    
    def label_faces(self,encodings: List[Face]):
        labels: List[Tuple[str,Face]] = []
        encodings = []
        for encoding in encodings:
            #First check hostile
            face_categories = ["hostile","neutral","friendly"]
            face_distances:Dict[str,float] = {"hostile":-1,"neutral":-1,"friendly":-1}
            face_data:Dict[str,Face] = {"hostile":None,"neutral":None,"friendly":None}
            for category in face_categories:
                distances = face_recognition.face_distance(list(map(lambda x: x.encoding,self.known_faces[category])),encoding)
                for i,distance in enumerate(distances):
                    if face_distances[category] == -1 or distance < face_distances[category]:
                        face_distances[category] = distance
                        face_data[category] = self.known_faces[category][i]
            labels.append((
                min(face_distances),
                face_data[min(face_distances)]
            ))
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
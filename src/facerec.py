import cv2
import face_recognition
import numpy as np
import pickle
from typing import *
class Face():
    name:str = None
    encodings:List[np.array] = None
    location:tuple = None
    known:bool = False
    def __init__(self,encoding:np.array | List[np.array],location=None,known = False,name='Stranger'):
        if type(encoding) == list:
            self.encoding = encoding
        else:
            self.encoding = [encoding]
        self.location = location
        self.known = known
        self.name = name

    def get_distance(self,encoding: np.array):
        return min(face_recognition.face_distance(self.encodings,encoding))
    
    def reinforce(self,encoding: np.array | List[np.array]):
        if type(encoding) == np.array:
            self.encodings.append(encoding)
        elif type(encoding) == list and type(encoding[0]) == np.array:
            self.encodings.extend(encoding)
    def __eq__(self, __value: object) -> bool:
        return self.__dict__ == __value.__dict__ and isinstance(__value,Face)
class FaceRecognition():
    known_faces: Dict[str, List[Face]] = {
        "hostile":[],
        "nonhostile":[],
    }
    def detect_faces(self,image_bgr,scale=1,detectencodings=True) -> List[Face]:
        image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
        if scale != 1:
            small = cv2.resize(image_rgb,(0,0),fx=scale,fy=scale)
        else:
            small = image_rgb
        face_locations = face_recognition.face_locations(small)
        if detectencodings:
            face_encodings = face_recognition.face_encodings(small,face_locations)
        #There should be the same number of face encodings and locations
        faces = []
        for i in range(len(face_locations)):
            if detectencodings:
                faces.append(
                    Face(
                        face_encodings[i],
                        face_locations[i]
                    )
                )
            else:
                faces.append(
                    face_locations[i]
                )
        return faces
    
    def save_faces(self):
        file = open("../saves/faces.faces","wb")
        pickle.dump(self.known_faces,file)
        file.close()

    def remove_face(self,id,category:str,by_name:bool = False,by_encoding:bool = False,by_index:bool = True):
        if by_name:
            newknown:List[Face] = []
            for i,face in enumerate(self.known_faces[category]):
                if face.name != id:
                    newknown.append(face)
            self.known_faces[category] = newknown
        elif by_encoding:
            newknown:List[Face] = []
            for i,face in enumerate(self.known_faces[category]):
                if face.encoding != id:
                    newknown.append(face)
            self.known_faces[category] = newknown
        elif by_index:
            del self.known_faces[category][id]

    def load_faces(self):
        file = open("../saves/faces.faces","rb")
        self.known_faces = pickle.load(file)
        file.close()

    def add_face(self,face:Face,category:str):
        self.known_faces[category].append(face)

    def reinforce_face(self,face:Face,id:int,category:str):
        pass
    
    def label_faces(self,faces: List[Face],threshold = 0.6) -> Tuple[List[str],List[bool]]:
        def add_label(category):
            if category == "Stranger":
                labels.append("Stranger")
                hostile.append(False)
                return
            labels.append(face_matches[category])
            hostile.append(category == "hostile")
        labels: List[str] = []
        hostile: List[bool] = []
        encodings = []
        for face in faces:
            encodings.append(face.encoding)
        face_categories = ["hostile","nonhostile"]
        for encoding in encodings:
            #First check hostile
            face_distances:Dict[str,float] = {"hostile":None,"nonhostile":None}

            face_matches:Dict[str,str] = {"hostile":"Stranger","nonhostile":"Stranger"}
            for category in face_categories:
                if not len(self.known_faces[category]):
                    continue
                distances = face_recognition.face_distance(
                    list(map(lambda x: x.encoding,self.known_faces[category])),
                    encoding
                )
                min_distance = np.argmin(distances)
                print(face_distances,category,min_distance,threshold)
                if distances[min_distance] < threshold:
                    face_matches[category] = self.known_faces[category][min_distance].name
                    face_distances[category] = distances[min_distance]
            #If either are gone
            if face_distances["hostile"] == None or face_distances["nonhostile"] == None:
                #I don't have a match! It's a stranger.
                if face_distances["hostile"] == None and face_distances["nonhostile"] == None:
                    add_label("Stranger")
                elif face_distances["hostile"] == None:
                    add_label("nonhostile")
                else:
                    add_label("hostile")
            elif face_distances["nonhostile"] < face_distances("hostile"):
                add_label("nonhostile")
            else:
                add_label("hostile")
        return (labels,hostile)

    def destroy(self):
        cv2.destroyAllWindows()

    def __del__(self):
        self.destroy()
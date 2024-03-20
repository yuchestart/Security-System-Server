import cv2
import face_recognition
import numpy as np
import pickle
from typing import *

class Face():
    encoding:np.array
    location:tuple
    tolerance:float = 0.4
    def __init__(self,encoding:np.array,location=None):
        self.encoding = encoding
        self.location = location
    def __eq__(self,value:object):
        if not isinstance(value,Face):
            return False
        return face_recognition.face_distance(self.encoding,value.encoding) < Face.tolerance

class Person():
    name:str
    description:str
    faces:List[Face]
    known:bool
    def __init__(self,face:Face | List[Face],known=False,name="Stranger",description="Unknown person",tolerance=0.4):
        if type(face) == Face:
            self.faces = [face]
        elif type(face) == list:
            self.faces = face
        else:
            raise TypeError("Invalid type for faces list")
        self.known = known

    def reinforce(self,face:Face|List[Face]):
        if type(face) == Face:
            self.faces.append(face)
        elif type(face) == list:
            self.faces.extend(face)
        else:
            raise TypeError("Invalid type for faces list")

    def __eq__(self,value:object):
        if type(value) == Person:
            for face0 in self.faces:
                for face1 in value.faces:
                    if face0 == face1:
                        return True
        elif type(value) == Face:
            for face in self.faces:
                if face == value:
                    return True
        return False

class FaceRecognition():
    known_persons: Dict[str,List[Person]] = {
        "hostile":[],
        "nonhostile":[]
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
        pickle.dump(self.known_persons,file)
        file.close()
    
    def remove_person(self,id,category:str,by_name:bool = False):
        if by_name:
            for i,person in enumerate(self.known_persons[category]):
                if person.name == id:
                    del self.known_persons[i]
            return
        del self.known_persons[category][id]

    def load_faces(self):
        try:
            file = open("../saves/faces.faces","rb")
            self.known_persons = pickle.load(file)
            file.close()
        except FileNotFoundError:
            print("Save file doesn't exist. Try saving something first!")
        except EOFError:
            print("Save file was corrupted. Try saving something!")
    
    def add_person(self,person:Person,category:str):
        self.known_persons[category].append(person)
    
    def clear_faces(self):
        self.known_persons = {
            "hostile":[],
            "nonhostile":[],
        }
    
    def reinforce_person(self,id:int,category:str,face:Face):
        self.known_persons[category][id].reinforce(face)
    
    def label_persons(self,faces: List[Face]) -> Tuple[List[Person],List[bool]]:
        def add_label(category):
            if category == "Stranger":
                labels.append("Stranger")
                hostile.append(False)
                return
            labels.append(face_matches[category])
            hostile.append(category == "hostile")
        labels: List[Person] = []
        hostile: List[bool] = []
        encodings = []
        for face in faces:
            encodings.extend(face.encodings)
        face_categories = ["hostile","nonhostile"]
        
        for encoding in encodings:
            #First check hostile
            face_distances:Dict[str,float] = {"hostile":None,"nonhostile":None}

            face_matches:Dict[str,str] = {"hostile":"Stranger","nonhostile":"Stranger"}
            for category in face_categories:
                if not len(self.known_persons[category]):
                    continue
                distances = []
                for face in self.known_persons[category]:
                    d = face_recognition.face_distance(face.encodings,encoding)
                    distances.append(min(d))
                min_distance = np.argmin(np.array(distances))
                if distances[min_distance] < Face.tolerance:
                    face_matches[category] = self.known_persons[category][min_distance]
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
            elif face_distances["nonhostile"] < face_distances["hostile"]:
                add_label("nonhostile")
            else:
                add_label("hostile")
        return (labels,hostile)

    def destroy(self):
        cv2.destroyAllWindows()

    def __del__(self):
        self.destroy()
import cv2
import face_recognition
import numpy as np
import pickle
import time

from typing import *

class Face():
    encoding:np.array
    location:tuple
    tolerance:float = 0.4
    name:str
    known:bool
    def __init__(self,encoding:np.array,location=None,name="Unknown",known=False):
        self.encoding = encoding
        self.location = location
        self.name = name
        self.known = known
    def __eq__(self,value:object):
        if not isinstance(value,Face):
            return False
        return face_recognition.face_distance([self.encoding],value.encoding) < Face.tolerance

class Person():
    name:str
    description:str
    faces:List[Face]
    known:bool
    date_entered: float
    date_last_seen: float
    cover_picture: np.array
    def __init__(self,face:Face | List[Face]=False,name="Unknown",description="Unknown person",known=False):
        if type(face) == Face:
            self.faces = [face]
        elif type(face) == list:
            self.faces = face
        else:
            raise TypeError("Invalid type for faces list")
        self.known = known
        self.name = name
        self.description = description

    def reinforce(self,face:Face|List[Face]):
        if type(face) == Face:
            self.faces.append(face)
        elif type(face) == list:
            self.faces.extend(face)
        else:
            raise TypeError("Invalid type for faces list")

    def see(self):
        self.date_last_seen = time.time()

    def enter(self):
        self.date_entered = time.time()

    def get_distance(self,value:object):
        if type(value) == Person:
            md = -1
            for face0 in self.faces:
                for face1 in value.faces:
                    distance = face_recognition.face_distance([face0.encoding],face1.encoding)
                    if distance < md or md == -1:
                        md = distance
            return md
        elif type(value) == Face:
            md = -1
            for face in self.faces:
                distance = face_recognition.face_distance([face.encoding],value.encoding)
                if distance < md or md == -1:
                    md = distance
            return md
        else:
            raise TypeError(f"Cannot compare type Person and type {type(value)}.")

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
    recently_detected: Dict[str,List[Person]] = {
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
        file = open("../saves/persons.persons","wb")
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
        newperson = person
        newperson.known = True
        newperson.enter()
        newperson.see()
        self.known_persons[category].append(person)
    
    def clear_faces(self):
        self.known_persons = {
            "hostile":[],
            "nonhostile":[],
        }
    
    def reinforce_person(self,id:int,category:str,face:Face):
        self.known_persons[category][id].reinforce(face)
    
    def label_persons(self,faces: List[Face]) -> Tuple[List[Face],List[bool]]:
        '''
        Output:
        [Faces with names, If they are hostile, If they are known]
        '''
        hostility: List[bool] = []
        labels: List[Face] = []
        face_categories = ["hostile","nonhostile"]
        for face in faces:
            match:Dict[str,Person] = {"hostile":None,"nonhostile":None}
            distance = {"hostile":-1,"nonhostile":-1}
            for category in face_categories:
                if not len(self.known_persons[category]):
                    continue
                candidate: Person
                for candidate in self.known_persons[category]:
                    if candidate == face:
                        d = candidate.get_distance(face)
                        if d < distance[category] or distance[category] == -1:
                            distance[category] = d
                            match[category] = candidate
            if not (match["hostile"] or match["nonhostile"]):
                labels.append(face)
                hostility.append(False)
            elif match["hostile"] and not match["nonhostile"]:
                newface = face
                newface.name = match["hostile"].name
                newface.known = True
                match["hostile"].see()
                labels.append(newface)
                hostility.append(True)                
            elif match["nonhostile"] and not match["hostile"]:
                newface = face
                newface.name = match["nonhostile"].name
                newface.known = True
                match["nonhostile"].see()
                labels.append(newface)
                hostility.append(True)
            else:
                if distance["nonhostile"] < distance["hostile"]:
                    cat = "nonhostile"
                    match["nonhostile"].see()
                else:
                    cat = "hostile"
                    match["hostile"].see()
                newface = face
                newface.known = True
                newface.name = match[cat].name
                labels.append(newface)
                if cat == "hostile":
                    hostility.append(True)

        return (labels,hostility)

    def destroy(self):
        cv2.destroyAllWindows()

    def __del__(self):
        self.destroy()
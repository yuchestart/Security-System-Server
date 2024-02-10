import cv2
import face_recognition

class FaceRecognition():
    known_face_encodings = {
        "hostile":[],
        "neutral":[],
        "friendly":[]
    }
    camera:cv2.VideoCapture = None
    camera_ID:int = None
    def __init__(self,camera):
        self.camera = cv2.VideoCapture(camera)
    def detect_faces(self,image_bgr,scale=0.25):
        image_rgb = cv2.cvtColor(image_bgr,cv2.COLOR_BGR2RGB)
        small = cv2.resize(image_rgb,fx=scale,fy=scale)
        face_encoding = face_recognition.face_encodings(small)
        face_location = face_recognition.face_locations(small)
        face_distance = face_recognition.face_distance(small)
        return {
            "encodings":face_encoding,
            "locations":face_location,
            "distances":face_distance
        }
    
    def switch_camera(self,camera):
        self.camera.release()
        self.camera = cv2.VideoCapture(camera)

    def destroy(self):
        self.camera.release()
        cv2.destroyAllWindows()
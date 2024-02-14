from ui import beginLoop, switchScreens, screens, addScreen
from facerec import FaceRecognition
import atexit

#recognition = FaceRecognition() #Getting the camera up and running takes some time
recognition = None

@atexit.register
def cleanup():
    pass

beginLoop()
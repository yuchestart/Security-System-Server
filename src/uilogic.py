from ui import load_xml,image_cv2tk,getWidgetByName
from facerec import Face,FaceRecognition,Person
import tkinter as tk
import tkinter.ttk as ttk
import xml.etree.ElementTree as ET
import cv2
import time
from tkinter.simpledialog import Dialog
from notifypy import Notify
from typing import *
from PIL import Image
import datetime


class CategorizeFace(Dialog):
    def body(self,master):
        
        self.category_value = tk.StringVar()
        self.name_value = tk.StringVar()
        self.name_value.set("Unknown")
        self.newperson = tk.Frame()
        self.existingperson = tk.Frame()
        self.label = tk.Label(master,text="Identify Face",font=("Segoe UI",15))
        self.cat_description = tk.Label(master,text="Category:",font=("Segoe UI",15))
        self.name_description = tk.Label(master,text="Name:",font=("Segoe UI",15))
        self.category = ttk.Combobox(master,textvariable=self.category_value,state="readonly")
        self.name = tk.Entry(master,textvariable=self.name_value)
        self.category["values"] = ("Non-hostile","Hostile")
        #self.category.configure
        self.label.grid(row=0,column=0,sticky="w")
        self.category.grid(row=1,column=1,sticky="w")
        self.name.grid(row=2,column=1,sticky="w")
        self.cat_description.grid(row=1,column=0,sticky="w")
        self.name_description.grid(row=2,column=0,sticky="w")
        self.values = {
            "hostile":None,
            "name":None
        }
        self.returned = False

    def apply(self):
        self.values["hostile"] = self.category_value.get() == "Hostile"
        self.values["name"] = self.name_value.get()
        self.returned = True

class GUI:
    #region
    root: tk.Tk = None
    navbar: tk.Frame = None
    screens: Dict[str,tk.Frame] = {}
    current_screen: str = None
    recognition: FaceRecognition = None
    closed:bool = False
    configuration: Dict[str,tk.Variable] = {
        "face_detection_enabled":tk.BooleanVar,
        "face_labeling_enabled":tk.BooleanVar,
    }
    variables: Dict[str,Any] = {
        "livestream_identifying_faces":False,
        "detected_faces":[],
    }
    livestream_last_frame: Dict[str,Any] = {
        "photoimage":None,
        "matrix":None,
        "time":0
    }
    icon:tk.PhotoImage = None
    switchscreen_eventbindings: Dict[str,List[Callable]] = {}
    templates:tk.Frame = None
    #endregion
    def __init__(self,screens:List[str],path:str = "../ui/",title:str="Python GUI",names:Dict[str,str] = {},icon:str=False):
        self.root = tk.Tk()
        self.root.title(title)
        if icon:
            self.icon = tk.PhotoImage(file=icon)
            self.root.iconphoto(False,self.icon)
        self.navbar = tk.Frame(self.root)
        self.templates = load_xml(path+"templates.xml",self.root)
        for i,screen in enumerate(screens):
            self.screens[screen] = load_xml(path+screen+".xml",self.root)
            func = eval(f"lambda: gui.switch_screens(\"{screen}\")",{
                "gui":self
            })
            navwidget = tk.Button(self.navbar,text=names[screen] if screen in names else screen,command = func,borderwidth=0,activebackground="#c7c7c7",font=("Segoe UI",10,"bold"))
            navwidget.grid(row=0,column=i,sticky="nw",padx=5)
        self.navbar.grid(column=0,row=0,sticky="nw")
        for label in self.configuration:
            self.configuration[label] = self.configuration[label]()
        self.recognition = FaceRecognition()
        self.recognition.load_faces()
        self.init_variables(path+"variableconfiguration.xml")
        self.init_events()
    
    def switch_screens(self,screen):
        if self.current_screen == screen:
            return
        if self.current_screen is not None:
            self.screens[self.current_screen].grid_forget()
        if screen in self.switchscreen_eventbindings:
            for binding in self.switchscreen_eventbindings[screen]:
                binding()
        self.screens[screen].grid(column=0,row=1,sticky="w")
        self.current_screen = screen
    
    def update_connection_status(self,status:bool):
        connectionstatuses:List[tk.Label] = [
            self.root.nametowidget("mainpage.connectionstatuscontainer.connectionstatus"),
            self.root.nametowidget("stream.status.connectionstatuscontainer.connectionstatus")
        ]
        for label in connectionstatuses:
            label.configure(text="Connected" if status else "Not Connected",foreground="green" if status else "red")

    def update_stream(self,image,facesDetected=None):
        if self.current_screen != "stream":
            return
        streamcanvas:tk.Canvas = getWidgetByName("stream.livestream",self.root)
        photoimage = image_cv2tk(cv2.resize(image,(0,0),fx=3,fy=3))
        streamcanvas.create_image((0,0),anchor="nw",image=photoimage)
        self.livestream_last_frame["photoimage"] = photoimage
        self.livestream_last_frame["matrix"] = cv2.resize(image,(0,0),fx=3,fy=3)
        self.variables["detected_faces"] = facesDetected if facesDetected else \
            (self.variables["detected_faces"] if self.variables["detected_faces"] else [])
        fpstext = getWidgetByName("stream.status.fpscontainer.fps",self.root)
        newtime = time.time()
        fpstext.configure(text=f"{(1/(newtime-self.livestream_last_frame['time'])):.3f}")
        self.livestream_last_frame["time"] = newtime
        face:Face
        for face in self.variables["detected_faces"]:
            location = face.location
            streamcanvas.create_rectangle(
                location[1]*3,
                location[0]*3,
                location[3]*3,
                location[2]*3,outline="#ff0000")
            streamcanvas.create_text(location[3]*3,location[2]*3,text=face.name,fill="red",font=("Segoe UI",15),anchor="sw")
        self.root.update()
    
    def configure(self,variable,value):
        self.configuration[variable] = value
        self.update_gui()

    def on_close(self):
        self.root.iconify()
    
    def begin(self):
        self.switch_screens("mainpage")
        
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW",self.on_close)
        self.root.mainloop()        

    def init_events(self):
        def toggleidentifyface():
            btn: tk.Button = getWidgetByName("stream.controls.identifyface",self.root)
            btn.configure(text="Click here to cancel")
            if self.variables["livestream_identifying_faces"]:
                self.variables["livestream_identifying_faces"] = False
                btn.configure(text="Identify Face")
            else:
                self.variables["livestream_identifying_faces"] = True
        def identifyface(e:tk.Event):
            if not self.variables["livestream_identifying_faces"] or not len(self.variables["detected_faces"]):
                return
            position: Tuple[int] = (e.x,e.y)
            face: Face
            for face in self.variables["detected_faces"]:
                if face.known:
                    continue
                if position[0] > face.location[3]*3 and \
                    position[0] < face.location[1]*3 and \
                    position[1] > face.location[0]*3 and \
                    position[1] < face.location[2]*3:
                    dialog = CategorizeFace(self.root)
                    if dialog.returned:
                        newperson = Person(face,known=True,name=dialog.values["name"],description="")
                        self.recognition.add_person(newperson,"hostile" if dialog.values["hostile"] else "nonhostile")
                        self.recognition.save_faces()
        def updatepersonslist():
            lists:List[tk.Widget] = [
                getWidgetByName("personslist.library.hostilepersons",self.root),
                getWidgetByName("personslist.library.nonhostilepersons",self.root)
            ]
            names = ["hostile","nonhostile"]
            for i,l in enumerate(lists):
                for child in l.winfo_children():
                    child.destroy()
                for j,person in enumerate(self.recognition.known_persons[names[i]]):
                    listitem: tk.Frame = tk.Frame(l,name=f"person{j}")
                    imgcontainer = tk.Frame(listitem,name="imagecontainer")
                    infocontainer = tk.Frame(listitem,name="infocontainer")
                    imgcontainer.pack(side="left")
                    infocontainer.pack(side="left")
                    datecontainer = tk.Frame(infocontainer,name="datecontainer")
                    datecontainer.grid(row=1,column=0,sticky="w")
                    person.getimage()
                    image = tk.Label(imgcontainer,image = person.cover_picture["image"])
                    image.pack(side="left")
                    
                    datedetected: str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(person.date_last_seen))
                    dateentered: str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(person.date_entered))

                    tk.Label(infocontainer,name="name",text=person.name).grid(row=0,column=0,sticky="w")
                    tk.Label(datecontainer,name="lastdetected",text="Last Detected: %s" % datedetected).pack(side="left")
                    tk.Label(datecontainer,name="entered",text="Time Entered: %s" % dateentered).pack(side="left")
                    listitem.grid(row=j,column=0,sticky="nw")
        def delete_faces():
            self.recognition.clear_faces()
            self.recognition.save_faces()
        identifyfacebutton: tk.Button = getWidgetByName("stream.controls.identifyface",self.root)
        identifyfacebutton.configure(command = toggleidentifyface)
        livestreamcanvas: tk.Canvas = getWidgetByName("stream.livestream",self.root)
        livestreamcanvas.bind("<Button-1>",identifyface)
        clearfacesbutton:tk.Button = getWidgetByName("settings.buttoncontrols.deletefaces",self.root)
        clearfacesbutton.configure(command = delete_faces)
        self.bind_switchscreen_event("personslist",updatepersonslist)
    def bind_switchscreen_event(self,screen,binded):
        if screen not in self.switchscreen_eventbindings:
            self.switchscreen_eventbindings[screen] = [binded]
        else:
            self.switchscreen_eventbindings[screen].append(binded)

    def init_variables(self,path:str):
        root = ET.parse(path).getroot()
        for variable in root:
            self.configuration[variable.attrib["name"]].set(eval(variable.attrib["value"]))
            for value in variable:
                widget = getWidgetByName(value.text,self.root)
                widget.configure(variable = self.configuration[variable.attrib["name"]])

    def reload(self):
        if self.current_screen in self.switchscreen_eventbindings:
            for binding in self.switchscreen_eventbindings[self.current_screen]:
                binding()

def notify_user_hostile(n):
    notification = Notify()
    notification.urgency = "critical"
    notification.application_name = "Security System"
    notification.title = "Warning: Hostile Person Detected"
    notification.icon = "../assets/warning.png"
    notification.message = f'{n if n>1 else "A"} hostile person{"s" if n > 1 else ""} have been detected. Proceed with caution.'
    notification.send()

def notify_user_clear():
    notification = Notify()
    notification.urgency = "critical"
    notification.application_name = "Security System"
    notification.title = "Notice"
    notification.icon = "../assets/icon.png"
    notification.message = "Hostile persons have not been detected for 10 minutes. Still proceed with caution, however as they may still be present."
    notification.send()

def notify_user_stranger(n):
    notification = Notify()
    notification.urgency = "critical"
    notification.application_name = "Security System"
    notification.title = "Caution: Stranger Detected"
    notification.icon = "../assets/caution.png"
    notification.message = f"{n if n>1 else 'A'} stranger{'s' if n>1 else ''} have been detected. Check it out!"
    notification.send()

if __name__ == "__main__":

    from utilities import Thread
    import atexit

    gui = GUI(["mainpage","stream","personslist","settings","templates"],title="Security System",names={
        "mainpage":"Home",
        "personslist":"Persons List",
        "stream":"Livestream",
        "settings":"Settings"
    },icon="../assets/icon.png")
    gui.switch_screens("stream")

    @atexit.register
    def stop():
        global shallgo, thread#, cap
        shallgo = False
        thread.terminate()
        #cap.release()

    #cap = cv2.VideoCapture(0)
    #def go():
    #    global shallgo
    #    yes = False
    #    while True:
    #        if not shallgo:
    #            return
    #        ret,image = cap.read()
    #        if not ret:
    #            return
    #        if yes:
    #            faces = gui.recognition.detect_faces(image)
    #            gui.update_stream(image,faces)
    #        else:
    #            gui.update_stream(image)
    #        yes = not yes
    #shallgo = True
    shallgo = True
    def go():
        global shallgo
        yes = False
        while shallgo:
            image = cv2.imread("../train/placeholder.png")
            if yes:
                faces = gui.recognition.detect_faces(image)
                if gui.current_screen == "stream":
                    labels,hostility,stranger = gui.recognition.label_persons(faces,image)
                else:
                    labels,hostility,stranger = gui.recognition.label_persons(faces)
                gui.update_stream(image,labels)
            else:
                gui.update_stream(image)
            yes = not yes
            time.sleep(0.05)
    thread = Thread(target=go)
    thread.start()
    gui.begin()
    
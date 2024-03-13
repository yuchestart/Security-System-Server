from ui import load_xml,image_cv2tk,getWidgetByName
from facerec import Face,FaceRecognition
import tkinter as tk
import tkinter.ttk as ttk
import xml.etree.ElementTree as ET
import cv2
from tkinter.simpledialog import Dialog
from notifypy import Notify
from typing import *
from PIL import Image


class CategorizeFace(Dialog):
    def __init__(self,master,title,image):
        super(Dialog,self).__init__(master,title)
        self.image = image
    def body(self,master):
        self.category_value = tk.StringVar()
        self.name_value = tk.StringVar()
        self.name_value.set("Stranger")
        self.label = tk.Label(master,text="Identify Face",font=("Segoe UI",15))
        self.cat_description = tk.Label(master,text="Category:",font=("Segoe UI",15))
        self.name_description = tk.Label(master,text="Name:",font=("Segoe UI",15))
        self.category = ttk.Combobox(master,textvariable=self.category_value)
        self.name = tk.Entry(master,textvariable=self.name_value)
        self.category["values"] = ("Non-hostile","Hostile")
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
    root: tk.Tk = None
    navbar: tk.Frame = None
    screens: Dict[str,tk.Frame] = {}
    current_screen: str = None
    recognition: FaceRecognition = None
    closed:bool = False
    configuration: Dict[str,Any] = {
        "face_detection_enabled":tk.BooleanVar,
        "face_labeling_enabled":tk.BooleanVar,
    }
    variables: Dict[str,Any] = {
        "livestream_identifying_faces":False,
        "identified_faces":[]
    }
    livestream_last_frame: Dict[str,Any] = {
        "photoimage":None,
        "matrix":None
    }
    icon:tk.PhotoImage = None

    def __init__(self,screens:List[str],path:str = "../ui/",title:str="Python GUI",names:Dict[str,str] = {},icon:str=False):
        self.root = tk.Tk()
        self.root.title(title)
        if icon:
            self.icon = tk.PhotoImage(file=icon)
            self.root.iconphoto(False,self.icon)
        self.navbar = tk.Frame(self.root)
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
        self.init_commands(path+"variableconfiguration.xml")
    
    def switch_screens(self,screen):
        if self.current_screen == screen:
            return
        if self.current_screen is not None:
            self.screens[self.current_screen].grid_forget()
        self.screens[screen].grid(column=0,row=1,sticky="w")
        self.current_screen = screen
    
    def update_connection_status(self,status:bool):
        connectionstatuses:List[tk.Label] = [
            self.root.nametowidget("mainmenu.connectionstatuscontainer.connectionstatus"),
            self.root.nametowidget("stream.status.connectionstatuscontainer.connectionstatus")
        ]
        for label in connectionstatuses:
            label.configure(text="Connected" if status else "Not Connected",foreground="green" if status else "red")

    def update_stream(self,image,facesDetected):
        if self.current_screen != "stream":
            return
        streamcanvas:tk.Canvas = getWidgetByName("stream.livestream",self.root)
        self.livestream_last_frame["photoimage"] = image_cv2tk(cv2.resize(image,(0,0),fx=3,fy=3))
        self.livestream_last_frame["matrix"] = cv2.resize(image,(0,0),fx=3,fy=3)
        streamcanvas.create_image((0,0),anchor="nw",image=self.livestream_last_frame["photoimage"])
        
        for face in facesDetected:
            location = face.location
            streamcanvas.create_rectangle(
                location[1]*3,
                location[0]*3,
                location[3]*3,
                location[2]*3,outline="#ff0000")
            streamcanvas.create_text(location[1]*3,location[0]*3,text=face.name,fill="red",font=("Segoe UI",15))
        self.root.update()
        self.livestream_current_buffer += 1
        if self.livestream_current_buffer == len(self.livestream_last_frame):
            streamcanvas.delete("all")
            self.livestream_current_buffer = 0
    
    def configure(self,variable,value):
        self.configuration[variable] = value
        self.update_gui()

    def update_gui(self):
        pass

    def on_close(self):
        self.root.iconify()
    
    def begin(self):
        self.switch_screens("mainpage")
        
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW",self.on_close)
        self.root.mainloop()        

    def create_events(self):
        def toggleidentifyface(e:tk.Event):
            btn: tk.Button = e.widget
            btn.configure(text="Click here to cancel")
            if self.variables["livestream_identifying_faces"]:
                self.variables["livestream_identifying_faces"] = False
                btn.configure(text="Identify Face")
        def identifyface(e:tk.Event):
            if not self.variables["livestream_identifying_faces"] or not len(self.variables["identified_faces"]):
                return
            canvas: tk.Canvas = e.widget
            position: Tuple[int] = canvas.winfo_pointerxy()
            face: Face
            for face in self.variables["identified_faces"]:
                if face.known:
                    continue
                if position[0] > face.location[1]*3 and \
                    position[0] < face.location[3]*3 and \
                    position[1] > face.location[0]*3 and \
                    position[1] < face.location[2]*3:
                    dialog = CategorizeFace(self.root,"Identify this face",self.livestream_last_frame["matrix"][face.location[1]:face.location[3],face.location[0]:face.location[2]])
                    
            
        
        identifyfacebutton: tk.Button = getWidgetByName("stream.controls.identifyface",self.root)
        identifyfacebutton.configure(command = toggleidentifyface)

        livestreamcanvas: tk.Canvas = getWidgetByName("stream.livestream",self.root)
        livestreamcanvas.bind("<Button-1>",identifyface)

    def init_commands(self,path:str):
        root = ET.parse(path).getroot()
        for variable in root:
            self.configuration[variable.attrib["name"]].set(eval(variable.attrib["value"]))
            #print( eval(variable.attrib["value"]))
            for value in variable:
                widget = getWidgetByName(value.text,self.root)
                widget.configure(variable = self.configuration[variable.attrib["name"]])

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
    gui = GUI(["mainpage","stream","personslist","settings"],title="Security System",names={
        "mainpage":"Home",
        "personslist":"Persons List",
        "stream":"Livestream",
        "settings":"Settings"
    },icon="../assets/icon.png")
    
    

    gui.begin()
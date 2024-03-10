from ui import load_xml,image_cv2tk
from notifypy import Notify
from typing import *
import tkinter as tk
import cv2


class GUI:
    root: tk.Tk = None
    navbar: tk.Frame = None
    screens: Dict[str,tk.Frame] = {}
    current_screen: str = None
    closed:bool = False
    def __init__(self,screens:List[str],path:str = "../ui/",title:str="Python GUI",names:Dict[str,str] = {},icon:str=False):
        self.root = tk.Tk()
        self.root.title(title)
        if icon:
            i = tk.PhotoImage(file=icon)
            self.root.iconphoto(False,i)
            print("ICONED")
        self.navbar = tk.Frame(self.root)
        for i,screen in enumerate(screens):
            self.screens[screen] = load_xml(path+screen+".xml",self.root)
            func = eval(f"lambda: gui.switch_screens(\"{screen}\")",{
                "gui":self
            })
            navwidget = tk.Button(self.navbar,text=names[screen] if screen in names else screen,command = func,borderwidth=0,activebackground="#c7c7c7",font=("Segoe UI",10,"bold"))
            navwidget.grid(row=0,column=i,sticky="nw",padx=5)
        self.navbar.grid(column=0,row=0,sticky="nw")
        #self.init_commands()
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
        streamcanvas:tk.Canvas = getWidgetByName("stream.livestream",self.root)
        last_frame = image_cv2tk(cv2.resize(image,(0,0),fx=3,fy=3))
        streamcanvas.delete("all")
        streamcanvas.create_image((0,0),anchor="nw",image=last_frame)
        for face in facesDetected:
            location = face.location
            streamcanvas.create_rectangle(
                location[1]*3,
                location[0]*3,
                location[3]*3,
                location[2]*3,outline="#ff0000")
            streamcanvas.create_text(location[1]*3,location[0]*3,text=face.name,fill="red",font=("Segoe UI",15))

    def update_gui(self):
        pass

    def on_close(self):
        self.root.iconify()
    
    def begin(self):
        self.switch_screens("mainpage")
        
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW",self.on_close)
        self.root.mainloop()

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

#def notify_user_stranger(n):
#    notification = Notify()
#    notification.urgency = "critical"
#    notification.application_name = "Security System"
#    notification.title = "Caution: Stranger Detected"
#    notification.icon = "../assets/caution.png"
#    notification.message = f"{n if n>1 else "A"} stranger{"s" if n>1 else ""} have been detected. Check it out!"
#    notification.send()

if __name__ == "__main__":
    from ui import getWidgetByName
    
    gui = GUI(["mainpage","stream","personslist","settings"],title="Security System",names={
        "mainpage":"Home",
        "personslist":"Persons List",
        "stream":"Livestream",
        "settings":"Settings"
    },icon="../assets/icon.png")
    
    

    gui.begin()
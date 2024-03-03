from ui import load_xml
from typing import *
import tkinter as tk

class GUI:
    root: tk.Tk = None
    navbar: tk.Frame = None
    screens: Dict[str,tk.Frame] = {}
    current_screen: str = None
    def __init__(self,screens:List[str],path:str = "../ui/",title:str="Python GUI",names:Dict[str,str] = {}):
        self.root = tk.Tk()
        self.root.title(title)
        self.navbar = tk.Frame(self.root)

        for i,screen in enumerate(screens):
            self.screens[screen] = load_xml(path+screen+".xml",self.root)
            func = eval(f"lambda: gui.switch_screens(\"{screen}\")",{
                "gui":self
            })
            navwidget = tk.Button(self.navbar,text=names[screen] if screen in names else screen,command = func,borderwidth=0,activebackground="#c7c7c7",font=("Segoe UI",10,"bold"))
            navwidget.grid(row=0,column=i,sticky="nw",padx=5)
        self.navbar.grid(column=0,row=0,sticky="nw")
    def switch_screens(self,screen):
        if self.current_screen == screen:
            return
        if self.current_screen is not None:
            self.screens[self.current_screen].grid_forget()
        self.screens[screen].grid(column=0,row=1,sticky="w")
        self.current_screen = screen

    def update_connection_status():
        pass

    def update_stream(self,screen):
        pass

    def begin(self):
        self.switch_screens("mainpage")
        
        self.root.geometry("900x700")
        self.root.mainloop()

    def on_close(self):
        pass

if __name__ == "__main__":
    gui = GUI(["mainpage","stream","personslist"],title="Security System",names={
        "mainpage":"Home",
        "personslist":"Persons List",
        "stream":"Livestream"
    })
    


    gui.begin()
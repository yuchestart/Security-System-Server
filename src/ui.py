import tkinter as tk
from typing import *

destroyfunction = ()
window: tk.Tk = tk.Tk()
window.title("Security System")
window.configure(background="#ffffff")
current_screen = "__BLANK__"
screens = {}

screens["loading"] = tk.Frame(window)


def switchScreens(name):
    if name == current_screen:
        return
    if current_screen != "__BLANK__":
        screens[current_screen].pack_forget()
    if name != "__BLANK__":
        screens[name].pack()

def beginLoop() -> NoReturn:
    switchScreens("loading")
    window.mainloop()
    

def addScreen():
    pass
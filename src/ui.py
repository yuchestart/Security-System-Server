import tkinter as tk
from typing import *

destroyfunction = ()
window: tk.Tk = tk.Tk()
window.title("Security System")

current_screen = "loading"
screens = {}

screens["loading"] = tk.Frame(window)


def switchScreens(name):
    if name == current_screen:
        return
    screens[current_screen].pack_forget()
    screens[name].pack()

def beginLoop():
    window.mainloop()

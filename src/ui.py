import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
import cv2
from typing import *
from PIL import Image,ImageTk
from tkinter.simpledialog import Dialog

def process_parameters(p:Dict[str,str]) -> Dict[str,Any]:
    parameters = p
    for i in parameters:
        if parameters[i].startswith("TK::"):
            parameters[i] = getattr(tk,parameters[i][4:])
        elif parameters[i].startswith("D:"):
            dtype = parameters[i].split(":")
            parameters[i] = eval(f"{dtype[1]}({dtype[2]})")
        elif parameters[i].startswith("C:"):
            parameters[i] = eval(f"{parameters[i][2:]}")
    return parameters

def load_tkinter(element: ET.Element, parent: tk.Widget) -> tk.Widget:
    display_mode = ""
    display_parameters = {}
    widget_constructor = getattr(tk,element.tag)
    
    widget_parameters = process_parameters(element.attrib)
    widget:tk.Widget = widget_constructor(parent,**widget_parameters)

    for child in element:
        if child.tag == "pack" or child.tag == "grid":
            display_mode = child.tag
            display_parameters = child.attrib
        else:
            load_tkinter(child,widget)
    display_parameters = process_parameters(display_parameters)
    if display_mode == "pack":
        widget.pack(**display_parameters)
    elif display_mode == "grid":
        if "sticky" not in display_parameters:
            display_parameters["sticky"] = "w" 
        widget.grid(**display_parameters)
    return widget

def load_xml(path: str,parent: tk.Widget) -> tk.Widget:
    tree = ET.parse(path)
    root = tree.getroot()
    return load_tkinter(root, parent)

def image_cv2tk(bgr: Iterable) -> ImageTk.PhotoImage:
    image_rgb = cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    image_tk = ImageTk.PhotoImage(image=image_pil)
    return image_tk

def image_file2tk(path: str) -> ImageTk.PhotoImage:
    image_pil = Image.open(path)
    image_tk = ImageTk.PhotoImage(image=image_pil)
    return image_tk

def getWidgetByName(name:str,parent:tk.Widget) -> tk.Widget:
    return parent.nametowidget(name)

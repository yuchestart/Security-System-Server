import threading
import ctypes
import inspect
from typing import *

class Thread(threading.Thread):
    def terminate(self,exctype = KeyboardInterrupt):
        if not inspect.isclass(exctype):
            raise TypeError("Okay you seriously tried to terminate a thread with an instance?")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident),ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("Apparently the thread's own ID is invalid?")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident),None)
            raise SystemError("Failed to terminate :(")

GLOBAL_CLEANUP = []

def register_global_cleanup(func: Callable):
    GLOBAL_CLEANUP.append(func)

def terminate():
    thread: Thread
    for thread in threading.enumerate():
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident),ctypes.py_object(KeyboardInterrupt))
        if res == 0:
            print("Thread no longer exists")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident),None)
            print("Failed to terminate :(")
    func: Callable
    for func in GLOBAL_CLEANUP:
        func()
    print("Exited.")
    
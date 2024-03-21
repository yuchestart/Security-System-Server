import threading
import ctypes
import inspect

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
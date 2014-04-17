#!C:\Python33\python.exe -u
#!/usr/bin/env python
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import *     #showerror
import os
import csv
import datetime, time
from CHLog import *


#******************************************************************************
class CommonRL():
    debug = True
    error_message = None
    parent_window = None                    #Parent_window is the TKinter object itself (often known as "root"
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    user_response = None
	

    def __init__(self, parent_window, controller):
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        self.logobject = CHLog(self.controller.enable_logging)

    def handle_error(self, error_message, abort_all=False, continue_after=False, module_to_reload_afterwards="datadict"):
        print("\nIn handle_error(), message is '%s' abort_all='%s' and module_to_reload_afterwards='%s'" % (error_message, abort_all, module_to_reload_afterwards) )
        title = "Warning"
        if abort_all:
            title = "Error"
        if error_message.strip()[-1] != ".":
            error_message = error_message.strip() + "."
        user_response = tkinter.messagebox.showwarning(title, error_message + "   Procedure cancelled.")
        if abort_all:
            sys.exit(1)
        if not continue_after:
            self.controller.clear_canvas()
            self.controller.redisplay_module_after_error(module_to_reload_afterwards)
	
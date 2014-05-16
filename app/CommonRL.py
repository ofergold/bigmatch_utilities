#!C:\Python33\python.exe -u
#!/usr/bin/env python
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import *     #showerror
import sys
import traceback
import os
import csv
import datetime, time
from CHLog import *


#******************************************************************************
class CommonRL():
    debug = False
    error_message = None
    parent_window = None                    #Parent_window is the TKinter object itself (often known as "root"
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    user_response = None
    datetime_str = None
	

    def __init__(self, parent_window, controller):
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\nIn CommonRL._init_", True, True )
        
    def handle_error(self, error_message="Unspecified Error", excp_type="", excp_value="", excp_traceback=None, continue_after_error=False, abort_all=False):
        print("\nIn CommonRL.handle_error(), message is '%s' abort_all='%s', continue_after_error='%s'. Type of logobject is %s" % (error_message, abort_all, continue_after_error, type(self.logobject)) )
        self.error_message = error_message
        #Date/time info
        now = datetime.datetime.now()
        self.datetime_str = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + " " + str(now.hour) + ":" + str(now.minute)  #+ str(now.second)
        if self.logobject:
            to_browser=False
            to_console = to_logfile = to_db = message_is_error = True
            print("\nIn CommonRL.handle_error(), about to call logobject with message '%s', excp_type: %s, excp_value: %s, type of traceback is %s" % (error_message, excp_type, excp_value, type(excp_traceback)) )
            self.logobject.logit("\n##############################" + "\nERROR " + str(self.datetime_str), to_console, to_logfile, to_db, to_browser, message_is_error)
            self.logobject.logit(str(error_message), to_console, to_logfile, to_db, to_browser, message_is_error)     #Log this error in disk log and/or database
            self.logobject.logit(str(excp_type), to_console, to_logfile, to_db, to_browser, message_is_error)     #Log this error in disk log and/or database
            self.logobject.logit(str(excp_value), to_console, to_logfile, to_db, to_browser, message_is_error)     #Log this error in disk log and/or database
            typ = str(type(excp_traceback)).lower().replace("<class '", "").replace("'>", "")
            if typ == "traceback":
                self.logobject.logit("Error Line: " + str(excp_traceback.tb_lineno), to_console, to_logfile, to_db, to_browser, message_is_error)     #Log this error in disk log and/or database
        title = "Warning"
        if abort_all:
            title = "Error"
        elif continue_after_error:
            title = "Warning"
        elif not continue_after_error:
            title = "Error"
        else:
            title = "Warning"
        if not error_message:
            error_message = "Unspecified error"
        print("\nAbout to pop up error message.")
        if str(error_message).strip()[-1] != ".":
            error_message = error_message.strip() + "."
        #**************************************************************************************************
        #Display a TKinter error alert dialog box
        text = error_message
        if abort_all or not continue_after_error:
            error_message += " Procedure cancelled."
        user_response = tkinter.messagebox.showwarning(title, error_message)
        #**************************************************************************************************
        print("\nEnd of CommonRL.handle_error()")
        if abort_all:
            raise
            sys.exit(1)
        else:
            if continue_after_error:
                pass
            else:
                pass
        return

#!C:\Python33\python.exe -u
#!/usr/bin/env python
import os
import platform
import csv
import getpass
import datetime
from FilePath import *

gl_font_color = "lightblue"
gl_font_style = "Arial"

#******************************************************************************
class CHLog():
    '''Log class handles displaying and/or recording information that is generally not intended for the user.  
	This class posts the information to the Python command window (default), a log file or database. '''
    debug = True
    testmode = True
    error_message = None
    enable_file_logging = False
    logfile = None
    logfile_dir = ''	
    logfile_handle = None
    logfile_is_open = False
    error_logfile = None
    #How should the information be posted?  (One or more methods can be specified)
    log_to_file = True
    log_to_db = False
    log_to_browser = False
    #If the Message is an Error, it can be flagged as such and posted to a different log than standard debugging logs.
    message_is_error = False
    uid = None
    stamp = None
    hour_stamp = None
    os_name = None
    os_platform = None
    os_release = None

    def __init__(self, enable_file_logging=False):        #Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here.
        self.enable_file_logging = enable_file_logging
        self.uid = getpass.getuser()
        print("\n uid: %s" % (self.uid) )
        self.initialize()

    def initialize(self):
        #Get operating system info
        self.os_name = os.name
        self.os_platform = platform.system()
        self.os_release = platform.release()
        #Date/time info
        now = datetime.datetime.now()
        self.stamp = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(now.second)
        self.hour_stamp = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + str(now.hour).rjust(2,'0')
        if not self.logfile_dir:
            head, tail = os.path.split(os.path.abspath(__file__))
            self.logfile_dir = head
        self.logfile = os.path.join(self.logfile_dir, "logs", "python_logfile_" + self.uid + "_" + self.hour_stamp + ".txt")  
        print("\n In log object, log-dir: %s, logfile: %s" % (self.logfile_dir, self.logfile) )
        if self.enable_file_logging:
            if not os.path.isdir(self.logfile_dir):
                os.mkdir(self.logfile_dir) 
            self.create_logfile()
        self.initialized = True

    def create_logfile(self):
        if not os.path.isfile(self.logfile):
            try:
                with open(self.logfile, 'w+') as logfile:
                   logfile.write("Python log file " + self.hour_stamp + "\n")
            except IOError:
                print('Error creating log file (initialize).')

    def open_logfile(self):
        if not os.path.isfile(self.logfile):
            self.create_logfile()
        #self.logfile_handle = open(self.logfile, 'ab')
        self.logfile_handle = open(self.logfile, 'a')
        self.logfile_is_open = True

    def close_logfile(self):
        self.logfile_handle.close()
        self.logfile_is_open = False

    def logit(self, text, to_console=False, to_logfile=False, to_db=False, to_browser=False):
        '''At its simplest, function logit() displays text in the command line console window. It can also write that text to a file or db, if permissions are sufficient. '''
        #Always log to console if TestMode is True, or if an error has occurred:
        if(self.testmode):
            to_console = True
        if(self.error_message != ''):
            to_console = True
            self.message_is_error = True
        if(self.log_to_file):
            to_logfile = True
        if(self.log_to_db):
            to_db = True
        if(self.log_to_browser):
            to_browser = True
        #*********************
        if(to_console):
           	print(text)
        if(to_logfile):
            if self.enable_file_logging:      #Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here.
                #print("#-#Text to log file:")
                #print(text)
                #if(text != '' and text is not None):
                if text:
                    #if(self.logfile_is_open == False):
                    if not self.logfile_is_open:
                        self.open_logfile()
                typ = str(type(text)).lower().replace("<class '", "").replace("'>", "")
                #print("#--#Type of log text: " + typ)
                if typ == "str":
                    #print("\nAbout to write string to logfile")
                    #self.logfile_handle.write(text.encode('utf-8'))
                    self.logfile_handle.write(text)
                elif typ == "list":
                    for listitem in text:
                        if str(type(listitem)).lower().replace("<class '", "").replace("'>", "") == "str":
                            #self.logfile_handle.write(str(listitem).encode('utf-8'))
                            self.logfile_handle.write(str(listitem))
                elif typ == "dict":
                    for key, value in text:
                        self.logfile_handle.write("%s = %s" % (str(key), str(value) ) )
                self.logfile_handle.write("\n")
                self.close_logfile()

    def test_subfolder_filewrite(self):
        '''Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here. '''
        return_value = True
        try:
            with open(self.logfile, 'a') as logfile:
                logfile.write("\nPython log file...testing file write at " + self.hour_stamp + "\n")
        except IOError:
            return_value = False
        return return_value

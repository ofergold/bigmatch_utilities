#!C:\Python33\python.exe -u
#!/usr/bin/env python
import sys
import os
import platform
import csv
import getpass
import datetime
import sqlite3
'''#The following libraries are currently within the BigMatch repo
current, tail = os.path.split(os.path.realpath(__file__))         #/bigmatch/app/
up_one, tail = os.path.split(current)                             #bigmatch
up_two, tail = os.path.split(up_one)                              #parent folder of bigmatch
#print("\n Up_one: '%s', Up_two: '%s'" % (up_one, up_two) )
python_common_found = None
if os.path.isdir(os.path.join(up_two, "common_functions", "python_common")):
    python_common_found = True
    sys.path.append(os.path.join(up_two, "common_functions", "python_common"))     #Python_Common subfolder within ETL folder (ETL is a sibling of Bigmatch folder)
    from Textfile import *
elif os.path.isdir(os.path.join(up_two, "python_common")):
    python_common_found = True
    sys.path.append(os.path.join(up_two, "python_common"))                   #Python_Common subfolder within ETL folder (ETL is a sibling of Bigmatch folder)
    from Textfile import *
'''
gl_font_color = "lightblue"
gl_font_style = "Arial"

#******************************************************************************
class CHLog():
    '''Log class handles displaying and/or recording information that is generally not intended for the user.  
	This class posts the information to the Python command window (default), a log file or database. '''
    debug = False
    testmode = True
    error_message = None
    enable_file_logging = False
    enable_db_logging = False
    logfile_dir = ''
    logfile = None
    logfile_handle = None
    logfile_is_open = False
    error_logfile = None
    errlogfile_handle = None
    errlogfile_is_open = False
    #Database logging
    db_conn = None                     #RDBMS connection object for storing data values
    db_platform = ""                   #RDBMS platform to be used for importing the flat file data (e.g., "sqlite3", "mysql")
    db_catalog = None                  #RDBMS database (catalog) name where data will be saved
    db_tablename = None                #RDBMS table name
    db_pathonly = None                 #DB file Path without the file name (Sqlite only)
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

    def __init__(self, enable_file_logging=False, enable_db_logging=False):        #Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here.
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
            self.logfile_dir = os.path.join(head, "logs")
        self.logfile = os.path.join(self.logfile_dir, "python_logfile_" + self.uid + "_" + self.hour_stamp + ".txt")  
        self.error_logfile = os.path.join(self.logfile_dir, "error_log.txt")
        print("\n In log object, log-dir: %s, logfile: %s" % (self.logfile_dir, self.logfile) )
        if self.enable_file_logging:
            if not os.path.isdir(self.logfile_dir):
                print("\nIn CHLog, attempting to create new log directory at %s" % (self.logfile_dir))
                os.mkdir(self.logfile_dir) 
            self.create_logfile(self.logfile)
            self.create_logfile(self.error_logfile)
        self.initialized = True

    def create_logfile(self, logfile_with_path=None):
        #print("\nCreating log file (if not exists) %s" % (logfile_with_path))
        if not logfile_with_path:
            logfile_with_path = self.logfile
        if not os.path.isfile(logfile_with_path):
            print("\nLog file does not exist, so creating %s" % (logfile_with_path))
            try:
                with open(logfile_with_path, 'w') as f:
                   f.write("Python log file " + self.hour_stamp + "\n")
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

    def open_errlogfile(self):
        if not os.path.isfile(self.error_logfile):
            self.create_logfile(self.error_logfile)
        #self.errlogfile_handle = open(self.logfile, 'ab')
        self.errlogfile_handle = open(self.error_logfile, 'a')
        self.errlogfile_is_open = True

    def close_errlogfile(self):
        self.errlogfile_handle.close()
        self.errlogfile_is_open = False

    #******************************************************************************************************************************
    def logit(self, text, to_console=None, to_logfile=None, to_db=None, to_browser=None, message_is_error=None):
        '''At its simplest, function logit() displays text in the command line console window. It can also write that text to a file or db, if permissions are sufficient. '''
        #Always log to console if TestMode is True, or if an error has occurred:
        if(self.testmode):
            to_console = True
        if(self.log_to_file):
            to_logfile = True
        if(self.log_to_db):
            to_db = True
        if(self.log_to_browser):
            to_browser = True
        if message_is_error:
            self.message_is_error = message_is_error
        if(self.error_message):
            to_console = True
            self.message_is_error = True
        #*********************
        #print("In CHLog, enable_file_logging=%s, to_console=%s, to_logfile=%s" % (self.enable_file_logging, to_console, to_logfile) )
        if(to_console):
           	print(text)
        if(to_logfile):
            if self.enable_file_logging:      #Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here.
                if text:
                    if not self.logfile_is_open:
                        self.open_logfile()
                    if self.message_is_error:
                        if not self.errlogfile_is_open:
                            self.open_errlogfile()
                    typ = str(type(text)).lower().replace("<class '", "").replace("<type '", "").replace("'>", "")
                    #print("#--#Type of log text: %s. Type of logfile_handle: %s. logfile_handle: %s, message_is_error? %s" % (typ, type(self.logfile_handle), self.logfile_handle, str(self.message_is_error)))
                    if typ == "str":
                        #print("About to write string to logfile:  -- '%s'" % (text))
                        #self.logfile_handle.write(text.encode('utf-8'))
                        #******************************************************************************
                        self.logfile_handle = open(self.logfile, 'a')
                        self.logfile_handle.write(text)                     #WRITE THE TEXT TO THE LOG
                        #self.logfile_handle.close()
                        #******************************************************************************
                        if self.message_is_error:                           #For error messages, write them to the standard log and then write them to an errors-only log for at-a-glance monitoring of errors
                            #print("\nCHLog about to write ERROR message '%s' to error log %s. ErrLogFileHandle type is %s" % (text.strip(), self.error_logfile, type(self.errlogfile_handle)))
                            self.errlogfile_handle.write(text)
                    elif typ == "list":
                        for listitem in text:
                            if str(type(listitem)).lower().replace("<class '", "").replace("'>", "") == "str":
                                #self.logfile_handle.write(str(listitem).encode('utf-8'))
                                self.logfile_handle.write(str(listitem))
                                if self.message_is_error:                           #For error messages, write them to the standard log and then write them to an errors-only log for at-a-glance monitoring of errors
                                    self.errlogfile_handle.write(str(listitem))
                    elif typ == "dict":
                        for key, value in text.items():    #for key, value in text:
                            self.logfile_handle.write("%s = %s" % (str(key), str(value) ) )
                            if self.message_is_error:                           #For error messages, write them to the standard log and then write them to an errors-only log for at-a-glance monitoring of errors
                                self.errlogfile_handle.write("%s = %s" % (str(key), str(value) ) )
                    self.logfile_handle.write("\n")
                    self.close_logfile()
                    if self.message_is_error:  
                        self.errlogfile_handle.write("\n")
                        self.close_errlogfile()
                else:     #No error text was found
                    pass
                #*************************
        if to_db:      #Log this message to the database
            pass

    def test_subfolder_filewrite(self):
        '''Because of problems with file write permissions, logging is restricted to console output by default.  When environment is file-write enabled, enable file logging here. '''
        print("\nIn CHLog object, testing log file write")
        return_value = True
        try:
            with open(self.logfile, 'a') as logfile:
                logfile.write("\nPython log file...testing file write at " + self.hour_stamp + "\n")
        except IOError:
            return_value = False
            print("Test log file write FAILED")
        return return_value

    def test_sqlite_data_write(self):        #, db_platform=None, db_catalog=None, db_tablename=None
        '''Determine whether a Sqlite database is available for writing.'''
        return_value = True
        db_platform = "sqlite"
        db_catalog = os.path.join(self.logfile_dir, "test.db")
        db_tablename = self.uid + "_" + self.hour_stamp
        try:
            self.db_conn = sqlite3.connect(db_catalog)
            cmd = "DROP TABLE IF EXISTS %s;" % (db_tablename) 
            self.db_conn.execute(cmd)
            cmd = "CREATE TABLE %s (text varchar(500), uid varchar(14), error_yn int(1));" % (db_tablename) 
            print("\nIn test_sqlite_data_write(), cmd=%s" % (cmd) )
            self.db_conn.execute(cmd)
        except IOError:
            return_value = False
        return return_value

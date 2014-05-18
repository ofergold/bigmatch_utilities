#!C:\Python33\python.exe -u
#!/usr/bin/env python
import os
import csv
import getpass
import datetime 
import socket
from FilePath import *

#******************************************************************************
class CHUser():
    '''User class handles custom configurations, etc. '''
    debug = True
    error_message = None
    uid = None
    stamp = None
    configfile = None
    configfile_dir = ''	
    configfile_handle = None
    configfile_is_open = False
    configfile_rowcount = None
    file_rows = None
    row_index = None
    host_name = None

    def __init__(self):
        self.initialize()

    def initialize(self):
        self.uid = getpass.getuser()
        self.host_name = socket.gethostname()
        print("\n uid: %s, host: %s, current _file_: %s" % (self.uid, self.host_name, os.path.abspath(__file__) ) )
        now = datetime.datetime.now()
        self.stamp = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(now.second)
        if not self.configfile_dir:
            head, tail = os.path.split(os.path.abspath(__file__))
            self.configfile_dir = head
        if not os.path.isdir(self.configfile_dir):
            os.mkdir(self.configfile_dir) 
        self.configfile = os.path.join(self.configfile_dir, "config", "configfile_" + self.uid + ".txt")
        print("\n dir: %s, configfile: %s" % (self.configfile_dir, self.configfile) )
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        setting = self.get_config_setting('cmd_onload')
        if not setting:
            self.write_setting_to_config_file('cmd_onload', 'load_recfile_datadict')    #Default for all users, until they change it, is to load the DataDict module on launch.
        self.initialized = True
	
    def open_configfile_read(self):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.configfile_handle = open(self.configfile, 'r')

    def open_configfile_readwrite(self):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.configfile_handle = open(self.configfile, 'r+')

    def open_configfile_write(self):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.configfile_handle = open(self.configfile, 'w')

    def open_configfile_append(self):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.configfile_handle = open(self.configfile, 'a')

    def create_configfile(self):
        if not os.path.isfile(self.configfile):
            try:
                with open(self.configfile, 'w+') as configfile:
                   configfile.write("#Chapin Hall python app config file for @user " + self.uid + " ~host " + self.host_name + " " + self.stamp + "\n")
                   print("Creating a new config file for user %s" % (self.uid) )
                   configfile.close()
            except IOError:
                print('Error creating config file (initialize).')

    def close_configfile(self):
        self.configfile_handle.close()

    def read_config_file(self):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.row_index = 0
        self.open_configfile_read()
        with self.configfile_handle as f:
            self.file_rows = f.readlines()                      #Copy the text into a space-delimited list called file_rows
            self.configfile_rowcount = len(self.file_rows)
            for row in self.file_rows:                          #Iterate thru the rows of text, and for each row create a ParmRow object
                print("\n Row %s: %s" % (self.row_index, row) )
                self.row_index += 1
            f.close()

    def get_config_setting(self, key=''):
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        row_to_return = ""
        self.row_index = 0
        self.open_configfile_read()
        print("\n In get_config_setting(), key='%s'" % (key) )
        if key:
            with self.configfile_handle as f:
                self.file_rows = f.readlines()                      #Copy the text into a space-delimited list called file_rows
                self.configfile_rowcount = len(self.file_rows)
                found = False
                for row in self.file_rows:                          #Iterate thru the rows of text, and for each row create a ParmRow object
                    print("\n -Row %s: %s" % (self.row_index, row) )
                    print("\n (%s) -Seeking '%s', found '%s'" % (self.row_index, key, row[:len(key)].lower().strip() ) )
                    if row[:len(key)].lower().strip() + '=' == key.lower().strip() + '=':
                        found = True
                        print("\n -Found '%s' in row %s, will return this value." % (key, self.row_index) )
                        row_to_return = row
                        break
                    self.row_index += 1
                f.close()
                print("\n -Found? %s" % (str(found)) )
                if found:
                    row_to_return = row_to_return[len(key):]
                    row_to_return = row_to_return.replace("=", "")
            print("\n -Return from GetSetting: '%s'" % (row_to_return) )
        return row_to_return

    def write_setting_to_config_file(self, key='', value=''):
        #Find out whether the specified key already exists.  If it exists, change this line to reflect the request entry.  If not exists, append it.
        if not os.path.isfile(self.configfile):
            self.create_configfile()
        self.row_index = 0
        row_to_change = 0
        self.open_configfile_read()
        print("\n In write_setting_to_config_file(), key='%s' and value='%s'" % (key, value) )
        if key and value:
            newtext = key.strip() + "=" + value.strip()
            with self.configfile_handle as f:
                self.file_rows = f.readlines()                      #Copy the text into a space-delimited list called file_rows
                print("\n File Rows:")
                print(self.file_rows)
                self.configfile_rowcount = len(self.file_rows)
                found = False
                for row in self.file_rows:                          #Iterate thru the rows of text, and for each row create a ParmRow object
                    print("\n Row %s: %s" % (self.row_index, row) )
                    print("\n (%s) Seeking '%s', found '%s'" % (self.row_index, key, row[:len(key)].lower().strip() ) )
                    if row[:len(key)].lower().strip() + '=' == key.lower().strip() + '=':
                        found = True
                        print("\n Found '%s' in row %s, will overwrite." % (key, self.row_index) )
                        row_to_change = self.row_index
                        break
                    self.row_index += 1
                f.close()
                print("\n Found? %s" % (str(found)) )
                if found:
                    self.open_configfile_write()
                    with self.configfile_handle as f:
                        self.file_rows[row_to_change] = newtext
                        #Overwrite the old file with updated metadata:
                        f.writelines(self.file_rows)
                        f.close()
                else:
                    self.open_configfile_append()
                    with self.configfile_handle as f:
                        f.write("\n" + newtext)


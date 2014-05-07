#!C:\Python33\python.exe -u
#!/usr/bin/env python
import os
import csv
import datetime, time, sched



#******************************************************************************
class DbReadWrite():
    debug = True
    error_message = None               


    def __init__(self, datafile="", db_tablename="", db_catalog="", db_platform="", datafile_type=""):
        self.copy_parms_to_properties(datafile, db_tablename, db_catalog, db_platform, datafile_type)
        

    def open_db_connection(self):
        if str(self.db_platform).lower().strip() == "sqlite3":
            if self.debug: print("\nAbout to open a Sqlite3 connection at: %s" % (self.db_catalog) )
            self.db_conn = sqlite3.connect(self.db_catalog)
            self.db_conn.text_factory = str

    def close_db_connection(self):
        if str(self.db_platform).lower().strip() == "sqlite3":
            if self.db_conn is not None:
                self.db_conn.close()

    def check_db_connection_open(self, conn):
        open = False
        if str(self.db_platform).lower().strip() == "sqlite3":
            try:
                cmd = "select * from %s LIMIT 1" % (self.db_tablename)
                conn.execute(cmd)
                open = True
            except:
                pass
        return open

    def format_db_name(self, db_catalog="", copy_to_class_property=True):
        if not db_catalog:
            db_catalog = self.db_catalog            #Default to whatever DB_CATALOG has been specified as a property of this object
        if self.db_platform == "sqlite3":	
            #Sqlite3 uses files rather than an RDBMS application -- We want to specify the entire path, rather than just default to the Python path of the current directory.
            if self.debug: print("\nDb_pathonly: %s, datafile_pathonly: %s" % (self.db_pathonly, self.datafile_pathonly) )
            head, tail = os.path.split(db_catalog)
            if self.debug: print("db_catalog head and tail: %s, %s" % (head, tail) )
            if not head:                            #If the sqlite database is not specified as a .db filename with a full path
                if self.debug: print("Db_catalog is not specified as an existing file.")
                if self.db_pathonly:
                    if(db_catalog.lower().find(self.db_pathonly) == -1):
                        db_catalog = os.path.join(self.datafile_pathonly, db_catalog)
                elif self.datafile_pathonly:
                    if(db_catalog.lower().find(self.datafile_pathonly.lower()) == -1):
                        db_catalog = os.path.join(self.datafile_pathonly, db_catalog)
            if not db_catalog.lower()[-3:] == ".db":
                db_catalog = db_catalog + ".db"
            if self.debug: print("Sqlite DB file location (after formatting): %s" % (db_catalog) )
        #Assume that this db_catalog should be stored as the db_catalog property of this object:
        if copy_to_class_property:
            self.db_catalog = db_catalog
        return db_catalog

    def copy_parms_to_properties(self, datafile="", db_tablename="", db_catalog="", db_platform="", datafile_type=""):
        self.db_tablename = str(db_tablename).lower().strip()
        if self.db_tablename == "" or self.db_tablename == "None" or self.db_tablename is None:
            self.db_tablename = "newtable_" + self.stamp
        self.db_catalog = str(db_catalog).lower().strip()
        if self.db_catalog == "" or self.db_catalog == "None" or self.db_catalog is None:
            self.db_catalog = "ccts"
        self.db_platform = str(db_platform).lower().strip()
        if self.db_platform == "" or self.db_platform == "None" or self.db_platform is None:
            self.db_platform = "sqlite3"
        #Don't default FileType here, because DataFile might not have been specified yet.
        self.datafile_type = str(datafile_type).lower().strip()
        #if self.datafile_type == "" or self.datafile_type == "None" or self.datafile_type is None:
        #    self.datafile_type = "flat"  '''


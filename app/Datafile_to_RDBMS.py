#!C:\Python33\python.exe -u
#!/usr/bin/env python
import sys
import os 
from os import path
import sqlite3
import datetime
from CHLog import *

#******************************************************************************
class Datafile_to_RDBMS():
    debug = True
    error_message = None               
    error_file = None	
    logobject = None                   #Instantiation of CHLog class
    stamp = None
    datadict = []                      #Data dictionary where columns are defined for reading data from flat file, and writing to RDBMS table
    sql_commands = []                  #List of commands to create a new RDBMS table to hold the data from self.datafile
    datafile = None                    #Data file path and filename
    datafile_type = None               #CSV or flat file?
    datafile_handle = None             #File Handle object for Python to access the data file (flat text)
    csvfile_handle = None              #File Handle object for Python to access CSV file
    datafile_rowcount = 0              #Rows found in the data file
    datafile_path_as_list = []         #Store the path and filename of the data file, split out into segments
    datafile_pathonly = None           #Path without the file name
    datafile_nameonly = None           #File name without path
    file_rows = None                   #Python list to hold the data file contents while traversing the file
    row_index = 1                      #Counter for iterating thru the data file
    row_index_cumulative = 1           #Counter for rows inserted during the LIFE of this class instance (not just this iteration of import_data()).	
    dont_drop_and_recreate_db_table = False   #Set to True if datafile should be added to the specified RDBMS table WITHOUT dropping and recreating that table.  Default behavior is to drop and re-create table 'db_tablename' in database 'db_catalog' each time function 'import_data()' is called.
    db_conn =  None                    #RDBMS connection object for storing data values
    db_conn_validate = None            #RDBMS connection object used for validating values
    db_platform = ""                   #RDBMS platform to be used for importing the flat file data (e.g., "sqlite3", "mysql")
    db_catalog = None                  #RDBMS database (catalog) name where data will be saved
    db_tablename = None                #RDBMS table name
    db_pathonly = None                 #DB file Path without the file name (Sqlite only)
    #db_table_trunc = None             #Prefix for RDBMS table name
    #db_table_suffix = ""              #Suffix for RDBMS table name - OPTIONAL, can be set to whatever is useful
    db_catalog_for_validation = None   #RDBMS database (catalog) name used for validation (only when specified--this is optional)
    validation_by_row_or_column = ""   #If "column" then invalid values are set to blank string and included in the save;  validation by "row" is executed once per row, and false result means do not write this row to the result file.
    row_validation_function = None     #If validation_by_row_or_column = "row", execute this function to validate the row of data.	
    validation_parm_values = []        #The validation function(s) can retrieve these parameters, which can be populated by the data-write function.
    column_list_for_insert =  ""       #List of columns to be used in the SQL INSERT statement
    values_list_for_insert = ""        #
    question_list_for_insert = ""      #
    colwidth_current = 0               #Temporary field used when parsing the data file - width of the current column
    startpos_before_current = 0        #Temporary field used when parsing the data file - starting position of the current column, before its own width is added to the total positions already processed.
    startpos_after_current = 0         #Temporary field used when parsing the data file 
    quit_after_row = 100                 #For debugging, process only n number of rows.

    def __init__(self, datafile="", db_tablename="", db_catalog="", db_platform="", datafile_type=""):
        '''DOCSTRING '''
        #Clean and neutralize the format in which the data file and its path are represented:
        #self.copy_datafile_path_to_list(datafile)
        now = datetime.datetime.now()
        self.stamp = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(now.second)
        self.startpos_before_current = 1        #Used when adding new columns, to calculate starting position
        self.startpos_after_current = 1         #Used when adding new columns, to calculate starting position
        self.copy_parms_to_properties(datafile, db_tablename, db_catalog, db_platform, datafile_type)
        self.logobject = CHLog(False)
		
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

    def add_column(self, name, type, width, startpos=None, datasource="file", source_func=None, validate=False, validate_func = None):
        '''Add a column to the data dictionary. Most typical use is a flat, undelimited, fixed-width text file, so we include starting position and length.
        Data source is normally "file" because we read the value for this column from the specified positions in the current row of the data file. But if datasource="function" then get the value by calling the specified function.'''
        #Column Name:
        name = self.clean(name)
        #Data source is normally "file" because we read the value for this column from the specified positions in the current row of the data file. But if datasource="function" then get the value by calling the specified function.
        datasource = self.clean(datasource).lower().strip()
        #Optionally, a value can be validated by submitting it to a specified function:
        validate = self.clean(validate).lower().strip()
        #Column Type, formatted for the specified database platform (MySql, Sqlite, etc.)
        type_db_specific = self.get_datatype_for_dbplatform(self.clean(type))
        try:
            #Column width:
            width = int(self.clean(width))
            #Allow column width to be zero for CSV files only:
            if self.datafile_type != "csv":
                if width == 0:
                    self.error_message = "Column width may not be zero."
            self.log_colwidth(width)                          #Function log_colwidth() allows us to calculate the starting position of each column based on the widths of all previous columns.
            if startpos is None:
                startpos = self.startpos_before_current       #This value is calculated by function log_colwidth() -- this allows us to calculate the starting position of each column based on the widths of all previous columns.
            #print("Adding column to datadict array: %s, %s, %s" % (name, width, startpos) )
        except ValueError:
            self.error_message = "Invalid column name, type or width: name='%s', type='%s', width=%s" % (name, type, width)
        if self.error_message:
            print("\n\n ERROR: %s" % (self.error_message) )
            return self.error_message
        #Add this column to the DataDict: 
        self.datadict.append({"name":name, "width":width , "type":type_db_specific, "startpos":startpos, "datasource":datasource, "source_func":source_func, "validate":validate, "validate_func":validate_func })
        return self.error_message

    def clean(self, string_parm):
        return_value = str(string_parm).replace(";", "")
        return_value = str(string_parm).replace("@", "")
        return_value = str(string_parm).replace("-", "_")
        return return_value

    def log_colwidth(self, colwidth):
        self.colwidth_current = colwidth
        self.startpos_before_current = self.startpos_after_current
        #self.startpos_after_current = self.startpos_before_current + colwidth
        self.startpos_after_current += colwidth
        #print("self.startpos before and after current field (cur width=%s): %s, %s" % (colwidth, self.startpos_before_current, self.startpos_after_current) )
        return colwidth

    #**************************************************************************************************		
    def import_data(self):
        '''Import_data is the main function where data is read from the data file and inserted into the RDBMS table.
        But it delegates the actual writing process to functions import_data_from_csv() or import_data_from_text()'''
        #Parse the data file path so it is formatted for different OS
        self.copy_datafile_path_to_list(self.datafile)
        head, tail = os.path.split(self.datafile)
        self.error_file = os.path.join(head, "errors.txt")       #Write any errors to a text file in the same directory with the data file
        if self.debug: print("Formatted datafile: %s ... is file? %s" % (self.datafile, os.path.isfile(self.datafile) ) )
        if self.datafile_type:
            self.datafile_type = str(self.datafile_type).lower().strip()
        else:
            print("\nFileExt: %s" % (self.datafile[-4:].lower().strip()) )
            if self.datafile[-4:].lower().strip().replace(".", "") == "csv":
                self.datafile_type = "csv"
            else:
                self.datafile_type = "flat"
        print("\nDatafile_Type: %s" % (self.datafile_type) )
        self.format_db_name(self.db_catalog)
        self.column_list_for_insert = self.build_column_list_for_insert()
        self.question_list_for_insert = self.build_question_list_for_insert()
        if len(self.datadict) == 0:
            self.error_message = "No data dictionary information was found"
        if self.debug: print("\nAbout to call open_db_connection()")
        #if self.db_conn is None:
        self.open_db_connection()
        if self.debug: print("\n Type of db_conn: %s" % (str(type(self.db_conn)) ) )
        if str(type(self.db_conn)) == "NoneType":
            self.error_message = "Failed to open database connection for : '%s'" % (self.db_platform)
        #Test - display tables in database        #self.drop_db_table("ccts_root_20140402")
        self.list_db_tables()
        if self.error_message:
            print("\n\n ERROR: %s" % (self.error_message) )
            return self.error_message
        #Define and execute the CREATE TABLE commands to create the RDBMS table that will hold the data			
        if self.debug: print("Dont_drop_and_recreate_db_table: %s" % (self.dont_drop_and_recreate_db_table) )
        if not self.dont_drop_and_recreate_db_table:
            self.build_tblcreate_sql_commands()
            self.execute_tblcreate_sql()                      
        #***************************************************
        if self.datafile_type == "csv":
            self.import_data_from_csv()
        else:
            self.import_data_from_text()
        #***************************************************
        #Data should now have been imported into the RDBMS
        if self.debug: 
            print("\n RESULTS (max.100 rows) from cmd '%s': "  % ("select * from " + self.db_tablename) ) 
            i = 1
            for row in self.db_conn.execute("select * from " + self.db_tablename): 
                #print("Type of row: %s" % (type(row)) )     #each row is a TUPLE
                #print("%s %s %s %s" % ( row[self.datadict[0]["name"]], row[self.datadict[1]["name"]], row[self.datadict[2]["name"]], row[self.datadict[3]["name"]] ) )
                if len(self.datadict) > 21:
                    print(row)
                elif len(self.datadict) > 20:
                    print("(%s)  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s %s  %s  %s  %s  %s  %s  %s  %s" % (i, str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), str(row[10]), str(row[11]), str(row[12]), str(row[13]), str(row[14]), str(row[15]), str(row[16]), str(row[17]), str(row[18]), str(row[19]), str(row[20]), str(row[21])  ) )
                elif len(self.datadict) > 12:
                    print("(%s)  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  %s" % (i, str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), str(row[10]), str(row[11]), str(row[12]) ) )
                    #print("(%s) %s %s   %s   %s   %s   %s   %s   %s   %s   %s   %s   %s   %s   %s" % (i, str(row[0]).encode(encoding='UTF-8'), str(row[1]).encode(encoding='UTF-8'), str(row[2]).encode(encoding='UTF-8'), str(row[3]).encode(encoding='UTF-8'), str(row[4]).encode(encoding='UTF-8'), str(row[5]).encode(encoding='UTF-8'), str(row[6]).encode(encoding='UTF-8'), str(row[7]).encode(encoding='UTF-8'), str(row[8]).encode(encoding='UTF-8'), str(row[9]).encode(encoding='UTF-8'), str(row[10]).encode(encoding='UTF-8'), str(row[11]).encode(encoding='UTF-8'), str(row[12]).encode(encoding='UTF-8'), str(row[13]).encode(encoding='UTF-8') ) )
                elif len(self.datadict) > 5:
                    #print("(%s), %s   %s, %s, %s, %s, %s, %s" % (i, str(row[0]).encode(encoding='UTF-8'), str(row[1]).encode(encoding='UTF-8'), str(row[2]).encode(encoding='UTF-8'), str(row[3]).encode(encoding='UTF-8'), str(row[4]).encode(encoding='UTF-8'), str(row[5]).encode(encoding='UTF-8')  ) )
                    print("(%s) %s %s %s %s %s %s %s" % (i, str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6])  ) )
                else:
                    print("(%s)  %s  %s  %s" % (i, str(row[0]), str(row[1]), str(row[2]) ) )
                i += 1
                if i > 100:
                    break
        #Close DB connection(s):
        typ = str(type(self.db_conn)).lower()
        if(typ.find("connection") != -1):
            self.close_db_connection()
        typ = str(type(self.db_conn_validate)).lower()
        if(typ.find("connection") != -1):
            self.db_conn_validate.close()

    def import_data_from_text(self):
        print("\nTop of import_data_from_text()")
        #if self.datafile_handle is None:   #This will be called iteratively, so it will only be NONE on the first iteration
        self.open_datafile()
        if self.debug: print("\nType of self.datafile_handle: %s" % (str(type(self.datafile_handle)) ) )
        if str(type(self.datafile_handle)) == "NoneType":
            self.error_message = "Failed to open file handle for the specified data file: '%s'" % (self.datafile)
        #Read the data file and copy it to the RDBMS table by means of iterative INSERT statements
        with self.datafile_handle as f:
            self.file_rows = f.readlines()                      #Copy the text into a space-delimited list called file_rows
            self.datafile_rowcount = len(self.file_rows)
            self.row_index = 0
            for row in self.file_rows:                          #Iterate thru the rows of text, and for each row create a ParmRow object
                if self.debug: 
                    print("\nRaw Datafile row (%s): %s" % (self.row_index, str(row)) )
                else: 
                    #print("FILE %s ROW (%s) columns 4 and 5: %s  %s" % (self.datafile_nameonly, self.row_index, row[23:32], row[33:44]) )
                    print("TEXT ROW (%s)(%s)" % (self.row_index_cumulative, self.row_index) )
                #Determine whether this is a blank row in the file
                rowcheck = ''.join(row)
                rowcheck = rowcheck.replace(",", "").replace("'", "").replace("\n", "").replace("?", "").strip()
                #self.logobject.logit("Rowcheck: %s" % (rowcheck), True, True)
                if rowcheck == "":
                    #self.logobject.logit("ROW IS EMPTY. SKIP IT.", True, True)
                    continue                  #If row is blank, skip it!
                #************************************************************************
                #Parse the current row of the data file and split it into values, according to the data dictionary built in function define_columns()
                self.values_list_for_insert = self.build_values_list_for_insert(row)       
                #************************************************************************
                #If validation_by_row_or_column = "row", execute this function to validate the row of data.	
                valid_row = True
                if self.validation_by_row_or_column.lower() == "row":
                    valid_row = self.row_validation_function()
                    if self.debug: print("Valid row? %s" % (valid_row) )
                if not valid_row:
                    continue     #Go to top of loop without writing this row's values.
                #Assuming the validation succeeded and we now have a list of values to insert into the database, proceed with the DB write operation.
                if len(self.values_list_for_insert) > 0:
                    insert_command = ""
                    try:
                        insert_command = '''INSERT INTO %s (%s) VALUES (%s)'''  % (self.db_tablename, self.column_list_for_insert, self.question_list_for_insert)
                        if self.debug: 
                            print(insert_command)
                            print("Values:")
                        print(self.values_list_for_insert)   #Even if not debugging, display this
                        self.db_conn.execute(insert_command, self.values_list_for_insert)
                        self.db_conn.commit()                    #IMPORTANT! Commit the changes to ensure persistence
                        self.row_index += 1
                        self.row_index_cumulative += 1						
                        if self.quit_after_row and self.debug:
                            if (self.row_index > self.quit_after_row) or (self.row_index_cumulative > self.quit_after_row):
                                break
                    except:
                        self.error_message = "Error while writing row to database: '%s'" % (self.datafile) + "  " + sys.exc_info()[0]
                        print("\n\nERROR: %s" % (self.error_message) )
                        with open(self.error_file, 'a') as f:
                            f.write("Write Failed: %s" % (insert_command) )
                            f.close()

            f.close()    #Close the data file handle:

    def import_data_from_csv(self):
        #Read the data file and copy it to the RDBMS table by means of iterative INSERT statements
        print("\nTop of import_data_from_csv()")
        with open(self.datafile, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')     #, quotechar='')
            count = 0
            self.row_index = 0
            for row in csvreader:
                if self.debug: 
                    print("\n(%s)--type is %s:  %s" % (self.row_index, str(type(row)), str(row)) )
                else: 
                    #print("CSV %s ROW (%s): %s" % (self.datafile_nameonly, self.row_index, row) )
                    print("CSV ROW (%s)(%s)" % (self.row_index_cumulative, self.row_index) )
                #Determine whether this is a blank row in the file
                rowcheck = ','.join(row)
                rowcheck = rowcheck.replace(",", "").replace("'", "").replace("\n", "").replace("?", "").strip()
                #self.logobject.logit("Rowcheck: %s" % (rowcheck), True, True)
                if rowcheck == "":
                    self.logobject.logit("ROW IS EMPTY. SKIP IT.", True, True)
                    continue                  #If row is blank, skip it!
                #************************************************************************
                #Parse the current row of the data file and split it into values, according to the data dictionary built in function define_columns()
                self.values_list_for_insert = self.build_values_list_for_insert(row)
                #************************************************************************
                #If validation_by_row_or_column = "row", execute this function to validate the row of data.	
                valid_row = True
                if self.validation_by_row_or_column.lower() == "row":
                    valid_row = self.row_validation_function()
                    if self.debug: print("Valid row? %s" % (valid_row) )
                if not valid_row:
                    continue     #Go to top of loop without writing this row's values.
                #Assuming the validation succeeded and we now have a list of values to insert into the database, proceed with the DB write operation.
                if len(self.values_list_for_insert) > 0:
                    insert_command = ""
                    try:
                        insert_command = '''INSERT INTO %s (%s) VALUES (%s)'''  % (self.db_tablename, self.column_list_for_insert, self.question_list_for_insert)
                        if self.debug: print(insert_command)
                        self.db_conn.execute(insert_command, self.values_list_for_insert)
                        self.db_conn.commit()                    #IMPORTANT! Commit the changes to ensure persistence
                        self.row_index += 1
                        self.row_index_cumulative += 1	
                        if self.quit_after_row and self.debug:
                            if (self.row_index > self.quit_after_row) or (self.row_index_cumulative > self.quit_after_row):
                                break
                    except:
                        #self.error_message = "Error while writing row to database: '%s'"% (self.datafile) + "  " + sys.exc_info()[0]
                        with open(self.error_file, 'a') as f:
                            f.write("Write Failed: %s" % (insert_command) )
                            f.close()

            csvfile.close()    #Close the data file handle:

    def build_tblcreate_sql_commands(self):
        create_tbl_done = False
        for col in self.datadict:
            if create_tbl_done == False:
                #cmd = "DROP TABLE IF EXISTS %s%s;" % (self.db_table_trunc, self.db_table_suffix) 
                cmd = "DROP TABLE IF EXISTS %s;" % (self.db_tablename) 
                self.sql_commands.append(cmd)
                #cmd = "CREATE TABLE %s%s (%s %s(%s) NULL);" % (self.db_table_trunc, self.db_table_suffix, col["name"], col["type"], col["width"] ) 
                cmd = "CREATE TABLE %s (%s %s(%s) NULL);" % (self.db_tablename, col["name"], col["type"], col["width"] ) 
                create_tbl_done = True
            else:
                #cmd = "ALTER TABLE %s%s ADD COLUMN %s %s(%s) NULL;" % (self.db_table_trunc, self.db_table_suffix, col["name"], col["type"], col["width"] )
                cmd = "ALTER TABLE %s ADD COLUMN %s %s(%s) NULL;" % (self.db_tablename, col["name"], col["type"], col["width"] )
            self.sql_commands.append(cmd)
            if self.debug: print(cmd)

    def execute_tblcreate_sql(self):
        if self.db_conn is None:
            self.open_db_connection()
        with self.db_conn:
            for cmd in self.sql_commands:
                #print("executing %s" % (cmd) )
                self.db_conn.execute(cmd)
            #self.close_db_connection()
            #self.db_conn.close()
			
    def build_column_list_for_insert(self):
        self.column_list_for_insert = ""
        for col in self.datadict:
            self.column_list_for_insert += str(col["name"]).lower() + ","
        self.column_list_for_insert = self.column_list_for_insert[:-1]           #Remove final comma
        if self.debug: print("\nColumn_list_for_insert: %s" % (self.column_list_for_insert) ) 
        return self.column_list_for_insert

    def build_question_list_for_insert(self):
        self.question_list_for_insert = ""
        for col in self.datadict:
            self.question_list_for_insert += "?,"
        self.question_list_for_insert = self.question_list_for_insert[:-1]        #Remove final comma
        return self.question_list_for_insert

    def build_values_list_for_insert(self, datarow):
        self.values_list_for_insert = []        #List object with all values to be inserted
        #self.value_string_for_insert = ""      #Comma-delimited string with all values to be inserted
        value = ""
        try:
            colnum = 0
            for col in self.datadict:
                value = ""                #Value of this column within this row
                valid = True              #Optionally, columns in the data dictionary can be flagged for validation.  Values are validated by submitting them to a specified function.
                startpos = int(col["startpos"])
                colwidth = int(col["width"])
                datatype = str(col["type"]).lower().strip()
                datasource = str(col["datasource"]).lower().strip()
                source_func = col["source_func"]
                validate_before_save = str(col["validate"]).lower().strip()
                if validate_before_save[:1] == "t" or validate_before_save[:1] == "y":
                    validate_before_save = True
                else:
                    validate_before_save = False
                validate_func = col["validate_func"]
                #Data source is normally "file" because we read the value for this column from the specified positions in the current row of the data file. But if datasource="function" then get the value by calling the specified function.
                if datasource == "file":  
                    #*******************************************************************
                    #Read the actual value for this row, for this column:
                    if self.datafile_type == "csv":
                        raw_value = datarow[colnum]
                    else:
                        raw_value = datarow[startpos-1 : startpos-1 + colwidth]                #Minus 1 because the string-array is zero-based
                    #*******************************************************************
                elif datasource == "function":
                    #If datasource="function" then get the value by calling the specified function.
                    raw_value = source_func(datarow)
                if datatype == "char" or datatype == "string" or datatype == "text":
                    #value = chr(39) + str(raw_value).strip() + chr(39)
                    value = str(raw_value).strip()
                else:
                    value = raw_value
                value = str(value)
                #value.encode(encoding='UTF-8')      #,errors='strict'
                #Optionally, a value can be validated by submitting it to a specified function:
                if validate_before_save:
                    valid = validate_func()
                if valid:
                    self.values_list_for_insert.append(value)
                    #self.value_string_for_insert += value + ","
                    #if self.value_string_for_insert[-1:] == ",":
                    #    self.value_string_for_insert = self.value_string_for_insert[:-1]           #Remove final comma if a straggler is present 
                colnum += 1
        except ValueError:
            print("Invalid column width or value: width=%s, value='%s'" % (width, value))

        #if self.debug: print("\nInsert Values: %s" % ( self.value_string_for_insert.encode(encoding='UTF-8') ) ) 
        #return self.value_string_for_insert
        return self.values_list_for_insert
         
    def get_datatype_for_dbplatform(self, data_type_generic):
        data_type_generic = str(data_type_generic).lower().strip()
        return_value = data_type_generic    #By default, if no other type code is found for the specified type, return it unchanged (as opposed to returning a blank value or raising an error)
        if self.db_platform == "sqlite3":
            if data_type_generic == "string" or data_type_generic == "text" or data_type_generic == "char":
                return_value = "text"
            elif data_type_generic == "int" or data_type_generic == "integer" or data_type_generic == "numeric":
                return_value = "int"
        elif self.db_platform == "mysql":
            if data_type_generic == "string" or data_type_generic == "text" or data_type_generic == "char":
                return_value = "char"
            elif data_type_generic == "int" or data_type_generic == "integer" or data_type_generic == "numeric":
                return_value = "int"

        return return_value

    def copy_datafile_path_to_list(self, datafile_with_path):
        temp_list = []
        i = 1
        drive, tail = os.path.splitdrive(datafile_with_path)      #Separate out the drive (if on a system that uses drive letters)
        if self.debug: print("Drive: %s Remainder: %s" % (drive, tail) )
        head = datafile_with_path
        for i in range(0,20):
            head, tail = os.path.split(head)
            if self.debug: print("%s %s" % (head, tail) )
            temp_list.append(str(20-i) + "~" + tail)
            if head.strip().replace(chr(47), "").replace(chr(92), "") == drive:
                break
        temp_list.append(str(20-i) + "~" + drive + os.sep)
        temp_list.sort()
        for seg in temp_list:
            tilde =seg.find('~')
            if(tilde > -1):
                seg = str(seg)[tilde+1:]
                self.datafile_path_as_list.append(seg)     #Copy the next path segment into a master list 
        temp_filename = ""
        if self.debug: print("Path segments:")
        for seg in self.datafile_path_as_list:
            if self.debug: print(seg)
            temp_filename = os.path.join(temp_filename, seg)
        self.datafile = temp_filename
        head, tail = os.path.split(self.datafile)
        self.datafile_pathonly = head
        self.datafile_nameonly = tail

    def open_datafile(self):
        if os.path.isfile(self.datafile):
            try: 
                self.datafile_handle = None
                #if self.datafile_handle is None:
                self.datafile_handle = open(self.datafile, 'r')
            except:
                self.error_message = "Error while opening file: '%s'" % (self.datafile) + "  " + sys.exc_info()[0]
                raise
        else:
            self.error_message = "Specified data file does not exist: '%s'" % (self.datafile) 
        if self.error_message:
            print("\n\n ERROR: %s" % (self.error_message) )
        
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

    def display_datadict(self):
        print("\n Data dictionary:")
        for col in self.datadict:
            print("%s %s %s %s %s %s %s %s" % (str(col["name"]).ljust(22), str(col["type"]).ljust(10), str(col["startpos"]).ljust(6), str(col["width"]).ljust(6), str(col["datasource"]).ljust(12), str(col["source_func"]).ljust(16), str(col["validate"]).ljust(6), str(col["validate_func"]).ljust(20)   ) )

    def list_db_tables(self):
        #if self.db_conn is None:
        self.open_db_connection()
        with self.db_conn:
            if self.db_platform == "sqlite3":
                #cmd = "select * from sqlite_master;"
                #for val in self.db_conn.execute(cmd): 
                #    print("MASTER: %s %s %s %s %s" % ( val[0], val[1], val[2], val[3], val[4] ) )    #, val[1], val[2], val[3], val[4], val[5], val[6], val[7], val[8], val[9] ) )
                cmd = "select name from sqlite_master where type = 'table';"
                if self.debug: print("\nList DB Tables in db '%s':" % (self.db_catalog) )
                for val in self.db_conn.execute(cmd): 
                    if self.debug: print("TABLE: %s" % ( val[0] ) )    #, val[1], val[2], val[3], val[4], val[5], val[6], val[7], val[8], val[9] ) )
            #self.close_db_connection()
            #self.db_conn.close()

    def drop_db_table(self, db_tablename):
        #if self.db_conn is None:
        self.open_db_connection()
        with self.db_conn:
            if self.db_platform == "sqlite3":
                cmd = "DROP TABLE IF EXISTS %s;" % (db_tablename) 
            if cmd:
                self.db_conn.execute(cmd)

    #*****************************************************************************************************************************
    #THE FOLLOWING FUNCTIONS ARE USED IN build_values_list_for_insert(), 
    #to fetch values for DB columns that are flagged to be populated by a function call, rather than read from the data file.
    def get_tblname(self, datarow):
        #head, tail = os.path.split(self.datafile)
        #return tail[:23]                  #Width for "datasource" column is only 26
        print("get_tblname tbl=%s" % (self.datafile_nameonly[:25]) )
        return self.datafile_nameonly[:25] #Width for "datasource" column is only 26
    
    def get_rowindex(self, datarow):
        return self.row_index

    def get_cumulative_rowindex(self, datarow):
        return self.row_index_cumulative

    def get_case_id(self, datarow):
        #print("In get_case_id, case_id=%s" % (datarow[0] + datarow[1] + datarow[2]) )
        return datarow[0] + datarow[1] + datarow[2]

    def check_if_record_exists(self, datarow):
        #if self.debug: print("\nAbout to open a Sqlite3 connection (for validation) at: %s" % (self.db_catalog_for_validation) )
        conn_needs_to_be_opened = False		
        typ = str(type(self.db_conn_validate)).lower()
        if(typ.find("connection") == -1):
            conn_needs_to_be_opened = True
        else:
            if not self.check_db_connection_open(self.db_conn_validate):
                conn_needs_to_be_opened = True
        if conn_needs_to_be_opened:
            self.db_conn_validate = sqlite3.connect(self.db_catalog_for_validation)
            self.db_conn_validate.text_factory = str    #To handle unicode strings
        notfound = True
        where_clause = ""
        where_clause_values = []
        p = 0
        for col in self.datadict:
            if str(col["datasource"]).lower() == "file":
                where_clause += str(col["name"]) + "=? AND "                      #Use question mark placeholders for parameterized query
                value_for_column = self.values_list_for_insert[p]
                #print("Value for col %s: %s" % (p, value_for_column ) ) 
                where_clause_values.append(value_for_column)
            p += 1
        if where_clause.strip()[-4:].lower().strip() == "and":
            where_clause = where_clause.strip()[:-3] + " "
        cmd = """select lname from members_unique_list WHERE %s""" % (where_clause)          #lname=? AND fname=? AND dob=? AND gender=? AND race=?"
        if self.debug: print("\nValidation Where_clause_values:")
        for val in where_clause_values:
            if self.debug: print("%s" % (val) )
        if self.debug: print("Validation SQL: %s" % (cmd) )
        cursor = self.db_conn_validate.cursor()
        #cursor = self.db_conn_validate.execute(cmd, where_clause_values)         #Should return a cursor object
        cursor.execute(cmd, where_clause_values)                                  #Should return data rows
        typ = str(type(cursor)).lower()
        if self.debug: print("Type of validation resultset: %s" % (typ) )
        rf = 0
        if typ.find("list") != -1 or typ.find("cursor") != -1 or typ.find("dict") != -1:
            rows = cursor.fetchall()		
            if self.debug: print("Type and length of rows: %s with %s members." % (type(rows), len(rows) ) )
            #for val in cursor: 
            for val in rows: 
                notfound = False
                #print("\nValidation cursor: %s" % ( str(val[0]).encode(encoding='UTF-8') ) )
                if self.debug: print("\nValidation cursor: %s" % ( str(val[0]) ) )
                rf += 1
        if self.debug: print("Validation rows found: %s" % (rf) )
        #self.db_conn_validate.close()
        return notfound
        

#******************************************************************************
class Datafile_Column():
    debug = True
    error_message = ""
    name = None
    type_generic = None
    type_platform_specific = None
    startpos = None
    width = None
    db_platform = None
    datafile_type = None               #CSV or flat file?

    def __init__(self, name, type_generic, startpos=0, width=0, db_platform="", datafile_type=""):
        self.name = str(name).strip()
        self.type_generic = str(type).strip()
        self.type_platform_specific = self.get_datatype_for_dbplatform(self.type_generic)
        self.startpos = startpos
        self.width = width
        self.db_platform = str(db_platform).strip().lower()
        self.datafile_type = str(datafile_type).strip().lower()
        if self.datafile_type != "csv":
            if self.width == 0 or self.startpos == 0:
                self.error_message = "Column width and/or starting position are required, but not specified."
                return self.error_message
         
    def get_datatype_for_dbplatform(self, data_type_generic):
        data_type_generic = str(data_type_generic).lower().strip()
        return_value = data_type_generic    #By default, if no other type code is found for the specified type, return it unchanged (as opposed to returning a blank value or raising an error)
        if self.db_platform == "sqlite3":
            if data_type_generic == "string" or data_type_generic == "text" or data_type_generic == "char":
                return_value = "text"
            elif data_type_generic == "int" or data_type_generic == "integer" or data_type_generic == "numeric":
                return_value = "int"
        elif self.db_platform == "mysql":
            if data_type_generic == "string" or data_type_generic == "text" or data_type_generic == "char":
                return_value = "char"
            elif data_type_generic == "int" or data_type_generic == "integer" or data_type_generic == "numeric":
                return_value = "int"

        return return_value
 

#******************************************************************************************		
#******************************************************************************************		
def main():
    #THIS IS NOT NORMALLY USED - NORMALLY THIS CLASS IS INSTANTIATED WITHIN ANOTHER PYTHON ROUTINE.
    master = Datafile_to_RDBMS("c:/greg/code/ccts/root_dummy.dat", "", "")
	#master.define_columns()
    master.add_column("lmd1_cat", "char", 1, None)
    master.add_column("lmd1_county", "char", 3, None)
    master.add_column("lmd1_basic_num", "char", 9, None)
    master.display_datadict()
    #master.build_tblcreate_sql_commands()
    master.import_data()

if __name__ == "__main__":
    main()  


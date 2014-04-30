#!C:\Python33\python.exe -u
#!/usr/bin/env python
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from TkEntry import EntryGrid
import sys
import csv
import os 
from os import path
from FilePath import *
from DataDict import *
from CHLog import *

gl_frame_color = "ivory"
gl_frame_width = 400
gl_frame_height = 100
gl_file_textbox_width = 80   

#******************************************************************************************
class RDBMS_Read_Export_UI_Model():
    debug = True
    error_message = None
    controller = None                  #Controller is the BigMatchController class in main.py 
    logobject = None                   #Instantiation of CHLog class
    #sql_commands = []                 #List of commands to create a new RDBMS table to hold the data from self.datafile
    sql_text = None                    #SQL SELECT command entered by the user in the text box
    sql_result = []                    #List of lists containing the data retrieved - each item in the list is a list of column values.
    sql_result_with_column_info = []   #List of lists of lists, each inner list containing column index value type and value. (Will this be useful in some instances?)
    sql_result_as_single_string = []   #List of lists containing the data retrieved - each item in the list is a list of column values.
    datafile = None                    #Data file path and filename
    datafile_type = None               #CSV or flat file?
    datafile_handle = None             #File Handle object for Python to access the data file (flat text)
    csvfile_handle = None              #File Handle object for Python to access CSV file
    datafile_rowcount = 0              #Rows found in the data file
    datafile_path_as_list = []         #Store the path and filename of the data file, split out into segments
    datafile_pathonly = None           #Path without the file name
    datafile_nameonly = None           #File name without path
    #file_rows = None                  #Python list to hold the data file contents while traversing the file
    row_index = 1                      #Counter for iterating thru the data file
    row_index_cumulative = 1           #Counter for rows inserted during the LIFE of this class instance (not just this iteration of import_data()).	
    db_conn =  None                    #RDBMS connection object for storing data values
    db_conn_validate = None            #RDBMS connection object used for validating values
    db_platform = None                 #RDBMS platform to be used for importing the flat file data (e.g., "sqlite3", "mysql")
    db_catalog = None                  #RDBMS database (catalog) name where data will be saved
    db_tablename = None                #RDBMS table name
    db_pathonly = None                 #DB file Path without the file name (Sqlite only)
    #db_table_trunc = None             #Prefix for RDBMS table name
    #db_table_suffix = ""              #Suffix for RDBMS table name - OPTIONAL, can be set to whatever is useful
    db_catalog_for_validation = None   #RDBMS database (catalog) name used for validation (only when specified--this is optional)
    validation_by_row_or_column = ""   #If "column" then invalid values are set to blank string and included in the save;  validation by "row" is executed once per row, and false result means do not write this row to the result file.
    row_validation_function = None     #If validation_by_row_or_column = "row", execute this function to validate the row of data.	
    validation_parm_values = []        #The validation function(s) can retrieve these parameters, which can be populated by the data-write function.
    colwidth_current = 0               #Temporary field used when parsing the data file - width of the current column
    startpos_before_current = 0        #Temporary field used when parsing the data file - starting position of the current column, before its own width is added to the total positions already processed.
    startpos_after_current = 0         #Temporary field used when parsing the data file 
    output_format = None               #Sqlite3 by default
    output_file = None			       #Sqlite file (if sqlite is the RDBMS)
    datadict_file = None
    filepathobj_load_from = None       #FilePath object to allow user to select a file
    filepathobj_save_to = None         #FilePath object to allow user to select a file
    filepathobj_datadict = None        #FilePath object to allow user to select a data dictionary (for parsing text into distinct columns)
    datadict = []                      #List of columns read in from the data dictionary (if one was specified by the user)
    controls = []
    control_index = 0
    converter = None                        #Object that handles the conversion
    #conversion_func_name = None
    csv_column_headers = []                 #List of column headers in the data dictionary CSV
    title = ''							    #Title to be displayed in the Frame object
    bgcolor = 'ivory'						#Background color of the Frame widget that displays the Data Dictionary contents
    frame_width = None 
    frame_height = None
    view_object = None
    show_view = None
    btnLoadFile = None
    btnSaveToFile = None
	
    def __init__(self, parent_window, controller, db_platform=None, output_format=None, output_file=None, show_view=None, title='File converson', **kw):      #, bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height
        self.parent_window = parent_window  #parent_window is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        now = datetime.datetime.now()
        self.init_time = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + ' ' + str(now.hour).rjust(2,'0') + ':' + str(now.minute).rjust(2,'0')
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\n\n____________________________________________________________________", True, True )
        self.logobject.logit("\nIn RDBMS_Read_Export_UI_Model._init_: db_platform='%s'output_format='%s' -- and type(controller)=%s" % (db_platform, output_format, type(controller)), True, True )
        self.db_platform = db_platform
        self.output_format = output_format
        self.output_file = output_file
        self.title = title
        self.show_view = show_view
        if self.check_key_exists("bgcolor", **kw):
            self.bgcolor = kw["bgcolor"]
        if not self.bgcolor:
            self.bgcolor=gl_frame_color
        if self.check_key_exists("frame_width", **kw):
            self.frame_width = kw["frame_width"]
        if not self.frame_width:
            self.frame_width=gl_frame_width		
        if self.check_key_exists("frame_height", **kw):
            self.frame_height = kw["frame_height"]
        if not self.frame_height:
            frame_height=gl_frame_height

    def set_output_format(self, output_format):
        self.output_format = output_format
        print("\nSetting the output_format to: %s" % (output_format) )

    def display_data(self, db_platform=None, db_catalog=None):
        if db_platform is None:
            db_platform = self.db_platform
        db_platform = str(db_platform).lower().strip()
        print("\nTop of function display_data() - db_platform=%s" % (db_platform) )
        #Read the DB records into memory
        if db_platform[:6] == "sqlite":
            self.read_sqlite_data()
        #Display the DB records on screen (one batch at a time)
        if not self.error_message:
            self.display_view()
        #Write the data to a file if a file was specified
        if not self.error_message:
            if self.output_file:
                print("\n\nWriting data to text file - please wait...")
                self.write_data_to_flat_file()

    def read_sqlite_data(self):
        #try:
        if True:
            if self.db_catalog is None:
                self.error_message = "No sqlite database file was specified"
            sqlcmd = self.sql_text.get()
            if self.sql_text is None or not self.sql_text.get():
                self.error_message = "No SQL statement was specified"
            if sqlcmd.upper().strip()[:6] != "SELECT":
                self.error_message = "Only SELECT commands can be executed."
            if self.error_message:
                print("\n\nERROR: %s" % (self.error_message) )
                return
            if self.debug: print("\nAbout to call open_db_connection()")
            self.open_db_connection()
            if self.debug: print("\n Type of db_conn: %s" % (str(type(self.db_conn)) ) )
            if str(type(self.db_conn)) == "NoneType":
                self.error_message = "Failed to open database connection for : '%s'" % (self.db_platform)
            #Test - display tables in database        #self.drop_db_table("ccts_root_20140402")
            self.list_db_tables()
            cursor = self.db_conn.cursor()
            print("\n.....................................\nSQL: %s" % (self.sql_text.get()) )
            cursor.execute(self.sql_text.get())
            #COPY THE CURSOR RESULTS INTO AN ARRAY (list of lists of dicts)
            self.sql_result_simple = ""                                  #Quick read of the first row, just to verify that data was retrieved and view it on screen
            ix = 0
            print("\nResults:")
            for row in cursor:
                tuple_as_list = list(row)
                tuple_as_list.insert(0, ix) 
                print("\nTuple_as_List: %s" % (tuple_as_list) )
                self.sql_result.append(tuple_as_list)                     #Store the data to a list of lists
                #############
                #ALTERNATELY: Store the data and include column-level info (will this be useful in some cases?
                row_as_list = []              #row_as_list will hold a row number and multiple COLUMN dictionaries {colnum, colvalue}
                print("Row type: %s, len: %s, val: %s" % ( str(type(row)), len(row), row ) )
                c = 0
                for col in row:                 #ROW in a cursor is a tuple
                    if col is None:
                        #print("col: Type %s, val %s" % ( str(type(col)), col ) )
                        col = "None"
                    else:
                        #print("col: Type %s, val %s" % ( str(type(col)), col ) )
                        pass
                    typ = str(type(col)).lower().replace("<class '", "").replace("'>", "")	#Data type of this value
                    if self.datadict_file:
                        width = self.get_width_for_column_pos(c)
                        if width:
                            col = str(col)[:width].ljust(width)
                    collist = [c, typ, col]
                    row_as_list.append(collist)      #Add this column to the current row of "row_as_list" list
                    c += 1
                self.sql_result_with_column_info.append(row_as_list)
                
                #print("%s) %s %s %s %s %s" % (ix, row[0], row[1], row[2], row[3], row[4], ) ) 
                '''if ix == 0:    #Top row
                    self.sql_result_simple = str(row[0]) + " " + str(row[1])       #Display a bit of text to verify that we actually retrieved some data.
                    self.result_box.delete(0, END) 
                    self.result_box.insert(END, self.sql_result_simple)'''
                ix +=1
            self.close_db_connection()
			
            #Display the data that was stored in array (copy of cursor)			
            print("\n____________________________________")
            r = 0
            for row_as_list in self.sql_result_with_column_info: 
                print("\nARRAY ROW %s type %s... %s" % (row_as_list[0], type(row_as_list), row_as_list))			 #Row number is item[0]
                rowtext = ""
                c = 0
                for col in row_as_list:
                    print("   %s" % ( col ) )                 #COL is a list containing the column number and the column value
                    rowtext += str(col[2]) + "  "             #COL[2] is the column's value
                    c += 1
                print(rowtext)
                rownum_plus_rowtext = [r, rowtext]
                self.sql_result_as_single_string.append(rownum_plus_rowtext)
                r +=1
            if self.error_message:
                print("\n\n ERROR: %s" % (self.error_message) )
                return self.error_message
        #except:
        #    self.error_message = "Error while reading database with %s catalog %s, statement: '%s'  [%s %s %s]" % (self.db_platform, self.db_catalog, self.sql_text.get(), sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2] ) 
        #    print("\n\nERROR: %s" % (self.error_message) )
            
    def write_data_to_flat_file(self):
        #*************************************
        #Write the data values:
        #*************************************
        if not self.output_file:
            self.error_message = "No output file was specified."
            print("\n\nERROR: %s" % (self.error_message) )
            return
        self.logobject.logit("\n In RDBMS_Read_Export_UI_Model.write_data_to_flat_file()", True, True )
        self.row_index = 0				
        curvalue = ""
        print("\nLength of self.sql_result_as_single_string: %s" % (len(self.sql_result_as_single_string)) )
        with open(self.output_file, 'w') as f:
            ix = 0
            for item in self.sql_result_as_single_string:
                f.write("%s %s \n" % (item[1], ix) )
                print("Row Value: %s %s" % (item[1], ix) )
                ix += 1
            f.close()

    def open_db_connection(self):
        #try:
        if True:
            if str(self.db_platform).lower().strip()[:6] == "sqlite":
                if self.debug: print("\nAbout to open a Sqlite connection at: %s" % (self.db_catalog) )
                self.db_conn = sqlite3.connect(self.db_catalog)
                self.db_conn.text_factory = str
        #except:
        #    self.error_message = "Error while opening database connection for %s catalog %s" % (self.db_platform, self.db_catalog) + "  " + str(sys.exc_info()[0])
        #    print("\n\nERROR: %s" % (self.error_message) )

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

    def list_db_tables(self):
        #if self.db_conn is None:
        self.open_db_connection()
        with self.db_conn:
            if self.db_platform == "sqlite3":
                #cmd = "select * from sqlite_master;"
                #for row in self.db_conn.execute(cmd): 
                #    print("MASTER: %s %s %s %s %s" % ( row[0], row[1], row[2], row[3], row[4] ) )    #, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9] ) )
                cmd = "select name from sqlite_master where type = 'table';"
                if self.debug: print("\nList DB Tables in db '%s':" % (self.db_catalog) )
                for val in self.db_conn.execute(cmd): 
                    if self.debug: print("TABLE: %s" % ( row[0] ) )    #, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9] ) )
            #self.close_db_connection()
            #self.db_conn.close()


    def instantiate_view_object(self, container):
        self.view_object = RDBMS_Read_Export_UI_View(container, self) 
        return self.view_object	

    def copy_datadict_to_class_properties(self):
        datadict = DataDict_Model(self.parent_window, self.controller)   #BigMatch DataDict class
        hdr_list = datadict.load_standard_datadict_headings()    #Make sure we are using the standard, updated list of column headings for the Data Dictionary
        datadict = None                         #Erase the class instantiation when done to release memory
        #Check our assumptions about which Data Dictionary column headings are in the standard:		
        if not "column_name" in hdr_list:
            self.error_message = "Expected item 'column_name' to be in Data Dictionary header row"
        if not "start_pos" in hdr_list:
            self.error_message = "Expected item 'start_pos' to be in Data Dictionary header row"
        if not "width" in hdr_list:
            self.error_message = "Expected item 'width' to be in Data Dictionary header row"
        if self.error_message:
            print("\n \n ERROR: " + self.error_message)
        try:
            #Read the Data Dictionary and store information for each COLUMN as properties of the 
            self.logobject.logit("\nAdding columns to the dxr.DataDictionary", True, True)
            with open(self.datadict_file, 'r') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')     #, quotechar='')
                ix = 0
                for row in csvreader:
                    if ix == 0:                                 #Top row of CSV
                        self.build_column_header_list(row)
                        break
                #Ascertain the correct position within the Data Dictionary where column name, width and startpos are stored
                pos_colname = int(self.get_position_of_datadict_column("column_name"))
                pos_width = int(self.get_position_of_datadict_column("width"))
                pos_startpos = int(self.get_position_of_datadict_column("start_pos"))
                ix = 0
                for row in csvreader:
                    #NOTE: CSV reader is a forward-only reader -- and it has already read row 0, the top row.  So now the next row WILL BE ROW 1!
                    #Add this column from the data dictionary to the list of columns that will be created in the RDBMS
                    #self.logobject.logit("Dict row " + str(ix) + ": " + row[0] + " " +row[1] + " " +row[2] + " " +row[3] + " " +row[4] + " " +row[5], True, True )
                    self.add_column(ix, row[pos_colname], "char", row[pos_width], row[pos_startpos], "file")
                    ix += 1
                csvfile.close()
                print("\nDatadict:")
                for col in self.datadict:
                    print(col)
        except:
            self.controller.common.handle_error(self.error_message, False, False, "datafile_rdbms_ui")   

    def get_position_of_datadict_column(self, which_column):
        which_column = which_column.lower().strip()
        returnval = ""
        for hdr in self.csv_column_headers:
            self.logobject.logit("Seeking datadict column %s... Found: %s"  % (which_column, hdr["col_hdr"].lower().strip() ), True, True )
            if hdr["col_hdr"].lower().strip() == which_column:
                returnval = hdr["col_index"]
                break
        self.logobject.logit("Seeking datadict column '%s'... Found position: %s"  % (which_column, returnval), True, True )
        return returnval

    def add_column(self, index, name, type, width, startpos=None, datasource="file", source_func=None, validate=False, validate_func = None):
        '''Add a column to the data dictionary. Data source is normally "file" because we read the value for this column from the specified positions in the current row of the data file. But if datasource="function" then get the value by calling the specified function.'''
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
        self.datadict.append({"index":index, "name":name, "width":width , "type":type_db_specific, "startpos":startpos, "datasource":datasource, "source_func":source_func, "validate":validate, "validate_func":validate_func })
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
    
    def build_column_header_list(self, hdr_row):
        col_index = 0
        for col_hdr in hdr_row:
            col_hdr = col_hdr.strip()
            self.logobject.logit("(%s) col_hdr: %s" % (col_index, col_hdr), True, True )
            temp = {"col_index":col_index, "col_hdr":col_hdr, "max_width":0, "start_pos":0, "data_type":"", "selected":""}
            self.csv_column_headers.append(temp)
            col_index += 1

    def get_width_for_column_pos(self, col_pos):
        width = None
        for col in self.datadict:
            if col["index"] == col_pos:
                width = col["width"]
                break
        print("Width of column in pos %s: %s" % (col_pos, width) )
        return width

    def display_view(self, container=None):
        #Most often, we will display the form in the main class's BigCanvas.BigFrame "container".
        self.logobject.logit("In DataFile_RDBMS_UI.Display_View, Type of Container is '%s'" % (str(type(container))), True, True )
        kw_db = {"width":120, "background":self.bgcolor}
        if container == None:
            container = self.controller.bigcanvas.bigframe			#This is the default canvas/frame object on which all other widgets are displayed.
        if self.view_object is None:                                #We have not yet instantiated the View.  Make sure to display any Open File dialogs at top before rendering other views.
            self.instantiate_view_object(container)					#Just in case we need to run this module outside the parent frame during testing.
			#Display a file open dialog so the user can point us to the Data Dictionary they'd like to open:
            self.display_openfile_dialogs(container, self.db_catalog)
            self.display_user_buttons(container)
            #print("\n In RDBMS_Read_Export_UI_Model.display_view(), about to call view_object.initUI().")
            #Display the VIEW for this data dictionary  
            #self.view_object.initUI(**kw_db)   #width=self.frame_width, background=self.bgcolor, borderwidth=2, padx=3, pady=3)
        else:        
            print("\n In RDBMS_ReadExportUI_Model.display_view(), calling new_view_object.initUI().")
            self.view_object.initUI(**kw_db)   #DISPLAY THE DATA
            self.controller.refresh_main_canvas()

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "RDBMS_ReadExport_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.button_frame.grid(row=stackslot, column=0, sticky=W)
        self.button_frame.config(width=self.frame_width, background=self.bgcolor)
        #Text entry box for user to define their SQL SELECT statement
        lbl = Label(self.button_frame, text="SQL SELECT: ")
        lbl.config(width=20, background=self.bgcolor, font=("Arial", 10, "bold"), borderwidth=0, padx=3, pady=3)
        lbl.grid(row=0, column=1, sticky=W)
        var = StringVar()
        self.sql_text = var
        self.sql_entry_box = Entry(self.button_frame, textvariable=var)
        self.sql_entry_box.config(width=124, state=NORMAL, background='snow', borderwidth=2)
        self.sql_entry_box.grid(row=0, column=2, sticky=W)
        self.sql_entry_box.bind(sequence="<Enter>", func=self.handle_sqltext_event)
        self.sql_entry_box.bind(sequence="<Button-1>", func=self.handle_sqltext_event)
        self.sql_entry_box.bind(sequence="<FocusIn>", func=self.handle_sqltext_event)
        self.sql_entry_box.bind(sequence="<FocusOut>", func=self.handle_sqltext_event)
        #Spacer
        lblblank = Label(self.button_frame, text="        ")
        lblblank.config(width=8, background=self.bgcolor, font=("Arial", 10, "bold"), borderwidth=0, padx=3, pady=3)
        lblblank.grid(row=0, column=3, sticky=W)
        #Button to launch the conversion process:
        self.btnSaveToFile = Button(self.button_frame, text="Display data", width=30, command=self.display_data) 
        self.btnSaveToFile.grid(row=0, column=4, sticky=W)
        self.btnSaveToFile.config(state=DISABLED)       #Do not enable this button unless the user has selected a data source
        self.btnSaveToFile.config(padx=4, pady=4) 
        #Box for temp RESULT display
        '''lbl = Label(self.button_frame, text="Result: ")
        lbl.config(width=8, background=self.bgcolor, borderwidth=0, padx=3, pady=3)
        lbl.grid(row=0, column=4, sticky=W)
        var2 = StringVar()
        self.result = var2
        self.result_box = Entry(self.button_frame, textvariable=var2)
        self.result_box.config(width=20, state=NORMAL, background='snow', borderwidth=2)
        self.result_box.grid(row=0, column=5, sticky=W)'''

    def handle_sqltext_event(self, parm=None):		
        print("\n SQL textbox stringvar: %s, stringvar value: %s ... %s '%s'" % (self.sql_text, self.sql_text.get(), parm, parm.widget) )
        self.enable_disable_buttons()

    def enable_disable_buttons(self):
        if self.db_catalog:
            if self.sql_text is not None and self.sql_text.get():
                print("\nENABLING SAVE BUTTON")
                self.btnSaveToFile.config(state=NORMAL)
            else:
                self.btnSaveToFile.config(state=DISABLED)
        else:
            self.btnSaveToFile.config(state=DISABLED)

    def display_openfile_dialogs(self, container, default_filepath=''):
        file_types = [('All files', '*'), ('DB files', '*.db;')]
        kw_fpath = {"bgcolor":self.bgcolor, "frame_width":"", "frame_height":"", "file_category":"datadict"}
        open_or_save_as = "open"
        self.filepathobj_load_from = FilePath_Model(self.parent_window, self, self.controller, "Sqlite .DB file:", open_or_save_as, "DbCatalogToLoad", file_types, **kw_fpath)
        self.filepathobj_load_from.display_view(container)	        #Display the dialog for user to select a data dict file
        file_types = [('All files', '*'), ('DB files', '*.db;')]
        open_or_save_as = "save_as"
        self.filepathobj_save_to = FilePath_Model(self.parent_window, self, self.controller, "File to save as (if exporting):", open_or_save_as, "OutputSaveAs", file_types, **kw_fpath)
        self.filepathobj_save_to.display_view(container)	        #Display the dialog for user to Save As... a new data dict file
        open_or_save_as = "open"
        self.filepathobj_datadict = FilePath_Model(self.parent_window, self, self.controller, "Data dictionary (if exporting):", open_or_save_as, "DatadictToLoad", file_types, **kw_fpath)
        self.filepathobj_datadict.display_view(container)            #Display the Open File dialog
		
    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        '''IMPORTANT: ALL FilePath objects created by this class will expect Function "update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        #self.logobject.logit("Master DataDict_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string), True, True )
        print("Master RDBMS_Read_Export_UI_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string))
        if callback_string.lower().strip()[:4] == "load" or callback_string.lower().strip()[:4] == "open":
            if str(callback_string).lower()[4:].find("datadict") != -1:      #User selected a DataDictionary file
                self.logobject.logit("datadict_file is being set to %s" % (file_name_with_path), True, True )
                self.datadict_file = file_name_with_path        #file_name_with_path is the name/path of the file selected by the user. We know to store this to self.db_catalog because of the "callback string" returned by the FilePath object.
                if self.datadict_file:                          #Refresh the view when the user selects a new file.
                    self.copy_datadict_to_class_properties()    #Copy the data dictionary into a globally accessible list
                    self.display_view()
                else:                                           #No file was specified (user might have cleared out a previously selected file name) 
                    self.view_object.clear_grid()      #Remove all existing values from the grid
            else:                                               #User selected the DB Source Catalog
                self.db_catalog = file_name_with_path           #file_name_with_path is the name/path of the file selected by the user. We know to store this to self.db_catalog because of the "callback string" returned by the FilePath object.
                if self.db_catalog:                             #Refresh the view when the user selects a new file.
                    self.display_view()
                else:                                           #No file was specified (user might have cleared out a previously selected file name) 
                    self.view_object.clear_grid()      #Remove all existing values from the grid
        elif callback_string.lower().strip()[:4] == "save":     #This is a file SAVE AS, not a FILE OPEN
            self.output_file = file_name_with_path
        self.enable_disable_buttons()
        self.update_master_paths(file_name_with_path)
        self.update_initial_dir_for_file_open_dialogs()

    def update_master_paths(self, file_name_with_path):
        if file_name_with_path:
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head
            self.controller.datadict_dir_last_opened = head                   #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
        print("\n Controller-saved paths-- LastDir: %s, LastDataDictDir: %s, LastRecDatadict: %s, LastMemDatadict: %s" % (self.controller.dir_last_opened, self.controller.datadict_dir_last_opened, self.controller.rec_datadict_last_opened, self.controller.mem_datadict_last_opened) )
		
    def update_initial_dir_for_file_open_dialogs(self):
        '''In addition to tracking "last file opened" at the main controller level, we also want to notify every FilePath object when the user has opened a new file, so that they can adjust thir Initial DIr properties to the location just opened.'''
        self.filepathobj_load_from.calc_initial_dir_for_file_open(self.db_catalog, "datadict", "")
        self.filepathobj_save_to.calc_initial_dir_for_file_open(self.output_file, "datadict", "")
        self.filepathobj_datadict.calc_initial_dir_for_file_open(self.datadict_file, "datadict", "")

    def add_control_to_list(self, object, var, **kw):
        control = Control(self, object, var, self.control_index, **kw)
        self.controls.append(control)            #self.controls is a list of the screen controls, which can be traversed after user has finished.
        self.control_index += 1
     
    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found


#******************************************************************************************
class RDBMS_Read_Export_UI_View(Frame):
    debug = True
    container = None
    #controller = None
    model = None
    entry_grid = None
    widgetstack_counter = None
    bgcolors = []
    bgcolor = None	
    row_index = 0
    rowtype = None	
    show_view = None
    start_row = 0
    rows_to_display = 30
    grid_initialized = False

    def __init__(self, container, model):
        Frame.__init__(self, container)
        self.container = container
        self.model = model		
        #self.controller = controller
        #ONLY ONCE AT INIT, display a blank list for now, knowing that it will be overwritten based on user actions.
        show_grid = False		
        #kw_grid = {"width":16}                            #Width of each grid cell 
        #self.entry_grid = EntryGrid(self, self.model.meta_columns, self.model.meta_rownums, self.model.meta_values, show_grid, **kw_grid)
        #Display the frame:
        print("\n" + "In RDBMS_Read_Export_UI_View._init_, db_catalog = '" + str(self.model.db_catalog) + "' -- and show_view=" + str(self.model.show_view) )
        if self.model.show_view:
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the parent window, directly below any previous frames. The grid() ROW designators refer to the parent window's Grid and determine which order the Frames will be displayed in.
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "RDBMS_Read_Export_UI_View.initUI()")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=W)                    #position the Frame within the Parent Window
        #self.config(width=self.model.frame_width, background=self.model.bgcolor, borderwidth=2, padx=3, pady=3)   #height=self.frame_height, 
        self.config(kw)
        for i in range(0,12):
            self.columnconfigure(i, weight=1, pad=3)
        for i in range(0,12):
            self.rowconfigure(i, pad=3)

        #*************************************************************************************
        self.display_data_simple(**kw)
        #*************************************************************************************

    def display_data_simple(self, start_row=None, **kw):
        #*************************************
        #Display the data values:
        #*************************************
        if start_row is not None:                     #We display only a small batch of rows at a time. Batch is defined by StartRow and Rows_to_Display
            self.start_row = start_row
        if self.start_row is None:
            self.start_row = 0
        self.model.logobject.logit("\n In RDBMS_Read_Export_UI_View.display_data_simple(), start_row=%s and rows_to_display is %s" % (self.start_row, self.rows_to_display), True, True )
        self.row_index = 0				
        curvalue = 0 
        data_column_name = ""
        chk_kw = {"width":6, "borderwidth":1, "font_size":11, "rowindex":self.row_index}
        kw_txtbox = {"width":20, "background":self.bgcolor, "foreground":"black", "borderwidth":1, "font":("Arial", 10, "normal")}  #, "data_column_name":data_column_name, "text":data_column_name}
        vert_position = self.get_widgetstack_counter()
        self.rowtype = "dataset_view"         
        ix = 0                               #index of the current row
        countrow = 0                         #count the number of rows displayed (differs from ix in some apps, but in this case they seem to be the same thing)
        bgcolor = "black"		
        print("\nLength of self.model.sql_result_as_single_string: %s" % (len(self.model.sql_result_as_single_string)) )
        ix = 0
        for item in self.model.sql_result_as_single_string:
            if ix >= self.start_row and countrow <= self.rows_to_display:        #We display only one batch at a time (batch is defined by StartRow and Rows_to_Display)
                self.data_rowid = item[0]
                self.model.logobject.logit("\nRow %s is between %s and %s so it will be displayed. data_rowid=%s" % (ix, self.start_row, int(self.start_row) + int(self.rows_to_display), self.data_rowid ), True, True )
                print("\nRow %s is between %s and %s so it will be displayed. data_rowid=%s" % (ix, self.start_row, int(self.start_row) + int(self.rows_to_display), self.data_rowid ) )
                vert_position = self.get_widgetstack_counter()
                label_text = ""
                #(1) Text box to display the row number
                gridcolumn = 0
                kw_txtbox["width"] = 4
                kw_txtbox["foreground"] = "blue"
                curvalue = str(ix)                    #Row number in the list (index)
                control_name = "ix_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                #(2) Record file match values:
                gridcolumn = 2
                kw_txtbox["width"] = 120
                kw_txtbox["foreground"] = "black"
                kw_txtbox["disabledforeground"] = "black"
                curvalue = str(item[1]) 
                print("Row Value: %s" % (curvalue) )
                control_name = "data_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                countrow += 1
                ix += 1
        self.grid_initialized = True
        self.container.refresh_canvas()

    #***********************************************************************************************************************************
    def create_textbox(self, label_text, gridrow, gridcolumn, curvalue='', textbox_name='txt_unknown', data_column_name='', rowtype='unknown', **kw):       #gridcolumn=0, width=12, font_size=12, rowindex=0
        #print("Displaying textbox '%s' with value %s" % (label_text, curvalue) )
        if(label_text):                                         #Optionally, display a label to the left of the textbox
            lbl = Label(self, text=label_text)
            lbl.grid(row=gridrow, column=gridcolumn, sticky=EW) 
            lbl.configure(background=self.bgcolor, font=("Arial", 10, "bold"), width=20)
            gridcolumn +=1    #If a label is specified, it occupies the grid column specified by the "gridcolumn" parameter -- so we must bump the actual text box over by one.
        var = StringVar(self)
        var.set(curvalue)
        entry = Entry(self, textvariable=var)
        entry.grid(row=gridrow, column=gridcolumn, sticky=EW)
        entry.configure(**kw)
        #Add this control to the controls collection:		
        self.model.add_control_to_list(entry, var, ref_name=textbox_name, row_index=self.row_index, row=gridrow, col=gridcolumn, control_type="textbox", data_rowid=self.data_rowid)

    def get_widgetstack_counter(self, who_called=''):
        if(self.widgetstack_counter == None):
            self.widgetstack_counter = 0
        else:  
            self.widgetstack_counter += 1
        #print("\n" + "widgetstack_counter: " + str(self.widgetstack_counter) + "  " + who_called )
        return self.widgetstack_counter


    #***********************************************************************************************************************************
    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        #self.model.logobject.logit("Master RDBMS_Read_Export_UI_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string), True, True )
        print("Master RDBMS_Read_Export_UI_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string))
        self.db_catalog = file_name_with_path

		
#******************************************************************************************		
#******************************************************************************************		
class Control():
    model = None           #Model object
    object = None          #The Tkinter object (textbox, checkbox, etc.)
    value_object = None    #A Tkinter StringVar() variable which holds the value of this object.
    value = None           #Actual string value, accessed as StringVar().get()
    row = None             #Position in the grid
    col = None             #Position in the grid 
    blocking_pass = None   #
    row_index = None       #
    control_index = None   #
    ref_name = None        #
    control_type = None    #
    meta_rowid = None      #meta_rowid corresponds to the 5th column in self.meta_values. See function split_result_file() above.

    def __init__(self, model, object, var, control_index, **kw):
        self.model = model       #MatchView Model object
        self.object = object     #Tkinter object
        self.value_object = var  #StringVar() object that holds the value of the Tkinter object
        self.control_index = control_index
        if self.model.check_key_exists("value", **kw):
            self.value = kw["value"]
        if self.model.check_key_exists("row", **kw):
            self.row = kw["row"]
        if self.model.check_key_exists("col", **kw):
            self.col = kw["col"]
        if self.model.check_key_exists("control_type", **kw):
            self.control_type = kw["control_type"]
        if self.model.check_key_exists("row_index", **kw):
            self.row_index = kw["row_index"]
        if self.model.check_key_exists("ref_name", **kw):
            self.ref_name = kw["ref_name"]
        if self.model.check_key_exists("blocking_pass", **kw):
            self.blocking_pass = kw["blocking_pass"]
        if self.model.check_key_exists("meta_rowid", **kw):
            self.meta_rowid = kw["meta_rowid"]



#******************************************************************************************		
def main():
    root = Tk()
    root.geometry("900x600+100+100")
    master = BigMatchController(root)
    root.mainloop()

if __name__ == '__main__':
    main()  
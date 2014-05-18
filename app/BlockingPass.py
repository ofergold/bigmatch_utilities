#!C:\Python33\python.exe -u
#!/usr/bin/env python
'''http://stackoverflow.com/questions/16429716/opening-file-tkinter '''
''' python c:\greg\code\python\Gms_TkFileSystem5_try_button.py '''  
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import *     #showerror
import os
import csv
import datetime, time, sched
from FilePath import *
from BigMatchParmFile import *
from CHLog import *

gl_frame_color = "ivory"
gl_frame_width = 500
gl_frame_height = 100

#******************************************************************************
class BlockingPass_Model():
    debug = False
    error_message = None
    parent_window = None                    #Parent_wiondow is the TKinter object itself (often known as "root"
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    title = None
    bgcolor = None
    bgcolors = []
    frame_width = None
    frame_height = None
    dedupe_single_file = False              #Is this a dedupe of a single file, or a match of two different files?
    #parmf_file = None
    datadict_recfile = None					#Data dictionary file name and path
    datadict_memfile = None					#Data dictionary file name and path
    bigmatch_parmf_file_to_load = None      #BigMatch "parmf.txt" parameter file; Blocking Pass information will be LOADED FROM this file (if specified--this is optional).
    bigmatch_parmf_file_to_save = None      #BigMatch "parmf.txt" parameter file; Blocking Pass information will be SAVED TO this file.
    parmfileobj = None	                    #An instance of the BigmatchParmfile() class, which reads the ParmF.txt parameter file
    filepathobj_recfile = None              #Instance of the FilePath_Model class, controlling the selection of self.datadict_recfile
    filepathobj_memfile = None              #Instance of the FilePath_Model class, controlling the selection of self.datadict_memfile
    filepathobj_parmfile_to_load = None        #Instance of the FilePath_Model class, controlling the selection of bigmatch_parmf_file_to_load
    filepathobj_parmfile_to_save = None        #Instance of the FilePath_Model class, controlling the selection of bigmatch_parmf_file_to_save
    meta_columns_recfile = []
    meta_columns_memfile = []
    meta_values_recfile = []
    meta_values_memfile = []	
    recfile_datadict_rowcount = 0
    memfile_datadict_rowcount = 0
    compare_methods = []                    #List of valid BigMatch comparison methods for a blocking run field pair.
    how_many_passes = 10                    #Number of Blocking Passes to display entry screens for.
    blocking_passes = None                  #blocking_passes is a list of dicts, used in writing the user's Blocking Pass attributes to a Parmf.txt parameter file.  Dict example: {"index":index, "count_blocking_fields":count_blocking_fields, "count_matching_fields":count_matching_fields}
    blockingpass_views = []                 #blockingpass_views is a list of Tkinter frame objects. This is useful for hiding them when the user reloads a new set of BlockingPass screens after selecting a different DataDict or Parameter file.
    blkpass_views_have_been_displayed =None #Flag to trap the event of a user displaying the blocking passes. This enables the "Save blocking pass info" button.	
    controls = []                           #self.controls is a list of the screen controls, which can be traversed after user has finished entering information
    controlrow_temp = {}                    #The self.controlrow_temp dict is used to temporarily assemble various controls into a single logical ROW. It will be EMPTY sometimes, if user did not select anything for a given blocking pass.
    control_index = 0                       #Counter or index of controls that have been added to the controls list
    cutoff_values = []                      #Four "Cutoff values" must be written to the ParmF.txt parameter file for EACH blocking pass. They appear after all blocking and matching fields are displayed.
    parmf_rows = []
    pass_index = None                       #Which blocking pass are we currently scanning?    
    include_this_pass = False
    include_this_row = False
    fieldname_col_in_recfile_dict = None    #Which column in the RECFILE data dictionary stores FIELDNAME?  
    startpos_col_in_recfile_dict = None
    width_col_in_recfile_dict = None
    uniqid_col_in_recfile_dict = None
    fieldname_col_in_memfile_dict = None
    startpos_col_in_memfile_dict = None
    width_col_in_memfile_dict = None
    uniqid_col_in_memfile_dict = None
    default_hi_cutoff = 100
    default_lo_cutoff = 0
    default_hi_prcutoff = 100
    default_lo_prcutoff = 0
    default_u_value = 10
    default_m_value = 90  
    recfile_record_length = 880
    memfile_record_length = 880
    widget_registry = []
    hold_time = None

    def __init__(self, parent_window, controller, title="Blocking pass", bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height):	
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        now = datetime.datetime.now()
        self.init_time = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + ' ' + str(now.hour).rjust(2,'0') + ':' + str(now.minute).rjust(2,'0')
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\n\n____________________________________________________________________", True, True )
        self.logobject.logit("%s In BlockingPass_Model._init_: title=%s" % (self.init_time, title), True, True )
        if title is not None:
            self.title = title
        else:
            self.title = "Nothing"		
        if frame_width is not None:
            self.frame_width = frame_width
        if frame_height is not None:
            self.frame_height = frame_height
        #if show_view is not None:
        #    self.show_view = show_view
        if bgcolor is not None:
            self.bgcolor = bgcolor
        else:
            self.bgcolor = gl_frame_color
        #self.bgcolors = ["#FDFFDF", "#F1FFDF", "#E4FFDF", "#DFFFE7", "#DFFFF0", "#DFFFFC", "#DFF6FF", "#DFEBFF", "#DFDFFF"]
        self.bgcolors = ["#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0"]
        #Load up the options for comparing match fields:
        self.load_compare_methods()
        #Read data dictionary file into Arrays:
        #self.datadict_recfile = os.path.join("c:\\", "greg", "code", "bigmatch_utilities", "BigMatchGUI", "recfile.dict.csv")
        #self.datadict_memfile = os.path.join("c:\\", "greg", "code", "bigmatch_utilities", "BigMatchGUI", "memfile.dict.csv")
        if self.error_message is not None:
            #self.error_message = "Crucial metadata not located"
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
            return

    def load_compare_methods(self):
        '''Bigmatch allows users to select from a predefined list of comparison algorithms for each pair of matching fields '''
        self.compare_methods.append("")
        self.compare_methods.append("c (exact string comparison)")
        self.compare_methods.append("ci (inverted string comparison)")
        self.compare_methods.append("uo (string comparison w/variation)")
        self.compare_methods.append("uoi (inverted string comparison w/var)")
        self.compare_methods.append("p (numeric comparison for age)")
        self.compare_methods.append("y (numeric comparison for year)")
        self.compare_methods.append("q (strict numeric for year/age)")
        self.compare_methods.append("s street name comparison")

    def get_compare_method_from_abbrev(self, abbrev):
        '''Display the full name of the Bigmatch comparison method, not the abbreviation '''
        return_value = ''
        abbrev = str(abbrev).lower().strip()
        for text in self.compare_methods:
            if str(text[:3]).replace("(", "").lower().strip() == abbrev:
                return_value = text
        return return_value
        
    def read_datadict_file_into_arrays(self, file_name, mem_or_rec): 
        self.logobject.logit("\nIn read_datadict_file_into_arrays, datadict_file_name = '" + str(file_name) + "'", True, True, True)
        if mem_or_rec == "rec":
            self.meta_values_recfile = []
            self.meta_columns_recfile = []
        elif mem_or_rec == "mem": 
            self.meta_values_memfile = []
            self.meta_columns_memfile = []
        f = open(file_name, "r")
        content = f.readlines()
        if mem_or_rec == "rec":
            self.recfile_datadict_rowcount = 0
        elif mem_or_rec == "mem":
            self.memfile_datadict_rowcount = 0
        i = 0
        for line in content:
            #self.logobject.logit("Type of Line: %s" % (str(type(line))), True, True )           #Debug--display this row from the data dictionary
            line = line.replace("\n", "")     #Remove linefeed characters
            if not line:                      #Blank row in the file
                continue
            if self.debug: self.logobject.logit(line, True, True)                       #Debug--display this row from the data dictionary
            if(i==0):                         #Header row in the CSV file
                if mem_or_rec == "rec":
                    self.meta_columns_recfile = line.split(",")
                elif mem_or_rec == "mem": 
                    self.meta_columns_memfile = line.split(",")
                #TO DO: Find out which column number associated with "Column_Name".  For now, assume it is Column[0].
            else:
                meta_temp = line.split(",")				            #meta_temp is a LIST consisting of one row from the data dictionary
                print("meta_values row: " + str(meta_temp) )
                if mem_or_rec == "rec":
                    self.meta_values_recfile.append(meta_temp)		#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
                elif mem_or_rec == "mem": 
                    self.meta_values_memfile.append(meta_temp)		#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
            i += 1
        if mem_or_rec == "rec":
            self.recfile_datadict_rowcount = i
        elif mem_or_rec == "mem": 
            self.memfile_datadict_rowcount = i
        f.close()

    def get_datacolumn_pos_from_datadict(self, column_name, mem_or_rec):
        '''Unlike locate_crucial_datadict_columns(), this method ITERATIVELY retrieves the starting position and width for a NAMED DATA COLUMN, such as "Lastname". 
        This is important when creating the ParmF.txt parameter file. When the user selects a data column for inclusion as a Blocking or Matching field, we need to write the startpos and width directly into ParmF.txt. '''		
        column_name = str(column_name).lower()
        fieldname = width = startpos = None		
        column_attribs = {}											#This dict will be returned to the caller, and contains Width and Startpos metadata for the requested Data Column.
        meta_values = []									    #meta_values is an abstraction that can point to either self.meta_values_RECfile or self.meta_values_MEMfile
        if mem_or_rec == "rec":
            meta_values = self.meta_values_recfile		#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
        elif mem_or_rec == "mem": 
            meta_values = self.meta_values_memfile    	#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
        if self.debug: self.logobject.logit("\n In get_datacolumn_pos(), type of meta_values is: '%s', SEEKING column_name='%s' ... mem_or_rec=%s" % ( str(type(meta_values)), column_name, mem_or_rec), True, True, True )
        #Traverse rows and columns of the Data Dictionary array until we locate the requested row (which represents a Data Column in the Data File)
        row_index = 0
        requested_row = None
        for row in meta_values:
            column_index = 0
            for cell in row:
                #print("Row (" + str(row_index) + ") col (" + str(column_index) + "): " + str(cell) )
                #When the Requested Row is found ("column_name" cell in the DataDict matches the requested "column_name" parameter), the Column loop exits, and the Row loop can now exit too.
                if mem_or_rec == "rec":
                    fieldname = str(row[self.fieldname_col_in_recfile_dict]).lower()
                elif mem_or_rec == "mem":
                    fieldname = str(row[self.fieldname_col_in_memfile_dict]).lower()
                if fieldname == column_name:
                    requested_row = row
                    if mem_or_rec == "rec":
                        startpos = str(row[self.startpos_col_in_recfile_dict]).lower()
                        width = str(row[self.width_col_in_recfile_dict]).lower()
                    elif mem_or_rec == "mem":
                        startpos = str(row[self.startpos_col_in_memfile_dict])
                        width = str(row[self.width_col_in_memfile_dict])
                    print("FOUND Requested field: %s, startpos: %s, width: %s" % (column_name, startpos, width) )
                    break
                column_index += 1 
            if requested_row is not None:
                column_attribs["startpos"] = startpos
                column_attribs["width"] = width
                break
            row_index += 1
        return column_attribs

    def locate_crucial_datadict_columns(self, mem_or_rec):
        '''This method is a one-time utility to identify the Column Index (within each row of a Data Dictionary) of a few crucial metadata points:  Field Name, Starting Position and Field Width.
		This method is called once for the Record File data dict and once for the Memory File data dict, since their column structures could be quite different.
        It answers the one-time question, "At what column in the Data Dictionary can we find the "Startpos" metadata?  Or the "Width" metadata?
		The end product of this method is population of self.fieldname_col_in_recfile_dict, self.startpos_col_in_recfile_dict, self.width_col_in_recfile_dict, and the corresponding MemFile elements.'''
        success = False		
        mem_or_rec = mem_or_rec.lower()		
        column_pos = {}
        datadict_file = None
        if mem_or_rec == "mem":
            datadict_file = self.datadict_memfile
        elif mem_or_rec == "rec":
            datadict_file = self.datadict_recfile
        if datadict_file is None:
            print("\n Error: datadict_file is None (locate_crucial_datadict_columns()")
        else:
            #print("In locate_crucial_datadict_columns(), mem_or_rec=%s ... datadict_file=%s" % (mem_or_rec, datadict_file) )
            #Traverse rows and columns of the Data Dictionary until we locate the requested row (which represents a Data Column in the Data File)
            with open(datadict_file, 'rt') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',') 
                row_index = 0
                column_index = 0
                colname_column = None
                startpos_column = None
                width_column = None
                uniqid_column = None
                for row in csvreader:
                    if(row_index == 0):       #Top (header) row in the Data Dictionary CSV
                        if self.debug: self.logobject.logit("*****locate_crucial_datadict_columns(): row[0] = " + str(row[0]) + " mem_or_rec: " + mem_or_rec + "***", True, True)
                        column_index = 0
                        for cell in row:
                            #print("Row (" + str(row_index) + ") col (" + str(column_index) + "): " + str(cell) )
                            if(row_index == 0):   #Top (header) row in the Data Dictionary CSV
                                if str(cell).lower() == "column_name" or str(cell).lower() == "columnname":
                                    colname_column = column_index
                                    print("colname_column = %s" % (column_index) )
                                elif str(cell).lower() == "start_pos":
                                    startpos_column = column_index
                                    print("startpos_column = %s" % (column_index) )
                                elif str(cell).lower() == "width":
                                    width_column = column_index
                                    print("width_column = %s" % (column_index) )
                                elif str(cell).lower() == "unique_id" or str(cell).lower() == "unique_id_yn" or str(cell).lower() == "seq_yn":
                                    uniqid_column = column_index
                                    print("unique_id_column = %s" % (column_index) )
                            column_index += 1
                    break         #Automatically break after the first ROW in the file, which is the header row in the Data Dictionary CSV
                if mem_or_rec == "mem":
                    self.logobject.logit("Populating Crucial Metadata Properties for the MEM file.", True, True)
                    self.fieldname_col_in_memfile_dict = colname_column
                    self.startpos_col_in_memfile_dict = startpos_column
                    self.width_col_in_memfile_dict = width_column
                    self.uniqid_col_in_memfile_dict = uniqid_column
                elif mem_or_rec == "rec":
                    self.logobject.logit("Populating Crucial Metadata Properties for the REC file.", True, True)
                    self.fieldname_col_in_recfile_dict = colname_column
                    self.startpos_col_in_recfile_dict = startpos_column
                    self.width_col_in_recfile_dict = width_column
                    self.uniqid_col_in_recfile_dict = uniqid_column
                if self.debug: self.logobject.logit("\n mem_or_rec: %s. colname_column: %s, startpos_column: %s, width_column: %s, uniqid_column: %s" % (mem_or_rec, colname_column, startpos_column, width_column, uniqid_column), True, True, True )
                self.logobject.logit("\n mem_or_rec: %s. colname_column: %s, startpos_column: %s, width_column: %s, uniqid_column: %s" % (mem_or_rec, colname_column, startpos_column, width_column, uniqid_column), True, True )
                if mem_or_rec == "mem":
                    if self.fieldname_col_in_memfile_dict is not None and self.startpos_col_in_memfile_dict is not None and self.width_col_in_memfile_dict is not None and self.uniqid_col_in_memfile_dict is not None:
                        success = True
                    else:
                        self.error_message = "fieldname_col_in_memfile_dict or a related property was not successfully populated."
                elif mem_or_rec == "rec":
                    if self.fieldname_col_in_recfile_dict is not None and self.startpos_col_in_recfile_dict is not None and self.width_col_in_recfile_dict is not None and self.uniqid_col_in_recfile_dict is not None:
                        success = True
                    else:
                        self.error_message = "fieldname_col_in_recfile_dict or a related property was not successfully populated."
                if self.error_message is not None:
                    self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
                    self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
                    return False
        return success

    def locate_sequence_column(self, mem_or_rec):
        '''This method is a one-time utility to identify to discover the width and starting position of the data file's SEQUENCE column (auto-increment identifier column).  
        We need to consult the Data Dictionary for this data file to determine which column name corresponds to the Sequence Column, and then get that column's width/pos by executing the function "get_datacolumn_pos_from_datadict()". '''
        success = False		
        mem_or_rec = mem_or_rec.lower()	
        datadict_file = None
        uniqid_column = None
        fieldname_column = None
        sequence_column_name = None
        col_attribs = None
        if mem_or_rec.lower() == "mem":
            datadict_file = self.datadict_memfile
            uniqid_column = self.uniqid_col_in_memfile_dict
            fieldname_column = self.fieldname_col_in_memfile_dict
        elif mem_or_rec.lower() == "rec":
            datadict_file = self.datadict_recfile
            uniqid_column = self.uniqid_col_in_recfile_dict
            fieldname_column = self.fieldname_col_in_recfile_dict
        if datadict_file is None:
            self.error_message = "datadict_file is None (locate_sequence_column()"
        elif uniqid_column is None:
            self.error_message = "uniqid_column is None (locate_sequence_column()"
        else:
            self.logobject.logit("\n In locate_sequence_column(), mem_or_rec=%s ... datadict_file=%s, UniqId column in DataDict is %s, Fieldname column in datadict is %s" % (mem_or_rec, datadict_file, str(uniqid_column), str(fieldname_column) ), True, True )
            #Traverse rows and columns of the Data Dictionary until we locate the requested row (which represents a Data Column in the Data File)
            with open(datadict_file, 'rt') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',') 
                row_index = 0
                for row in csvreader:
                    if self.debug: self.logobject.logit("Row length: %s" % (len(row) ), True, True)
                    if len(row) == 1:             
                        if str(row[0]) == "\n":            #blank row has just newline feed 
                            row[0] = row[0].replace("\n", "")
                    if not row or len(row) == 0:            
                        continue
                    print("Value in column %s is: %s" % (uniqid_column, str(row[uniqid_column]).lower()) )
                    if str(row[uniqid_column]).lower().strip() == 'y' or str(row[uniqid_column]).lower().strip() == 't' or str(row[uniqid_column]).strip() == '1':       #For each row in the Data Dictionary, check the column that has been previously identified as the uniqidM column in the Data Dictionary, where user types "Y" to indicate that this field is the data file's SEQUENCE COLUMN.
                        sequence_column_name = str(row[fieldname_column])         #fieldname_column was previously identified as the Data Dictionary column that stores "Column_name" (normally column 0, the first column in the Data Dictionary CSV file)
                        break         #Automatically break after the first ROW in the file
                #Get starting position and column width in the DATA FILE of the Sequence column (starting pos and width should be specified in the data dictionary)
                if sequence_column_name is not None:
                    col_attribs = self.get_datacolumn_pos_from_datadict(sequence_column_name, mem_or_rec)
                print("\n In locate_sequence_column() AFTER get_datacolumn_pos_from_datadict(), sequence_column_name=%s ... datadict_file=%s, uniqid column in DataDict is %s, Fieldname column in datadict is %s" % (mem_or_rec, datadict_file, str(uniqid_column), str(fieldname_column) ) )
                if col_attribs is None:
                    self.error_message = "col_attribs is None (locate_sequence_column()"
                elif sequence_column_name is None:
                    self.error_message = "sequence_column_name is None (locate_sequence_column()"
                else: 
                    col_attribs["sequence_column_name"]	= sequence_column_name			
                    #print("col_attribs for Sequence column in data file:")
                    #for key,value in col_attribs.items():
                    #    print("%s = %s" % (str(key), str(value) ) )
        if sequence_column_name is None:
            self.error_message = "No unique ID field was flagged in data dictionary file '" + str(datadict_file) + "'"
        if self.error_message is not None:
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
            return
        return col_attribs

    #************************************************************************************************
    #Tracking of user controls, which provide values for output written to ParmF.txt parameter file.
    #************************************************************************************************
    def display_control_values(self):
        for control in self.controls:
            varname = control.value_object
            value = control.value
            control.display_properties()
            print("CONTROL: " + str(control.blocking_pass) + " " + str(control.row_index) + " " + str(control.control_index) + " " + str(control.ref_name)  + " " + str(control.field_name) + " ROWTYPE: " + str(control.row_type) + " " + str(control.startpos_recfile) + " " + str(control.width_recfile) + " " + str(control.startpos_memfile) + " " + str(control.width_memfile)  + " " + str(varname) + " " + str(value))
            #for key, value in item.items():
                #print(key + " = " + str(value))
                #print(value)

    def display_parmf_values(self):
        print("############ PARMF.TXT ROWS #############################")
        for item in self.parmf_rows:
            #print(item)
            print(str(item["recfile_column"]).lower() + " " + str(item["recfile_startpos"]) + " " + str(item["recfile_width"]) + " " + str(item["memfile_startpos"]) + " " + str(item["memfile_width"]) + " " + str(item["blank_flag"]) )
	
    def trigger_pathf_assembly(self):
        #******************************************
        self.assemble_pathf_elements()
        #******************************************

    def add_control_to_list(self, var, **kw):
        #Before writing the ParmF information to this array, retrieve column-position information from the Data Dictionaries (both recfile and memfile): 
        control = Control(var, self.control_index, **kw)
        self.controls.append(control)        #self.controls is a list of the screen controls, which can be traversed after user has finished.
        self.control_index += 1

    def assemble_pathf_elements(self):
        '''Read information from the user's inputs and store it in an array.  This will be used to write out a ParmF.txt parameter file. '''	
        success = True
        self.include_this_pass = False
        self.include_this_row = False
        hold_pass = None
        hold_rowindex = 0
        self.parmf_rows = []                        #Clear out any leftover elements form this List (user might click "write to parm file" multiple times)
        self.controlrow_temp = {}	                #controlrow_temp dictionary temporarily holds a series of controls that will be written as a single row to the ParmF file.  They also probably appear as a distinct row on screen, but we do not assume that -- each control is added to self.controls as a distinct atomic unit.
        for control in self.controls:
            #if self.controlrow_temp:                #The self.controlrow_temp dict will be EMPTY sometimes, if user did not select anything for a given blocking pass.
            #    print("_________Current CONTROL row, at top of loop: " )
            #    print(self.controlrow_temp)
            blockpass = control.blocking_pass
            rowindex = control.row_index
            if blockpass != hold_pass:
                #We have encountered a NEW Blocking Pass.  Copy the current row of controls into ParmF_Rows, a list that will be used to write a new ParmF.txt parameter file.
                print("\n NEW PASS (index %s)--currently, include_this_pass=%s" % (self.pass_index, self.include_this_pass) )
                if self.include_this_pass == True and self.controlrow_temp:                  #The self.controlrow_temp dict will be EMPTY sometimes, if user did not select anything for a given blocking pass.
                    self.parmf_rows.append(self.controlrow_temp.copy())
                    print("\n NEW PASS: Just added temp dict to parmf_rows. Parmf_rows now appears like this:")
                    #print(self.parmf_rows)
                #if hold_pass is not None and self.include_this_pass == True:       #This is not the first pass, so we can display the PREVIOUS pass for debugging purposes.
                #    print("\n ASSEMBLED ROW after blocking pass %s has been scanned:" % (str(hold_pass)))
                #    print(self.controlrow_temp)
                #    print("\n parmf_rows so far, after blocking pass %s has been scanned:" % (str(hold_pass)))
                #    print(self.parmf_rows)	#self.display_parmf_values
                #Prep for the next blocking pass:
                self.controlrow_temp.clear()
                self.include_this_pass = False
                self.include_this_row = False					#Include only the rows where the main checkbox has been checked by the user, indicating they wish to include this row of controls in the ParmF.txt parameter file (OR this row is an oddball such as Cutoff Values row).
                hold_rowindex = 0
                hold_pass = blockpass
                if self.pass_index is None:
                    self.pass_index = 0
                else:
                    self.pass_index += 1
                print("\n At top of new pass, checking to see whether this row was flagged to be included: %s" % (str(control.control_index)) )
                #If this is the 1st control for this row, check to see whether the user has checked the row to be included.  If so, then ALL controls in this row must be included.
                self.include_this_row = self.add_control_to_pathf_row(control)    
                if self.include_this_row:            #If user checked the main checkbox for this data field (or if this is an oddball row such as cutoff values) then INCLUDE THE ROW IN THE PARMF.TXT PARAMETER FILE.
                    self.include_this_pass = True        #If any row in this Blocking pass was selected by the user, then write this BLOCKING PASS to the ParmF.txt parameter file.
            elif blockpass == hold_pass and rowindex != hold_rowindex:          #Encountered a new row within the same blocking pass.
                #We have encountered a NEW ROW of controls.  Copy the current row of controls into ParmF_Rows, a list that will be used to write a new ParmF.txt parameter file.
                self.include_this_row = False					#Include only the rows where the main checkbox has been checked by the user, indicating they wish to include this row of controls in the ParmF.txt parameter file (OR this row is an oddball such as Cutoff Values row).
                if self.controlrow_temp:                    #The self.controlrow_temp dict will be EMPTY sometimes, if user did not select anything for a given blocking pass.
                    #self.parmf_rows.append(self.controlrow_temp)
                    #self.parmf_rows.extend(self.controlrow_temp)
                    self.parmf_rows.append(self.controlrow_temp.copy())
                    #print("\n ***NEW ROW: Just added previous temp dict to parmf_rows. ParmF_Rows now appears like this:")
                    #print(self.parmf_rows)
                    self.controlrow_temp.clear()				#Blow out the old values in the Temp dictionary of controls, which held the controls assembled for the previous ROW.
                print("Checking to see whether this new row was flagged to be included: %s" % (str(control.control_index)) )
                #If this is the 1st control for this row, check to see whether the user has checked the row to be included.  If so, then ALL controls in this row must be included.
                self.include_this_row = self.add_control_to_pathf_row(control)
                print("Include? %s" % (self.include_this_row) )
                if self.include_this_row:            #If user checked the main checkbox for this data field (or if this is an oddball row such as cutoff values) then INCLUDE THE ROW IN THE PARMF.TXT PARAMETER FILE.
                    self.include_this_pass = True        #If any row in this Blocking pass was selected by the user, then write this BLOCKING PASS to the ParmF.txt parameter file.
                hold_rowindex = rowindex
            elif blockpass == hold_pass and rowindex == hold_rowindex:
                if self.include_this_row:
                    print("Calling add_control_to_pathf_row() with control index: %s" % (str(control.control_index)) )
                    self.add_control_to_pathf_row(control)
            varname = str(control.value_object)               #Each control in the Controls list has an element called "object" which is typically the StringVar() that gets updated when the user changes a value.  This is crucial because when the user is done entering info, we traverse this list and chack all these StringVar() values for indications that the user entered something.
            value = str(control.value_object.get())                
            #print(str(control.blocking_pass) + " " + str(control.control_index) + " " + control.ref_name  + " " + control.field_name + " " + control.control_type + " " + control.startpos_recfile + " " + control.width_recfile + " " + control.startpos_memfile + " " + control.width_memfile  + " " + varname + " " + value)
			    
        #END OF LOOP: We have finished all controls. Copy the current row of controls into ParmF_Rows, a list that will be used to write a new ParmF.txt parameter file.
        if self.controlrow_temp:	              #The self.controlrow_temp dict will be EMPTY sometimes, if user did not select anything for a given blocking pass.
            #Copy the current row of controls into ParmF_Rows, a list that will be used to write a new ParmF.txt parameter file.
            self.parmf_rows.append(self.controlrow_temp.copy())
            #print("\n END: Just added temp dict to parmf_rows")
            #self.display_parmf_values  #print(self.parmf_rows)
        #print("\n parmf_rows after ALL blocking passes have been scanned:")
        #self.display_parmf_values()  #print(self.parmf_rows)

        return success

    def add_control_to_pathf_row(self, control):
        '''This method glues together screen controls that constitute a SINGLE ROW (and will constitute a single row in the ParmF.txt parameter file).
        Each row is uniquely identified by the combination of BlockingPass and RowIndex elements from the controls array. 
        But not every row of screen controls will have been selected by the user.  This function returns false if the current ROW is blank (which we know by the status of the main Checkbox that appears at the beginning of each row). 
		If the row is not checked, then don't bother evaluating the remaining controls in the row.'''
        #The return value from this function is a boolean flag indicating whether this ROW of controls contains user-entered information. It's set to True if the main checkbox is clicked by the user.  Once set to True, it remains at True until a new row of controls is encountered.
        #BUT DO NOT EVER SET IT TO FALSE within this function, because this function is called multiple times for the same row of controls.  
        #It is set to TRUE when the FIRST control in each row is evaluated.  Thereafter it remains unchanged until a NEW ROW is encountered.
        varname = str(control.value_object)
        varvalue = str(control.value_object.get())
        rowtype = str(control.row_type).lower()
        controltype = control.control_type.lower()			
        refname = str(control.ref_name).lower()
        recfile_column = control.field_name        #If this row is a Cutoff Values row or other non-datafield row, MAKE SURE that no "fieldname" (data_column_name) is specified for this control in the Controls list! If specified, the code will attempt to find a field width and starting position for a non-existent datafield.
        current_control_is_master_checkbox = False
        #print("add_control(), %s %s %s refname: %s . %s --value: %s rowtype:%s" % (str(control.blocking_pass), str(control.row_index), str(control.control_index), refname, refname[:8].lower(), varvalue, rowtype) ) 
        #IF this control is a "main" checkbox (to indicate whether this row should be included in pass) AND the user checked the checkbox (value =1) then we will store the entire row of controls to an array for later use.
        if refname[:7].lower() == "chkmain":		                
            current_control_is_master_checkbox = True
        if refname[:7].lower() == "chkmain" and int(varvalue) == 1:     #Main checkbox for each row (could be either Blocking or Matching row), indicating whether this field/row should be including in this blocking pass (as a blocking variable or matching variable)
            self.include_this_row = True	
            print("This row is to be INCLUDED in the blocking pass! (column name: %s ... %s)" % (control.field_name, control.text) )
            #Initialize the new row of controls by storing row-level information in the temporary controlrow_temp dictionary:
            self.initialize_controlrow(control, recfile_column)
        elif refname[:15].lower() == "optblock_memfld":                     #OptBlock fields are option menus (dropdowns) displaying Memory File fields.  The user selects the field that should be matched against the Record File field named in the Check Box.
            #For both blocking and matching fields, the ParmF.txt parameter file needs to list the StartPos and Width for the specified Fieldname. Therefore, call get_datacolumn_pos_from_datadict() to grab width and startpos (as a dict). 
            memfile_column = varvalue
            self.controlrow_temp["memfile_column"] = memfile_column            #Column name in the Memory File (blocking fields section)
            #For the specified Memory File column name, get the starting position and width, so we can write these values out to the ParmF.txt parameter file
            memfile_attribs = self.get_datacolumn_pos_from_datadict(memfile_column, "mem")
            self.controlrow_temp["memfile_startpos"] = memfile_attribs["startpos"]
            self.controlrow_temp["memfile_width"] = memfile_attribs["width"]
        elif refname[:14].lower() == "spnblock_blank" and rowtype == "blocking_fields":
            self.controlrow_temp["blank_flag"] = varvalue
        #End of Blocking Field rows, start Matching Field rows.
        elif refname[:15].lower() == "optmatch_memfld" and rowtype == "matching_fields":
            memfile_column = varvalue
            self.controlrow_temp["memfile_column"] = memfile_column        #Column name in the Memory File (blocking fields section)
            #For the specified Memory File column name, get the starting position and width, so we can write these values out to the ParmF.txt parameter file
            memfile_attribs = self.get_datacolumn_pos_from_datadict(memfile_column, "mem")
            print("\n Memfile attributes:")
            print(memfile_attribs)
            if memfile_attribs:
                self.controlrow_temp["memfile_startpos"] = memfile_attribs["startpos"]
                self.controlrow_temp["memfile_width"] = memfile_attribs["width"]
            else:
                self.error_message = "Failed to locate starting position for control with refname '%s', rowtype '%s' and value '%s'" % (refname, rowtype, memfile_column) 
                self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
                self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
                return
        elif refname[:15].lower() == "optmatch_compar":     # and rowtype == "matching_fields":
            print("\n Comparison Method is being set to %s \n" % (varvalue[:2].strip()) )
            if varvalue == '':
                varvalue = 'uo'
            self.controlrow_temp["comparison_method"] = varvalue[:3].replace("(", "").strip()   #Comparison method (matching fields section ONLY)
        elif refname[:7].lower() == "hidden_":  
            self.controlrow_temp["null_flag"] = 0
        elif refname[:10].lower() == "spnmatch_m":  # and rowtype == "matching_fields":
            self.controlrow_temp["m-value"] = float(varvalue)
        elif refname[:10].lower() == "spnmatch_u":  # and rowtype == "matching_fields":
            self.controlrow_temp["u-value"] = float(varvalue)
        #End of Matching Fields, start Cutoff Values
        elif refname[:18].lower() == "txtcutof_cutoff_hi" and rowtype == "cutoff_fields":
            if self.include_this_pass == True:
                self.include_this_row = True   #All cutoff rows are written to the ParmF file (assuming that at least one row from this pass have been selected by the user)
                self.initialize_controlrow(control, '')
                self.controlrow_temp["cutoff_hi"] = float(varvalue)
        elif refname[:18].lower() == "txtcutof_cutoff_lo" and rowtype == "cutoff_fields":
            if self.include_this_pass == True:
                self.controlrow_temp["cutoff_low"] = float(varvalue)
        elif refname[:20].lower() == "txtprcut_prcutoff_hi" and rowtype == "prcutoff_fields":
            if self.include_this_pass == True:
                self.include_this_row = True   #All cutoff rows are written to the ParmF file (assuming that at least one row from this pass have been selected by the user)
                self.initialize_controlrow(control, '')
                self.controlrow_temp["prcutoff_hi"] = float(varvalue)
        elif refname[:20].lower() == "txtprcut_prcutoff_lo" and rowtype == "prcutoff_fields":
            if self.include_this_pass == True:
                self.controlrow_temp["prcutoff_low"] = float(varvalue)
        #elif refname[:15].lower() == "pass_index" and rowtype == "hidden":
        #    if self.include_this_pass == True:
        #        self.controlrow_temp["num_passes = float(varvalue)

        #If the current control is the main checkbox or a subsequent control in a selected row, display it for debugging purposes.
        if self.include_this_row == True or not current_control_is_master_checkbox:
            #print("CONTROL: " + str(control.blocking_pass) + " " + str(control.row_index) + " " + control.ref_name  + " " + control.field_name + " " + control.row_type + " " + control.startpos_recfile + " " + control.width_recfile + " " + control.startpos_memfile + " " + control.width_memfile  + " " + varname + " " + value
            #print("Temp CONTROL row, so far: " )
            #print(self.controlrow_temp)
            return self.include_this_row

    def initialize_controlrow(self, control, recfile_column=''):
        self.controlrow_temp["blockpass"] = control.blocking_pass
        self.controlrow_temp["rowindex"] = control.row_index
        self.controlrow_temp["rowtype"] = str(control.row_type).lower()
        #For the specified Record File column name, get the starting position and width, so we can write these values out to the ParmF.txt parameter file
        if recfile_column == '':                              #If this row is a Cutoff Values row or other non-datafield row, MAKE SURE that no "fieldname" is specified for this control in the Controls list! If specified, the code will attempt to find a field width and starting position for a non-existent datafield.
            self.controlrow_temp["recfile_column"] = ""
            self.controlrow_temp["recfile_startpos"] = ""
            self.controlrow_temp["recfile_width"] = ""
        else:		
            self.controlrow_temp["recfile_column"] = recfile_column          #Column name in the Record File, such as "LastName"
            recfile_attribs = self.get_datacolumn_pos_from_datadict(recfile_column, "rec")
            self.controlrow_temp["recfile_startpos"] = recfile_attribs["startpos"]
            self.controlrow_temp["recfile_width"] = recfile_attribs["width"]
        #Note: memfile information will be added by secondary controls within this ROW (that is, they are not known when this dict is initialized). But initialize the keys here so that controlrow_temp always contains all keys right from the start. 
        self.controlrow_temp["memfile_startpos"] = ""
        self.controlrow_temp["memfile_width"] = ""
        self.controlrow_temp["blank_flag"] = "1"
        self.controlrow_temp["null_flag"] = "0"
        self.controlrow_temp["comparison_method"] = ""
        self.controlrow_temp["u-value"] = "0"
        self.controlrow_temp["m-value"] = "0"
        self.controlrow_temp["cutoff_hi"] = "0"
        self.controlrow_temp["cutoff_low"] = "0"
        self.controlrow_temp["prcutoff_hi"] = "0"
        self.controlrow_temp["prcutoff_low"] = "0"

    def get_control_name(self, widget_type, row_type, data_column_name, parm_type, blocking_pass_index):
        return_value = ""
        #"opt" + self.rowtype[:5] + "_" + data_column_name + "_" + str(self.pass_index)       
        return_value = widget_type.lower().strip()[:3] + row_type.lower().strip()[:5] + "_" + parm_type.lower().strip() + "_" + data_column_name + "_" + str(blocking_pass_index)
        return return_value

    def create_parmf_file_from_blocking_passes(self):
        '''This method creates a new ParmF.txt parameter file from user input in the Blocking Pass forms. The user inputs have been copied to self.parmf_rows list, which has one row of controls per row f the ParmF.txt file.'''
        success = True
        try:		
            self.trigger_pathf_assembly()         #Triggers function assemble_pathf_elements() to pull user inputs into an array. Required before writing the ParmF.txt parameter file.
            #head, tail = os.path.split(self.bigmatch_parmf_file_to_save)
            #self.parmf_file = os.path.join(head, "parmf.txt")
            self.logobject.logit("\n ParmF file will be saved to: %s \n" % (self.bigmatch_parmf_file_to_save), True, True )
            bigspace = "                    " 		
            #For line 2 in ParmF.txt we need total number of passes, with number of blocking and matching fields for each pass. Loop thru the ParmF_Rows to count the number of non-empty blocking passes and blocking/matching fields:
            self.blocking_passes = []
            hold_section = section = ""
            index = count_blocking_fields = count_matching_fields = count_populated_blocking_passes = 0
            for row in self.parmf_rows:
                if str(row["rowtype"]).lower() == "blocking_fields":          #BlockingFields are the first rows appearing in each Blocking Pass.
                    if hold_section != "blocking" and hold_section != "":     #We just encountered a new BLOCKING RUN PASS (and not the very first row of the list)
                        print("In self.blocking_passes, Found a new Blocking Fields section")
                        pass_ = {"index":index, "count_blocking_fields":count_blocking_fields, "count_matching_fields":count_matching_fields}
                        self.blocking_passes.append(pass_)
                        count_populated_blocking_passes += 1
                        #After storing the values from the previous Blocking Pass, prep for next Blocking Pass
                        count_blocking_fields = 0
                        count_matching_fields = 0
                        index += 1
                    count_blocking_fields += 1    #A blocking field found for the CURRENT PASS
                    hold_section = "blocking"
                elif str(row["rowtype"]).lower() == "matching_fields":
                    count_matching_fields += 1
                    hold_section = "matching"

            #After traversing the parms_rows list, finish out by writing the final pass's information to the blocking_passes list.
            pass_ = {"index":index, "count_blocking_fields":count_blocking_fields, "count_matching_fields":count_matching_fields}
            self.blocking_passes.append(pass_)
            count_populated_blocking_passes += 1
            #count_populated_blocking_passes = len(self.blocking_passes)
            if self.debug:
                print("\n Final Blocking Pass totals:")
                for pass_ in self.blocking_passes:
                    print(pass_)
                print("\n")
            #Armed with these totals-per-pass, open ParmF.txt for writing out the information: 
            #with open(self.parmf_file, "w") as f:
            #if os.path.isfile(self.bigmatch_parmf_file_to_save):
            #    os.remove(self.bigmatch_parmf_file_to_save)		              #Should not need to delete the file, but it has been appending new text at end of file instead of erasing existing text and re-writing-- even though the file open uses "w" not "w+", and it is closed after every write session.
            with open(self.bigmatch_parmf_file_to_save, "w") as f: 
                #FIRST ROW.
                #Line 1, which can be created using defaults (except for the first digit which specifies the number of blocking passes, and the 6th digit which is set to 1 if this is a single-file dedupe)
                if self.dedupe_single_file == True:
                    dedupe_digit = "1"
                else:
                    dedupe_digit = "0"
                f.write(str(count_populated_blocking_passes) + " 1 1 0 1 " + str(dedupe_digit) + " 0 " + str(self.recfile_record_length) + " " + str(self.memfile_record_length) + " \n") 
                #SECOND ROW.
                #Line 2, write the number of blocking fields per pass to the file:
                for pass_ in self.blocking_passes:
                    f.write(str(pass_["count_blocking_fields"]) + " ")
                f.write("\n")
                #Line 3, write the number of matching fields per pass to the file:
                for pass_ in self.blocking_passes:
                    f.write(str(pass_["count_matching_fields"]) + " ")
                f.write("\n")
                #Now run thru the parmf_rows again, this time writing out the actual blocking pass fields:
                for row in self.parmf_rows:
                    #print(row)
                    if str(row["rowtype"]).lower() == "blocking_fields":
                        if self.debug: self.logobject.logit(row, True, True, True)
                        blocking_row_string = str(row["recfile_column"]).lower().ljust(10) + bigspace + str(row["recfile_startpos"]).ljust(4) + " " + str(row["recfile_width"]).ljust(5) + " " + str(row["memfile_startpos"]).ljust(4) + " " + str(row["memfile_width"]).ljust(5) + " " + str(row["blank_flag"]).ljust(4)
                        f.write(blocking_row_string + "\n" )
                    elif str(row["rowtype"]).lower() == "matching_fields":
                        #M-Value (matched):
                        mvalue = str(row["m-value"])
                        if mvalue == '' or mvalue is None:
                            mvalue = '0'
                        if float(mvalue) > 100:
                            mvalue = "100"
                        elif float(mvalue) == 100:
                            mvalue = "1.00"
                        elif float(mvalue) < 10:
                            mvalue = "0.0" + str(round(float(mvalue),0)).replace(".0", "")
                        elif float(mvalue) < 100:
                            mvalue = "0." + str(round(float(mvalue),0)).replace(".0", "")
                        #U-Value (unmatched):
                        uvalue = str(row["u-value"])
                        if uvalue == '' or mvalue is None:
                            uvalue = '0'
                        if float(uvalue) > 100:
                            uvalue = "100"
                        elif float(uvalue) == 100:
                            uvalue = "1.00"
                        elif float(uvalue) < 10:
                            uvalue = "0.0" + str(round(float(uvalue),0)).replace(".0", "")
                        elif float(uvalue) < 100:
                            uvalue = "0." + str(round(float(uvalue),0)).replace(".0", "")
                        blocking_row_string = str(row["recfile_column"]).lower().ljust(10) + bigspace + str(row["recfile_startpos"]).ljust(4) + " " + str(row["recfile_width"]).ljust(5) + " " + str(row["memfile_startpos"]).ljust(4) + " " + str(row["memfile_width"]).ljust(5) + " 0 " + str(row["comparison_method"]).ljust(5) + " " + mvalue.ljust(7) + " " + uvalue.ljust(7)
                        #Write the row to the ParmF.txt parameters file
                        f.write(blocking_row_string + "\n" )
                    elif str(row["rowtype"]).lower() == "cutoff_fields":
                        cutoff_row_string = str(row["cutoff_hi"]).ljust(6) + " " + str(row["cutoff_low"]).ljust(4)
                        f.write(cutoff_row_string + "\n" )
                    elif str(row["rowtype"]).lower() == "prcutoff_fields":
                        cutoff_row_string = str(row["prcutoff_hi"]).ljust(6) + " " + str(row["prcutoff_low"]).ljust(4)
                        f.write(cutoff_row_string + "\n" )
                #Final Line of the ParmF.txt parameter file indicates column name, width and starting position for the Sequence Column in Record file and Memory file.
                col_attribs = self.locate_sequence_column("rec")
                if col_attribs is not None:
                    f.write(str(col_attribs["sequence_column_name"]).ljust(10) + bigspace + str(col_attribs["startpos"]) + " " + str(col_attribs["width"]) + " ")
                col_attribs = self.locate_sequence_column("mem")
                if col_attribs is not None:
                    f.write(col_attribs["startpos"] + " " +col_attribs["width"] + "\n")

                f.flush()
                os.fsync(f.fileno())
                f.close()
                f = None
                #Display a temporary message notifying the user that their file was created.
                self.update_message_region("File has been saved")
        except:
            success = False
            self.error_message = "Creation of ParmF.txt parameter file failed."
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=4, file=sys.stdout)
            self.logobject.logit("\n Error Line: %s" % (exc_traceback.tb_lineno), True, True )
            self.error_message += " - " + exc_value + ' --at Line: ' + str(exc_traceback.tb_lineno)
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
        finally:
            pass
        return success

    def get_datafield_name_from_dict_startpos(self, startpos, mem_or_rec):
        '''Search the mem or rec DataDict file to find the column with a starting position equal to the "startpos" parameter.  Return the column name.'''
        return_value = ''	
        list = None
        stposindx = None
        fldnmindx = None
        if mem_or_rec == "mem":
            list = self.meta_values_memfile	
            stposindx = self.startpos_col_in_memfile_dict
            fldnmindx = self.fieldname_col_in_memfile_dict
        elif mem_or_rec == "rec":
            list = self.meta_values_recfile
            stposindx = self.startpos_col_in_recfile_dict
            fldnmindx = self.fieldname_col_in_recfile_dict
        if list:
            for item in list:
                if self.debug: self.logobject.logit("SEEKING %s, FOUND %s" % (startpos, item[stposindx]), True, True )
                if int(item[stposindx]) == int(startpos):
                    if self.debug: self.logobject.logit("GOT IT.", True, True)
                    return_value = str(item[fldnmindx])
                    break
        else:
            self.error_message = "Expected meta-values list, but encountered empty object."
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
            return
        if self.debug: self.logobject.logit("\nGET_Datfldnm_frdict_strtpos(), mem-rec=%s, startpo=%s, fldnmdx=%s, stposdx=%s, result=%s" % (mem_or_rec, startpos, fldnmindx, stposindx, return_value), True, True )
        if not return_value:
            return_value = ''     #Get rid of zero or None
        return return_value

    def remove_widget(self):
        self.widget_registry.append(self.b4)
        #self.b4.grid_forget()
        self.widget_registry[0].grid_forget()

    def instantiate_bigmatch_parmfile_object(self, load_or_save='load'):
        '''Class BigmatchParmfile() currently handles only the loading of variables FROM a saved Parmf.txt parameter file.
        The loaded variables are to be displayed in the Blocking Pass entry forms, rendered by the current class (BlockingPass_Model)'''
        if load_or_save is not None:
            load_or_save = str(load_or_save).lower().strip()
            if load_or_save == "load":                  #LOAD indicates that the BigmatchParmfile() class is assisting in loading values from a PARMF.TXT file into this form.
                if self.bigmatch_parmf_file_to_load:    #If the file has been specified, then load up a copy of the ParmFile object
                    self.parmfileobj = BigmatchParmfile(self.bigmatch_parmf_file_to_load)
                    self.parmfileobj.set_logobject(self.logobject)
            if load_or_save == "save":                  #SAVE indicates that the BigmatchParmfile() class is assisting in saving values from this BloakingPass form to a PARMF.TXT file. NOT YET OPERATIONAL.
                pass  #Not needed yet, but leave placeholder for future

    def get_current_variable_value(self, blocking_pass, row_type, control_type, data_column_name=''):
        #Based on an existing ParmF.txt parameter file, determine whether the control now being displayed has a corresponding stored value.
        parmdict = {}
        blocking_pass = str(blocking_pass).strip()
        data_column_name = str(data_column_name).lower().strip()
        row_type = str(row_type).lower().strip()
        control_type = str(control_type).lower().strip()
        if self.bigmatch_parmf_file_to_load and not self.parmfileobj:       #parmfileobj is an instantiation of the BigmatchParmFile class
            self.instantiate_bigmatch_parmfile_object("load")
        if self.bigmatch_parmf_file_to_load and self.parmfileobj:
            if self.debug: self.logobject.logit("IN get_current_variable_value(), blocking_pass: %s, row_type: %s, control_type: %s, data_column_name: %s" % (blocking_pass, row_type, control_type, data_column_name), True, True, True)
            found_blkpass = found_rowtype = None     			#found_ctltyp =
            blkps_already_checked = []
            for parm in self.parmfileobj.parms:
                #Each item in parmfileobj.parms is a dictionary containing information about an item in the PARMF.TXT parameter file.
                #Definition of the PARM dict: parmstuff = {"blocking_pass": blkpass_index, "row_index": self.row_index, "row_type": parmrow.row_type, "num_parms_in_row": parm["num_parms_in_row"], "parm_index": parm["parm_index"], "parm_counter":cntr, "parm_value": parm["parm_value"], "parm_type": parm["parm_type"]}
                #if self.debug: self.logobject.logit("PARMFILE PARM: blkpass: %s, row_index: %s, row_type: '%s', num parms in row: %s, parm_index: %s, parm_type: '%s', parm_value: '%s'" % (parm["blocking_pass"], parm["row_index"], parm["row_type"], parm["num_parms_in_row"], parm["parm_index"], parm["parm_type"], parm["parm_value"] ), True, True, True )
                match = False
                blkpass = str(parm["blocking_pass"]).strip()
                rowtp = str(parm["row_type"]).lower().strip()
                ctltp = str(parm["parm_type"]).lower().strip()
                #Before doing a full comparison on each row, check a few high-level variables such as Blocking Pass number, and if it doesn't match then move on to the next row.
                if blkpass == blocking_pass:           #The blocking pass in this Parmf.txt row matches the blocking pass of the item being sought.
                    found_blkpass = True
                else: 
                    if found_blkpass:                  #We previously encountered the correct blocking pass, but now we've encountered a non-matching blocking pass. This means we can ignore the remaining rows in the PARMF.TXT file
                        break
                    else:                              #This blocking pass does not match, but we need to keep looping because we have not yet encountered the correct blocking pass
                        if blkpass in blkps_already_checked:
                            continue                   #We already checked this blocking pass and it was no the one we seek
                        else:
                            blkps_already_checked.append(blkpass)  #Add this blocking pass to the list of passes we already ruled out
                            continue
                if rowtp == row_type:                  #The row_type in this Parmf.txt row matches the row_type of the item being sought.
                    found_rowtype = True
                else: 
                    if found_rowtype:                  #We previously encountered the correct row type, but now we've encountered a non-matching row type. This means we can ignore the remaining rows in the PARMF.TXT file
                        break
                    else:                              #This row_type does not match, but we need to keep looping because we have not yet encountered the correct row_type.
                        continue
                if ctltp != control_type:
                    continue
                #Now we have the correct blocking pass, row type and control_type. Search only the PARMF.TXT rows that meet these criteria.
                if self.debug: self.logobject.logit("PARMFILE PARM-- blkpass: %s, row_index: %s, row_type: '%s', num parms in row: %s, parm_index: %s, parm_type: '%s', parm_value: '%s'" % (parm["blocking_pass"], parm["row_index"], parm["row_type"], parm["num_parms_in_row"], parm["parm_index"], parm["parm_type"], parm["parm_value"] ), True, True, True )
                if str(control_type).lower()[:7] == "cutoff_" or str(control_type).lower()[:9] == "prcutoff_" or control_type == "uniqid":    #We can't use the First_Parm_In_Row for cutoff fields because they don't appear in a row with a Recfile_Field, the way BlockingField and MatchingField rows do.
                    if str(parm["blocking_pass"]).lower() == blocking_pass and str(parm["row_type"]).lower() == row_type and str(parm["parm_type"]).lower() == control_type:
                        match = True
                else:                     #This row can be identified uniquely by blkpass_index + First_Parm_In_Row
                    if str(parm["blocking_pass"]).lower() == blocking_pass and str(parm["row_type"]).lower() == row_type and str(parm["parm_type"]).lower() == control_type and str(parm["first_parm_in_row"]).lower() == data_column_name:
                        match = True
                if match:
                    if self.debug: self.logobject.logit("**FOUND:BkPs %s, rwtp %s, pmtp %s 1stprminrw %s" % (blocking_pass, row_type, control_type, data_column_name), True, True, True )
                    if self.debug: self.logobject.logit("PARMFILE PARM: in get_current_varval, blkpass: %s, row_index: %s, row_type: %s, num_parms in row: %s, parm_index: %s, parm_type: %s, parm_value: %s, first_parm_in_row: %s" % (parm["blocking_pass"], parm["row_index"], parm["row_type"], parm["num_parms_in_row"], parm["parm_index"], parm["parm_type"], parm["parm_value"], parm["first_parm_in_row"] ), True, True, True )
                    #return_value = parm["parm_value"]
                    #"parm" refers to the dictionary describing the current item in PARMF.TXT.
                    parmdict = parm.copy()
                    break
					
        return parmdict
		
    #*****************************************************************************************************************************************
    #BLOCKING PASS VIEW OBJECTS
    #NOTE: BlockingPass VIEWS are typically invoked by calling this MODEL object. The following methods are handlers for instantiating VIEWS.
    def instantiate_view_object(self, container, index):
        #Instantiate blocking pass VIEWS here.  
        #Note that the currently instantiated MODEL object serves as model for ALL of the views, so attributes that should be different for each iteration cannot be read form the MODEL.
        blockingpass_view = BlockingPass_View(container, self, index)
        self.blockingpass_views.append(blockingpass_view)   #Add this View to the index
        return blockingpass_view

    def display_view(self, container, index, **kw):
        #if self.blockingpass_view is None:
        blockingpass_view = self.instantiate_view_object(container, index)
        print("Kwargs for BlockingPass_Model.display_view(): ")
        self.logobject.logit(str(kw), True, True)
        for key, value in kw.items():
            self.logobject.logit("%s = %s" % (key, value), True, True )
        self.logobject.logit("\n In BlockingPass_Model.display_view(), calling blockingpass_view.initUI().", True, True)
        blockingpass_view.initUI(**kw)   #DISPLAY THE FRAME OBJECT ON SCREEN
        return blockingpass_view

    def display_views(self, container=None, how_many_passes=None):
        #Instantiate blocking pass VIEWS here.  
        #Note that the currently instantiated MODEL object serves as model for ALL of the views, so attributes that should be different for each iteration cannot be read form the MODEL.
        if container is None:
            container = self.controller.bigcanvas.bigframe
        if how_many_passes:
            self.how_many_passes = how_many_passes
        self.logobject.logit("\n Top of BlockingPass_Model.display_views(), how_many_passes=%s" % (self.how_many_passes), True, True)
        #DISPLAY THE SPECIFIED NUMBER OF BLOCKING PASS ENTRY FORMS (but only if the Data Dict files have been specified):
        if self.datadict_memfile and self.datadict_recfile:
            self.read_datadict_file_into_arrays(self.datadict_recfile, "rec")
            self.read_datadict_file_into_arrays(self.datadict_memfile, "mem")
            success1 = self.locate_crucial_datadict_columns("rec")
            self.logobject.logit("\n fieldname_col_in_recfile_dict: %s, startpos_col_in_recfile_dict: %s, width_col_in_recfile_dict: %s, uniqid_col_in_recfile_dict: %s" % (str(self.fieldname_col_in_recfile_dict), str(self.startpos_col_in_recfile_dict), str(self.width_col_in_recfile_dict), str(self.uniqid_col_in_recfile_dict) ), True, True, True )
            success2 = self.locate_crucial_datadict_columns("mem")
            self.logobject.logit("\n fieldname_col_in_memfile_dict: %s, startpos_col_in_memfile_dict: %s, width_col_in_memfile_dict: %s, uniqid_col_in_memfile_dict: %s" % (str(self.fieldname_col_in_memfile_dict), str(self.startpos_col_in_memfile_dict), str(self.width_col_in_memfile_dict), str(self.uniqid_col_in_memfile_dict) ), True, True, True )
            print("\n In BlockingPass_Model.display_views(), about to call function display_view() -- multiple times.")
            if self.error_message is not None:
                self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
                self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
                return False
            for i in range(0, self.how_many_passes):
                bgcolor = self.bgcolors[i]    #bgcolor = "#FDFFDF"   
                print("\n In BlockingPass_Model.display_views(), calling display_view() for iteration #" + str(i) +". BgColor=" + bgcolor)
                #DISPLAY THE BLOCKING PASS ENTRY SCREEN HERE:
                self.display_view(container, i, width=self.frame_width, background=bgcolor, borderwidth=2, padx=3, pady=3)
            #Now disable the button which loads BlockingPasses--they load new passes in addition to the old ones.  TO DO: write clean-up routine to clear out old passes when user wants to re-load from scratch.
            self.blkpass_views_have_been_displayed = True
            self.update_button_state()
        else:
            #User has not yet selected Data Dictionaries, which are required for displaying Blocking Pass entry screens.
            self.display_openfile_dialogs(container)
            self.display_user_buttons(container)

    def display_openfile_dialogs(self, container):
        self.display_openfile_dialog(container, self.datadict_recfile, "datadict", "open", "rec")
        self.display_openfile_dialog(container, self.datadict_memfile, "datadict", "open", "mem")
        self.display_openfile_dialog(container, self.bigmatch_parmf_file_to_load, "parmfile", "open", "")
        self.display_openfile_dialog(container, self.bigmatch_parmf_file_to_save, "parmfile", "save_as", "")

    def display_openfile_dialog(self, container, current_file='', file_category='', open_or_save_as='', mem_or_rec=''):
        '''Whenever the user has an option (or requirement) to open or save a file, we instantiate the FilePath_Model() class. '''
        success = True
        caption = ''
        fpathobj = None
        file_types = [('All files', '*'), ('Text files', '*.csv;*.txt')]
        #initial_dir = self.calc_initial_dir_for_file_open(current_file, file_category, mem_or_rec)      #Set a directory location where the FileOpen dialog will start out
        kw_fpath = {"bgcolor":self.bgcolor, "frame_width":"", "frame_height":"", "file_category":file_category}     #, "initial_dir":initial_dir
        self.logobject.logit("\nIn display_openfile_dialog(), filecat: %s, open-save: %s, mem-rec: %s, curfile: %s" % (file_category, open_or_save_as, mem_or_rec, current_file), True, True )
        if file_category.lower().strip() == "datadict":	
            if mem_or_rec.lower().strip() == "mem":
                caption = "Memory file data dictionary:"
                self.filepathobj_memfile = FilePath_Model(self.parent_window, self, self.controller, caption, open_or_save_as, caption, file_types, **kw_fpath)
                fpathobj = self.filepathobj_memfile
            elif mem_or_rec.lower() == "rec":
                caption = "Record file data dictionary:"
                self.filepathobj_recfile = FilePath_Model(self.parent_window, self, self.controller, caption, open_or_save_as, caption, file_types, **kw_fpath)
                fpathobj = self.filepathobj_recfile
        elif file_category.lower().strip() == "parmfile":
            if open_or_save_as.lower().strip() == "open":
                caption = "Parameter file to load (optional):"
                self.filepathobj_parmfile_to_load = FilePath_Model(self.parent_window, self, self.controller, caption, open_or_save_as, caption, file_types, **kw_fpath)
                fpathobj = self.filepathobj_parmfile_to_load
            elif open_or_save_as.lower().strip() == "save_as":
                caption = "Parameter file to save to:"
                self.filepathobj_parmfile_to_save = FilePath_Model(self.parent_window, self, self.controller, caption, open_or_save_as, caption, file_types, **kw_fpath)
                fpathobj = self.filepathobj_parmfile_to_save
        else:
            success = False
            self.error_message = "Invalid type: '%s'" % (file_category.lower()) 
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            self.controller.common.handle_error(self.error_message, False, False, "blockingpass")
            return
        print("\n Type of fpathobj: '%s' \n" % (str(type(fpathobj)) ) )
        if fpathobj:
            fpathobj.calc_initial_dir_for_file_open(current_file, file_category, mem_or_rec)      #Set a directory location where the FileOpen dialog will start out
            fpathobj.display_view(container)	                      #Display the Open File dialog for user to select a data dict file
        return success

    '''def calc_initial_dir_for_file_open(self, current_file='', file_category='', mem_or_rec=''):
        initial_dir = None
        if current_file:
            if os.path.isfile(current_file):                              #If a file is specified as initial directory, use the FOLDER, not the file.
                head, tail = os.path.split(current_file)
                initial_dir = head 
        else:
            file_category = file_category.lower().strip()                 #It's useful to know whether the file being opened is a DATADICT, PARM, etc. because the main BigMatch controller object (main.py) stores a record of the last folder location navigated to for each major file type.
            if file_category == "datadict":
                if mem_or_rec.lower() == "mem" and self.controller.mem_datadict_last_opened:
                    head, tail = os.path.split(self.controller.mem_datadict_last_opened)
                    initial_dir = head
                elif mem_or_rec.lower() == "rec" and self.controller.rec_datadict_last_opened:
                    head, tail = os.path.split(self.controller.rec_datadict_last_opened)
                    initial_dir = head
                else:
                    initial_dir = self.controller.datadict_dir_last_opened
            elif file_category == "parmfile":
                initial_dir = self.controller.parmfile_dir_last_opened
                self.logobject.logit("CalcInitDir(), parmfile_dir_last_opened: %s" % (self.controller.parmfile_dir_last_opened), True, True )
        if not initial_dir:
            initial_dir = self.controller.dir_last_opened                  #If we can't find a more specific history of user's previous folders opened, use the more generic:
            self.logobject.logit("CalcInitDir(), found no specific matches so setting to %s" % (self.controller.dir_last_opened), True, True )
        if not initial_dir:
            #if no other strategy is found, punt and use the current executing program's folder
            initial_dir = os.path.dirname(os.path.realpath(__file__))
        self.logobject.logit("\nIn calc_initial_dir(), initdir is %s" % (initial_dir), True, True )
        return initial_dir
    '''

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "BlockingPass_Model.display_user_buttons()")
        else:
            stackslot = 0
        #Testing: show a button that will dump to the command window the current contents of all the screen CONTROLS.
        self.button_frame.grid(row=stackslot, column=0, sticky=EW)
        self.button_frame.config(background=self.bgcolor)
		
        self.btnDisplayBlkpasses = Button(self.button_frame, text="Display blocking passes", width=30, command=self.display_views)
        self.btnDisplayBlkpasses.grid(row=0, column=0, sticky=W)
        self.btnDisplayBlkpasses.configure(state=DISABLED)        #Do not enable this button unless the user has selected Data Dictionary files
        #self.btnLoadParmFile = Button(self.button_frame, text="Load parameter file", width=30, command=self.enable_parmfile_load)
        #self.btnLoadParmFile.grid(row=0, column=1, sticky=W)
        #self.btnLoadParmFile.configure(state=DISABLED)           #Do not enable this button unless the user has selected s ParmF file to load
        self.btnSaveToParmFile = Button(self.button_frame, text="Save blocking info to parameter file", width=30, command=self.create_parmf_file_from_blocking_passes)
        self.btnSaveToParmFile.grid(row=0, column=2, sticky=W)
        self.btnSaveToParmFile.configure(state=DISABLED)          #Do not enable this button unless the user has selected a ParmF file to save to
        #self.b3 = Button(self.button_frame, text="View control values", width=25, command=self.display_control_values)
        #self.b3.grid(row=0, column=3, sticky=W)
        #self.b6 = Button(button_frame, text="Remove me", width=25, command=self.remove_widget)
        #self.b6.grid(row=0, column=3, sticky=W)
        #self.b9 = Button(self.button_frame, text="Test msg", width=25, command=self.update_message_region)
        #self.b9.grid(row=0, column=3, sticky=W)
        #Create a Message Region where we can display text temporarily, such as "File was successfully saved"
        msg = ""                       #Testing 123456789012345678901234567890123456789012345678901234567890"
        self.message_region = Message(self.button_frame, text=msg) 
        self.message_region.grid(row=0, column=5, sticky=E)
        kw = {"anchor":E, "width":800, "foreground":"dark green", "background":self.bgcolor, "borderwidth":1, "font":("Arial", 12, "bold"), "padx":8, "pady":3 }  
        self.message_region.configure(**kw)

    def update_message_region(self, text='', clear_after_ms=5000, **kw):
        self.message_region.configure(text=text)
        self.message_region.after(clear_after_ms, self.clear_message_region)
		
    def clear_message_region(self):
        self.message_region.configure(text="")

    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):  
        '''Any FilePath objects created by this class will expect "Function update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        print("Master BlockingPass_Model object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string) )
        self.datadict_recfile = self.filepathobj_recfile.file_name_with_path
        self.datadict_memfile = self.filepathobj_memfile.file_name_with_path
        self.bigmatch_parmf_file_to_load = self.filepathobj_parmfile_to_load.file_name_with_path
        self.bigmatch_parmf_file_to_save = self.filepathobj_parmfile_to_save.file_name_with_path
        print("\n In BlockingPass_Model.update_filepath(), datadict_recfile='%s', datadict_memfile='%s', bigmatch_parmf_file_to_load='%s', bigmatch_parmf_file_to_save='%s'" % (str(self.datadict_recfile), str(self.datadict_memfile), str(self.bigmatch_parmf_file_to_load), str(self.bigmatch_parmf_file_to_save) ) )
        print("\n BEFORE update_button_state: self.filepathobj_parmfile_to_save.file_name_with_path = '%s' and self.bigmatch_parmf_file_to_save = '%s'" % (self.filepathobj_parmfile_to_save.file_name_with_path, self.bigmatch_parmf_file_to_save) )
        self.update_button_state()
        #Refresh the Blocking Pass view when the user selects a new DataDict file.
        #self.display_view()
        self.update_master_paths(file_name_with_path)                           #The main controller object (main.py) tracks the locations that the user has opened files in. Update that now.
        self.update_initial_dir_for_file_open_dialogs()                         #Update the Tkinter file-open-dialog frames with the latest user selections of folders for file-open.
        if callback_string.lower().strip()[:4] == "save": #This is a file SAVE AS, not a FILE OPEN
            #Display a temporary message notifying the user that their file was created.
            print("\nEnable SAVE button because callback_string='%s'" % (callback_string) )
            self.update_message_region("Click 'Save blocking info to parameter file' to save changes to the Parmf.txt file")

    def update_master_paths(self, file_name_with_path):
        if file_name_with_path:	
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head                              #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
        if self.datadict_memfile:
            head, tail = os.path.split(self.datadict_memfile)
            self.controller.datadict_dir_last_opened = head                     #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            self.controller.mem_datadict_last_opened = self.datadict_memfile    #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
        if self.datadict_recfile:
            self.controller.datadict_dir_last_opened = head                     #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            self.controller.rec_datadict_last_opened = self.datadict_recfile    #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
        if self.bigmatch_parmf_file_to_load:
            self.controller.parmfile_dir_last_opened = head                     #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            self.controller.parmf_last_opened = self.bigmatch_parmf_file_to_load #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
        if self.bigmatch_parmf_file_to_save:
            self.controller.parmfile_dir_last_opened = head                     #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            self.controller.parmf_last_opened = self.bigmatch_parmf_file_to_save #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
        self.logobject.logit("\n Controller-saved paths-- LastDir: %s, LastDataDictDir: %s, LastRecDatadict: %s, LastMemDatadict: %s, LastParmFile: %s" % (self.controller.dir_last_opened, self.controller.datadict_dir_last_opened, self.controller.rec_datadict_last_opened, self.controller.mem_datadict_last_opened, self.controller.parmf_last_opened), True, True )
        
    def update_initial_dir_for_file_open_dialogs(self):
        '''In addition to tracking "last file opened" at the main controller level, 
        we also want to notify every FilePath object when the user has opened a new file, so that they can adjust thir Initial DIr properties to the location just opened.'''
        self.filepathobj_memfile.calc_initial_dir_for_file_open(self.datadict_memfile, "datadict", "mem")
        self.filepathobj_recfile.calc_initial_dir_for_file_open(self.datadict_recfile, "datadict", "rec")
        self.filepathobj_parmfile_to_load.calc_initial_dir_for_file_open(self.bigmatch_parmf_file_to_load, "parmfile", "")
        self.filepathobj_parmfile_to_save.calc_initial_dir_for_file_open(self.bigmatch_parmf_file_to_save, "parmfile", "")
        
    def update_button_state(self):
        if self.datadict_recfile and self.datadict_memfile:
            #Set the flag for single-file dedupe vs. multiple file linkage
            if str(self.datadict_recfile).lower().strip() == str(self.datadict_memfile).lower().strip():       #DataDictionaries are the exact same file in the same location -- user wants to dedupe a single file, not match two files against each other.
                self.dedupe_single_file = True
            else:
                self.dedupe_single_file = False
            #Enable DISPLAY button
            if self.blkpass_views_have_been_displayed:      #Once the blocking passes have been displayed, do not allow the user to click "Display" again!
                self.disable_display()
            else:
                self.enable_display()
            #Enable SAVE button?
            if self.blkpass_views_have_been_displayed and self.bigmatch_parmf_file_to_save:
                self.enable_save()
            else:
                self.disable_save()
            #Enable parmfile load
            if self.bigmatch_parmf_file_to_load:
                self.enable_parmfile_load()
        else:
            #Disable DISPLAY button
            self.disable_display()

    def enable_display(self):
        if not self.blkpass_views_have_been_displayed:
           self.btnDisplayBlkpasses.config(state=NORMAL)        #Button is initially disabled. It is disabled again once the blocking passes are displayed.

    def disable_display(self):
        self.btnDisplayBlkpasses.config(state=DISABLED) 

    def enable_parmfile_load(self):
        #self.btnLoadParmFile.config(state=NORMAL)                           #Button is initially disabled
        #if self.bigmatch_parmf_file_to_load and not self.parmfileobj:       #parmfileobj is an instantiation of the BigmatchParmFile class
        #    self.instantiate_bigmatch_parmfile_object("load")
        pass

    def enable_save(self):
        print("In enable_save(), blkpass_views_have_been_displayed = %s" % (self.blkpass_views_have_been_displayed) )
        self.btnSaveToParmFile.config(state=NORMAL)          #Button is initially disabled

    def disable_save(self):
        self.btnSaveToParmFile.config(state=DISABLED)          #Button is initially disabled

        
#End of class BlockingPass

#******************************************************************************
#******************************************************************************
class BlockingPass_View(Frame):
    debug = False
    container = None
    model = None
    widgetstack_counter = None
    bgcolors = []
    bgcolor = None	
    pass_index = None		#Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
    row_index = 0
    rowtype = None	
    show_view = None
	
    def __init__(self, container, model=None, pass_index=None, show_view=None):
        Frame.__init__(self, container)
        if container:
            self.container = container
        if model is None:
            model = BlockingPass_Model()				#Normally this VIEW object will be called by an already-instantiated MODEL object.  But this line is there to catch any direct instantiations of the VIEW.		
        self.model = model 
        self.pass_index = pass_index                              #Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
        self.show_view = show_view
        #Set the debug flag to the Model's debug flag
        self.debug = self.model.debug
        #Display the frame:
        print("\n In BlockingPass_View._init_: self.show_view=" + str(self.show_view))
        if self.show_view:		#Normally this does NOT trigger the screen display, because the class is instantiated and THEN displayed later.
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the container (usually a frame, but could be canvas or the container window), directly below any previous widgets. 
        #The grid() ROW designators refer to the container window's Grid and determine which order the Frames will be displayed in.
        print("\n Type Of Container: " + str(type(self.container)) )
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "BlockingPass_View.Init")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=W)                    #position the Frame within the container Window
        #self.config(width=self.model.frame_width, background=self.model.bgcolor, borderwidth=2, padx=3, pady=3)   #self.model.bgcolor #height=self.frame_height, 
        self.config(**kw)
        self.bgcolor = kw["background"]
        self.config(background=self.bgcolor)
        print("In initUI(), background=" + str(self.bgcolor))
        for i in range(0,6):		
            self.columnconfigure(0, weight=0, pad=3)
        for i in range(0, self.model.recfile_datadict_rowcount):
            self.rowconfigure(0, pad=3)
        #Frame Title:
        if self.debug: print("\n In BlockingPass_View.initUI: About to display main BlockingPass frame title")
        widgetspot = self.get_widgetstack_counter()
        self.label_object = Label(self, text=self.model.title + " #" + str(self.pass_index +1))
        self.label_object.grid(row=widgetspot, column=0, columnspan=4, sticky=W) 
        self.label_object.config(background=self.bgcolor, font=("Arial", 18, "bold"), borderwidth=1, width=30, anchor=CENTER, justify=tkinter.LEFT)

        #Column labels:
        vert_position = self.get_widgetstack_counter()
        lbl_kw = {"width":20, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 12, "bold") }
        lbl = self.create_label("Record file field", vert_position, 0, **lbl_kw)
        lbl = self.create_label("Memory file field", vert_position, 1, **lbl_kw)
        #Row_index tracks ALL control rows in the current blocking pass (blocking fields, matching fields, cutoff values, etc.)
        self.row_index = 0				
        curvalue = 0 
		
        #*************************************
        #Display the Blocking Pass controls:
        #*************************************
        lbl_config = {"font": ("Arial", 12, "bold italic"), "background": "#FEF0A0", "fg": "#024CC6", "borderwidth":2, "width":80, "anchor":W}
        #BLOCKING FIELDS:
        if self.debug: self.model.logobject.logit("Displaying Blocking Field controls", True, True, True)
        i = 0
        self.rowtype = "blocking_fields"         #Each row in the CONTROLS list must be stamped with its row type (e.g., "blocking_fields", "matching_fields", etc.
        vert_position = self.get_widgetstack_counter()
        self.lbl_blockfld = Label(self, text="Blocking fields")
        self.lbl_blockfld.grid(row=vert_position, column=0, columnspan=4, sticky=W)
        self.lbl_blockfld.config(lbl_config)
        for item in self.model.meta_values_recfile:
            data_column_name = item[0]                      #data_column_name is the next column listed in the current data dictionary
            vert_position = self.get_widgetstack_counter()
            #Check to see whether this ROW in this BlockingPass was found in the PARMF.TXT parameters file (if a parmf file was specified). If so, find the value that the current control should be set to.
            curvalue = 0   
            control_type = "recfile_field"
            if self.debug: self.model.logobject.logit("\nAbout to check for a saved value in Parmf.txt file for data_column '%s' on pass %s, rowtype '%s', control_type '%s'" % (data_column_name, self.pass_index, self.rowtype, control_type) )
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, control_type, data_column_name)
            if parmdict:              #A Record File field was found for this ROW in the BLOCKING FIELDS SECTION.
                curvalue = 1          #Check the Checkbox      #parmdict["parm_value"] 
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for RecFile fld, row %s (BlockFld sect) parmdict:" % (self.row_index), True, True, True ) 
                #if self.debug: self.model.logobject.logit(parmdict, True, True, True)
            else:
                if self.debug: self.model.logobject.logit("(not found in parmf.txt for this blocking pass)", True, True, True)
            #************************************************
            ##Checkbox to indicate that this field should be included in the current Blocking Pass:
            chk = self.create_checkbox(data_column_name, vert_position, curvalue, "chkmainblk_" + self.rowtype[:2] + "_" + data_column_name, gridcolumn=0, width=12, font_size=11, rowindex=self.row_index, data_column_name=data_column_name, text=data_column_name)
            #************************************************
            ##Dropdown list of Memory File columns:			
            fieldnames = ['']     #Build a list of columns/fields in the MEMORY FILE, so we can display the list for the user to match these to RECORD FILE columns.
            for metavalue in self.model.meta_values_memfile:
                fieldnames.append(metavalue[0])
            curvalue = ''   
            control_type = "memfile_startpos"
            if self.debug: self.model.logobject.logit("\nAbout to check for a saved value in Parmf.txt file for data_column '%s' on pass %s, rowtype %s, control_type %s" % (data_column_name, self.pass_index, self.rowtype, control_type) )
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, control_type, data_column_name)
            if parmdict:             #A Memory File field was found for this ROW in the BLOCKING FIELDS SECTION.
                #For MEMORY FILE fields, we can't retrieve the FIELD NAME from the ParmF.txt file because it is referenced only by a starting position, not name.
                startpos = parmdict["parm_value"]
                curvalue = self.model.get_datafield_name_from_dict_startpos(startpos, "mem")
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for MemFile fld, row %s (BlockFld sect), curvalue='%s', parmdict:" % (self.row_index, curvalue), True, True, True ) 
                #if self.debug: self.model.logobject.logit(parmdict) 
                #if self.debug: self.model.logobject.logit(parmdict, True, True, True) 
            control_name = self.model.get_control_name("opt", self.rowtype, data_column_name, "memfld", str(self.pass_index) )    #get_control_name_prefix(widget_type, row_type, data_column_name, parm_type, blocking_pass_index)
            opt = self.create_optmenu(fieldnames, curvalue, control_name, vert_position, gridcolumn=1, width=12, rowindex=self.row_index, rowtype=self.rowtype, data_column_name=data_column_name, text=data_column_name)
            #************************************************
            ##Spinner for 0/1 value of Blank Flag.  Normally set to 1.			
            curvalue = '1'
            control_type = "blank_flag"
            if self.debug: self.model.logobject.logit("\nAbout to check for a saved value in Parmf.txt file for data_column '%s' on pass %s, rowtype %s, control_type %s" % (data_column_name, self.pass_index, self.rowtype, control_type) )
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, control_type, data_column_name)
            if parmdict:
                curvalue = parmdict["parm_value"]
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for BlankFlag, row %s (BlockFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict) 
            value_tuple = (0,1)
            control_name = self.model.get_control_name("spn", self.rowtype, data_column_name, "blankflag", str(self.pass_index) ) 
            spn = self.create_spinner(0, 1, value_tuple, control_name, vert_position, 2, "1", rowtype=self.rowtype, rowindex=self.row_index, controltype="spinner", data_column_name=data_column_name, text="")
            i += 1
            self.row_index += 1
        #***********************************
        #MATCHING FIELDS:
        i = 0
        curvalue = 0 
        self.rowtype = "matching_fields"
        vert_position = self.get_widgetstack_counter()
        self.lbl_matchfld = Label(self, text="Matching fields")
        self.lbl_matchfld.grid(row=vert_position, column=0, columnspan=4, sticky=W)
        self.lbl_matchfld.config(lbl_config) 
        for item in self.model.meta_values_recfile:
            data_column_name = item[0]                      #data_column_name is the next column listed in the current Memory File data dictionary
            vert_position = self.get_widgetstack_counter()
            #Check to see whether this Row in this BlockingPass was found in the PARMF.TXT parameters file (if a parmf file was specified)
            curvalue = 0   
            control_type = "recfile_field"
            if self.debug: self.model.logobject.logit("\nAbout to check for a saved value in Parmf.txt file for data_column '%s' on pass %s, rowtype %s, control_type %s" % (data_column_name, self.pass_index, self.rowtype, control_type) )
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, control_type, data_column_name)
            if parmdict:
                curvalue = 1    #parmdict["parm_value"] 
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for RecFile fld, row %s (MatchFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict)
            #Checkbox to indicate that this field should be included in the current Blocking Pass:
            chk = self.create_checkbox(data_column_name, vert_position, curvalue, "chkmainmtch_" + self.rowtype[:2] + "_" + data_column_name, gridcolumn=0, width=12, font_size=11, rowindex=self.row_index, rowtype=self.rowtype, data_column_name=data_column_name, text=data_column_name)
            #*********************************************************			
            #Dropdown list of Memory File columns:			
            fieldnames = ['']     #Build a list of columns/fields in the MEMORY FILE, so we can display the list for the user to match these to RECORD FILE columns.
            for metavalue in self.model.meta_values_memfile:
                fieldnames.append(metavalue[0])
            curvalue = ''
            control_type = "memfile_startpos"
            if self.debug: self.model.logobject.logit("\nAbout to check for a saved value in Parmf.txt file for data_column '%s' on pass %s, rowtype %s, control_type %s" % (data_column_name, self.pass_index, self.rowtype, control_type) )
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, control_type, data_column_name)
            if parmdict:
                #For MEMORY FILE fields, we can't retrieve the FIELD NAME from the ParmF.txt file because it is referenced only by a starting position, not name.
                startpos = parmdict["parm_value"]
                curvalue = self.model.get_datafield_name_from_dict_startpos(startpos, "mem")
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for MemFile fld, row %s (MatchFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict)
            control_name = self.model.get_control_name("opt", self.rowtype, data_column_name, "memfld", str(self.pass_index) )    #get_control_name_prefix(widget_type, row_type, data_column_name, parm_type, blocking_pass_index)
            opt = self.create_optmenu(fieldnames, curvalue, control_name, vert_position, gridcolumn=1, width=12, rowindex=self.row_index, rowtype=self.rowtype, data_column_name=data_column_name, text=data_column_name)
            #Hidden control - not displayed and always set to "0", but needs to be in the self.controls list because that's how values get written to the ParmF.txt parameter file.
            #curvalue = 0
            #control_name = "null_flag_" + str(self.row_index)
            #opt = self.create_hidden_control(curvalue, control_name, vert_position, gridcolumn=99, width=0, rowindex=self.row_index, rowtype=self.rowtype, data_column_name=data_column_name, text=data_column_name)
            #**********************************************************			
            #Dropdown list of Data Field Comparison Methods:			
            curvalue = ''
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "comparison_method", data_column_name)
            if parmdict:
                curvalue = parmdict["parm_value"]
                curvalue = self.model.get_compare_method_from_abbrev(curvalue)            #parm file stores a partial, not user-friendly text string
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for ComparFld, row %s (MatchFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict) 
            control_name = self.model.get_control_name("opt", self.rowtype, data_column_name, "compar", str(self.pass_index) )    
            opt = self.create_optmenu(self.model.compare_methods, curvalue, control_name, vert_position, gridcolumn=2, width=30, rowindex=self.row_index, data_column_name=data_column_name, text=data_column_name)
            #**********************************************************
            #Spinner for M-value:
            curvalue = self.model.default_m_value                                          #DEFAULT m-value
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "m-value", data_column_name)
            if parmdict:
                try:
                    curvalue = round(float(parmdict["parm_value"]) * 100, 0)    #M-values and U-values are stored in the PARMF.txt file as decimal numbers, but the Spinner needs to show whole numbers. (Parmf.txt file shows 0.76, spinner shows 76)
                    if str(curvalue).find(".0") != -1:
                        curvalue = int(str(curvalue).replace(".0", ""))
                except ValueError:
                    curvalue = 0
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for M-Value, row %s (MatchFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict) 
            value_tuple = (0,10,20,30,40,50,60,70,80,90,100)
            control_name = self.model.get_control_name("spn", self.rowtype, data_column_name, "m-value", str(self.pass_index) ) 
            spn = self.create_spinner(0, 100, value_tuple, control_name, vert_position, 3, curvalue, rowtype=self.rowtype, rowindex=self.row_index, controltype="spinner", data_column_name=data_column_name, text="")
            #**********************************************************
            #Spinner for U-value:
            curvalue = self.model.default_u_value                                          #DEFAULT u-value
            parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "u-value", data_column_name)
            if parmdict:
                try:
                    curvalue = round(float(parmdict["parm_value"]) * 100, 0)    #M-values and U-values are stored in the PARMF.txt file as decimal numbers, but the Spinner needs to show whole numbers. (Parmf.txt file shows 0.76, spinner shows 76)
                    if str(curvalue).find(".0") != -1:
                        curvalue = int(str(curvalue).replace(".0", ""))
                except ValueError:
                    curvalue = 0
                #if self.debug: self.model.logobject.logit("--After Get_cur_var...val() for U-Value, row %s (MatchFld sect), parmdict:" % (self.row_index) ) 
                #if self.debug: self.model.logobject.logit(parmdict) 
            control_name = self.model.get_control_name("spn", self.rowtype, data_column_name, "u-value", str(self.pass_index) ) 
            spn = self.create_spinner(0, 100, value_tuple, control_name, vert_position, 4, curvalue, rowtype=self.rowtype, rowindex=self.row_index, controltype="spinner", data_column_name=data_column_name, text="")
            i += 1
            self.row_index += 1
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            self.container.refresh_canvas()
        #**************************************
        #CUTOFF VALUES FOR THIS BLOCKING PASS:
        #For Cutoff Values and other non-datafield rows, MAKE SURE that no "fieldname" (data_column_name) is specified for this control in the Controls list! If specified, the code will attempt to find a field width and starting position for a non-existent datafield.
        data_column_name = ""
        #********************
        #Cutoff HiVal:
        self.rowtype = "cutoff_fields"                             #RowType determines where and how data is copied to the ParmF.txt parameters file.
        vert_position = self.get_widgetstack_counter()	           #Determine which ROW this occupies in the Frame
        label_text = "Output cutoffs - High:"
        gridcolumn = 0
        curvalue = 100
        parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "cutoff_hi", data_column_name)
        if parmdict:
            curvalue = parmdict["parm_value"]
            if self.debug: self.model.logobject.logit("__After calling get_current_variable_value(), parmdict is:") 
            if self.debug: self.model.logobject.logit(parmdict) 
        cutoff_kw = {"width":12, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 11, "bold")}  #, "data_column_name":data_column_name, "text":data_column_name}
        control_name = self.model.get_control_name("txt", self.rowtype, data_column_name, "cutoff_hi", str(self.pass_index) ) 
        txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **cutoff_kw)
        #Cutoff LowVal:
        label_text = "Low:"
        gridcolumn = 2
        curvalue = self.model.default_lo_cutoff                                         #DEFAULT low cutoff
        parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "cutoff_low", data_column_name)
        if parmdict:
            curvalue = parmdict["parm_value"]
            if self.debug: self.model.logobject.logit("__After calling get_current_variable_value(), parmdict is:") 
            if self.debug: self.model.logobject.logit(parmdict) 
        control_name = self.model.get_control_name("txt", self.rowtype, data_column_name, "cutoff_low", str(self.pass_index) ) 
        txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **cutoff_kw)
        self.row_index += 1
        #**********************
        #Print Cutoff HiVal:
        self.rowtype = "prcutoff_fields"                             #RowType determines where and how data is copied to the ParmF.txt parameters file.
        vert_position = self.get_widgetstack_counter()	           #Determine which ROW this occupies in the Frame
        label_text = "Print output cutoffs - High:"
        gridcolumn = 0
        curvalue = self.model.default_hi_cutoff                                          #DEFAULT hi cutoff
        parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "prcutoff_hi", data_column_name)
        if parmdict:
            curvalue = parmdict["parm_value"]
            if self.debug: self.model.logobject.logit("\n After calling get_current_variable_value(), parmdict is:") 
            if self.debug: self.model.logobject.logit(parmdict) 
        control_name = self.model.get_control_name("txt", self.rowtype, data_column_name, "prcutoff_hi", str(self.pass_index) ) 
        txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **cutoff_kw)
        #Print Cutoff LowVal:
        label_text = "Low:"
        gridcolumn = 2
        curvalue = self.model.default_lo_prcutoff                                          #DEFAULT low Print Cutoff
        parmdict = self.model.get_current_variable_value(self.pass_index, self.rowtype, "prcutoff_low", data_column_name)
        if parmdict:
            curvalue = parmdict["parm_value"]
            if self.debug: self.model.logobject.logit("\n After calling get_current_variable_value(), parmdict is:") 
            if self.debug: self.model.logobject.logit(parmdict) 
        control_name = self.model.get_control_name("txt", self.rowtype, data_column_name, "prcutoff_low", str(self.pass_index) ) 
        txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **cutoff_kw)
        self.row_index += 1

    def get_widgetstack_counter(self, who_called=''):
        if(self.widgetstack_counter == None):
            self.widgetstack_counter = 0
        else:  
            self.widgetstack_counter += 1
        #print("\n" + "widgetstack_counter: " + str(self.widgetstack_counter) + "  " + who_called )
        return self.widgetstack_counter

    def create_label(self, text, gridrow, gridcolumn, **kw):
        lbl = Label(self, text=text)
        lbl.grid(row=gridrow, column=gridcolumn, sticky=W) 
        lbl.config(**kw)

    def create_textbox(self, label_text, gridrow, gridcolumn, curvalue='', textbox_name='txt_unknown', data_column_name='', rowtype='unknown', **kw):       #gridcolumn=0, width=12, font_size=12, rowindex=0
        #cutoff_kw = {"width":12, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 12, "bold"), "data_column_name":data_column_name, "text":data_column_name}
        #print("\n About to display textbox '" + label_text + "'")
        if(label_text):
            lbl = Label(self, text=label_text)
            lbl.grid(row=gridrow, column=gridcolumn, sticky=W) 
            lbl.config(background=self.bgcolor, font=("Arial", 10, "bold"), width=26)
        var = StringVar(self)
        var.set(curvalue)   #
        txt = Entry(self, textvariable=var)
        txt.grid(row=gridrow, column=gridcolumn+1, sticky=W)
        txt.config(**kw)
        #Add this control to the controls collection:		
        self.model.add_control_to_list(var, blockpass=self.pass_index, fieldname=data_column_name, refname=textbox_name, rowtype=self.rowtype, rowindex=self.row_index, controltype="textbox", text=data_column_name)

    def create_checkbox(self, label_text, gridrow, curvalue=0, chkbox_name='chk_unknown', **kw):       #gridcolumn=0, width=12, font_size=11, rowindex=0
        #print("\n About to display checkbox '" + label_text + "'")
        var = StringVar(self)
        var.set(curvalue)   #CurValue is set to 1 if already selected (i.e., specified in parmf.txt file). The ParmF value is checked by function get_current_variable_value()
        gridcolumn = kw["gridcolumn"]
        font_size = kw["font_size"]
        width = kw["width"]
        chk = Checkbutton(self, text=label_text, variable=var)
        chk.grid(row=gridrow, column=gridcolumn, sticky=W)
        chk.config(background=self.bgcolor, font=("Arial", font_size, "bold"), borderwidth=2, width=width, anchor=W)
        #Add this control to the controls collection:		
        self.model.add_control_to_list(var, blockpass=self.pass_index, fieldname=kw["data_column_name"], refname=chkbox_name, rowtype=self.rowtype, rowindex=kw["rowindex"], controltype="checkbox", text=kw["text"])

    def create_optmenu(self, value_list, curvalue='', optmenu_name='', gridrow=None, **kw):     #gridcolumn=1, width=12, rowindex=0
        var = StringVar(self)
        var.set(curvalue)
        gridcolumn = kw["gridcolumn"] 
        optmenu = OptionMenu(self, var, *value_list, command=lambda x:self.capture_menu_click(optmenu_name, var) )
        optmenu.grid(column=gridcolumn, row=gridrow, sticky=W)                #position the Frame within the container Window or Frame
        optmenu.config(font=('calibri',(10)), bg='white', width=kw["width"])
        optmenu['menu'].config(background=self.bgcolor, font=("calibri",(12)),bg='white')
        #Add this control to the controls collection:		
        #var_dict = {"blockpass": self.pass_index, "refname": optmenu_name, "rowtype": self.rowtype, "rowindex": kw["rowindex"], "object": var, "value": var.get()}
        self.model.add_control_to_list(var, blockpass=self.pass_index, fieldname=kw["data_column_name"], refname=optmenu_name, rowtype=self.rowtype, rowindex=kw["rowindex"], controltype="optmenu", text=kw["text"])

    def create_spinner(self, from_=0, to=100, value_tuple=(), spinner_name='', gridrow=None, gridcolumn=1, curvalue=1, **kw):
        #print("\n Creating Spinbox with gridrow " + str(gridrow) + " and column " + str(gridcolumn))
        var = StringVar(self)
        var.set(curvalue)
        if value_tuple:
            spn = Spinbox(self, values=value_tuple)
        else:
            spn = Spinbox(self, from_=from_, to=to)
        spn.grid(row=gridrow, column=gridcolumn, sticky=W)
        spn.config(textvariable=var, background=self.bgcolor, width=8)		
        #Add this control to the controls collection:		
        self.model.add_control_to_list(var, blockpass=self.pass_index, fieldname=kw["data_column_name"], refname=spinner_name, rowtype=self.rowtype, rowindex=kw["rowindex"], controltype="optmenu", text=kw["text"])

    def create_hidden_control(self, curvalue, control_name, vert_position, gridcolumn=99, width=0, rowindex=0, rowtype="", data_column_name="", text=""):
        var = StringVar(self)
        var.set("")
        self.model.add_control_to_list(var, blockpass=self.pass_index, fieldname="hidden", refname="hidden_" + str(rowindex), rowtype=self.rowtype, rowindex=rowindex, controltype="hidden", text="") 

    def capture_menu_click(self, optmenu_name, var):
        print("\n YOU HAVE CAPTURED THE VALUE: " + str(var.get()) + " FOR " + optmenu_name )
        return True

 # End of class BlockingPass_View


#******************************************************************************************		
class Control():
    debug = False
    error_message = None
    value_object = None    #A Tkinter StringVar() variable which holds the value of this object.
    value = None           #Actual string value, accessed as StringVar().get()
    blocking_pass = None   #
    row_index = None       #
    control_index = None   #
    ref_name = None        #
    field_name = None
    control_type = None
    startpos_recfile = None
    width_recfile = None
    width_memfile = None
    startpos_memfile = None
    row_type = None
    text = None
	#Comparison methods for BigMatch:
    #compare_methods = []	

    def __init__(self, stringvar, control_index, **kw):
        self.value_object = stringvar
        self.value = self.value_object.get()
        #for key, value in kw.items():
        #    print(key + " = " + str(value))
        if self.check_key_exists("blockpass", **kw):
            self.blocking_pass = kw["blockpass"]
        if self.check_key_exists("rowindex", **kw):
            self.row_index = kw["rowindex"]
        if self.check_key_exists("rowtype", **kw):
            self.row_type = kw["rowtype"]
        #self.control_index = kw["controlindex"]
        if self.check_key_exists("controltype", **kw):
            self.control_type = kw["controltype"]
        if self.check_key_exists("fieldname", **kw):
            self.field_name = kw["fieldname"]
        if self.check_key_exists("refname", **kw):
            self.ref_name = kw["refname"]
        if self.check_key_exists("startpos_recfile", **kw):
            self.startpos_recfile = kw["startpos_recfile"]
        if self.check_key_exists("width_recfile", **kw):
            self.width_recfile = kw["width_recfile"]
        if self.check_key_exists("startpos_memfile", **kw):
            self.startpos_memfile = kw["startpos_recfile"]
        if self.check_key_exists("width_memfile", **kw):
            self.width_memfile = kw["width_memfile"]
        if self.check_key_exists("text", **kw):
            self.text = kw["text"]

    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        #if keyvalue in dict:
        #    found = True
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found

    def display_properties(self):
        #for key,value in __dict__.items():
        #    print("%s = '%s'" % (str(key), str(value) ) )
        pass        
        
    def write_control_as_dict(self):
        var_dict = { "object": self.value_object, "value": self.value_object.get(), "blockpass": self.blocking_pass, "rowindex": self.row_index, "controlindex": self.control_index, "fieldname": self.fieldname, "controltype": self.controltype, "refname": self.refname, "startpos_recfile": startpos_recfile, "width_recfile": width_recfile, "startpos_memfile": startpos_memfile, "width_memfile": width_memfile, "rowtype": self.rowtype, "text": self.text}
        return var_dict

    def add_new(self):
        pass

#End class Control		

#******************************************************************************************		
class ControlRow():
    debug = False
    error_message = None
    blocking_pass = None   #
    row_index = None       #
    row_type = None
    
    def add_new(self):
        pass

#End class ControlRow

#******************************************************************************************		
#******************************************************************************************		
def main():
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    '''Geometry for all windows in this app is set by main.py '''
    root = Tk()
    root.geometry("500x500+80+80")
    master = BlockingPass_Model()
    master.display_view(root)
    root.mainloop()

if __name__ == '__main__':
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    main()  

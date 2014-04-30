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
from Datafile_to_RDBMS import *

gl_frame_color = "ivory"
gl_frame_width = 400
gl_frame_height = 100
gl_file_textbox_width = 80   

#******************************************************************************************
class CSVFile_to_Flatfile_UI_Model():
    debug = True
    error_message = None
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    dxr = None                              #Instance of the Datafile_to_RDBMS() class
    source_format = None                    #Flat text file by default
    output_format = None                    #Sqlite3 by default
    source_file = None	                    #Name and path of the source file to be converted
    output_file = None			            #Sqlite file (if sqlite is the RDBMS)
    datadict_file = None
    filepathobj_load_from = None            #FilePath object to allow user to select a file
    filepathobj_save_to = None              #FilePath object to allow user to select a file
    filepathobj_datadict = None             #FilePath object to allow user to select a data dictionary (for parsing text into distinct columns)
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
	
    def __init__(self, parent_window, controller, source_format=None, output_format=None, source_file=None, output_file=None, show_view=None, title='File converson', **kw):      #, bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height
        self.parent_window = parent_window  #parent_window is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        now = datetime.datetime.now()
        self.init_time = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + ' ' + str(now.hour).rjust(2,'0') + ':' + str(now.minute).rjust(2,'0')
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\n\n____________________________________________________________________", True, True )
        self.logobject.logit("\nIn CSVFile_to_Flatfile_UI_Model._init_: source_file='%s' -- and type(controller)=%s" % (source_file, type(controller)), True, True )
        self.source_format = source_format
        self.output_format = output_format
        self.source_file = source_file
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

    def set_source_format(self, source_format):
        self.source_format = source_format
        print("\nSetting the source_format to: %s" % (source_format) )

    def set_output_format(self, output_format):
        self.output_format = output_format
        print("\nSetting the output_format to: %s" % (output_format) )

    def convert_file(self, source_format=None, output_format=None):
        '''Called after the user has selected a source file and an output file '''
        if not source_format:
            source_format = self.source_format
        if not output_format:
            output_format = self.output_format
        source_format = source_format.lower().strip()
        output_format = output_format.lower().strip()
        #Based on source and output formats, call the appropriate function to handle the conversion.
        if source_format == "txt" and output_format[:6] == "sqlite":
            self.convert_txt_to_sqlite(self.source_file, self.output_file)
        
    def convert_txt_to_sqlite(self, source_file=None, output_file=None): 
        '''DOCSTRING '''
        if not source_file:
            source_file = self.source_file
        if not output_file:
            output_file = self.output_file
        #Instantiate the Datafile_to_RDBMS class
        self.converter = Datafile_to_RDBMS()
        self.logobject.logit("\nAbout to convert file '%s' to table in RDBMS '%s'" % (source_file, output_file), True, True )
        self.converter.datafile = source_file
        head, tail = os.path.split(source_file)
        db_tablename = tail.lower().strip()
        dotpos = db_tablename.find(".")
        if(dotpos != -1):
            db_tablename = db_tablename[:dotpos].replace(".", "")
        self.converter.db_tablename = db_tablename
        self.converter.db_catalog = output_file
        self.converter.db_platform = "sqlite3"
        self.logobject.logit("\n Type of self.converter: %s" % (str(type(self.converter))), True, True )
        #if(str(type(self.converter)).lower().find("datafile_to_rdbms") == -1):    #When the class is first instantiated, load the data dictionary
        if len(self.converter.datadict) == 0:
            self.copy_datadict_to_class_properties()
        self.converter.display_datadict()
        #*******************************************
        self.converter.import_data()
        #*******************************************
        return self.converter.error_message

    def instantiate_view_object(self, container):
        self.view_object = CSVFile_to_Flatfile_UI_View(container, self) 
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
                count = 0
                for row in csvreader:
                    if count == 0:                                 #Top row of CSV
                        self.build_column_header_list(row)
                        break
                #Ascertain the correct position within the Data Dictionary where column name, width and startpos are stored
                pos_colname = int(self.get_position_of_datadict_column("column_name"))
                pos_width = int(self.get_position_of_datadict_column("width"))
                pos_startpos = int(self.get_position_of_datadict_column("start_pos"))
                count = 0
                for row in csvreader:
                    #NOTE: CSV reader is a forward-only reader -- and it has already read row 0, the top row.  So now the next row WILL BE ROW 1!
                    #Add this column from the data dictionary to the list of columns that will be created in the RDBMS
                    #self.logobject.logit("Dict row " + str(count) + ": " + row[0] + " " +row[1] + " " +row[2] + " " +row[3] + " " +row[4] + " " +row[5], True, True )
                    self.converter.add_column(row[pos_colname], "char", row[pos_width], row[pos_startpos], "file")
                    count += 1
                csvfile.close()
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

    def build_column_header_list(self, hdr_row):
        col_index = 0
        for col_hdr in hdr_row:
            col_hdr = col_hdr.strip()
            self.logobject.logit("(%s) col_hdr: %s" % (col_index, col_hdr), True, True )
            temp = {"col_index":col_index, "col_hdr":col_hdr, "max_width":0, "start_pos":0, "data_type":"", "selected":""}
            self.csv_column_headers.append(temp)
            col_index += 1

    def display_view(self, container=None):
        #Most often, we will display the form in the main class's BigCanvas.BigFrame "container".
        self.logobject.logit("In DataFile_RDBMS_UI.Display_View, Type of Container is '%s'" % (str(type(container))), True, True )
        kw_dict = {"width":self.frame_width, "background":self.bgcolor, "borderwidth":2, "padx":3, "pady":3}
        if container == None:
            container = self.controller.bigcanvas.bigframe			#This is the default canvas/frame object on which all other widgets are displayed.
        if self.view_object is None:                                #We have not yet instantiated the View.  Make sure to display any Open File dialogs at top before rendering other views.
            self.instantiate_view_object(container)					#Just in case we need to run this module outside the parent frame during testing.
			#Display a file open dialog so the user can point us to the Data Dictionary they'd like to open:
            self.display_openfile_dialogs(container, self.source_file)
            self.display_user_buttons(container)
            #print("\n In CSVFile_to_Flatfile_UI_Model.display_view(), about to call view_object.initUI().")
            #Display the VIEW for this data dictionary  
            #self.view_object.initUI(**kw_dict)   #width=self.frame_width, background=self.bgcolor, borderwidth=2, padx=3, pady=3)
        else:        
            #self.view_object.display_datadict_in_grid(**kw_dict)    #When first initiated, the View object will call this during its InitUI() method.  But to refresh it afterwards, call display_datadict_in_grid() explicitly.
            self.controller.refresh_main_canvas()

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "CSV_to_FLatfile_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.button_frame.grid(row=stackslot, column=0, sticky=W)
        self.button_frame.config(background=self.bgcolor)
        #Button to launch the conversion process:
        self.btnSaveToFile = Button(self.button_frame, text="Convert File", width=30, command=self.convert_file)   #convert_txt_to_sqlite
        self.btnSaveToFile.grid(row=0, column=1, sticky=W)
        self.btnSaveToFile.config(state=DISABLED)       #Do not enable this button unless the user has selected a Data Dictionary file to save as

    def display_openfile_dialogs(self, container, default_filepath=''):
        file_types = [('All files', '*'), ('SAS files', '*.sas7bdat; *.txt')]
        kw_fpath = {"bgcolor":self.bgcolor, "frame_width":"", "frame_height":"", "file_category":"datadict"}
        open_or_save_as = "open"
        self.filepathobj_load_from = FilePath_Model(self.parent_window, self, self.controller, "Source file to load:", open_or_save_as, "ConvertSourceToLoad", file_types, **kw_fpath)
        self.filepathobj_load_from.display_view(container)	        #Display the dialog for user to select a data dict file
        open_or_save_as = "save_as"
        self.filepathobj_save_to = FilePath_Model(self.parent_window, self, self.controller, "Sqlite .DB file:", open_or_save_as, "ConvertOutputToSaveAs", file_types, **kw_fpath)
        self.filepathobj_save_to.display_view(container)	        #Display the dialog for user to Save As... a new data dict file
        open_or_save_as = "open"
        self.filepathobj_datadict = FilePath_Model(self.parent_window, self, self.controller, "Data dictionary to define database columns:", open_or_save_as, "DatadictToLoad", file_types, **kw_fpath)
        self.filepathobj_datadict.display_view(container)            #Display the Open File dialog
		
    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        '''IMPORTANT: ALL FilePath objects created by this class will expect Function "update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        #self.logobject.logit("Master DataDict_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string), True, True )
        print("Master CSVFile_to_Flatfile_UI_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string))
        if callback_string.lower().strip()[:4] == "load" or callback_string.lower().strip()[:4] == "open":
            if str(callback_string).lower()[4:].find("datadict") != -1:      #User selected a DataDictionary file
                self.logobject.logit("datadict_file is being set to %s" % (file_name_with_path), True, True )
                self.datadict_file = file_name_with_path        #file_name_with_path is the name/path of the file selected by the user. We know to store this to self.source_file because of the "callback string" returned by the FilePath object.
                if self.datadict_file:                          #Refresh the view when the user selects a new file.
                    self.display_view()
                else:                                           #No file was specified (user might have cleared out a previously selected file name) 
                    self.view_object.clear_datadict_grid()      #Remove all existing values from the grid
            else:                                               #User selected the Source File
                self.source_file = file_name_with_path          #file_name_with_path is the name/path of the file selected by the user. We know to store this to self.source_file because of the "callback string" returned by the FilePath object.
                if self.source_file:                            #Refresh the view when the user selects a new file.
                    self.display_view()
                else:                                           #No file was specified (user might have cleared out a previously selected file name) 
                    self.view_object.clear_datadict_grid()      #Remove all existing values from the grid
        elif callback_string.lower().strip()[:4] == "save":     #This is a file SAVE AS, not a FILE OPEN
            self.output_file = file_name_with_path
            if self.output_file:
                self.btnSaveToFile.config(state=NORMAL)
            else:
                self.btnSaveToFile.config(state=DISABLED)
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
        self.filepathobj_load_from.calc_initial_dir_for_file_open(self.source_file, "datadict", "")
        self.filepathobj_save_to.calc_initial_dir_for_file_open(self.output_file, "datadict", "")
        self.filepathobj_datadict.calc_initial_dir_for_file_open(self.datadict_file, "datadict", "")
        
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
class CSVFile_to_Flatfile_UI_View(Frame):
    debug = True
    container = None
    #controller = None
    model = None
    entry_grid = None
	
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
        print("\n" + "In CSVFile_to_Flatfile_UI_View._init_, source_file = '" + str(self.model.source_file) + "' -- and show_view=" + str(self.model.show_view) )
        if self.model.show_view:
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the parent window, directly below any previous frames. The grid() ROW designators refer to the parent window's Grid and determine which order the Frames will be displayed in.
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "CSVFile_to_Flatfile_UI_View.initUI()")
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
        #
        #*************************************************************************************
        #Entry Grid code is courtesy of bvdet at http://bytes.com/topic/python/answers/882126-grid-view-table-list-tkinter '''
        #self.lblDictHeader = Label(self, text=self.model.title)
        #self.lblDictHeader.grid(row=0, column=0, columnspan=12, sticky=W) 
        #self.lblDictHeader.config(font=("Arial", 14, "bold"), borderwidth=1, width=100, justify="left")
        #self.lblDictHeader.config(**kw)
        #self.lblSpacer = Label(self, text=" ")
        #self.lblSpacer.grid(row=0, column=1, sticky=W+N+E+S) 
        #self.lblSpacer.config(borderwidth=0, width=4)
        #self.lblSpacer.config(**kw)
		#Display the Data Dict file in a grid:
        '''self.display_datadict_in_grid(**kw)'''

    #***********************************************************************************************************************************
    '''def display_datadict_in_grid(self, **kw):
        #Populate the grid, based on META_xx arrays read in from the Data Dictionary file.
        already_init = self.entry_grid.has_been_initialized()
        #self.model.logobject.logit("\n Already_init=%s " % (str(already_init) ), True, True )   #... About to call clear_grid() from initUI() in CSVFile_to_Flatfile_UI_View.
        print("\n Already_init=%s " % (str(already_init) ))   #... About to call clear_grid() from initUI() in CSVFile_to_Flatfile_UI_View.
        #self.entry_grid.clear_grid()
        #Re-populating the data dictionary display grid is a significantly different process from initial load.
        if already_init == True:
            #self.model.logobject.logit("\n" + "About to call repopulate_grid() from CSVFile_to_Flatfile_UI_View.display_datadict_in_grid(). # Columns: " + str(len(self.model.meta_columns)) +  "# Rownums: " + str(len(self.model.meta_rownums)) + " # meta-value-rows: " + str(len(self.model.meta_values)), True, True )
            print("\n" + "About to call repopulate_grid() from CSVFile_to_Flatfile_UI_View.display_datadict_in_grid(). # Columns: " + str(len(self.model.meta_columns)) +  "# Rownums: " + str(len(self.model.meta_rownums)) + " # meta-value-rows: " + str(len(self.model.meta_values)))
            self.entry_grid.repopulate_grid(self.model.meta_columns, self.model.meta_rownums, self.model.meta_values)
        else:
            #self.model.logobject.logit("\n" + "About to call initialize_grid() from initUI() in CSVFile_to_Flatfile_UI_View. # Columns: " + str(len(self.model.meta_columns)) +  "# Rows: " + str(len(self.model.meta_rownums)) + " # value-rows: " + str(len(self.model.meta_values)), True, True )
            print("\n" + "About to call initialize_grid() from initUI() in CSVFile_to_Flatfile_UI_View. # Columns: " + str(len(self.model.meta_columns)) +  "# Rows: " + str(len(self.model.meta_rownums)) + " # value-rows: " + str(len(self.model.meta_values)))
            self.entry_grid.initialize_grid(self.model.meta_columns, self.model.meta_rownums, self.model.meta_values)

    def clear_datadict_grid(self):
        self.entry_grid.clear_all()
    '''
    #***********************************************************************************************************************************
    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        #self.model.logobject.logit("Master CSVFile_to_Flatfile_UI_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string), True, True )
        print("Master CSVFile_to_Flatfile_UI_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string))
        self.source_file = file_name_with_path

#******************************************************************************************		
def main():
    root = Tk()
    root.geometry("900x600+100+100")
    master = BigMatchController(root)
    root.mainloop()

if __name__ == '__main__':
    main()  
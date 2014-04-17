#!C:\Python33\python.exe -u
#!/usr/bin/env python
'''http://stackoverflow.com/questions/16429716/opening-file-tkinter '''
''' python c:\greg\code\python\Gms_TkFileSystem5_try_button.py '''  
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from TkEntry import EntryGrid
import csv
import os 
from os import path
from FilePath import *
from CHLog import *

gl_frame_color = "ivory"
gl_frame_width = 400
gl_frame_height = 100
gl_file_textbox_width = 80   

#******************************************************************************************
class DataDict_Model():
    debug = True
    error_message = None
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    datadict_file_to_load_from = None	    #Data dictionary file name and path, which will be loaded into the entry grid if user requests.
    #datadict_loadfile_displaybox = None	#A textbox where the data dict file to be loaded will be displayed
    datadict_file_to_save_to = None			#Data dictionary file name and path, to which the metadata will be saved if user requests.
    #datadict_savefile_displaybox = None	#A textbox where the save-to data dict file will be displayed
    filepathobj_load_from = None            #FilePath object to allow user to select a file
    filepathobj_save_to = None              #FilePath object to allow user to select a file
    title = ''							    #Title to be displayed in the Frame object
    mem_or_rec = None                       #Is this datadict associated with a Record File or a Memory File?
    bgcolor = 'ivory'						#Background color of the Frame widget that displays the Data Dictionary contents
    frame_width = None 
    frame_height = None
    view_object = None
    show_view = None
    #Arrays to hold the contents of the Data Dictionary:
    meta_columns = None					  #List of column names within the data dictionary CSV (column_name, column_width, etc.)
    meta_rownums = None	  				  #For convenience, a simple List of integers that will be displayed vertically on the left side of the Data Dict grid display.
    meta_values = None					  #List of values for each cell within the data dictionary CSV (actually a list of lists - a list of "rows" from the data dictionary CSV)
    meta_values_after_edit = []           #List of values from the Entry Grid, AFTER the user has modified the values and clicked SAVE.
    btnLoadDictFile = None
    btnSaveToDictFile = None
	
    def __init__(self, parent_window, controller, datadict_file_to_load_from=None, show_view=None, title='Data dictionary', **kw):      #, bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height
        #Frame.__init__(self, parent_window)
        self.parent_window = parent_window  #parent_window is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        print("\nIn DataDict._init_, datadict_file_to_load_from = '" + str(self.datadict_file_to_load_from) + "' -- and show_view=" + str(self.show_view))
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\nIn DataDict._init_: datadict_file_to_load_from = '" + str(self.datadict_file_to_load_from) + "' -- and show_view=" + str(self.show_view), True, True )
        self.title = title
        self.show_view = show_view
        self.datadict_file_to_load_from = datadict_file_to_load_from
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
        if self.check_key_exists("mem_or_rec", **kw):
            self.mem_or_rec = str(kw["mem_or_rec"]).lower().strip()

    def read_datadict_file_into_arrays(self, file_name):  
        '''A data dictionary CSV file is read into arrays (which are properties of this Model object). From the arrays they can be written back to a CSV file later. '''	
        #self.logobject.logit("\n" + "In DataDict.read_datadict_file_into_arrays, datadict_file_to_load_from = '" + str(file_name) + "'", True, True)
        print("\n" + "In DataDict.read_datadict_file_into_arrays, datadict_file_to_load_from = '" + str(file_name) + "'", True, True)
        self.meta_columns = []
        self.meta_rownums = []
        self.meta_values = []
        datadict_arrays = {}
        f = open(file_name, "r")
        content = f.readlines()
        i = 0
        for line in content:
            print(line)
            if(i==0):                                    #Header row in the CSV file
                self.meta_columns = line.split(",")
            else:
                meta_temp = line.split(",")             #meta_temp is a LIST consisting of one row from the data dictionary
                self.meta_values.append(meta_temp)		#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
                self.meta_rownums.append(str(i))
            i += 1

    def write_datadict_from_entrygrid(self, file_name=None):
        if file_name is None:
            file_name = self.datadict_file_to_save_to
        print("\n Top of write_datadict_from_entrygrid(), file_name is '%s'" % (file_name) ) 
        #Call the View object to retrieve Entry Grid values (after they have been update by the user).
        if file_name:
            del self.meta_values_after_edit[:]    
            self.meta_values_after_edit = []      #Clear out any previous entries
            #Load the entry grid items into the meta_values_after_edit list:			
            self.meta_values_after_edit = self.view_object.retrieve_grid_values()
            if self.meta_values_after_edit:
                newrow = []
                #self.logobject.logit("Dict file in write_datadict_from_entrygrid(): %s ...File will be deleted if it already exists." % ( str(file_name) ), True, True )
                print("Dict file in write_datadict_from_entrygrid(): %s ...File will be deleted if it already exists." % ( str(file_name) ))
                if os.path.isfile(file_name):
                    os.remove(file_name)		              #Should not need to delete the file, but it has been appending new text at end of file instead of erasing existing text and re-writing-- even though the file open uses "w" not "w+", and it is closed after every write session.
                with open(file_name, 'w', encoding='UTF8') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')   #os.linesep)    #chr(13) + chr(10)
                    #Get a list of column names retrieved from the Entry Grid -- these are CSV header columns.
                    j = 0;
                    for col in self.view_object.entry_grid.colList:
                        newcol = str(col).replace("\n", "").strip()
                        newcol = newcol.replace(chr(10), "")
                        newcol = newcol.replace(chr(13), "")
                        if (j == 0 and newcol == ''):				#First "column name" is usually blank because it is the row-numbers column, which has no header caption
                            pass
                        else:
                            newrow.append(newcol)
                        j += 1
                    csvwriter.writerow(newrow)						#Write the Column Headers to the CSV file			
                    newrow = []
                    i = 0
                    for row in self.meta_values_after_edit:
                        #self.logobject.logit("\n In write_datadict(), ROW: %s (length is %s and type is %s" % (str(i), str(len(row)), str(type(row)) ), True, True)
                        print("\n In write_datadict(), ROW: %s (length is %s and type is %s" % (str(i), str(len(row)), str(type(row)) ) )
                        #self.logobject.logit(row, True, True)
                        print(row)
                        newrow = []
                        j = 0
                        for col in row:
                            #if col.find("\n") != -1:
                            #    print("Reassigning col %s in row %s to a string value," % (str(j), str(i)) )
                            #    #row[i] = newcol    #str(col)
                            #else:
                            #newcol = str(col)
                            rowcheck = ', '.join(row)
                            if rowcheck.replace(',', '').strip() != '':
                                print("Next Row to be written: %s" % (rowcheck) )
                                newcol = str(col).replace("\n", "")
                                newcol = newcol.replace(chr(10), "")
                                newcol = newcol.replace(chr(13), "")
                                #print(newcol)
                                newrow.append(newcol)
                            j += 1
                        #print(newrow)
                        csvwriter.writerow(newrow)
                        i += 1
                
                    csvfile.close()

    def load_standard_datadict_headings(self):
        self.meta_columns = []
        self.meta_columns = ['column_name', 'start_pos', 'width', 'unique_id_yn', 'matchfield_yn', 'bigmatch_type', 'data_format', 'comments']
        return self.meta_columns

    def instantiate_view_object(self, container):
        self.view_object = DataDict_View(container, self) 
        return self.view_object	

    def display_view(self, container=None):
        #Most often, we will display the Data Dictionary form in the main class's BigCanvas.BigFrame "container".
        print("In DataDict.Display_View, Type of Container is '%s'" % (str(type(container))) )
        kw_dict = {"width":self.frame_width, "background":self.bgcolor, "borderwidth":2, "padx":3, "pady":3}
        if container == None:
            container = self.controller.bigcanvas.bigframe			#This is the default canvas/frame object on which all other widgets are displayed.
            #self.controller.clear_main_canvas()
        if self.datadict_file_to_load_from:	
            #Function "read_datadict_file_into_arrays" extracts the contents of the Data Dictionary file and stores it in arrays. The arrays are them passed to TkEntry to be displayed.
            print("\n" + "In DataDict.display_view(), about to run read_datadict_file_into_arrays() with '" + str(self.datadict_file_to_load_from) + "'" )
            self.read_datadict_file_into_arrays(self.datadict_file_to_load_from)
        if self.view_object is None:                                #We have not yet instantiated the View.  Make sure to display any Open File dialogs at top before rendering other views.
            self.instantiate_view_object(container)					#Just in case we need to run this module outside the parent frame during testing.
			#Display a file open dialog so the user can point us to the Data Dictionary they'd like to open:
            self.display_openfile_dialogs(container, self.datadict_file_to_load_from)
            self.display_user_buttons(container)
            print("\n In DataDict.display_view(), about to call view_object.initUI().")
            #Display the VIEW for this data dictionary        
            self.view_object.initUI(**kw_dict)   #width=self.frame_width, background=self.bgcolor, borderwidth=2, padx=3, pady=3)
        else:        
            self.view_object.display_datadict_in_grid(**kw_dict)    #When first initiated, the View object will call this during its InitUI() method.  But to refresh it afterwards, call display_datadict_in_grid() explicitly.
            self.controller.refresh_main_canvas()

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "DataDict_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.button_frame.grid(row=stackslot, column=0, sticky=W)
        self.button_frame.config(background=self.bgcolor)
        #Note: the specified CSV data dictionary file is loaded automatically when the user selects it (because update_filepath() is called )
        #self.btnLoadDictFile = Button(self.button_frame, text="Load Data Dictionary from CSV File", width=30, command=self.display_view)
        #self.btnLoadDictFile.grid(row=0, column=0, sticky=W)
        #self.btnLoadDictFile.config(state=DISABLED)       #Do not enable this button unless the user has selected a Data Dictionary file to load
        self.btnSaveToDictFile = Button(self.button_frame, text="Save Data Dictionary to CSV File", width=30, command=self.write_datadict_from_entrygrid)
        self.btnSaveToDictFile.grid(row=0, column=1, sticky=W)
        self.btnSaveToDictFile.config(state=DISABLED)       #Do not enable this button unless the user has selected a Data Dictionary file to save as

    def display_openfile_dialogs(self, container, default_filepath=''):
        file_types = [('All files', '*'), ('Text files', '*.csv;*.txt')]
        kw_fpath = {"bgcolor":self.bgcolor, "frame_width":"", "frame_height":"", "file_category":"datadict"}
        open_or_save_as = "open"
        self.filepathobj_load_from = FilePath_Model(self.parent_window, self, self.controller, "Data dictionary file to load:", open_or_save_as, "DataDictToLoad", file_types, **kw_fpath)
        self.filepathobj_load_from.display_view(container)	        #Display the dialog for user to select a data dict file
        open_or_save_as = "save_as"
        self.filepathobj_save_to = FilePath_Model(self.parent_window, self, self.controller, "Save data dictionary to file:", open_or_save_as, "DataDictToSaveAs", file_types, **kw_fpath)
        self.filepathobj_save_to.display_view(container)	        #Display the dialog for user to Ave As... a new data dict file
		
    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        '''IMPORTANT: ALL FilePath objects created by this class will expect Function "update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        #self.logobject.logit("Master DataDict_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string), True, True )
        print("Master DataDict_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string))
        if callback_string.lower().strip()[:4] == "load" or callback_string.lower().strip()[:4] == "open":
            self.datadict_file_to_load_from = file_name_with_path
            #if file_name_with_path:                        #Commented this out because btnLoadDictFile seems to be unnecessary - we automatically load the Data Dict
            #    self.btnLoadDictFile.config(state=NORMAL)
            #Refresh the Data Dictionary view when the user selects a new DataDict file.
            if self.datadict_file_to_load_from: 
                self.display_view()
            else:                                           #No file was specified (user might have cleared out a previously selected file name) 
                self.view_object.clear_datadict_grid()      #Remove all existing values from the grid
        elif callback_string.lower().strip()[:4] == "save": #This is a file SAVE AS, not a FILE OPEN
            self.datadict_file_to_save_to = file_name_with_path
            if self.datadict_file_to_save_to:
                self.btnSaveToDictFile.config(state=NORMAL)
            else:
                self.btnSaveToDictFile.config(state=DISABLED)
        self.update_master_paths(file_name_with_path)
        self.update_initial_dir_for_file_open_dialogs()
 
    def update_master_paths(self, file_name_with_path):
        if file_name_with_path:
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head
            self.controller.datadict_dir_last_opened = head                   #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            if self.mem_or_rec == "mem":
                self.controller.mem_datadict_last_opened = file_name_with_path    #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
            if self.mem_or_rec == "rec":
                self.controller.rec_datadict_last_opened = file_name_with_path    #The controller tracks last file opened of this type, so that when the user is again prompted to open the same type of file, we can default this value in.
        print("\n Controller-saved paths-- LastDir: %s, LastDataDictDir: %s, LastRecDatadict: %s, LastMemDatadict: %s" % (self.controller.dir_last_opened, self.controller.datadict_dir_last_opened, self.controller.rec_datadict_last_opened, self.controller.mem_datadict_last_opened) )
		
    def update_initial_dir_for_file_open_dialogs(self):
        '''In addition to tracking "last file opened" at the main controller level, we also want to notify every FilePath object when the user has opened a new file, so that they can adjust thir Initial DIr properties to the location just opened.'''
        self.filepathobj_load_from.calc_initial_dir_for_file_open(self.datadict_file_to_load_from, "datadict", "mem")
        self.filepathobj_save_to.calc_initial_dir_for_file_open(self.datadict_file_to_save_to, "datadict", "rec")
        
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
class DataDict_View(Frame):
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
        kw_grid = {"width":16}                            #Width of each grid cell 
        self.entry_grid = EntryGrid(self, self.model.meta_columns, self.model.meta_rownums, self.model.meta_values, show_grid, **kw_grid)
        #Display the frame:
        print("\n" + "In DataDict_View_Contnts._init_, datadict_file_to_load_from = '" + str(self.model.datadict_file_to_load_from) + "' -- and show_view=" + str(self.model.show_view) )
        if self.model.show_view:
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the parent window, directly below any previous frames. The grid() ROW designators refer to the parent window's Grid and determine which order the Frames will be displayed in.
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "DataDict_View.initUI()")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=W)                    #position the Frame within the Parent Window
        #self.config(width=self.model.frame_width, background=self.model.bgcolor, borderwidth=2, padx=3, pady=3)   #height=self.frame_height, 
        self.config(kw)
        for i in range(0,12):
            self.columnconfigure(i, weight=1, pad=3)
        for i in range(0,12):
            self.rowconfigure(i, pad=3)
        #Make sure the meta_xxx arrays are populated before we instantiate the EntryGrid object
        if not self.model.meta_columns:
            #Default in the standard column headings if they don't already exist:
            self.model.load_standard_datadict_headings()
        if not self.model.meta_rownums:
            self.model.meta_rownums = []
            i = 1
            num_initial_rows = 26    #The number of blank rows that will be displayed initially in the Data Dictionary Entry Grid.
            for i in range(1, num_initial_rows):
                self.model.meta_rownums.append(i)     #['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']
        if not self.model.meta_values:
            self.model.meta_values = []
            for i in range(0, num_initial_rows):
               meta_temp = ['', '', '', '', '', '', '', '']     #number of columns in each row -- MUUST MATCH THE NUMBER ENTERED IN THE DEFAULT COLUMN LIST
               self.model.meta_values.append(meta_temp)		#meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.
			   
        if False:  #self.debug:
            print("\n" + "Type of meta_columns: " + str(type(self.model.meta_columns)) + "...Length is: " + str(len(self.model.meta_columns)) )
            for col in self.model.meta_columns:
                print(str(col))
            print("\n" + "Type of rownums: " + str(type(self.model.meta_rownums)))
            for int in self.model.meta_rownums:
                print(str(int))
            print("\n" + "Type of meta_values: " + str(type(self.model.meta_values)))
            print("\n" + str(self.model.meta_values[0]) )
            print("\n" + "Type of meta_values[0]: " + str(type(self.model.meta_values[0])))
            print("\n [0][0]" + str(self.model.meta_values[0][0]) )
            print("\n [0][1]" + str(self.model.meta_values[0][1]) )
            print("\n [0][2]" + str(self.model.meta_values[0][2]) )		
            for item in self.model.meta_values:		
                print(str(item))
		
        #*************************************************************************************
        #Display a grid where user can choose which fields to include in a Blocking Pass		
        #*************************************************************************************
        #Entry Grid code is courtesy of bvdet at http://bytes.com/topic/python/answers/882126-grid-view-table-list-tkinter '''
        self.lblDictHeader = Label(self, text=self.model.title)
        self.lblDictHeader.grid(row=0, column=0, columnspan=12, sticky=W) 
        self.lblDictHeader.config(font=("Arial", 14, "bold"), borderwidth=1, width=100, justify="left")
        self.lblDictHeader.config(**kw)
        self.lblSpacer = Label(self, text=" ")
        self.lblSpacer.grid(row=0, column=1, sticky=W+N+E+S) 
        self.lblSpacer.config(borderwidth=0, width=4)
        self.lblSpacer.config(**kw)
		#Display the Data Dict file in a grid:
        self.display_datadict_in_grid(**kw)

    #***********************************************************************************************************************************
    def display_datadict_in_grid(self, **kw):
        #Populate the grid, based on META_xx arrays read in from the Data Dictionary file.
        already_init = self.entry_grid.has_been_initialized()
        #self.model.logobject.logit("\n Already_init=%s " % (str(already_init) ), True, True )   #... About to call clear_grid() from initUI() in DataDict_View.
        print("\n Already_init=%s " % (str(already_init) ))   #... About to call clear_grid() from initUI() in DataDict_View.
        #self.entry_grid.clear_grid()
        #Re-populating the data dictionary display grid is a significantly different process from initial load.
        if already_init == True:
            #self.model.logobject.logit("\n" + "About to call repopulate_grid() from DataDict_View.display_datadict_in_grid(). # Columns: " + str(len(self.model.meta_columns)) +  "# Rownums: " + str(len(self.model.meta_rownums)) + " # meta-value-rows: " + str(len(self.model.meta_values)), True, True )
            print("\n" + "About to call repopulate_grid() from DataDict_View.display_datadict_in_grid(). # Columns: " + str(len(self.model.meta_columns)) +  "# Rownums: " + str(len(self.model.meta_rownums)) + " # meta-value-rows: " + str(len(self.model.meta_values)))
            self.entry_grid.repopulate_grid(self.model.meta_columns, self.model.meta_rownums, self.model.meta_values)
        else:
            #self.model.logobject.logit("\n" + "About to call initialize_grid() from initUI() in DataDict_View. # Columns: " + str(len(self.model.meta_columns)) +  "# Rows: " + str(len(self.model.meta_rownums)) + " # value-rows: " + str(len(self.model.meta_values)), True, True )
            print("\n" + "About to call initialize_grid() from initUI() in DataDict_View. # Columns: " + str(len(self.model.meta_columns)) +  "# Rows: " + str(len(self.model.meta_rownums)) + " # value-rows: " + str(len(self.model.meta_values)))
            self.entry_grid.initialize_grid(self.model.meta_columns, self.model.meta_rownums, self.model.meta_values)

    def clear_datadict_grid(self):
        self.entry_grid.clear_all()

    #***********************************************************************************************************************************
    def retrieve_grid_values(self):
        #self.model.logobject.logit("\n About to call entry_grid.retrieve_grid_values()", True, True)
        print("\n About to call entry_grid.retrieve_grid_values()")
        meta_values_after_edit = self.entry_grid.retrieve_grid_values()
        return meta_values_after_edit

    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        #self.model.logobject.logit("Master DataDict_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string), True, True )
        print("Master DataDict_View object has gotten the alert: filename is %s and callback_string is %s" % (file_name_with_path, callback_string))
        self.datadict_file_to_load_from = file_name_with_path

#******************************************************************************************		
def main():

    root = Tk()
    root.geometry("900x600+100+100")
    master = BigMatchController(root)
    root.mainloop()


if __name__ == '__main__':
    main()  
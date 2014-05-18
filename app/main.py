#!C:\Python33\python.exe -u
#!/usr/bin/env python

import sys
import traceback
import os, os.path
import platform
import socket
import subprocess
from tkinter import *
from BlockingPass import *  
from DataDict import *
from FilePath import *
from MatchReview import *
from ConvertFile import *
from Datafile_to_RDBMS_UI import *
from RDBMS_Read_Export_UI import *
from BigMatchParmFile import *
from CHLog import *
from CHUser import *
from CommonRL import *
from Error_UI import *
#The following libraries are not within the BigMatch repo, so they might be left out of a BigMatch GUI installation or found in an unexpected place.
current, tail = os.path.split(os.path.realpath(__file__))         #/bigmatch/app/
up_one, tail = os.path.split(current)                             #bigmatch
up_two, tail = os.path.split(up_one)                              #parent folder of bigmatch
print("\n Up_one: '%s', Up_two: '%s'" % (up_one, up_two) )
python_common_found = None
if os.path.isdir(os.path.join(up_two, "common_functions", "python_common")):
    python_common_found = True
    sys.path.append(os.path.join(up_two, "common_functions", "python_common"))     #Python_Common subfolder within ETL folder (ETL is a sibling of Bigmatch folder)
    from Textfile import *
elif os.path.isdir(os.path.join(up_two, "python_common")):
    python_common_found = True
    sys.path.append(os.path.join(up_two, "python_common"))                   #Python_Common subfolder within ETL folder (ETL is a sibling of Bigmatch folder)
    from Textfile import *
sas7bdat_found = None
if os.path.isdir(os.path.join(current, "ch_lib", "sas7bdat_py3")):
    sas7bdat_found = True
    sys.path.append(os.path.join(current, "ch_lib", "sas7bdat_py3"))
    import sas7bdat
    from sas7bdat import *	
sqlite_found = None
try:
    import sqlite3
    sqlite_found = True
except:
    sqlite_found = False

#*****************************************************************************************************************************************************************
class BigMatchController():
    '''BigMatchController class creates a menu and a canvas for displaying various widgets. It also calls all methods necessary for instantiating those various widgets.'''
    debug = True
    error_message = None
    error_list = []                 #Collection of errors that have been logged
    parent_window = None	
    bigcanvas = None				#Main scrolling canvas on which the main frame object sits.  The canvas serves mainly to host the scrollbars.
    framestack_counter = None	    
    #Objects that represent major functions of this application (Blocking Pass, Data Dictionary, etc.)
    blockingpass_model = None       
    blocking_passes = []			#Index of Blocking Pass objects that have been instantiated
    how_many_blk_passes = 10
    matchreview_model = None
    error_ui = None            #Frame for displaying error information at runtime
    datadict_model = None
    #datadictobj_recfile = None
    #datadictobj_memfile = None
    #filepathobj_recfile	= None
    #filepathobj_memfile = None
    #filepathobj_recfile_dict = None
    #filepathobj_memfile_dict = None
    dir_last_opened = None
    datadict_dir_last_opened = None
    blockingpass_dir_last_opened = None
    parmfile_dir_last_opened = None
    resultfile_last_opened = None
    convertfile_last_opened = None
    rec_datadict_last_opened = None
    mem_datadict_last_opened = None 
    parmf_last_opened = None
    parmn_last_opened = None
    match_result_dir_last_opened = None
    logobject = None
    user = None
    common = None
    host_name = None
    bigmatch_exe_location = None
    enable_logging = None                    #Shut down logging until we solve permissions issues on Pennhurst server
    enable_sqlite = None
    sqlite_found = None
    sas7bdat_found = None
    python_common_found = None
    os_name = None
    os_platform = None
    os_release = None
    uid = None
	
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.parent_window.title("BigMatch configuration")   #parent window title
        self.parent_window.columnconfigure(0, weight=0, pad=3)
        self.parent_window.rowconfigure(0, weight=0, pad=3)
        self.host_name = str(socket.gethostname()).lower().strip()
        self.uid = getpass.getuser().lower().strip()
        print("\n--------------------------------------------------------------------------------")
        print("\n STARTING NEW SESSION. hostname: %s, user: %s" % (self.host_name, getpass.getuser() ) )
        #Get operating system info
        self.os_name = os.name
        self.os_platform = platform.system()
        self.os_release = platform.release()
        self.python_common_found = python_common_found
        self.sas7bdat_found = sas7bdat_found
        self.sqlite_found = sqlite_found
        print("\nPython_common_found? %s" % (self.python_common_found) )
        print("\n os_name: %s, os_platform: %s, os_release: %s" % (self.os_name, self.os_platform, self.os_release) )
        if (self.host_name == "chrsd1-gsanders" and self.uid == "gsanders"):
            self.enable_logging = True
        elif (self.host_name == "greg-hp" and self.uid == "greg") or (self.host_name == "gregory" and self.uid == "lisa"):
            self.enable_logging = True
        if self.enable_logging:
            #"Enable logging" does not mean the user has the necessary file/folder permissions. But from the GUI rules standpoint, this user can write logs if the permissions are in place.
            print("Logging enabled (by user ID)")
            #Make sure we can actually write to a file (file/folder permissions support logging)
            self.logobject = CHLog(self.enable_logging, self.enable_logging)    
            logtest = self.logobject.test_subfolder_filewrite()
            print("Logging write test returned %s)" % (logtest) )
            self.enable_logging = logtest             #If test failed, set enable_logging to False
            if not self.enable_logging:
                print("Logging write test failed")
                self.logobject = None
            if self.sqlite_found:
                self.enable_sqlite = self.logobject.test_sqlite_data_write()
        if self.enable_logging:
            self.user = CHUser()
        self.common = CommonRL(self.parent_window, self)
        self.bigmatch_exe_location = self.get_bigmatch_exe_location()
        head, tail = os.path.split(os.path.abspath(__file__))
        #self.update_controller_dirpaths(head)            #No need to set this to a default location at the outset.  That default-setting is handled by the individual FilePath objects.

        ## Grid sizing behavior in window
        self.parent_window.grid_rowconfigure(0, weight=1) 
        self.parent_window.grid_columnconfigure(0, weight=1)
        #Add a Canvas to the parent window:
        self.bigcanvas = ScrollCanvas(parent_window)						#BigCanvas is the main container which holds bigfraame, which everything else

        #******************************************************
        #INTRO SCREEN:
        self.load_splash("Chapin Hall's BigMatch user interface - blocking pass definitions")

        #******************************************************
        #Disable the following section.  OpenFile dialogs are managed by individual modules such as datadict, blockingpass, etc. 
        #FILE LOCATION FRAMES:  
		#Parms:  FilePath(parent_window, show_view=False, title='', bgcolor=gl_frame_color, file_types=[('All files', '*'),('Text files', '*.csv;*.txt')], frame_width=gl_frame_width, frame_height=gl_frame_height)
        #frame_color = "ivory"
        #open_or_save_as = "open"
        #self.filepathobj_memfile_dict.display_view(self.bigcanvas.bigframe)	        #Display the dialog for user to select a data dict file
			
        #*******************************************************************************************************************
        #MENU OPTIONS
        menubar = Menu(self.parent_window)
        self.parent_window.config(menu=menubar)
        dictMenu = Menu(menubar, tearoff=0)
        dictMenu.add_command(label="Create or edit data dictionary", command=self.load_datadict)
        #dictMenu.add_command(label="Create or edit data dictionary for the Record File", command=self.load_recfile_datadict)
        #dictMenu.add_command(label="Create or edit data dictionary for the Memory File", command=self.load_memfile_datadict)
        dictMenu.add_command(label="Start over with new data dictionary", command=self.startclean_new_datadict)
        menubar.add_cascade(label="Data dictionaries", menu=dictMenu)
		
        blockMenu = Menu(menubar, tearoff=0)
        blockMenu.add_command(label="Create parameter file from blocking passes", command=self.load_blocking_passes)
        blockMenu.add_command(label="Start over with new blocking pass", command=self.startclean_new_blockingpass)
        menubar.add_cascade(label="Blocking passes", menu=blockMenu)

        reviewMenu = Menu(menubar, tearoff=0)
        reviewMenu.add_command(label="Review match results", command=self.load_match_review)
        menubar.add_cascade(label="Match results", menu=reviewMenu)

        '''def get_command_for_file_convert_sas_to_text():
            cmd_string = "self.load_convert_file('sas', 'text')"
            print("\nReturning the string %s" % (cmd_string) )
            return cmd_string'''

        if self.python_common_found:
            #if self.uid.find("sanders") > -1:
            convertMenu = Menu(menubar, tearoff=0)
            if sas7bdat_found:
                convertMenu.add_command(label="Convert SAS file to text", command=self.load_convert_file_sas_to_text)
            convertMenu.add_command(label="Convert CSV file to flat file", command=self.load_convert_file_csv_to_text)
            convertMenu.add_command(label="Convert csv or flat file to sqlite table", command=self.load_convert_file_txt_to_sqlite)
            menubar.add_cascade(label="Convert files", menu=convertMenu)

        if self.sqlite_found:
            #if self.uid.find("sanders") > -1:
            dbMenu = Menu(menubar, tearoff=0)
            dbMenu.add_command(label="Display Sqlite data", command=self.display_sqlite_data)
            menubar.add_cascade(label="Read database", menu=dbMenu)

        if self.enable_logging:
            defltMenu = Menu(menubar, tearoff=0)
            defltMenu.add_command(label="Set startup to Data Dictionary", command=self.set_startup_module_to_data_dict)
            defltMenu.add_command(label="Set startup to Blocking Pass", command=self.set_startup_module_to_blocking_pass)
            defltMenu.add_command(label="Set startup to Match Review", command=self.set_startup_module_to_match_review)
            defltMenu.add_command(label="Set startup to File Conversion", command=self.set_startup_module_to_file_convert)
            menubar.add_cascade(label="Default settings", menu=defltMenu)
            #Test error display:
            self.add_error_to_list("Testing 123", "Type exception", "Hey, you can't do that!", None)
            self.add_error_to_list("Another Test", "Format exception", "No, you can't do that either.", None)
            errMenu = Menu(menubar, tearoff=0)
            errMenu.add_command(label="View errors", command=self.load_error_display)
            menubar.add_cascade(label="Error display", menu=errMenu)

        #if self.bigmatch_exe_location:
        #    runMenu = Menu(menubar, tearoff=0)
        #    runMenu.add_command(label="Run BigMatch", command=self.generate_parmfile)
        #    menubar.add_cascade(label="Run BigMatch", menu=runMenu)
		
        #genMenu = Menu(menubar, tearoff=0)
        #genMenu.add_command(label="Create parameter file", command=self.generate_parmfile)
        #genMenu.add_command(label="Load ParmF file", command=self.load_blocking_pass_from_parmfile)
        #menubar.add_cascade(label="Generate", menu=genMenu)
		
        #otherMenu = Menu(menubar, tearoff=0)
        #otherMenu.add_command(label="Clear display", command=self.bigcanvas.bigframe.clear_canvas)
        #otherMenu.add_command(label="Restore display", command=self.bigcanvas.bigframe.clear_canvas)
        #menubar.add_cascade(label="Clear", menu=otherMenu)

        #End of MENU OPTIONS
        #*************************************************************        
        #Load the user's preferred start-up module:
        if self.enable_logging:
            setting = self.user.get_config_setting("cmd_onload")
            if setting.lower().strip() == "load_datadict":
                self.load_datadict()
            elif setting.lower().strip() == "load_blocking_passes":
                self.load_blocking_passes()
            elif setting.lower().strip() == "load_match_review":
                self.load_match_review()
            elif setting.lower().strip() == "load_convert_file":
                self.load_convert_file_csv_to_text()
            else:
                self.load_datadict()
        else:
            self.load_datadict()

    def update_controller_dirpaths(self, file_name_with_path):     #Set default locations for FileOpen dialogs at session launch.
        if file_name_with_path:
            head, tail = os.path.split(file_name_with_path)
            self.dir_last_opened = head
            self.datadict_dir_last_opened = head                   #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
            self.parmfile_dir_last_opened = head
            self.match_result_dir_last_opened = head
        print("\n _MAIN_saved paths-- LastDir: %s, LastDataDictDir: %s, LastRecDatadict: %s, LastMemDatadict: %s" % (self.dir_last_opened, self.datadict_dir_last_opened, self.rec_datadict_last_opened, self.mem_datadict_last_opened) )

    def load_splash(self, caption="Chapin Hall's BigMatch utilities"):
        self.splash_frame = Frame(self.bigcanvas.bigframe)
        stackslot = self.bigcanvas.bigframe.get_widget_position(self.splash_frame, "main.load_splash()")
        self.splash_frame.grid(row=stackslot, column=0, columnspan=4, sticky=EW)
        self.splash_frame.config(background="ivory", width=130, padx=0, pady=0)
        self.splash_label = Label(self.splash_frame, text=caption)
        self.splash_label.grid(row=0, column=0, sticky=W) 
        self.splash_label.config(font=("Arial", 16, "bold"), borderwidth=1, width=65, anchor=W, justify="left", padx=0, pady=0, background="ivory")  #width=100, 
        self.bigcanvas.bigframe.refresh_canvas()
		
    def load_datadict(self, datadict_filename="", mem_or_rec="rec"):
        print("In main.load_datadict() with mem_or_rec=%s and datadict_filename=%s" % (str(mem_or_rec), str(datadict_filename) ) )
        show_frame = False            #Don't immediately display the view
        if self.datadict_model:
            self.datadict_model = None
        kw_datadict = {"mem_or_rec":mem_or_rec}
        self.bigcanvas.bigframe.clear_canvas()          #Unload (hide) all frame objects
        self.load_splash("BigMatch data dictionary manager")    #dictionary for " + which_name)
        self.datadict_model = DataDict_Model(self.parent_window, self, datadict_filename, show_frame, "Record file data dictionary", **kw_datadict)
        self.datadict_model.display_view(self.bigcanvas.bigframe)
        return True

    '''
    def load_datadict(self, datadict_filename="", mem_or_rec="rec"):
        print("In main.load_datadict() with mem_or_rec=%s and datadict_filename=%s" % (str(mem_or_rec), str(datadict_filename) ) )
        if which.lower()=="rec":
            which_name = "Record File"
        elif which.lower()=="mem":
            which_name = "Memory File"
        else:
            self.error_message = "Invalid data dictionary type: " + which
            print(self.error_message)
        self.bigcanvas.bigframe.clear_canvas()          #Unload (hide) all frame objects
        self.load_splash("BigMatch data dictionary manager")    #dictionary for " + which_name)
        self.datadictobj.display_view(self.bigcanvas.bigframe)
        return True
        
    def load_recfile_datadict(self, datadict_filename=""):
        show_frame = False            #Don't immediately display the view
        #if not self.datadictobj_recfile:
        #    self.datadictobj_recfile = DataDict_Model(self.parent_window, self, datadict_filename, show_frame, "Record file data dictionary")
        if self.datadictobj_recfile:
            self.datadictobj_recfile = None
        kw_datadict = {"mem_or_rec":"rec"}
        self.datadictobj_recfile = DataDict_Model(self.parent_window, self, datadict_filename, show_frame, "Record file data dictionary", **kw_datadict)
        #if datadict_filename:         #If a filename was passed to this function, store it to the DataDict object's "datadict_filename" property.
        #    self.datadictobj_recfile.datadict_filename = datadict_filename
        result = self.load_datadict("rec", datadict_filename)
        return result

    def load_memfile_datadict(self, datadict_filename=""):
        show_frame = False            #Don't immediately display the view
        #if not self.datadictobj_memfile:
        #    self.datadictobj_memfile = DataDict_Model(self.parent_window, self, datadict_filename, show_frame, "Memory file data dictionary")
        if self.datadictobj_memfile:
            self.datadictobj_memfile = None
        kw_datadict = {"mem_or_rec":"mem"}
        self.datadictobj_memfile = DataDict_Model(self.parent_window, self, datadict_filename, show_frame, "Memory file data dictionary", **kw_datadict)
        #if datadict_filename:         #If a filename was passed to this function, store it to the DataDict object's "datadict_filename" property.
        #    self.datadictobj_memfile.datadict_filename = datadict_filename
        result = self.load_datadict("mem", datadict_filename)
        return result
    '''
	
    def load_blocking_passes(self):
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- define blocking passes")
        self.blockingpass_model = BlockingPass_Model(self.parent_window, self)
        self.blockingpass_model.display_views(self.bigcanvas.bigframe, self.how_many_blk_passes)

    '''def load_blocking_pass_from_parmfile(self):
        parmfile = os.path.join('C:\Greg', 'code', 'bigmatch_utilities', 'BigMatchGui', 'parmf.txt')
        parmfileobj = BigmatchParmfile(parmfile)
        for parm in parmfileobj.parms:
            print("PARMFILE PARM: blkpass: %s, row_index: %s, row_type: %s, parms in row: %s, parm_index: %s, parm_type: %s, parm_value: %s" % (parm["blocking_pass"], parm["row_index"], parm["row_type"], parm["parms_in_row"], parm["parm_index"], parm["parm_type"], parm["parm_value"] ) )
    '''

    def load_match_review(self):
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- review match results")
        self.matchreview_model = MatchReview_Model(self.parent_window, self)
        #self.matchreview_model.display_view(self.bigcanvas.bigframe)
        self.matchreview_model.display_views(self.bigcanvas.bigframe, 1)

    def load_error_display(self):
        print("In main.load_error_display()")
        self.bigcanvas.bigframe.clear_canvas()          #Unload (hide) all frame objects
        self.load_splash("BigMatch utilities - error report")
        if not self.error_list:
            self.error_list = ["Unspecified error (main)"]
        self.error_ui = Error_UI_Model(self.parent_window, self, self.error_list)
        self.error_ui.display_views(self.bigcanvas.bigframe, len(self.error_list))
        print("\n\nBack in MAIN.PY after error was displayed. \n\n")
        
    '''def load_convert_file(self, source_format="sas", output_format="text"):
        print("\nIn MAIN, load_convert_file() with source %s and output %s" % (source_format, output_format) ) 
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- convert files")
        self.convertfile_model = ConvertFile_Model(self.parent_window, self, source_format, output_format)
        self.convertfile_model.display_view(self.bigcanvas.bigframe)'''

    def instantiate_convert_file(self, source_format=None, output_format=None):
        print("\nIn MAIN, load_convert_file() with source %s and output %s" % (source_format, output_format) ) 
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- convert files")
        self.convertfile_model = ConvertFile_Model(self.parent_window, self, source_format, output_format)
        self.convertfile_model.display_view(self.bigcanvas.bigframe)

    def instantiate_datafile_rdbms_ui(self, source_format="txt", output_format="sqlite"):
        print("\nIn MAIN, load datafile_to_rdbms_ui()") 
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- convert text file to database table")
        self.convertfile_model = Datafile_to_RDBMS_UI_Model(self.parent_window, self, source_format, output_format)
        self.convertfile_model.display_view(self.bigcanvas.bigframe)

    def instantiate_readexport_rdbms_ui(self, db_platform="sqlite", output_format="text"):
        print("\nIn MAIN, load ReadExport_Rdbms_UI()") 
        self.bigcanvas.bigframe.clear_canvas()       #Hide all frame objects
        self.load_splash("Chapin Hall's BigMatch user interface -- read/export data from database")
        self.db_readexport_model = RDBMS_Read_Export_UI_Model(self.parent_window, self, db_platform, output_format)
        self.db_readexport_model.display_view(self.bigcanvas.bigframe)

    def display_sqlite_data(self):
        self.instantiate_readexport_rdbms_ui("sqlite")
        
    def load_convert_file_sas_to_text(self):
        self.instantiate_convert_file("sas", "text")
        #self.convertfile_model.set_source_format("sas")
        #self.convertfile_model.set_output_format("text")
        
    def load_convert_file_csv_to_text(self):
        self.instantiate_convert_file("csv", "text")

    def load_convert_file_txt_to_sqlite(self):
        self.instantiate_datafile_rdbms_ui("txt", "sqlite")
        
    def generate_parmfile(self, filename_with_path=''):
        print("This function is not yet available.")

    def clear_canvas(self):
        '''clear_canvas() calls the function of the same name, within the child frame within this object's child scrolling frame.
        This is used when the user switches between Data Dictionary and Blocking Pass screens, or similar switch.'''
        self.bigcanvas.bigframe.clear_canvas()

    def refresh_main_canvas(self):
        self.bigcanvas.bigframe.update_idletasks()
        self.bigcanvas.update_idletasks()
        self.bigcanvas.config(scrollregion=self.bigcanvas.bbox(ALL))				             #Canvas object needs to encompass new items

    def set_startup_module_to_blocking_pass(self):
        self.user.write_setting_to_config_file('cmd_onload', 'load_blocking_passes')

    def set_startup_module_to_match_review(self):
        self.user.write_setting_to_config_file('cmd_onload', 'load_match_review')

    def set_startup_module_to_file_convert(self):
        self.user.write_setting_to_config_file('cmd_onload', 'load_convert_file_csv_to_text')

    def set_startup_module_to_data_dict(self):
        self.user.write_setting_to_config_file('cmd_onload', 'load_datadict')

    def startclean_new_datadict(self):
        self.clear_canvas()
        self.redisplay_module_after_error("datadict")

    def startclean_new_blockingpass(self):
        self.clear_canvas()
        self.redisplay_module_after_error("blockingpass")
        
    def redisplay_module_after_error(self, module_name="errordisplay"):
        '''Note: This function might be executed after an error, but it might be initiated by the user if they want to wipe out what they started, and start fresh. '''
        print("\n Back in main.py after error, calling module %s" % (module_name) )
        if str(module_name).lower().strip() == "datadict":
            self.load_datadict()
        elif str(module_name).lower().strip() == "blockingpass":
            self.load_blocking_passes()
        elif str(module_name).lower().strip() == "matchreview":
            self.load_match_review()
        elif str(module_name).lower().strip() == "convertfile":
            self.load_convert_file_csv_to_text()
        elif str(module_name).lower().strip() == "errordisplay":
            self.load_error_display()
        else:
            self.load_error_display()
        print("\nEnd of Main.redisplay_module_after_error()")

    def kill_module(self, module_name):
        '''Set to nothing the object that is to be destroyed. This assumes that this BigMatch Controller holds the only reference to that object (which is most often the case)'''
        print("\n Main.py kill_module(), killing module %s" % (module_name) )
        if str(module_name).lower().strip() == "datadict":
            self.datadict_model = None
        elif str(module_name).lower().strip() == "blockingpass":
            self.blockingpass_model = None
        elif str(module_name).lower().strip() == "matchreview":
            self.matchreview_model = None
        elif str(module_name).lower().strip() == "convertfile":
            self.convertfile_model = None
        print("\nEnd of Main.kill_module()")

    def get_bigmatch_exe_location(self):
        if self.host_name.lower() == "pennhurst1.chapinhall.org":
            loc = os.path.join("/usr", "local", "bin", "bigmatch")
            self.bigmatch_exe_location = loc
        elif self.host_name.lower() == "chrsd1-gsanders":
            loc = os.path.join("C:\Greg", "ChapinHall", "RecordLinking", "BigMatch", "bigmatchqst.exe")
            self.bigmatch_exe_location = loc
        else:
            self.bigmatch_exe_location = "bigmatch"
        return self.bigmatch_exe_location

    def call_bigmatch(self):
        #subprocess.call(args, *, stdin=None, stdout=None, stderr=None, shell=False)		
        process = subprocess.Popen(self.bigmatch_exe_location, stdout=subprocess.PIPE, creationflags=0x08000000)
        process.wait()
           
    def get_command_for_file_convert_sas_to_text(self):
        cmd_string = "self.load_convert_file('sas', 'text')"
        print("\nReturning the string %s" % (cmd_string) )
        return cmd_string

    def handle_error(self, error_message='Error. Procedure cancelled.', excp_type="", excp_value="", excp_traceback="", continue_after_error=False, abort_all=False, calling_object_name=None, module_to_reload_afterwards="errordisplay"):
        print("\nTop of Main.handle_error(), error_message: %s, excp_type: %s, excp_value: %s, continue_after: %s" % (error_message, excp_type, excp_value, continue_after_error))
        self.error_message = error_message
        self.add_error_to_list(self.error_message, excp_type, excp_value, excp_traceback)
        if self.logobject:
            self.logobject.logit("\nCalling Common.handle_error with message '%s'" % (self.error_message), True, True )   #Log this error in disk log and/or database
        self.common.handle_error(self.error_message, excp_type, excp_value, excp_traceback, continue_after_error, abort_all)                           #To make the error handler more generic, place it in a lightweight common functions lib so that it can be called even when this BigMatch controller is not in use.
        if abort_all:
            sys.exit(1)                                  #Shut down the Python interpreter
        if not continue_after_error:
            if calling_object_name:                      #Whatever class/object called this error handler is unceremoniously dumped as a result
                self.kill_module(calling_object_name)
            self.clear_canvas()
            self.redisplay_module_after_error(module_to_reload_afterwards)
        print("\n\nEnd of Main.handle_error()")

    def add_error_to_list(self, error_message="Unspecified error (in main)", excp_type="", excp_value="", excp_traceback=""):
        errdict = {"error_message":error_message, "exc_type":excp_type, "exc_value":excp_value, "exc_traceback":excp_traceback}
        self.error_list.append(errdict)
        return len(self.error_list)

#******************************************************************************
class ScrollCanvas(Canvas):
    debug = True                        #If debug=True, then output is sent to the Python command window for debugging.
    parent_window = None				#parent_window is the TK() root.
    framestack = None					#"framestack" refers to the stack of objects that are displayed on the big frame.  They arrange from top to bottom using .grid(row=x) positioning.
    framestack_counter = None           #See framestack description.  The Framestack_Counter is incremented once for each widget that is placed on the big frame, so it becomes that widget's index number and row number within the big frame.
    bigframe = None						#This Frame widget is placed directly on the Scrolling Canvas widget, and all other widgets are placed on the big frame.
    bgcolor = None	

    def __init__(self, parent_window):
        Canvas.__init__(self, parent_window)
        if parent_window:
            self.parent_window = parent_window

        ## Canvas
        self.grid(row=0, column=0, sticky='nswe')
        ## Scrollbars for canvas
        hScroll = Scrollbar(parent_window, orient=HORIZONTAL, command=self.xview)
        hScroll.grid(row=1, column=0, sticky='we')
        vScroll = Scrollbar(parent_window, orient=VERTICAL, command=self.yview)
        vScroll.grid(row=0, column=1, sticky='ns')
        self.bgcolor = "ivory"
        self.configure(xscrollcommand=hScroll.set, yscrollcommand=vScroll.set, scrollregion=(0, 0, 1000, 1000), background=self.bgcolor)
             
        ## Main Frame within the Main Canvas:
        self.bigframe = BigFrame(self.parent_window, self)
        print("\n Type of bigframe: '" + str(type(self.bigframe)) + "'")
        self.bigframe.config(background="lightgrey", padx=0, pady=0)
        self.bigframe.grid()
        ## This puts the frame in the canvas's scrollable zone
        self.create_window(0, 0, window=self.bigframe, anchor='nw')
        self.config(scrollregion=self.bbox(ALL))

    def clear_canvas(self):
        '''clear_canvas() calls the function of the same name, within the child frame within this scrolling frame.
        This is used when the user switches between Data Dictionary and Blocking Pass screens, or similar switch.'''
        self.bigframe.clear_canvas()

#**********************************************************************************************************************        
class BigFrame(Frame):
    debug = True
    parent_window = None
    parent = None						#Parent is assumed to be the main canvas.
    widgetstack = None					#List object which holds references to the stack of objects that are displayed on the big frame.  They arrange from top to bottom using .grid(row=x) positioning.
    widgetstack_counter = None          #See widgetstack description.  The widgetstack_Counter is incremented once for each widget that is placed on the big frame, so it becomes that widget's index number and row number within the big frame.
    bgcolor = None
	
    def __init__(self, parent_window, parent_widget):
        Frame.__init__(self, parent_widget)
        self.parent_window = parent_window
        self.parent = parent_widget
        self.bgcolor = "ivory"
        self.config(background=self.bgcolor)

    def get_widget_position(self, widget, who_called='(unknown)'):
        if(self.widgetstack is None):
            self.widgetstack = []
        self.widgetstack.append(widget)						#IMPORTANT! Add a reference to this widget in the framestack
        if(self.widgetstack_counter is None):
            self.widgetstack_counter = 0
        else:
            self.widgetstack_counter += 1
        print("\n" + "widgetstack_counter: " + str(self.widgetstack_counter) + ":  " + who_called) #+ "  -- class: " + str(frame.winfo_class()) )
        return self.widgetstack_counter
       
    def refresh_canvas(self):
        self.update_idletasks()
        self.parent.update_idletasks()
        self.parent.config(scrollregion=self.bbox(ALL))				#Canvas object needs to encompass new items

    def clear_canvas(self):
        if self.widgetstack:
            i = 0
            for widget in self.widgetstack:
                print("Next widget to clear: " + str(type(widget)) + " " + str(i))
                widget.grid_forget()									#Remove the next widget from visible display    
                i += 1
            self.refresh_canvas()
        #self.datadictobj_recfile = None
        #self.datadictobj_memfile = None

    def restore_canvas(self):
        if self.widgetstack:
            i = 0
            for widget in self.widgetstack:
                print("Next: " + str(type(widget)) + " " + str(i))
                widget.grid()											#Add the next widget back to visible display 
                i += 1
            self.refresh_canvas()

#******************************************************************************************		
class SpacerFrame(Frame):
    parent_window = None
    controller = None
    frame_width = None
    frame_height = None

    def __init__(self, parent_window, controller, frame_width=gl_frame_width, frame_height=40):
        Frame.__init__(self, parent_window)
        self.parent_window = parent_window        
        self.controller = controller
        self.initUI(frame_width, frame_height)
        self.frame_width = 400    #frame_width
        self.frame_height = frame_height
        
    def initUI(self, frame_width=gl_frame_width, frame_height=40):
        stackslot = self.controller.get_framestack_counter("Spacer")
        self.grid(column=0, row=stackslot, sticky=W)                    #position this Frame object within the Window (the DataDictFrame is "row 1", right after "row 0")
        self.config(width=self.frame_width, height=self.frame_height, borderwidth=2, padx=0, pady=0)  #, background="BLUE"
        self.columnconfigure(0, weight=1, pad=3)
        self.rowconfigure(0, pad=3)
        #Dummy SPACER:
        #self.lblSpacer = Label(self, text=" ")
        #self.lblSpacer.grid(row=0, column=0, sticky=W+E)
        #self.lblSpacer.config(borderwidth=2, width=(frame_width-10))
		

#******************************************************************************************		
def main():
    root = Tk()
    root.geometry("1280x700+50+50")
    #master = ScrollCanvas(root)
    master = BigMatchController(root)
    root.mainloop()

if __name__ == '__main__':
    main() 

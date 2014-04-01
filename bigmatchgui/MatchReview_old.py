#!C:\Python33\python.exe -u
#!/usr/bin/env python
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from TkEntry import EntryGrid
import csv
import os 
from os import walk
from os import path
from FilePath import *
from CHLog import *
from BigMatchParmFile import *

gl_frame_color = "ivory"
gl_frame_width = 500
gl_frame_height = 100

#******************************************************************************
class MatchReview_Model():
    debug = True
    error_message = None
    parent_window = None                    #Parent_window is the TKinter object itself (often known as "root"
    controller = None                       #Controller is the BigMatchController class in main.py 
    logobject = None                        #Instantiation of CHLog class
    title = None
    bgcolor = None
    bgcolors = []
    frame_width = None
    frame_height = None
    meta_values = []
    view_object = None
    matchfile_rows = 0
    matchreview_file_selected_by_user = None #The user navigates to a .dat file, but can then choose to display ONLY this file, or combine it with ALL files in the same folder with the same name but different suffix (Mymatch_Pairs_00.dat would be combined with Mymatch_Pairs_01.dat, etc.)
    matchreview_file_to_load_from = None	 #Data dictionary file name and path, which will be loaded into the entry grid if user requests.
    matchreview_file_to_save_to = None		 #Data dictionary file name and path, to which the metadata will be saved if user requests.
    exact_match_output_file = None           #Automatically create a file of exact matches for every blocking pass, so that we can generate statistics and so the user can view matches if desired.
    combined_matchreview_file = None	     #The user navigates to a .dat file, but can choose to combine it with ALL files in the same folder with the same name but different suffix (Mymatch_Pairs_00.dat would be combined with Mymatch_Pairs_01.dat, etc.)
    allow_view_combined_files = False        #Allowing the user to combine BigMatch results files and handle the entire batch at once is an advanced feature, not for casual users.
    viewing_one_or_all_files = None          #If the user chooses to combine the selected file with ALL files in the same folder sharing a similar name but different suffix, this flag switches from "ONE" to "ALL"
    result_filename_trunc = None             #If the user chooses to combine the selected file with ALL files in the same folder sharing a similar name but different suffix (Mymatch_Pairs_00.dat would be combined with Mymatch_Pairs_01.dat, etc.)
    match_files_for_batch = None             #Files that will be combined into self.combined_matchreview_file
    filepathobj_load_from = None             #FilePath object to allow user to select a file
    filepathobj_save_to = None               #FilePath object to allow user to select a file
    matchreview_views = []
    howmany_passes = 1                       #Number of Blocking Passes to display data for
    sort_asc_or_desc = None                  #Sort order for the list of possible matches (based on assigned weight of each row)
    sort_column = None                       #The list of pairs may be sorted by Weight or by Blocking Pass and then Weight. Blocking Pass is column0 and Weight is column 1.
    controls = []                            #self.controls is a list of the screen controls, which can be traversed after user has finished entering information
    control_index = 0
    recfile_values_for_current_row = None    #Method create_resultrow_frame() uses this property because it needs access to BOTH rec and memfile values simultaneously (which is not feasible when looping thru the controls separately)
    memfile_values_for_current_row = None    #Method create_resultrow_frame() uses this property because it needs access to BOTH rec and memfile values simultaneously (which is not feasible when looping thru the controls separately)
    result_comparison_frames_in_grid = []    #List of frame objects that can be populated with text for clerical review comparisons.

    def __init__(self, parent_window, controller, title="Linkage results -- review", bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height):	
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        self.logobject = CHLog()
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
        self.bgcolors = ["#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0", "#FDFFDF", "#DFFFF0"]
        self.sort_asc_or_desc = "DESC"
        #Instantiate, but do not display, the View object:
        self.instantiate_view_object(None, 0)

    def handle_error(self, error_message=None):
        #TO DO: Display errors in the GUI for users to see!
        if error_message is not None and error_message != self.error_message:
            self.error_message = str(self.error_message) + " " + error_message
            self.error_message.strip()
        astr = "*" * 80
        print("\n \n" + astr)
        print("ERROR: %s" % (self.error_message) )
        print(astr + "\n \n")
        return

    #*********************************************************************************************
    def combine_result_files(self):
        print("\n FILE SELECTED: %s aka %s" % (self.matchreview_file_selected_by_user, str(self.matchreview_file_selected_by_user)[-12:][:6].lower().strip() ) )
        head, tail = os.path.split(self.matchreview_file_selected_by_user)
        match_result_filename_trunc = self.get_result_filename_trunc(self.matchreview_file_selected_by_user)
        self.combined_matchreview_file = os.path.join(head, match_result_filename_trunc + "pairs_99.dat").lower().strip()
        if str(self.matchreview_file_selected_by_user)[-12:][:6].lower().strip() == "pairs_":
            #Find all files in the same folder as that selected by the user, that also have the same filename (except for final suffix) as the user-selected file.  (Example: Myfile_Pairs_00.bat, Myfile_Pairs_01.bat, etc.)
            self.build_list_of_all_pairs_files_for_batch()
            if len(self.match_files_for_batch) == 0:
                self.error_message = "Combining BigMatch result files failed."
            else:
                try:
                    with open(self.combined_matchreview_file, 'w') as outfile:
                        for filenm in self.match_files_for_batch:
                            suffix = filenm[-6:-4]
                            if "012345678".find(suffix[:1]) != -1:
                                try:
                                    suffix = str(int(suffix))   
                                except ValueError:
                                    pass
                            nextfile = os.path.join(head, filenm)
                            if nextfile.lower().strip() != self.combined_matchreview_file:      #DO NOT allow the newly created file to be included in this loop, or it will set up an endless loop!
                                with open(nextfile) as infile:
                                    for line in infile:
                                        outfile.write("bp:" + suffix + " " + line)
                                outfile.write("***************************************************** \n")
                except IOError as e:
                    print("I/O error({0}): {1}".format(e.errno, e.strerror))
                    self.error_message = str(e.strerror)
        if self.error_message is not None:
            self.handle_error()
            return
        
    def build_list_of_all_pairs_files_for_batch(self):
        self.match_files_for_batch = []
        head, tail = os.path.split(self.matchreview_file_selected_by_user)
        dirpath = head
        match_result_filename_trunc = self.get_result_filename_trunc(self.matchreview_file_selected_by_user)
        print("In build_list_of_all_pairs_files_for_batch(), match_result_filename_trunc=%s" % (match_result_filename_trunc))
        for (dirpath, dirnames, filenames) in walk(head):
            for filenm in filenames:
                filenm = str(filenm).lower().strip()
                print("Next file in dir: %s .... %s" % (filenm, filenm[:-12]) )
                if filenm[:-12] == match_result_filename_trunc and filenm[-4:] == ".dat":    #This is a batch-mate of the selected file
                    if filenm[-6:] != "99.dat":                       #Don't include this COMBINED file, as it will be overwritten anyway
                        self.match_files_for_batch.append(filenm)
            break
        print("\n In build_list_of_all_pairs_files_for_batch(), Batch Files Found:")
        for f in self.match_files_for_batch:
            print(f)

    def get_result_filename_trunc(self, filename=None):
        if filename is None:
            filename = self.matchreview_file_selected_by_user
        head, tail = os.path.split(filename)
        self.match_result_filename_trunc = tail.lower().strip()[:-12]
        return self.match_result_filename_trunc

    #*********************************************************************************************
    def split_result_file(self, matchreview_file=None):
        if matchreview_file is None:
            matchreview_file = self.matchreview_file_to_load_from
        if not matchreview_file:
            self.handle_error("No result file was specified")
            return
        '''if self.recvalues_file is None:
            ext = matchreview_file.lower().strip()[-4:]
            self.recvalues_file = matchreview_file.lower().strip().replace(ext, "_recflmatches" + ext)
        if self.memvalues_file is None:
            ext = matchreview_file.lower().strip()[-4:]
            self.memvalues_file = matchreview_file.lower().strip().replace(ext, "_memflmatches" + ext)'''
        #Traverse the specified Match Results file and extract parts of each row into a list
        print("\n TOP OF FUNCTION split_result_file() -- file: %s" % (str(matchreview_file)) )
        count = blkpass_rowcount = meta_rowid = weight_pos = 0
        maxlen = 20   #Start out assuming a very narrow set of matching fields -- then use the maximum width to set a "justify" line so that the results appear less ragged.
        blkpass = holdpass = ""
        sep = "?   ~"                    #In the BigMatch results files, this string separates the first column (weight and unique ID) from the blocking and matching field values.
        with open(matchreview_file, 'r') as matchfile:
            with open(self.exact_match_output_file, 'w') as exactfile:
                for row in matchfile:
                    if len(row) == 0:
                        continue                         #Empty row
                    if str(row)[:4]=="****":             #Asterisk lines are placed in the file to denote the start of a new section of results (different blocking pass)
                        continue
                    halves = str(row).split(sep, 1)
                    first_half_as_list = halves[0].strip().split(" ")
                    chunk1 = first_half_as_list[0].lower().strip() #First chunk of text could be Weight (if the BigMatch result file is unaltered) -OR- it could be Blocking Pass number (if file was altered by this GUI or some other post-process)
                    bp_pos = chunk1.find("bp:")            #If the file being reviewed has been post-processed by this GUI to combine results from multiple blocking passes, then it should have the string "bp:" in every row, specifying which blocking pass the row was generated by.
                    if bp_pos == -1:
                        blkpass = self.get_blocking_pass_num_from_results_filename()                   # "0"
                        weight = chunk1
                        weight_pos = 0
                    else:
                        blkpass = chunk1[bp_pos+3: bp_pos+5].lower().strip()
                        weight = first_half_as_list[1]
                        weight_pos = 1
                    if blkpass != holdpass:                    #Reset this counter when we encounter a new Blocking Pass section
                        blkpass_rowcount = 0
                        holdpass = blkpass
                    weight = weight.replace("+", "")
                    try:
                        weight = str(round(float(weight), 3))
                    except ValueError:
                        weight = str(weight)                #In case of unexpected non-numeric values
                        #continue
                    #Now grab the other values within the first section of this row (note that this code assumes NO BLANKS in unique ID fields!)
                    id_rec = first_half_as_list[weight_pos +1]         #First part of each row has weight and ID numbers, and blocking field values
                    id_mem = first_half_as_list[weight_pos +2]         #First part of each row has weight and ID numbers, and blocking field values
                    blkfldvals = first_half_as_list[3:]                #Following the Weight and two Unique IDs, an indefinite number of Blocking Values appear.
                    blkfldvals = ''.join(str(itm).strip().ljust(len(itm.strip())+1) for itm in blkfldvals).strip()     #Convert indefinite number of Blocking Field Values from a list to a string
                    blkfldvals = blkfldvals.replace("       ", "")     #Remove long blank spaces
                    #print("Next: weight: %s, %s blkpass: %s, id_rec:%s, id_mem: %s, blkvals: '%s'" % (weight, "||", blkpass, id_rec, id_mem, blkfldvals) )
                    #Move on to the second half of the row:
                    matchvals = halves[1]                   #Second half of each row has the selected blocking/matching field values
                    matchlist = matchvals.split("~")        #Tilde separates Record File attributes from Memory File attributes, within the 2nd half of the row.
                    recmatches = self.reduce_blank_spaces(str(matchlist[0]).strip())  #Record File attributes
                    if len(recmatches) > maxlen:                                      #Use the maximum width to set a "justify" line so that the results appear less ragged
                        maxlen = len(recmatches)
                    memmatches = self.reduce_blank_spaces(str(matchlist[1]).strip())  #Memory File attributes
                    if len(memmatches) > maxlen:                                      #Use the maximum width to set a "justify" line so that the results appear less ragged
                        maxlen = len(memmatches)
                    if recmatches == memmatches:            #Exact matches are written to a separate file
                        print("Exact match: %s -|- %s" % (recmatches, memmatches) ) 
                        exactfile.write("%s %s %s %s %s: %s %s %s: %s \n" % (blkpass, " | ", weight.rjust(9), " | ", id_rec, recmatches.ljust(maxlen+10), " | ", id_mem, memmatches.ljust(maxlen+10)) )
                    else:                 #NOT exact matches - store these in the meta_values array
                        #print("Adding row to meta_values: %s, %s, %s, %s" % (blkpass, weight, recmatches, memmatches) )
                        #Populate the meta_values array (list of lists) that will be used to populate the Entry Grid
                        meta_temp = [blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid]     #meta_temp is a LIST consisting of one row from the Review File
                        self.meta_values.append(meta_temp)		          #meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.\
                        #print("\n -- ROW %s" % (count) )
                        #print("rec: %s" % (recmatches) )
                        #print("mem: %s" % (memmatches) )
                        meta_rowid += 1                   #Count this as a row that will be added to self.meta_values
                    count += 1
                #Close files:
                exactfile.close()
            matchfile.close()
        self.matchfile_rows = count
        print("\n At end of split_result_file(), meta_values has %s rows, and the matchfile has %s rows." % (len(self.meta_values) , self.matchfile_rows) )  
        self.sort_list()

    '''def init_grid_arrays(self):
        i = 0
        for i in range(0, self.matchfile_rows):
            self.meta_rownums.append(str(i))        #Display row numbers in the Entry Grid
        self.meta_columns = ["Record file data values", "Memory file data values"]'''

    def load_single_file(self):
        self.viewing_one_or_all_files = "one"
        self.display_views()

    def load_combined_files(self):
        self.viewing_one_or_all_files = "all"
        self.combine_result_files()
        #Now the COMBINED file displaces the USER-SELECTED file as self.matchreview_file_to_load_from
        self.matchreview_file_to_load_from = self.combined_matchreview_file
        #Load (or re-load) the grid so that the user can review this file row by row
        self.display_views()

    def write_accepted_pairs(self):
        if not self.matchreview_file_to_save_to or not self.controls or not self.meta_values:
            return
        with open(self.matchreview_file_to_save_to, "w") as f: 
            i = 0
            chkvalue = ""
            for item in self.meta_values:
                meta_rowid = item[6]                            #item[6] is "meta_rowid"
                for control in self.controls:
                    #print("Seeking meta_rowid %s, found %s... type: %s" % (meta_rowid, control.meta_rowid, str(control.control_type).lower().strip()) )
                    if control.meta_rowid == meta_rowid and str(control.control_type).lower().strip()=="checkbox":
                        chkvalue = control.value_object.get()
                        print("Checkbox with meta_rowid %s and weight %s has value: %s" % (control.meta_rowid, item[1], chkvalue) )
                        break
                if str(chkvalue) == "1":
                    f.write("%s %s %s %s \n" % (item[0], item[1], item[2], item[3] ) )
                i += 1
            f.close()
        

    def sort_list(self):
        #Sort the list by weight:
        print("\n Sorting the values list")
        if str(self.sort_asc_or_desc).upper().strip() == "ASC":
            if str(self.sort_column).lower().strip() == "weight":
                self.meta_values.sort(key=lambda x: x[1])
            else:
                self.meta_values.sort()
        else:    #"DESC"
            if str(self.sort_column).lower().strip() == "weight":
                self.meta_values.sort(key=lambda x: x[1], reverse=True)
            else:
                self.meta_values.sort(reverse=True)

        #When we re-sort, refresh the display and go back to the Top of the record list.
        if self.view_object is not None:
            self.view_object.start_row = 0
            self.view_object.repopulate_grid()
        #Refresh the state of sort buttons:
        self.enable_disable_buttons()

    def sort_list_ascending(self):
        self.sort_asc_or_desc = "ASC"
        self.sort_list()
        if self.view_object is not None:
            self.view_object.repopulate_grid()

    def sort_list_descending(self):
        self.sort_asc_or_desc = "DESC"
        self.sort_list()
        if self.view_object is not None:
            self.view_object.repopulate_grid()

    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found

    def display_openfile_dialogs(self, container, default_filepath=''):
        file_types = [('All files', '*'), ('Text files', '*.csv;*.txt', '*.dat')]
        kw_fpath = {"bgcolor":self.bgcolor, "frame_width":"", "frame_height":"", "file_category":"matchreview"}
        open_or_save_as = "open"
        self.filepathobj_load_from = FilePath_Model(self.parent_window, self, self.controller, "Match result file to load:", open_or_save_as, "MatchResultToLoad", file_types, **kw_fpath)
        self.filepathobj_load_from.display_view(container)	        #Display the dialog for user to select a data dict file
        open_or_save_as = "save_as"
        self.filepathobj_save_to = FilePath_Model(self.parent_window, self, self.controller, "Save match choices to file:", open_or_save_as, "MatchResultToSaveAs", file_types, **kw_fpath)
        self.filepathobj_save_to.display_view(container)	        #Display the dialog for user to Ave As... a new data dict file
	    
    def add_control_to_list(self, object, var, **kw):
        control = Control(self, object, var, self.control_index, **kw)
        self.controls.append(control)            #self.controls is a list of the screen controls, which can be traversed after user has finished.
        self.control_index += 1

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "MatchReview_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.button_frame.grid(row=stackslot, column=0, sticky=EW)
        self.button_frame.configure(background=self.bgcolor, padx=4, pady=1)
		
        #self.btnDisplayAllFiles = Button(self.button_frame, text="View all files from this batch", width=24, command=self.load_combined_files)
        #self.btnDisplayAllFiles.grid(row=0, column=1, sticky=W)
        #self.btnDisplayAllFiles.configure(state=DISABLED)       #Do not enable this button unless the user has selected MatchReview files
		
        self.btnNextPage = Button(self.button_frame, text="Next", width=12, command=self.scroll_page)
        self.btnNextPage.grid(row=0, column=0, sticky=W)
        self.btnNextPage.configure(state=DISABLED, padx=4, pady=1)
		
        self.btnPrevPage = Button(self.button_frame, text="Back", width=12, command=self.scroll_backwards)
        self.btnPrevPage.grid(row=0, column=1, sticky=W)
        self.btnPrevPage.configure(state=DISABLED, padx=4, pady=1)
        
        self.btnSortDesc = Button(self.button_frame, text="Sort Descending", width=16, command=self.sort_list_descending)
        self.btnSortDesc.grid(row=0, column=2, sticky=W)
        self.btnSortDesc.configure(state=DISABLED, padx=4, pady=1)            #Disable this button if the list is already sorted Descending
		
        self.btnSortAsc = Button(self.button_frame, text="Sort Ascending", width=16, command=self.sort_list_ascending)
        self.btnSortAsc.grid(row=0, column=3, sticky=W)
        self.btnSortAsc.configure(state=DISABLED, padx=4, pady=1)            #Disable this button if the list is already sorted Ascending
		
        self.lblAcceptAbove = Label(self.button_frame, text="Accept above: ")
        self.lblAcceptAbove.grid(row=0, column=4, sticky=W) 
        self.lblAcceptAbove.configure(background=self.bgcolor, font=("Arial", 10, "normal"), borderwidth=0, width=11, anchor=E, padx=4, pady=1)
		
        self.spinvar = StringVar(self.button_frame)
        self.spinvar.set(9)
        spn = Spinbox(self.button_frame, from_=0, to=30)
        spn.grid(row=0, column=5, sticky=W)
        spn.config(textvariable=self.spinvar, background=self.bgcolor, width=5)
        spn.bind(sequence="<FocusOut>", func=self.spinhandler)

        self.btnSaveToDictFile = Button(self.button_frame, text="Write accepted pairs to file", width=20, command=self.write_accepted_pairs)
        self.btnSaveToDictFile.grid(row=0, column=6, sticky=W)
        self.btnSaveToDictFile.configure(state=DISABLED, padx=4, pady=1)       #Do not enable this button unless the user has selected a MatchResults file to save as

    def display_advanced_buttons(self, container):
        '''Function display_advanced_buttons shows advanced features IF the user is authorized and explicitly chooses to open this panel.. '''
        self.advanced_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.advanced_frame, "MatchReview_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.advanced_frame.grid(row=stackslot, column=0, sticky=EW)
        self.advanced_frame.configure(background=self.bgcolor, padx=4, pady=1)
		
        self.btnDisplayOneFile = Button(self.advanced_frame, text="View the selected file", width=24, command=self.load_single_file)
        self.btnDisplayOneFile.grid(row=0, column=0, sticky=W)
        self.btnDisplayOneFile.configure(state=DISABLED, padx=4, pady=1)        #Do not enable this button unless the user has selected MatchReview files
		
        self.btnDisplayAllFiles = Button(self.advanced_frame, text="View all files from this batch", width=24, command=self.load_combined_files)
        self.btnDisplayAllFiles.grid(row=0, column=1, sticky=W)
        self.btnDisplayAllFiles.configure(state=DISABLED, padx=4, pady=1)       #Do not enable this button unless the user has selected MatchReview files
		
        self.lblSortBy = Label(self.advanced_frame, text="Sort on: ")
        self.lblSortBy.grid(row=0, column=2, sticky=W) 
        self.lblSortBy.configure(background=self.bgcolor, font=("Arial", 9, "normal"), borderwidth=0, width=7, anchor=E, padx=4, pady=1)
        var = StringVar(self.advanced_frame)
        var.set("Blocking Pass+Weight")
        value_list = ["Blocking Pass+Weight", "Weight"]
        self.optSortBy = OptionMenu(self.advanced_frame, var, *value_list, command=lambda x:self.change_sort_column(var) )
        self.optSortBy.grid(row=0, column=3, sticky=W)
        self.optSortBy.config(font=('calibri',(9)), bg='light grey', width=18, padx=4, pady=1)
        self.optSortBy['menu'].config(background=self.bgcolor, font=("calibri",(11))) 
 
    def spinhandler(self, parm=None):
        print("\n Spinner stringvar: %s, stringvar value: %s, parm: %s, widget: %s" % (self.spinvar, self.spinvar.get(), parm, parm.widget) )
        if not self.controls or not self.meta_values:
            return
        i = 0
        for item in self.meta_values:
            print("Is %s greater than %s? %s" % (item[1], self.spinvar.get(),  (float(item[1]) >= float(self.spinvar.get())) ) )
            if float(item[1]) >= float(self.spinvar.get()):     #item[1] is "weight"
                meta_rowid = item[6]                            #item[6] is "meta_rowid"
                for control in self.controls:
                    #print("Seeking meta_rowid %s, found %s... type: %s" % (meta_rowid, control.meta_rowid, str(control.control_type).lower().strip()) )
                    if control.meta_rowid == meta_rowid and str(control.control_type).lower().strip()=="checkbox":
                        print("SELECTing the checkbox with meta_rowid %s" % (control.meta_rowid) )
                        control.object.select()      #Check the checkbutton object
                        break
                
            i += 1
        #self.view_object.start_row = 0
        #self.view_object.repopulate_grid()
        self.view_object.container.refresh_canvas()

    def change_sort_column(self, var):
        print("\n in change_sort_column(), var='%s'" % (str(var.get()) ) )
        self.sort_column = str(var.get()).lower().strip().replace(" ", "_")      #"weight"
        self.sort_list()

    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        '''IMPORTANT: ALL FilePath objects created by this class will expect Function "update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        #self.logobject.logit("Master MatchReview_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string), True, True )
        print("Master MatchReview_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string))
        if callback_string.lower().strip()[:4] == "load" or callback_string.lower().strip()[:4] == "open":
            self.matchreview_file_selected_by_user = file_name_with_path           #File selected to be reviewed -- BUT user can choose to combine this with others from the same batch
            self.matchreview_file_to_load_from = file_name_with_path               #For now, set this to the selected file, but later it might be changed to a COMBINED file that includes the selected file and its batch-mates.
            if not self.matchreview_file_to_save_to:
                self.matchreview_file_to_save_to = self.get_default_saveto_filename()  #By default, results are saved to a .dat file with the same name as the source file, but with suffix "_ACCEPTED"
                self.filepathobj_save_to.update_filepath_display(self.matchreview_file_to_save_to)	#Make sure the FilePath object also registers this Save_To file.
                self.exact_match_output_file = self.get_exact_match_filename()				
                print("\n Matchreview_file_to_save_to is being set to: %s" % (self.matchreview_file_to_save_to) )
            if self.matchreview_file_to_load_from:            #and self.matchreview_file_to_save_to:
                self.load_single_file()                       #Refresh the view when the user selects (loads) a new file.
            else:                                             #No file was specified (user might have cleared out a previously selected file name) 
                if self.view_object is not None:
                    self.view_object.clear_grid()             #Remove all existing values from the grid'''
        elif callback_string.lower().strip()[:4] == "save":   #This is a file SAVE AS, not a FILE OPEN
            self.matchreview_file_to_save_to = file_name_with_path

        self.update_controller_dirpaths(file_name_with_path)  #Let the BigMatchController know that this path is a regular user location (for future file-open dialogs to start from)
        self.enable_disable_buttons()
        if self.error_message is not None:
            self.handle_error()
            return

    def get_default_saveto_filename(self):
        returnval = ""
        if self.matchreview_file_to_load_from:
            returnval = self.matchreview_file_to_load_from[:-4] + "_ACCEPTED" + self.matchreview_file_to_load_from[-4:] 
        return returnval

    def get_exact_match_filename(self):
        returnval = ""
        if self.matchreview_file_to_load_from:
            returnval = self.matchreview_file_to_load_from[:-4] + "_EXACT" + self.matchreview_file_to_load_from[-4:] 
        return returnval

    def get_blocking_pass_num_from_results_filename(self):
        returnval = "0"
        if self.matchreview_file_to_load_from:
            try:
                returnval = int(self.matchreview_file_to_load_from[-6:-4])
            except ValueError:
                pass
        return returnval

    def reduce_blank_spaces(self, text):
        text = text.replace("                      ", " ")
        text = text.replace("                    ", " ")
        text = text.replace("                  ", " ")
        text = text.replace("                ", " ")
        text = text.replace("              ", " ")
        text = text.replace("            ", " ")
        text = text.replace("          ", " ")
        text = text.replace("        ", " ")
        text = text.replace("      ", " ")
        text = text.replace("    ", " ")
        text = text.replace("  ", " ")
        return text

    def update_controller_dirpaths(self, file_name_with_path):
        if file_name_with_path:
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head                       #The controller tracks last folders opened for this type, so that when the user is again prompted to open the same type of file, we can set this as the initial dir.
        print("\n Controller-saved paths-- LastDir: %s" % (self.controller.dir_last_opened) )

    def enable_disable_buttons(self):
        #Buttons related to viewing result files:
        print("\n In enable_disable_buttons, MatchReviewFile is %s" % (self.matchreview_file_to_load_from) )
        if self.matchreview_file_to_load_from: 
            self.enable_display()
        else:
            self.disable_display()
        
        #Buttons related to saving match choices:		
        if self.matchreview_file_to_save_to:
            self.enable_save()
        else:
            self.disable_save()
        
    def enable_display(self):
        if str(self.viewing_one_or_all_files).lower() == "one": 
            if self.allow_view_combined_files:
                self.btnDisplayOneFile.configure(state=DISABLED)       #Disable this button if the list is already populated with the user-selected file only
                self.btnDisplayAllFiles.configure(state=NORMAL)        #Enable this button if the list is currently showing the user-selected file only.
        elif str(self.viewing_one_or_all_files).lower() == "all":
            if self.allow_view_combined_files:
                self.btnDisplayOneFile.configure(state=NORMAL)         #Enable this button if the list is currently showing the user-selected file only
                self.btnDisplayAllFiles.configure(state=DISABLED)	   #Disable this button if the list is already populated with the COMBINED files
        else:
            if self.allow_view_combined_files:
                self.btnDisplayOneFile.configure(state=NORMAL)         #Allow the user to choose either single or combined
                self.btnDisplayAllFiles.configure(state=NORMAL)        #Allow the user to choose either single or combined

        if self.viewing_one_or_all_files is not None:                  #All of the following buttons require that the user has already loaded EITHER a single file or a combined file.
            if self.view_object is None:
                self.btnNextPage.configure(state=DISABLED)
                self.btnPrevPage.configure(state=DISABLED)
            else:
                if (self.view_object.start_row + self.view_object.rows_to_display) <= len(self.meta_values):
                    self.btnNextPage.configure(state=NORMAL)
                else:
                    self.btnNextPage.configure(state=DISABLED)
                if self.view_object.start_row > 0:
                    self.btnPrevPage.configure(state=NORMAL)
                else:
                    self.btnPrevPage.configure(state=DISABLED)
            if str(self.sort_asc_or_desc).upper().strip()[:4] == "DESC":
                self.btnSortDesc.configure(state=DISABLED)                #Disable this button if the list is already sorted Descending
                self.btnSortAsc.configure(state=NORMAL)                   #Enable this button if the list is currently sorted Descending
            if str(self.sort_asc_or_desc).upper().strip()[:3] == "ASC":
                self.btnSortAsc.configure(state=DISABLED)                 #Disable this button if the list is already sorted Ascending
                self.btnSortDesc.configure(state=NORMAL)                  #Enable this button if the list is currenty sorted Ascending

    def disable_display(self):
        if self.allow_view_combined_files:
            self.btnDisplayOneFile.configure(state=DISABLED)
            self.btnDisplayAllFiles.configure(state=DISABLED)	
        self.btnNextPage.configure(state=DISABLED)
        self.btnSortDesc.configure(state=DISABLED)            #Disable this button if the list is already sorted Descending
        self.btnSortAsc.configure(state=DISABLED)            #Disable this button if the list is already sorted Ascending

    def enable_save(self):
        self.btnSaveToDictFile.configure(state=NORMAL)       #Do not enable this button unless the user has selected a MatchResults file to save as

    def disable_save(self):
        self.btnSaveToDictFile.configure(state=DISABLED)       #Do not enable this button unless the user has selected a MatchResults file to save as

    #*****************************************************************************************************************************************
    def instantiate_view_object(self, container, index):
        #Instantiate table-formatted match VIEWS here.
        #Note that the currently instantiated MODEL object serves as model for ALL of the views, so attributes that should be different for each iteration cannot be read form the MODEL.
        if container is None:
            container = self.controller.bigcanvas.bigframe
        self.view_object = MatchReview_View(container, self, index)
        self.matchreview_views.append(self.view_object)   #Add this View to the index
        return self.view_object

    #**********************************************************************************************************
    def display_view(self, container, index, **kw):
        if self.error_message is not None:
            self.handle_error()
            return
        #If the view object has not yet been instantiated, do that now:
        new_view_object = None
        if self.view_object is None: 
            self.view_object = self.instantiate_view_object(container, index)
        if self.view_object.grid_initialized:       #The grid has already been populated at least once, so now we follow a very different process to re-load it with new data.
            self.view_object.repopulate_grid()
        else:      #The grid view has not yet been initialized (loaded with data cells) -- INITIALIZE IT NOW.
            print("\n In MatchReview_Model.display_view(), calling new_view_object.initUI().")
            self.view_object.initUI(**kw)   #DISPLAY THE FRAME OBJECT ON SCREEN

        if self.error_message is not None:
            self.handle_error()
            return
        return new_view_object

    def display_views(self, container=None, howmany_passes=None):
        #Instantiate table-formatted match VIEWS here.  
        #Note that the currently instantiated MODEL object serves as model for ALL of the views, so attributes that should be different for each iteration cannot be read form the MODEL.
        if container is None:
            container = self.controller.bigcanvas.bigframe
        if howmany_passes is None:
            howmany_passes = self.howmany_passes
        print("\n Top of MatchReview_Model.display_views() -- matchreview_file_to_load_from: %s, length of meta_values=%s" % (self.matchreview_file_to_load_from, len(self.meta_values)) )
        #DISPLAY THE SPECIFIED NUMBER OF BLOCKING PASS RESULTS (but only if the Data Dict files have been specified):
        if self.matchreview_file_to_load_from:    #and self.matchreview_file_to_save_to:
            #Function "split_result_files" extracts the contents of the Match Result file and stores it in arrays. The arrays are them passed to the VIEW object to be displayed.
            print("\n" + "In MatchResult.display_view(), about to run split_result_file() with '" + str(self.matchreview_file_to_load_from) + "'" )
            #***********************************************************************
            self.split_result_file(self.matchreview_file_to_load_from)              #Read the match results file into array 
            #***********************************************************************
            if len(self.meta_values) == 0:
                self.error_message = "Meta values array is blank, procedure cancelled."
            if self.error_message is not None:
                self.handle_error()
                return
            for i in range(0, howmany_passes):
                bgcolor = self.bgcolors[i]    #bgcolor = "#FDFFDF"   
                print("\n In MatchView_Model.display_views(), calling display_view() for iteration #" + str(i) +". BgColor=" + bgcolor)
                #**********************************************************************************************************
                #DISPLAY THE MATCH REVIEW SCREEN HERE:
                self.display_view(container, i, width=self.frame_width, background=bgcolor, borderwidth=2, padx=3, pady=3)
            #Now disable the button which loads BlockingPasses--they load new passes in addition to the old ones.  TO DO: write clean-up routine to clear out old passes when user wants to re-load from scratch.
            #self.disable_display()  
        else:
            #***********************************************************************
            #User has not yet selected Data Dictionaries, which are required for displaying Blocking Pass entry screens.
            print("\n About to display the OpenFile dialogs")
            self.display_openfile_dialogs(container)
            self.display_user_buttons(container)
            if self.allow_view_combined_files:
                self.display_advanced_buttons(container)

    def scroll_page(self):
        if self.error_message is not None:
            self.handle_error()
            return
        if self.view_object is not None:
            print("\n About to SCROLL THE PAGE")
            self.view_object.start_row = self.view_object.start_row + self.view_object.rows_to_display
            if self.view_object.start_row >= len(self.meta_values):
                self.view_object.start_row = (len(self.meta_values) +1 - self.view_object.rows_to_display)
            self.view_object.repopulate_grid()
        #Refresh the state of sort buttons:
        self.enable_disable_buttons()		
		
    def scroll_backwards(self):
        if self.error_message is not None:
            self.handle_error()
            return
        if self.view_object is not None:
            print("\n About to SCROLL THE PAGE BACKWARDS")
            self.view_object.start_row = self.view_object.start_row - self.view_object.rows_to_display
            if self.view_object.start_row < 0:
                self.view_object.start_row = 0
            self.view_object.repopulate_grid()
        #Refresh the state of sort buttons:
        self.enable_disable_buttons()		
		
    def debug_display_arrays(self):
        i = 0
        print("self.meta_values:")
        for val in self.meta_values:
            print(str(i) + "  " + str(val))
            i += 1

        i = 0
        print("self.controls:")
        for control in self.controls:
            print("%s) Row: %s, Col: %s, Name: %s, Type: %s" % ( i, control.row, control.col, control.ref_name, control.control_type ))
            i += 1


#******************************************************************************
#******************************************************************************
class MatchReview_View(Frame):
    debug = True
    container = None
    model = None
    widgetstack_counter = None
    bgcolors = []
    bgcolor = None	
    pass_index = None		#Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
    row_index = 0
    rowtype = None	
    show_view = None
    rows_to_display = 30
    start_row = 0
    grid_initialized = False
    pass_index = 0
    meta_rowid = None       #Meta_rowid is a unique identifier (autonum) for each row of self.meta_values, the main array.  It is stored in column 4 (fifth column) in the list.
	
    def __init__(self, container, model=None, pass_index=None, show_view=None):
        Frame.__init__(self, container)
        if container:
            self.container = container
        if model is None:
            model = BlockingPass_Model()				#Normally this VIEW object will be called by an already-instantiated MODEL object.  But this line is there to catch any direct instantiations of the VIEW.		
        self.model = model 
        self.pass_index = pass_index                              #Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
        self.show_view = show_view
        #Display the frame:
        print("\n In matchreview_table_view._init_: self.show_view=" + str(self.show_view))
        if self.show_view:		#Normally __init__ does NOT trigger the screen display, because the class is instantiated and THEN displayed later.
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the container (usually a frame, but could be canvas or the container window), directly below any previous widgets. 
        #The grid() ROW designators refer to the container window's Grid and determine which order the Frames will be displayed in.
        print("\n Type Of Container: " + str(type(self.container)) )
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "matchreview_view.Init")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=EW)                    #position the Frame within the container Window
        #self.configure(width=self.model.frame_width, background=self.model.bgcolor, borderwidth=2, padx=3, pady=3)   #self.model.bgcolor #height=self.frame_height, 
        self.configure(**kw)
        if self.model.check_key_exists("background", **kw):
            self.bgcolor = kw["background"]
        self.configure(background=self.bgcolor)
        print("In initUI(), background=" + str(self.bgcolor))
        for i in range(0,6):
            self.columnconfigure(0, weight=0, pad=2)
        for i in range(0, len(self.model.meta_values)):
            if i < self.rows_to_display:
                self.rowconfigure(0, pad=2)
        #Frame Title:
        print("\n In matchreview_view.initUI: About to display main MatchReview frame title")
        widgetspot = self.get_widgetstack_counter()
        self.label_object = Label(self, text=self.model.title)    #+ " #" + str(self.pass_index +1))
        self.label_object.grid(row=widgetspot, column=0, columnspan=7, sticky=EW)
        self.label_object.configure(background=self.bgcolor, font=("Arial", 16, "bold"), borderwidth=1, width=80, anchor=CENTER, justify=tkinter.LEFT)
        #Column labels:
        vert_position = self.get_widgetstack_counter()
        lbl_kw = {"width":5, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 10, "bold") }
        lbl = self.create_label("Accept", vert_position, 0, **lbl_kw)
        lbl = self.create_label("Pass", vert_position, 1, **lbl_kw)
        lbl = self.create_label("Weight", vert_position, 2, **lbl_kw)
        lbl = self.create_label("Row #", vert_position, 3, **lbl_kw)
        lbl_kw = {"width":20, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 10, "bold") }
        lbl = self.create_label("Record file field", vert_position, 4, **lbl_kw)
        lbl = self.create_label("Memory file field", vert_position, 5, **lbl_kw)
        #Display the first page of results:  
        self.display_review_page(0)
		
    def display_review_page(self, start_row=None):
        #*************************************
        #Display the match values:
        #*************************************
        if start_row is not None:
            self.start_row = start_row
        if self.start_row is None:
            self.start_row = 0
        print("\n In matchreview_view.display_review_page(), start_row=%s" % (self.start_row) )
        self.row_index = 0				
        curvalue = 0 
        data_column_name = ""
        chk_kw = {"width":6, "borderwidth":1, "font_size":11, "rowindex":self.row_index, "text":data_column_name}
        kw_txtbox = {"width":20, "background":self.bgcolor, "foreground":"black", "borderwidth":1, "font":("Arial", 10, "normal")}  #, "data_column_name":data_column_name, "text":data_column_name}
        vert_position = self.get_widgetstack_counter()
        self.rowtype = "matchreview"         #Each row in the CONTROLS list must be stamped with its row type (e.g., "blocking_fields", "matching_fields", etc.
        ix = 0                               #index of the current row
        countrow = 0                         #count the number of rows displayed
        holdweight = holdpass = ""
        bgcolor = "light grey"		
        weight_color = "dark slate blue"
        for item in self.model.meta_values:
            if ix >= self.start_row and countrow <= self.rows_to_display:
                self.meta_rowid = item[6]
                print("Row %s is between %s and %s so it will be displayed. Meta_rowid=%s" % (ix, self.start_row, int(self.start_row) + int(self.rows_to_display), self.meta_rowid ) )
                vert_position = self.get_widgetstack_counter()
                label_text = ""
                #(1) Checkbox to indicate that this field should be accepted as a match:
                gridcolumn = 0
                chk = self.create_checkbox("", vert_position, gridcolumn, curvalue, "chkaccept_" + self.rowtype[:2], **chk_kw)
                #(2) Text box to display the Blocking Pass number that this row was generated by
                gridcolumn = 1
                kw_txtbox["width"] = 6
                curvalue = str(item[0]).strip()       #Weights and unique IDs
                control_name = "blkpass_" + str(self.pass_index) + "_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                if curvalue != holdpass:
                    if bgcolor == "light grey":
                        bgcolor = self.bgcolor
                    else:
                        bgcolor = "light grey"
                    holdpass = curvalue
                if curvalue != holdweight:
                    #remove the color calculation here - move it to get_weight_color()
                    holdweight = curvalue
                kw_txtbox["background"] = bgcolor
                #(3) Text box to display the weight   #and unique IDs
                gridcolumn = 2
                kw_txtbox["width"] = 6
                curvalue = str(item[1]).strip()       #Weights and unique IDs
                curvalue = curvalue.split(" ")[0].strip()     #Just get the weight, discard the unique key values for now
                control_name = "weight_" + str(self.pass_index) + "_" + str(ix)
                weight_color = self.get_weight_color(curvalue, holdweight)
                kw_txtbox["foreground"] = weight_color
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                kw_txtbox["foreground"] = "black"
                #(4) Text box to display the row number
                gridcolumn = 3
                kw_txtbox["width"] = 4
                curvalue = str(ix)                    #Row number in the list (index)
                control_name = "ix_" + str(self.pass_index) + "_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                #(5) Record file match values:
                gridcolumn = 4
                kw_txtbox["width"] = 70
                '''
                kw_txtbox["disabledforeground"] = "black"
                curvalue = str(item[2])       #Record file match values
                control_name = "recfl_" + str(self.pass_index) + "_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                #(6) Memory file match values:
                gridcolumn = 5
                curvalue = str(item[3])       #Memory file match values
                control_name = "memfl_" + str(self.pass_index) + "_" + str(ix)
                txt = self.create_textbox(label_text, vert_position, gridcolumn, curvalue, control_name, data_column_name, self.rowtype, **kw_txtbox)
                '''
                self.recfile_values_for_current_row = str(item[2])
                self.memfile_values_for_current_row = str(item[3])
                kw_fresult = {"background":self.bgcolor, "borderwidth":1, "height":1, "padx":4, "pady":2}              #, "data_column_name":data_column_name, "text":data_column_name, "font":("Arial", 10, "normal") }
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "rec", vert_position, gridcolumn, **kw_fresult)             #RECORD FILE matching fields are contained in item[2]
                gridcolumn +=1
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "mem", vert_position, gridcolumn, **kw_fresult)             #MEMORY FILE matching fields are contained in item[3]
                countrow += 1
                ix += 1
                self.row_index += 1 
                
        self.grid_initialized = True
        self.container.refresh_canvas()

    def get_weight_color(self, weight, holdweight=None, schema=None):
        weight_color = ""
        if schema is None:
            schema = "weight_scale"            #"alternating"
        if schema.lower().strip() == "weight_scale":
            if float(weight) > 30:
                weight_color = "red"
            elif float(weight) > 24:
                weight_color = "dark orchid"
            elif float(weight) > 18:
                weight_color = "dark_violet"
            elif float(weight) > 12:
                weight_color = "dark slate blue"
            elif float(weight) > 10:
                weight_color = "blue"
            elif float(weight) > 9:
                weight_color = "blue"
            elif float(weight) > 8:
                weight_color = "dark turquoise"
            elif float(weight) > 7:
                weight_color = "medium sea green"
            elif float(weight) > 6:
                weight_color = "dark olive green"
            elif float(weight) > 5:
                weight_color = "dark goldenrod"
            elif float(weight) > 4:
                weight_color = "dark gray"
            else:
                weight_color = "black"
        elif schema.lower().strip() == "alternating":
            if curvalue != holdweight:
                if weight_color == "dark green":    
                    weight_color = "dark slate blue"
                elif weight_color == "dark slate blue":
                    weight_color = "dark green"    
                #print("Old Weight: %s, New Weight: %s, New Color: %s" % (holdweight, curvalue, weight_color) )
        return weight_color
    
    def clear_grid(self):
        if self.model.controls:
            for control in self.model.controls:
                col = control.col
                row = control.row
                control_type = str(control.control_type).lower().strip()				
                #print("CLEARING: Col: %s Row: %s Type: %s" % ( str(control.col), str(control.row), control_type ) )
                value = ""				
                if control_type == "checkbox":
                    control.object.deselect()     #Un-check the checkbutton object
                else:
                    value = control.value_object.get()
                    control.value_object.set('')
                #print("CLEARED: Col: %s Row: %s Type: %s, Current control value: %s" % ( str(control.col), str(control.row), str(control.control_type), value ) ) 
                control.object.grid(column=col, row=row)

    def repopulate_grid(self):
        '''Function repopulate_grid() is called when the Entry grid is re-drawn with new values.  This happens all the time, because the user displays a small number of rows at a time.'''
        #print("\n ARRAYS before clear:")
        #self.model.debug_display_arrays()
        self.clear_grid()    #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_arrays() deletes these class properties.
        #print("\n ARRAYS after clear:")
        #self.model.debug_display_arrays()
		
        #NOTE: each item in self.meta_values is itself a list of cell values - so each item represents a row of cells.
        print("\n *********************************************************************")
        print("RE-POPULATING self.model.controls LIST FROM self.model.meta_values")
        print("StartRow: %s EndRow: %s" % (self.start_row, int(self.start_row) + int(self.rows_to_display) ) )
        ix = 0                              #index of the current row
        countrow = 0                        #count the number of rows displayed
        holdweight = ""
        weight_color = "dark slate blue"
        for item in self.model.meta_values:
            #print("In Repopulate, row %s" % (ix) )
            if ix >= self.start_row and countrow <= self.rows_to_display:
                self.recfile_values_for_current_row = ""
                self.memfile_values_for_current_row = ""
                self.meta_rowid = item[6]
                #print("Repopulating: Row %s is between %s and %s so it will be displayed. Meta_rowid=" % (ix, self.start_row, int(self.start_row) + int(self.rows_to_display, self.meta_rowid) ) )
                #Checkbox:
                col = 0
                newvalue = 0                           #Un-check the boxes when we re-draw the page
                #Blocking Pass:
                col = 1
                newvalue = str(item[0]).strip()        #Weights and unique IDs
                #newvalue = newvalue.split(" ")[0]     #Just get the weight, discard the unique key values for now
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                self.update_control_in_grid(countrow, col, newvalue)
				
                #Weight:
                col = 2
                newvalue = str(item[1]).strip()        #Weights and unique IDs
                if newvalue != holdweight:             #Don't use the alternating weight colors here - get colors from the function instead
                    holdweight = newvalue
                weight_color = self.get_weight_color(newvalue, holdweight)
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                self.update_control_in_grid(countrow, col, newvalue, weight_color)

                #Text box to display the row number
                col = 3
                newvalue = str(ix)                     #Row number within the list (index)
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                self.update_control_in_grid(countrow, col, newvalue)
				
                #Record file match values:
                col = 4
                newvalue = str(item[2])       #Record file match values
                self.recfile_values_for_current_row = str(item[2])
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                self.update_control_in_grid(countrow, col, newvalue, "recfile_values")
				
                #Memory file match values:
                col = 5
                newvalue = str(item[3])       #Memory file match values
                self.memfile_values_for_current_row = str(item[3])
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                self.update_control_in_grid(countrow, col, newvalue, "memfile_values")
                
                #Re-render the comparison frames for the user to review:
                kw_fresult = {"background":self.bgcolor, "borderwidth":1, "height":1, "padx":4, "pady":2}   
                vert_position = ix +3            #Column labels are at row 0, blank space at row 1		
                gridcolumn = 4
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "rec", vert_position, gridcolumn, **kw_fresult)             #RECORD FILE matching fields are contained in item[2]
                gridcolumn = 5
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "mem", vert_position, gridcolumn, **kw_fresult)             #MEMORY FILE matching fields are contained in item[3]
				
                countrow += 1
            ix += 1
        #self.debug_display_arrays()
        self.container.refresh_canvas()

    def update_control_in_grid(self, row, col, newvalue, controltype=None, fontcolor=None):
        #Find the correct element in self.controls where COL attribute = col, and the ROW attribute = row.
        #print("Seeking row=%s and col=%s ... new value is %s" % (str(row), str(col), newvalue ) )
        found = False
        for control in self.model.controls:
            #When we find the correct Entry object in the self.controls list, update its value to reflect the newly-submitted meta_values.
            #print("NEXT UP: COL: %s ROW: %s Current value: %s, New value: %s" % (str(control.col), str(control.row), str(control.value_object.get()), newvalue  ) )
            if str(control.col) == str(col) and str(control.row) == str(row):
                #print("FOUND: Col: %s Row: %s Current value: %s, New value: %s" % (str(control.col), str(control.row), str(control.value_object.get()), newvalue ) )
                control.value_object.set(newvalue)
                control.object.grid(column=col, row=row)
                control.object.config(foreground=fontcolor)
                #print("AFTER: Col: %s Row: %s control value: %s" % (str(control.col), str(control.row), str(control.value_object.get())))
                found = True
                self.container.refresh_canvas()
                break

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
        lbl.configure(**kw)

    def create_textwidget(self, label_text, gridrow, gridcolumn, curvalue='', textbox_name='txt_unknown', data_column_name='', rowtype='unknown', **kw):       #gridcolumn=0, width=12, font_size=12, rowindex=0
        textwidg = Text(self)
        textwidg.grid(row=gridrow, column=gridcolumn, sticky=EW)
        textwidg.insert(INSERT, curvalue)
        textwidg.configure(foreground="blue")
        textwidg.configure(**kw)

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
        self.model.add_control_to_list(entry, var, blocking_pass=self.pass_index, ref_name=textbox_name, row_index=self.row_index, row=gridrow, col=gridcolumn, control_type="textbox", meta_rowid=self.meta_rowid)

    def create_checkbox(self, label_text, gridrow, gridcolumn, curvalue=0, chkbox_name='chk_unknown', **kw):       #gridcolumn=0, width=12, font_size=11, rowindex=0
        #print("\n About to display checkbox '" + label_text + "'")
        var = StringVar(self)
        var.set(curvalue)   #CurValue is set to 1 if already selected (i.e., specified in parmf.txt file). The ParmF value is checked by function get_current_variable_value()
        font_size = kw["font_size"]
        chkwidth = kw["width"]
        chk = Checkbutton(self, text=label_text, variable=var)
        chk.grid(row=gridrow, column=gridcolumn, sticky=W)
        chk.configure(background=self.bgcolor, font=("Arial", font_size, "bold"), borderwidth=2, width=chkwidth, anchor=W)
        chk.configure(state=NORMAL)
        #Add this control to the controls collection:		
        self.model.add_control_to_list(chk, var, blocking_pass=self.pass_index, ref_name=chkbox_name, row_index=kw["rowindex"], row=gridrow, col=gridcolumn, control_type="checkbox", meta_rowid=self.meta_rowid)

    def create_optmenu(self, value_list, curvalue='', optmenu_name='', **kw):     #gridrow=None, gridcolumn=1, width=12, rowindex=0
        var = StringVar(self)
        var.set(curvalue)
        gridrow = gridcolumn = rowindex = 0
        if self.model.check_key_exists("gridrow", **kw):
            gridrow = kw["gridrow"] 
        if self.model.check_key_exists("gridcolumn", **kw):
            gridcolumn = kw["gridcolumn"] 
        if self.model.check_key_exists("rowindex", **kw):
            rowindex = kw["rowindex"]		
        optmenu = OptionMenu(self, var, *value_list, command=lambda x:self.capture_menu_click(optmenu_name, var) )
        optmenu.grid(column=gridcolumn, row=gridrow, sticky=W)                      #position the Frame within the container Window or Frame
        optmenu.config(font=('calibri',(10)), bg='white', width=kw["width"])
        optmenu['menu'].config(background=self.bgcolor, font=("calibri",(11)) )     #,bg='white'
        #Add this control to the controls collection:		
        self.model.add_control_to_list(optmenu, var, blocking_pass=self.pass_index, ref_name=optmenu_name, row_index=rowindex, row=gridrow, col=gridcolumn, control_type="optmenu", meta_rowid=self.meta_rowid)

    def create_spinner(self, from_=0, to=20, value_tuple=(), spinner_name='', gridrow=None, gridcolumn=1, curvalue=1, **kw):
        var = StringVar(self)
        var.set(curvalue)
        if value_tuple:
            spn = Spinbox(self, values=value_tuple)
        else:
            spn = Spinbox(self, from_=from_, to=to)
        spn.grid(row=gridrow, column=gridcolumn, sticky=W)
        spn.config(textvariable=var, background=self.bgcolor, width=8)		
        #Add this control to the controls collection:		
        self.model.add_control_to_list(spn, var, blocking_pass=self.pass_index, ref_name=spinner_name, row_index=kw["rowindex"], row=gridrow, col=gridcolumn, control_type="optmenu", meta_rowid=self.meta_rowid)

    def create_resultrow_frame(self, matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw):
        '''Pass both the RECORD and MEMORY matching fields values to this function, so that we can compare each segment of those values and highlight differences'''
        print("\n In create_resultrow_frame(), mem_or_rec: %s, matchvals_rec: %s, matchvals_mem: %s, gridcolumn: %s" % (mem_or_rec, matchvals_rec, matchvals_mem, gridcolumn) )
        mem_or_rec = str(mem_or_rec).lower().strip()
        frame = Frame(self)
        frame.grid(row=gridrow, column=gridcolumn, sticky=EW)
        if not self.model.check_key_exists("background", **kw):
            kw["background"] = self.bgcolor
        if not self.model.check_key_exists("width", **kw):
            kw["width"] = 80
        frame.configure(**kw)
        var0 = StringVar(self)
        var0.set("")
        lbl0 = Label(frame, textvariable=var0)
        var_lbl0 = [var0, lbl0]
        var1 = StringVar(self)
        var1.set("")
        lbl1 = Label(frame, textvariable=var1)
        var_lbl1 = [var1, lbl1]
        var2 = StringVar(self)
        var2.set("")
        lbl2 = Label(frame, textvariable=var2)
        var_lbl2 = [var2, lbl2]
        var3 = StringVar(self)
        var3.set("")
        lbl3 = Label(frame, textvariable=var3)
        var_lbl3 = [var3, lbl3]
        var4 = StringVar(self)
        var4.set("")
        lbl4 = Label(frame, textvariable=var4)
        var_lbl4 = [var4, lbl4]
        var5 = StringVar(self)
        var5.set("")
        lbl5 = Label(frame, textvariable=var5)
        var_lbl5 = [var5, lbl5]
        var6 = StringVar(self)
        var6.set("")
        lbl6 = Label(frame, textvariable=var6)
        var_lbl6 = [var6, lbl6]
        var7 = StringVar(self)
        var7.set("")
        lbl7 = Label(frame, textvariable=var7)
        var_lbl7 = [var7, lbl7]
        var8 = StringVar(self)
        var8.set("")
        lbl8 = Label(frame, textvariable=var8)
        var_lbl8 = [var8, lbl8]
        var9 = StringVar(self)
        var9.set("")
        lbl9 = Label(frame, textvariable=var9)
        var_lbl9 = [var9, lbl9]
        #Add a row to the result_comparison_frames_in_grid list. Each row consists of a single frame object and the StringVars and Label objects associated with that frame object.
        frame_and_its_labels = [frame, var_lbl0, var_lbl1, var_lbl2, var_lbl3, var_lbl4, var_lbl5, var_lbl6, var_lbl7, var_lbl8, var_lbl9]
        self.model.result_comparison_frames_in_grid.append(frame_and_its_labels)
        frame_index = len(self.model.result_comparison_frames_in_grid) - 1
        #Configure each Label that was just added to the list.
        color = "black"
        lbl = self.model.result_comparison_frames_in_grid[0][1][1]
        #ilbx = 1
        #for ilbx in range(0, 9):
        #    lbl = self.model.result_comparison_frames_in_grid[frame_index][ilbx][1]
        lbl.grid(row=0, column=0, sticky=W)
        lbl.config(**kw)
        lbl.config(anchor=W, font=("Arial", 10, "normal"))
        lbl.config(foreground=color)
		#Display this frame object in the grid:
        self.populate_resultrow_frame(frame_index, matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw)          #Display the comparison values

    def populate_resultrow_frame(self, frame_index, matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw):
		#Display the comparison text in the mem or rec frame:
        print("\n In populate_resultrow_frame(), mem_or_rec: %s, matchvals_rec: %s, matchvals_mem: %s, gridcolumn: %s" % (mem_or_rec, matchvals_rec, matchvals_mem, gridcolumn) )
        matchsegs_rec = matchvals_rec.split(" ")
        matchsegs_mem = matchvals_mem.split(" ")
        max_num_segments = len(matchsegs_rec)
        min_num_segments = len(matchsegs_rec)
        if len(matchsegs_mem) < len(matchsegs_rec):         #MAKE SURE we set num_segments to the SMALLER number of segments between REC and MEM.  Otherwise an error occurs because the array index exceeds the number of items in the array.
            min_num_segments = len(matchsegs_mem)
        elif len(matchsegs_mem) > len(matchsegs_rec):
            max_num_segments = len(matchsegs_mem)
        print("\n FrameIndex=%s... Items in model.result_comparison_frames_in_grid[frame_index]: %s" % (frame_index, len(self.model.result_comparison_frames_in_grid[frame_index]) ) )
        itmx = 0
        for item in self.model.result_comparison_frames_in_grid[frame_index]:    #Item0 is a frame, the remaining items are all StringVars associated with labels within the frame.
            if itmx > 0:
                print("Type of ResltComprFrm row %s item %s: %s" % (frame_index, itmx, type(item[itmx]) ) )
                #print("Type of ResltComprFrm row %s item %s sub-item[0]=%s, Type of sub-item[1]=%s" % (frame_index, itmx, type(item[itmx][0]), type(item[itmx][0]) ) )
                #item[itmx][0].set("")                         #Erase existing values that were previously displayed
            itmx +=1
        ix = 0
        color = "black"
        recseg = memseg = text = ""
        for ix in range(0, max_num_segments):
            memseg = recseg = ""
            if len(matchsegs_rec) > ix:
                recseg = str(matchsegs_rec[ix])
            if len(matchsegs_mem) > ix:
                memseg = str(matchsegs_mem[ix])
            if len(matchsegs_rec) > ix and len(matchsegs_mem) > ix:    #Both RECORD and MEMORY matching field values have at least this many segments -- compare them to see whether they match.
                if recseg.lower().strip() == memseg.lower().strip():     
                    color = "black"                                      #This segment is identical between the RECORD FILE and the MEMORY FILE
                else:                                                    
                    color = "red"                                        #This segment is NOT identical between the RECORD FILE and the MEMORY FILE
            else:                                                        
                color = "gray"                                            #RECORD and MEMORY matching field values might have a different number of segments
            if mem_or_rec == "mem":
                text = memseg
            elif mem_or_rec == "rec":
                text = recseg
            print("Seg: %s" % (text) )
            #GMS TEMP REM - self.model.result_comparison_frames_in_grid[frame_index][ix][0].set(text)   #Update the StringVar values stored in this array, from which labels take their values.
            kw["width"] = len(text) + 1
            #lbl = Label(frame, textvariable=var)
            #var.set(text)
            lbl.grid(row=0, column=ix, sticky=W)
            lbl.config(**kw)
            lbl.config(anchor=W, font=("Arial", 10, "normal"))
            lbl.config(foreground=color)
            ix +=1
		

    def get_color_for_match_segment(self, matchvals1, matchvals2):
        ''' docstring '''
        color = ""
        ix = 1
        for seg in matchsegs1:
            if len(matchsegs2) >= ix:
                if seg == matchsegs2[ix]:        #This segment is identical between the RECORD FILE and the MEMORY FILE
                    color = "black"
                else:                            #This segment is identical between the RECORD FILE and the MEMORY FILE
                    color = "red"
            ix +=1
        return color

        
    def capture_menu_click(self, optmenu_name, var):
        print("\n YOU HAVE CAPTURED THE VALUE: " + str(var.get()) + " FOR " + optmenu_name )
        return True

 # End of class matchreview_view


		
#******************************************************************************************		
#******************************************************************************************		
class Control():
    model = None           #MatchReview_Model object
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
#******************************************************************************************		
def main():
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    '''Geometry for all windows in this app is set by main.py '''
    master = MatchReview_Model(None, None)
    master.matchreview_file_to_load_from = "C:\\Greg\ChapinHall\\RecordLinking\\BigMatch\\building_permits_0_5k_test_newfldwidths-GeogParcel_Chicago_SqlSvrExport_March2014_Pairs_00.dat"
    master.split_result_file()

if __name__ == "__main__":
    main()  

#print("Kwargs for MatchReview_Model.display_view(): ")
#print(str(kw))
#for key, value in kw.items():
#    print("%s = %s" % (key, value) )

#!C:\Python33\python.exe -u
#!/usr/bin/env python
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from TkEntry import EntryGrid
import traceback
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
    '''Display a standard BigMatch result file for the user, so that potential matches can be assessed and either accepted or rejected.
    The logic of displaying these pairs falls to the View class (see below, class MatchReview_View())
    first, all values form the BigMatch result file (which can have 100,000+ rows in some cases) are loaded into self.meta_values.
    But we display only 30 rows at a time on screen. The user can scroll from page to page, looking for the cutoff between acceptable and non-acceptable matches.
    '''
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
    combined_exact_accepted_file = None      #Combined matched pairs (exact and accepted) for all passes in a batch
    allow_view_combined_files = True         #Allowing the user to combine BigMatch results files and handle the entire batch at once is an advanced feature, not for casual users.
    viewing_one_or_all_files = None          #If the user chooses to combine the selected file with ALL files in the same folder sharing a similar name but different suffix, this flag switches from "ONE" to "ALL"
    result_filename_trunc = None             #If the user chooses to combine the selected file with ALL files in the same folder sharing a similar name but different suffix (Mymatch_Pairs_00.dat would be combined with Mymatch_Pairs_01.dat, etc.)
    match_files_for_batch = None             #Files that will be combined into self.combined_matchreview_file or combined_exact_accepted_file
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
    no_delimiters_in_result_file = None      #Some users might not want field delimiters embedded in the result file
    write_descrips_in_result_file = None     #Some users might want column descriptions embedded in the result file
    max_length_rec_id = 0                    #
    max_length_mem_id = 0                    #
    max_length_matching_text = 0             #In order to produce justified output files, we need to know how to line up the columns (depends on the max.width of the text in this particular file)
    length_matching_text_column = 0          #In order to produce justified output files, we need to know how to line up the columns (depends on the max.width of the text in this particular file)
    separator_for_result_files = "?   ~"     #In the BigMatch results files, this string separates the first column (weight, unique IDs and blocking field values) from the matching field values.

    def __init__(self, parent_window, controller, title="Linkage results -- review", bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height):	
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        now = datetime.datetime.now()
        self.init_time = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + ' ' + str(now.hour).rjust(2,'0') + ':' + str(now.minute).rjust(2,'0')
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\n\n____________________________________________________________________", True, True )
        self.logobject.logit("%s In MatchReview_Model._init_: title=%s" % (self.init_time, title), True, True )
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
    def split_result_file(self, matchreview_file=None):
        '''Parse the standard BigMatch result file, extracting key information such as the match weight, ID (sequence) fields, matched values, etc.
        All of this information is stored in self.meta_values. But NOTE: the simple match values stored in self.meta_values proved to be insufficient for a robust user assessment.
        So match values are stored separately in self.frame_and_its_labels, so that they can be displayed and re-displayed in color-coded segments. See below function populate_resultrow_frame()'''
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
            self.memvalues_file = matchreview_file.lower().strip().replace(ext, "_memflmatches" + ext)
        #Run through a small number of rows to estimate the width of the match file text
        '''
        #Traverse the specified Match Results file and extract parts of each row into a list
        print("\n TOP OF FUNCTION split_result_file() -- file: %s" % (str(matchreview_file)) )
        count = blkpass_rowcount = meta_rowid = weight_pos = 0
        self.max_length_matching_text = 20   #Start out assuming a very narrow set of matching fields -- then use the maximum width to set a "justify" line so that the results appear less ragged.
        blkpass = holdpass = ""
        #Run thru a small number of rows just to get an idea of how long the matching text is, so we space the columns correctly
        self.length_matching_text_column = self.estimate_matchfile_text_length(matchreview_file)
        #Now loop thru the entire file and store values to an in-memory list, or write values to disk, as appropriate for the situation.
        with open(matchreview_file, 'r') as matchfile:
            with open(self.exact_match_output_file, 'w') as exactfile:
                for row in matchfile:
                    if len(row) == 0:
                        continue                         #Empty row
                    if str(row)[:4]=="****":             #Asterisk lines are placed in the file to denote the start of a new section of results (different blocking pass)
                        continue
                    '''GMS halves = str(row).split(sep, 1)
                    first_half = self.reduce_blank_spaces( str(halves[0]).strip() )
                    first_half = first_half.replace("  ", " ")   #Not sure why the reduce...() function didn't get rid of all double-spaces.
                    first_half_as_list = first_half.split(" ")
                    #if self.debug: self.logobject.logit("1st half: %s" % (first_half), True, True, True )
                    chunk1 = first_half_as_list[0].lower().strip() #First chunk of text could be Weight (if the BigMatch result file is unaltered) -OR- it could be Blocking Pass number (if file was altered by this GUI or some other post-process)
                    bp_pos = chunk1.find("bp:")            #If the file being reviewed has been post-processed by this GUI to combine results from multiple blocking passes, then it should have the string "bp:" in every row, specifying which blocking pass the row was generated by.
                    if bp_pos == -1:                       #If the bloaking pass number has not been added to this results file (it usually is not added), then we can discover the blocking pass by parsing the Bigmatch result file name.
                        blkpass = self.get_blocking_pass_num_from_results_filename()                   # "0"
                        weight = chunk1
                        weight_pos = 0
                    else:
                        blkpass = chunk1[bp_pos+3: bp_pos+5].lower().strip()
                        weight = first_half_as_list[1]
                        weight_pos = 1
                    '''
                    '''GMS weight = weight.replace("+", "")
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
                    if self.debug: self.logobject.logit("Next: first_half_as_list: %s, weight: %s | blkpass: %s, id_rec:%s, id_mem: %s, blkvals: '%s'" % (first_half_as_list, weight, blkpass, id_rec, id_mem, blkfldvals), True, True, True )
                    #Move on to the second half of the row:
                    matchvals = halves[1]                   #Second half of each row has the selected blocking/matching field values
                    matchlist = matchvals.split("~")        #Tilde separates Record File attributes from Memory File attributes, within the 2nd half of the row.
                    recmatches = self.reduce_blank_spaces(str(matchlist[0]).strip())  #Record File attributes
                    #if len(recmatches) > self.max_length_matching_text:                                      #Use the maximum width to set a "justify" line so that the results appear less ragged
                    #    self.max_length_matching_text = len(recmatches)
                    memmatches = self.reduce_blank_spaces(str(matchlist[1]).strip())  #Memory File attributes
                    #if len(memmatches) > self.max_length_matching_text:                                      #Use the maximum width to set a "justify" line so that the results appear less ragged
                    #    self.max_length_matching_text = len(memmatches)
                    if self.debug: self.logobject.logit("Recmatches: %s, Memmatches: %s" % (recmatches, memmatches), True, True, True )
                    '''
                    #**************************************************************
                    meta_row = self.parse_resultfile_row(row, meta_rowid)
                    #**************************************************************
                    blkpass = meta_row[0]
                    if blkpass != holdpass:                    #Reset this counter when we encounter a new Blocking Pass section
                        blkpass_rowcount = 0
                        holdpass = blkpass
                    weight = meta_row[1]
                    recmatches = meta_row[2]
                    memmatches = meta_row[3]
                    id_rec = meta_row[4]
                    id_mem = meta_row[5]
                    #meta_rowid = meta_row[6]
                    #blkfldvals = meta_row[7]
                    if recmatches == memmatches:            #Exact matches are written to a separate file
                        if self.debug: self.logobject.logit("Exact match: %s -|- %s" % (recmatches, memmatches), True, True, True ) 
                        if self.no_delimiters_in_result_file:
                            exactfile.write("%s %s %s %s %s %s \n" % (blkpass, weight.rjust(9), id_rec.ljust(self.max_length_rec_id), recmatches.ljust(self.length_matching_text_column+10), id_mem.ljust(self.max_length_mem_id), memmatches.ljust(self.length_matching_text_column+10)) )
                        else:
                            exactfile.write("%s | %s | %s | %s | %s | %s \n" % (blkpass, weight.rjust(9), id_rec.ljust(self.max_length_rec_id), recmatches.ljust(self.length_matching_text_column+10), id_mem.ljust(self.max_length_mem_id), memmatches.ljust(self.length_matching_text_column+10) ) )
                    else:                 #NOT exact matches - store these in the meta_values array
                        '''GMS accept_wgt = accept_usr = 0                                   #accept_wgt and accept_usr flags will track rows which the user has ACCEPTED via a weight cutoff threshold (above which rows are "accepted" or an explicit selection by user click of a checkbox) '''
                        if self.debug: self.logobject.logit("Adding row to meta_values: %s, %s, %s, %s" % (blkpass, weight, recmatches, memmatches), True, True, True )
                        #**************************************************************************************************************
                        #Populate the meta_values array (list of lists) that will be used to populate the Entry Grid
                        self.meta_values.append(meta_row)		          #meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.\
                        #**************************************************************************************************************
                        #print("\n -- ROW %s" % (count) )
                        #print("rec: %s" % (recmatches) )
                        #print("mem: %s" % (memmatches) )
                        meta_rowid += 1                   #Count this as a row that will be added to self.meta_values
                    count += 1
                #Close files:
                exactfile.close()
            matchfile.close()
        self.matchfile_rows = count
        self.logobject.logit("\n At end of split_result_file(), meta_values has %s rows, and the matchfile has %s rows." % (len(self.meta_values) , self.matchfile_rows), True, True, True )  
        self.sort_list()
     
    def parse_resultfile_row(self, row, meta_rowid=None, update_column_widths=None):
        halves = str(row).split(self.separator_for_result_files, 1)
        first_half = self.reduce_blank_spaces( str(halves[0]).strip() )
        first_half = first_half.replace("  ", " ")   #Not sure why the reduce...() function didn't get rid of all double-spaces.
        first_half_as_list = first_half.split(" ")
        #if self.debug: self.logobject.logit("1st half: %s" % (first_half), True, True, True )
        chunk1 = first_half_as_list[0].lower().strip() #First chunk of text could be Weight (if the BigMatch result file is unaltered) -OR- it could be Blocking Pass number (if file was altered by this GUI or some other post-process)
        bp_pos = chunk1.find("bp:")            #If the file being reviewed has been post-processed by this GUI to combine results from multiple blocking passes, then it should have the string "bp:" in every row, specifying which blocking pass the row was generated by.
        if bp_pos == -1:           #If the bloaking pass number has not been added to this results file (it usually is not added), then we can discover the blocking pass by parsing the Bigmatch result file name.
            blkpass = self.get_blocking_pass_num_from_results_filename()                   # "0"
            weight = chunk1
            weight_pos = 0
        else:
            blkpass = chunk1[bp_pos+3: bp_pos+5].lower().strip()
            weight = first_half_as_list[1]
            weight_pos = 1
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
        if self.debug: self.logobject.logit("Next: first_half_as_list: %s, weight: %s | blkpass: %s, id_rec:%s, id_mem: %s, blkvals: '%s'" % (first_half_as_list, weight, blkpass, id_rec, id_mem, blkfldvals), True, True, True )
        #Move on to the second half of the row:
        matchvals = halves[1]                   #Second half of each row has the selected blocking/matching field values
        matchlist = matchvals.split("~")        #Tilde separates Record File attributes from Memory File attributes, within the 2nd half of the row.
        recmatches = self.reduce_blank_spaces(str(matchlist[0]).strip())  #Record File attributes
        memmatches = self.reduce_blank_spaces(str(matchlist[1]).strip())  #Memory File attributes
        #In order to space the columns in our output files, we need to know IN ADVANCE how wide these columns are.  So we parse 50 rows in advance, and hope that this captures a good estimate of the maximum column widths.
        if update_column_widths:
            if len(str(id_rec).strip()) > self.max_length_rec_id:
                self.max_length_rec_id = len(str(id_rec).strip())
            if len(str(id_mem).strip()) > self.max_length_mem_id:
                self.max_length_mem_id = len(str(id_mem).strip())
        if self.debug: self.logobject.logit("Recmatches: %s, Memmatches: %s" % (recmatches, memmatches), True, True, True )
        accept_wgt = accept_usr = 0                       #accept_wgt and accept_usr flags will track rows which the user has ACCEPTED via a weight cutoff threshold (above which rows are "accepted" or an explicit selection by user click of a checkbox)
        if self.debug: self.logobject.logit("Adding row to meta_values: %s, %s, %s, %s" % (blkpass, weight, recmatches, memmatches), True, True, True )
        #**************************************************************************************************************
        #Populate the meta_values array (list of lists) that will be used to populate the Entry Grid
        meta_row = [blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid, blkfldvals, accept_wgt, accept_usr]     #meta_temp is a LIST consisting of one row from the Review File
        return meta_row
        
    def estimate_matchfile_text_length(self, matchreview_file):
        with open(matchreview_file, 'r') as matchfile:
            i = 0
            for row in matchfile:
                if i > 50:
                    break
                #**************************************************************
                update_column_widths = True
                meta_row = self.parse_resultfile_row(row, 0, update_column_widths)
                #**************************************************************
                i += 1
            matchfile.close()
        self.max_length_rec_id = self.max_length_rec_id +2
        self.max_length_mem_id = self.max_length_mem_id +2
        self.length_matching_text_column = self.max_length_matching_text +10                            #Account for the fact that some rows might be wider than any of the first few rows
        return self.length_matching_text_column

    '''def init_grid_arrays(self):
        i = 0
        for i in range(0, self.matchfile_rows):
            self.meta_rownums.append(str(i))        #Display row numbers in the Entry Grid
        self.meta_columns = ["Record file data values", "Memory file data values"]'''

    def sort_list(self):
        '''Sort the list by match-weight'''
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
        #We need a second button frame for this module
        self.button_frame2 = Frame(container)
        stackslot = container.get_widget_position(self.button_frame2, "MatchReview_Model.display_user_buttons_2()")
        self.button_frame2.grid(row=stackslot, column=0, sticky=EW)
        self.button_frame2.configure(background=self.bgcolor, padx=4, pady=1)
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
        
        #Second user_buttons frame to hold weight-based manipulations
        #User can jump to rows with a specific weight here.
        self.lblJumpToWeight = Label(self.button_frame2, text="Jump to weight: ")
        self.lblJumpToWeight.grid(row=0, column=0, sticky=W) 
        self.lblJumpToWeight.configure(background=self.bgcolor, font=("Arial", 10, "normal"), borderwidth=0, width=15, anchor=E, padx=4, pady=1)

        self.jump_to_weight = StringVar(self.button_frame2)
        self.jump_to_weight.set(8)                      #If no rows are found with this weight, the next highest weight found will be used. If none found, then no action.
        self.jump_to_weight.trace("w", self.catch_jump_to_weight_change)
        txtJumpTo = Entry(self.button_frame2)
        txtJumpTo.grid(row=0, column=1, sticky=W)
        txtJumpTo.config(textvariable=self.jump_to_weight, background=self.bgcolor, width=5)
        txtJumpTo.bind(sequence="<FocusOut>", func=self.handle_jump_to_weight)
        txtJumpTo.bind(sequence="<Return>", func=self.handle_jump_to_weight)
        #txtJumpTo.bind(sequence="<ButtonRelease-1>", func=self.handle_jump_to_weight)
        
        #User can set the threshold for ACCEPTANCE here.
        self.lblAcceptAbove = Label(self.button_frame2, text="Accept above: ")
        self.lblAcceptAbove.grid(row=0, column=2, sticky=W) 
        self.lblAcceptAbove.configure(background=self.bgcolor, font=("Arial", 10, "normal"), borderwidth=0, width=15, anchor=E, padx=4, pady=1)

        ''' GMS spinner is not ideal, change to Entry		
        #self.accept_threshold = StringVar(self.button_frame2)
        #self.accept_threshold.set(10)
        #spn = Spinbox(self.button_frame2, from_=0, to=30)
        #spn.grid(row=0, column=3, sticky=W)
        #spn.config(textvariable=self.accept_threshold, background=self.bgcolor, width=5)
        #spn.bind(sequence="<FocusOut>", func=self.spinhandler)
        #spn.bind(sequence="<Return>", func=self.spinhandler)
        #spn.bind(sequence="<ButtonRelease-1>", func=self.spinhandler)  '''
	    
        self.accept_threshold = StringVar(self.button_frame2)
        self.accept_threshold.set(10)
        self.accept_threshold.trace("w", self.catch_threshold_change)
        spn = Entry(self.button_frame2)
        spn.grid(row=0, column=3, sticky=W)
        spn.config(textvariable=self.accept_threshold, background=self.bgcolor, width=5)
        spn.bind(sequence="<FocusOut>", func=self.spinhandler)
        spn.bind(sequence="<Return>", func=self.spinhandler)
        spn.bind(sequence="<ButtonRelease-1>", func=self.spinhandler)
        
        self.btnSaveToDictFile = Button(self.button_frame2, text="Write accepted pairs to file", width=20, command=self.write_accepted_pairs)
        self.btnSaveToDictFile.grid(row=0, column=4, sticky=W)
        self.btnSaveToDictFile.configure(state=DISABLED, padx=4, pady=1)       #Do not enable this button unless the user has selected a MatchResults file to save as


        #Create a message region to display notifications to the user
        self.message_region = Message(self.button_frame2, text="")              
        self.message_region.grid(row=0, column=5, sticky=E)
        kw = {"anchor":E, "width":800, "foreground":"dark green", "background":self.bgcolor, "borderwidth":1, "font":("Arial", 12, "bold"), "padx":8, "pady":3 }  
        self.message_region.configure(**kw)

    def display_advanced_buttons(self, container):
        '''Function display_advanced_buttons shows advanced features IF the user is authorized and explicitly chooses to open this panel.. '''
        self.advanced_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.advanced_frame, "MatchReview_Model.display_user_buttons()")
        else:
            stackslot = 0
        self.advanced_frame.grid(row=stackslot, column=0, sticky=EW)
        self.advanced_frame.configure(background=self.bgcolor, padx=4, pady=1)
		
        #self.btnDisplayOneFile = Button(self.advanced_frame, text="View the selected file", width=24, command=self.load_single_file)
        #self.btnDisplayOneFile.grid(row=0, column=0, sticky=W)
        #self.btnDisplayOneFile.configure(state=DISABLED, padx=4, pady=1)        #Do not enable this button unless the user has selected MatchReview files
		
        #self.btnDisplayAllFiles = Button(self.advanced_frame, text="View all files from this batch", width=24, command=self.load_combined_files)
        #self.btnDisplayAllFiles.grid(row=0, column=1, sticky=W)
        #self.btnDisplayAllFiles.configure(state=DISABLED, padx=4, pady=1)       #Do not enable this button unless the user has selected MatchReview files
        if self.allow_view_combined_files:
            self.btnWriteGoodPairs = Button(self.advanced_frame, text="Combine exact and accepted pairs for this batch", width=36, command=self.combine_good_pairs_all_passes)
            self.btnWriteGoodPairs.grid(row=0, column=0, sticky=W)
            self.btnWriteGoodPairs.configure(state=NORMAL, padx=4, pady=1)       #Do not enable this button unless the user has selected MatchReview files
		
        #self.lblSortBy = Label(self.advanced_frame, text="Sort on: ")
        #self.lblSortBy.grid(row=0, column=2, sticky=W) 
        #self.lblSortBy.configure(background=self.bgcolor, font=("Arial", 9, "normal"), borderwidth=0, width=7, anchor=E, padx=4, pady=1)
        #var = StringVar(self.advanced_frame)
        #var.set("Blocking Pass+Weight")
        #value_list = ["Blocking Pass+Weight", "Weight"]
        #self.optSortBy = OptionMenu(self.advanced_frame, var, *value_list, command=lambda x:self.change_sort_column(var) )
        #self.optSortBy.grid(row=0, column=3, sticky=W)
        #self.optSortBy.config(font=('calibri',(9)), bg='light grey', width=18, padx=4, pady=1)
        #self.optSortBy['menu'].config(background=self.bgcolor, font=("calibri",(11))) 

    def handle_jump_to_weight(self, parm=None):
        if not self.meta_values or not self.view_object:
            return
        print("\nJumpToWeight: %s" % (self.jump_to_weight.get()) )
        if not self.jump_to_weight.get():
            return
        try:
            desired_weight = float(self.jump_to_weight.get())
            self.logobject.logit("\nIn handle_jump_to_weight(), desired_weight is %s, sort_asc_or_desc is %s" % (desired_weight, self.sort_asc_or_desc), True, True, True )
            i = 0
            new_start_row = 0
            for item in self.meta_values:                       #meta_values is a list of lists storing the content from the two files that were matched (components: blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid, blkfldvals)
                if self.debug: self.logobject.logit("Next weight %s. Greater than %s? %s. Lower than %s? %s" % (item[1], desired_weight, float(str(item[1])) >= desired_weight, desired_weight, float(str(item[1])) <= desired_weight), True, True, True )
                if self.sort_asc_or_desc.lower().strip() == "asc":              #List is currently sorted ASCENDING
                    if float(str(item[1])) >= desired_weight:       #item[1] is the match weight for this row.  #This row has a weight greater than or equal to the weight that the user wants to "jump to" in the list. So set this row as the "Start Row" for viewing a block of 30 records on screen.
                        new_start_row = i
                        break
                elif self.sort_asc_or_desc.lower().strip() == "desc":            #List is currently sorted ASCENDING
                    if float(str(item[1])) <= desired_weight:       #item[1] is the match weight for this row.  #This row has a weight greater than or equal to the weight that the user wants to "jump to" in the list. So set this row as the "Start Row" for viewing a block of 30 records on screen.
                        if self.debug: self.logobject.logit("\nFound a weight lower than the target weight: %s. New start row will be %s" % (float(str(item[1])), i), True, True, True )
                        new_start_row = i
                        break
                i += 1 
            if new_start_row:
                self.view_object.start_row = new_start_row
                if self.debug: self.logobject.logit("New start item after jump-to-weight: %s" % (new_start_row), True, True, True )
            else: 
                self.view_object.start_row = i - 1
                if self.debug: self.logobject.logit("Jump-to-weight not found in list. Defaulting to: %s. Check self.view_object.start_row: %s" % (i, self.view_object.start_row), True, True, True )
            self.view_object.repopulate_grid()
            self.enable_disable_buttons()
        except:
            if self.debug:
                raise
    
    def catch_jump_to_weight_change(self, val1=None, val2=None, val3=None, val4=None):
        print("\n\nJUMP-TO-WEIGHT VAR CHANGED - parms are %s %s %s" % (val1, val2, val3) )
        self.handle_jump_to_weight()

    def catch_threshold_change(self, val1=None, val2=None, val3=None, val4=None):
        print("\n\nTHRESHOLD VAR CHANGED - parms are %s %s %s" % (val1, val2, val3) )
        self.spinhandler()

    def spinhandler(self, parm=None):    #, parm=None
        '''Read the spinner value and check/un-check each ACCEPTANCE checkbox based on whether the associated MATCH WEIGHT is greater than or less than the spinner's user-entered value.
        PARM is a multi-valued parameter submitted by the TKINTER spinner object thru its BIND event handlers. 
        But we're more interested in the value of the STRINGVAR that was designated to hold the value of the Spinner widget. That Stringvar's value is retrieved via self.accept_threshold.get()'''
        #self.logobject.logit("\n Spinner stringvar: %s, stringvar value: %s, parm: %s, widget: %s" % (self.accept_threshold, self.accept_threshold.get(), parm, parm.widget), True, True, True )
        if self.debug: self.logobject.logit("\n Spinner stringvar: %s, stringvar value: %s" % (self.accept_threshold, self.accept_threshold.get()), True, True, True )
        if not self.controls or not self.meta_values:
            return
        spinnerval = 0
        if self.accept_threshold.get():
            spinnerval = float(self.accept_threshold.get())
        i = 0
        for control in self.controls:
            #if self.debug: self.logobject.logit("Is %s greater than %s? %s" % (item[1], spinnerval,  (float(item[1]) >= spinnerval) ), True, True, True )
            typ = str(control.control_type).lower().strip()
            if typ == "checkbox":
                #First, un-check every checkbox regardless of its weight. This is because at the end of the list rows that are no longer populated do not hit the meta_values loop below, and might leave checked boxes on now-empty rows.
                control.value_object.set("")    #Uncheck the checkbox
                control.object.deselect()       #Uncheck the checkbox
                meta_rowid = control.meta_rowid
                for item in self.meta_values:
                    #if self.debug: self.logobject.logit("Seeking meta_rowid %s, found %s" % (meta_rowid, item[6] ), True, True, True )
                    if item[6] == meta_rowid:                   #Found the META_VALUES row corresponding to this control's META_ROWID
                        if float(item[1]) >= spinnerval:        #item[1] is "weight" - the match probability as estimated by BigMatch. The user wants to acccept every row with a weight greater than N.
                            #if self.debug: self.logobject.logit("SELECTing the checkbox with meta_rowid %s, row_index %s, gridrow %s, weight %s" % (control.meta_rowid, control.row_index, control.gridrow, item[1] ), True, True, True )
                            control.object.select()             #Check the checkbutton object
                            break
                        else:                                               #This item's WEIGHT (item[1]) falls below the user-entered cutoff (set by the spinner) for ACCEPTANCE.
                            #if self.debug: print("DE-Selecting the checkbox with meta_rowid %s" % (control.meta_rowid), True, True, True )
                            control.object.deselect()           #UN-Check the checkbutton object
                            break
            i += 1
        self.view_object.container.refresh_canvas()

    def write_accepted_pairs(self):
        '''After the user has "accepted" the rows (set a threshold weight above which records should be written
        or checked boxes for all rows where Record file and Memory file matching-field-values appear to confirm that the two records represent the same entity),
        write the matching-field-value strings to a text file'''
        if not self.matchreview_file_to_save_to or not self.controls or not self.meta_values:
            return
        try:
            with open(self.matchreview_file_to_save_to, "w") as f: 
                i = 0
                chkvalue = control_found = ""
                if self.write_descrips_in_result_file:
                    f.write("blk.pass    weight    record file id    record file match values     memory file id     memory file match values")
                for item in self.meta_values:                       #meta_values is a list of dicts storing the content from the two files that were matched (components: blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid)
                    control_found = ""
                    if self.debug: self.logobject.logit("meta_rowid %s has weight %s. Include? %s" % (item[6], item[1], float(str(item[1])) >= float(self.accept_threshold.get()) ), True, True, True )
                    if float(str(item[1])) >= float(self.accept_threshold.get()):       #item[1] is the match weight for this row
                        chkvalue = "1"                              #By default, this row should be written to the results, by virtue of its high match weight (above the user-designated threshold)
                    #Now check the currently-displayed rows to make sure this row is still "checked" - the user might have unchecked it.
                    meta_rowid = str(item[6])                       #item[6] is "meta_rowid"
                    if True:        #TO DO: assign each row in meta_values an index that will change as the list is re-sorted, so that we can tell at any time where this item is positioned in the list. This would allow us to know whether this row is currently displayed on screen, without looping thru the CONTROLS collection.
                        for control in self.controls:               #self.controls is a list of the screen controls
                            #if self.debug: self.logobject.logit("Seeking meta_rowid %s, found %s... type: %s" % (meta_rowid, control.meta_rowid, str(control.control_type).lower().strip() ), True, True, True )
                            if str(control.meta_rowid) == meta_rowid and str(control.control_type).lower().strip()=="checkbox":
                                chkvalue = control.value_object.get()
                                if self.debug: self.logobject.logit(" Checkbox with meta_rowid %s and weight %s has value: %s (user might have un-checked). Include? %s" % (control.meta_rowid, item[1], chkvalue, str(chkvalue) == "1" ), True, True, True )
                                control_found = True
                                break
                    if self.debug and not control_found: self.logobject.logit("(control was not found for this item -- only 30 rows are displayed in screen controls at a time)", True, True, True)
                    #Write this row to the ACCEPTED results file
                    if str(chkvalue) == "1": 
                        #if self.write_descrips_in_result_file:
                        #    f.write("bp:%s wt:%s rcfid:%s rcmtch:%s mmfid:%s mmtch:%s \n" % (item[0], item[1], item[4], item[2], item[5], item[3] ) )         #[blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid, accept_wgt, accept_usr]
                        #else:
                        #meta_temp is a LIST consisting of one row from the Review File  [blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid, accept_wgt, accept_usr]						
                        ##exactfile.write("%s %s %s %s %s: %s %s %s: %s \n" % (blkpass, weight.rjust(9), id_rec, recmatches.ljust(self.length_matching_text_column+10), id_mem, memmatches.ljust(self.length_matching_text_column+10)) )
                        if self.no_delimiters_in_result_file:
                            #exactfile.write("%s %s %s %s %s %s \n" % (blkpass, weight.rjust(9), id_rec, recmatches.ljust(self.length_matching_text_column+10), id_mem, memmatches.ljust(self.length_matching_text_column+10)) )
                            f.write("%s %s %s %s %s %s \n" % (item[0], item[1].rjust(9), item[4].ljust(self.max_length_rec_id), item[2].ljust(self.length_matching_text_column+10), item[5].ljust(self.max_length_mem_id), item[3].ljust(self.length_matching_text_column+10) ) )
                        else:
                            #exactfile.write("%s %s %s %s %s: %s %s %s: %s \n" % (blkpass, " | ", weight.rjust(9), " | ", id_rec, recmatches.ljust(self.length_matching_text_column+10), " | ", id_mem, memmatches.ljust(self.length_matching_text_column+10)) )
                            f.write("%s | %s | %s | %s | %s | %s \n" % (item[0], item[1].rjust(9), item[4].ljust(self.max_length_rec_id), item[2].ljust(self.length_matching_text_column+10), item[5].ljust(self.max_length_rec_id), item[3].ljust(self.length_matching_text_column+10) ) )
                    i += 1
                f.close()
        except:
            if self.debug: 
                raise
        #Display a temporary message notifying the user that their file was created.
        self.update_message_region("File has been saved")

    def change_sort_column(self, var):
        print("\n in change_sort_column(), var='%s'" % (str(var.get()) ) )
        self.sort_column = str(var.get()).lower().strip().replace(" ", "_")      #"weight"
        self.sort_list()

    def update_message_region(self, text='', clear_after_ms=5000, **kw):
        self.message_region.configure(text=text)
        self.message_region.after(clear_after_ms, self.clear_message_region)
		
    def clear_message_region(self):
        self.message_region.configure(text="")

    def update_filepath(self, file_name_with_path='', callback_string='', alias=''):
        '''IMPORTANT: ALL FilePath objects created by this class will expect Function "update_file_path" to exist! FilePath objects alert their masters when a filepath is selected in an open-file dialog.'''
        #self.logobject.logit("Master MatchReview_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string), True, True )
        print("Master MatchReview_Model object has gotten the alert: filename is %s and callback_string is '%s'" % (file_name_with_path, callback_string))
        if callback_string.lower().strip()[:4] == "load" or callback_string.lower().strip()[:4] == "open":
            self.matchreview_file_selected_by_user = file_name_with_path           #File selected to be reviewed -- BUT user can choose to combine this with others from the same batch
            self.matchreview_file_to_load_from = file_name_with_path               #For now, set this to the selected file, but later it might be changed to a COMBINED file that includes the selected file and its batch-mates.
            #For this module, it's important that the SAVE TO file should be named so that it is recognized as associated with the Match Result file.
            #if not self.matchreview_file_to_save_to:
            self.filepathobj_save_to.clear_file()             #If the user selects a new Match Result file, clear the Save To file, since in this module the Save To should follow a standard naming convention based on the Match Review file.
            self.matchreview_file_to_save_to = self.get_default_saveto_filename()  #By default, results are saved to a .dat file with the same name as the source file, but with suffix "_ACCEPTED"
            self.filepathobj_save_to.update_filepath_display(self.matchreview_file_to_save_to)	#Make sure the FilePath object also registers this Save_To file.
            self.exact_match_output_file = self.get_exact_match_filename()				
            self.logobject.logit("\n Matchreview_file_to_save_to is being set to: %s" % (self.matchreview_file_to_save_to), True, True, True )
            if self.matchreview_file_to_load_from:            #and self.matchreview_file_to_save_to:
                self.load_single_file()                       #Refresh the view when the user selects (loads) a new file.
            else:                                             #No file was specified (user might have cleared out a previously selected file name) 
                if self.view_object is not None:
                    self.view_object.clear_grid()             #Remove all existing values from the grid
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

    #*********************************************************************************************************
    def load_single_file(self):
        self.viewing_one_or_all_files = "one"
        self.display_views()

    def load_combined_files(self):
        '''See note at combine_result_files() '''
        self.viewing_one_or_all_files = "all"
        self.combine_result_files()
        #Now the COMBINED file displaces the USER-SELECTED file as self.matchreview_file_to_load_from
        self.matchreview_file_to_load_from = self.combined_matchreview_file
        #Load (or re-load) the grid so that the user can review this file row by row
        self.display_views()

    def combine_good_pairs_all_passes(self):
        '''Bigmatch result files are created for each blocking pass, and each must be evaluated separately because the logic of weight cutoffs differs significantly across passes.
        However, after the user has accepted matches by a pass-by-pass review process, the results can be combined for post-processing. 
        So if we find all files with the _EXACT.dat and _ACCEPTED.dat suffixes, we can combine them and write a new file with just unique IDs of the matching records.'''
        print("\n FILE SELECTED: %s aka %s" % (self.matchreview_file_selected_by_user, str(self.matchreview_file_selected_by_user)[-12:][:6].lower().strip() ) )
        head, tail = os.path.split(self.matchreview_file_selected_by_user)
        match_result_filename_trunc = self.get_result_filename_trunc(self.matchreview_file_selected_by_user)
        self.combined_exact_accepted_file = os.path.join(head, match_result_filename_trunc + "pairs_exact_accpt.dat").lower().strip()
        if str(self.matchreview_file_selected_by_user)[-12:][:6].lower().strip() == "pairs_":
            #Find all files in the same folder as that selected by the user, that also have the same filename (except for final suffix) as the user-selected file.  (Example: Myfile_Pairs_00.bat, Myfile_Pairs_01.bat, etc.)
            self.build_list_of_all_pairs_files_for_batch("good")
            if len(self.match_files_for_batch) == 0:
                self.error_message = "Combining BigMatch result files failed."
            else:
                try:
                    with open(self.combined_exact_accepted_file, 'w') as outfile:
                        for filenm in self.match_files_for_batch:
                            if self.debug: self.logobject.logit("Next file in batch of good pairs: %s" % (filenm), True, True, True)
                            suffix_exact = filenm[-12:-11]
                            suffix_accpt = filenm[-15:-14]
                            try:
                                if "012345678".find(suffix_exact[:1]) != -1:
                                    suffix = str(int(suffix_exact))
                                elif "012345678".find(suffix_accpt[:1]) != -1:
                                    suffix = str(int(suffix_accpt))
                            except ValueError:
                                pass
                            nextfile = os.path.join(head, filenm)
                            if nextfile.lower().strip() != self.combined_exact_accepted_file:      #DO NOT allow the newly created file to be included in this loop, or it will set up an endless loop!
                                key_text = None
                                weight_pos = 1
                                delimiter = "|"
                                with open(nextfile) as infile:
                                    for row in infile:                                      #blkpass, weight, recmatches, memmatches, id_rec, id_mem, meta_rowid, accept_wgt, accept_usr
                                        segments = str(row).split(delimiter)
                                        #Note! these positions are not the same as position in the Meta_Values list. These are read from the ACCEPTED or EXACT file, to which only a subset of meta_values was written.
                                        blkpass = str(segments[0]).strip()
                                        weight = str(segments[1]).strip()
                                        rec_id = str(segments[2]).strip()
                                        recmatches = str(segments[3]).strip()
                                        mem_id = str(segments[4]).strip()
                                        memmatches = str(segments[5]).strip()
                                        if self.debug: 
                                            self.logobject.logit("Row has len %s. Segments has len %s.  %s Segments: %s" % (len(row), len(segments), row, segments ), True, True, True)
                                            self.logobject.logit("Writing: %s %s %s %s \n" % (blkpass, weight.rjust(9), rec_id.ljust(self.max_length_rec_id), mem_id.ljust(self.max_length_mem_id) ), True, True, True)
                                        outfile.write("%s %s %s %s \n" % (blkpass, weight.rjust(9), rec_id.ljust(self.max_length_rec_id), mem_id.ljust(self.max_length_mem_id) ) )
                except IOError as e:
                    print("I/O error({0}): {1}".format(e.errno, e.strerror))
                    self.error_message = str(e.strerror)
        if self.error_message is not None:
            self.handle_error()
            return

    def combine_result_files(self):
        '''Not currently active.  This function combines BigMatch result files so that the user can review all at once. It was deactivated at least temporarily due to concern that ideal cutoff thresholds differ from pass to pass, so no general rule about the cutoff can be arrived at.'''
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

    def build_list_of_all_pairs_files_for_batch(self, rawpairs_or_goodpairs="good"):
        '''See note at combine_result_files() '''
        rawpairs_or_goodpairs = str(rawpairs_or_goodpairs).lower().strip()
        self.match_files_for_batch = []
        head, tail = os.path.split(self.matchreview_file_selected_by_user)
        dirpath = head
        match_result_filename_trunc = self.get_result_filename_trunc(self.matchreview_file_selected_by_user)
        print("\nIn build_list_of_all_pairs_files_for_batch(), rawpairs_or_goodpairs: %s, match_result_filename_trunc=%s" % (rawpairs_or_goodpairs, match_result_filename_trunc))
        for (dirpath, dirnames, filenames) in walk(head):
            for filenm in filenames:
                filenm = str(filenm).lower().strip()
                print("\nNext file in dir: %s .... %s" % (filenm, filenm[:-12]) )
                #if rawpairs_or_goodpairs=="raw":
                #    if filenm[:-12] == match_result_filename_trunc and filenm[-4:] == ".dat":    #This is a batch-mate of the selected file
                #        if filenm[-6:] != "99.dat":                       #Don't include this COMBINED file, as it will be overwritten anyway
                #            self.match_files_for_batch.append(filenm)
                #elif rawpairs_or_goodpairs=="good":
                self.logobject.logit("\nFilename trunk: %s, trunk(14): %s, suffix(13): %s, suffix(10): %s" % (match_result_filename_trunc, filenm[:-14], filenm[-13:], filenm[-10:]), True, True, True)
                if filenm[:-21] == match_result_filename_trunc and filenm[-13:] == "_accepted.dat": 
                    self.match_files_for_batch.append(filenm)
                elif filenm[:-18] == match_result_filename_trunc and filenm[-10:] == "_exact.dat":
                    self.match_files_for_batch.append(filenm)
            break
        print("\n In build_list_of_all_pairs_files_for_batch(), Batch Files Found:")
        for f in self.match_files_for_batch:
            print(f)

    def get_result_filename_trunc(self, filename=None):
        '''See note at combine_result_files() '''
        if filename is None:
            filename = self.matchreview_file_selected_by_user
        head, tail = os.path.split(filename)
        self.match_result_filename_trunc = tail.lower().strip()[:-12]
        return self.match_result_filename_trunc
    #*********************************************************************************************
        
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
            #if self.allow_view_combined_files:
            #    self.btnDisplayOneFile.configure(state=DISABLED)       #Disable this button if the list is already populated with the user-selected file only
            #    self.btnDisplayAllFiles.configure(state=NORMAL)        #Enable this button if the list is currently showing the user-selected file only.
            pass
				
        elif str(self.viewing_one_or_all_files).lower() == "all":
            #if self.allow_view_combined_files:
            #    self.btnDisplayOneFile.configure(state=NORMAL)         #Enable this button if the list is currently showing the user-selected file only
            #    self.btnDisplayAllFiles.configure(state=DISABLED)	   #Disable this button if the list is already populated with the COMBINED files
            pass
        else:
            if self.allow_view_combined_files:
                #self.btnDisplayOneFile.configure(state=NORMAL)         #Allow the user to choose either single or combined
                #self.btnDisplayAllFiles.configure(state=NORMAL)        #Allow the user to choose either single or combined
                pass

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
            self.logobject.logit("\n About to SCROLL THE PAGE", True, True, True)
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
            self.logobject.logit("\n About to SCROLL THE PAGE BACKWARDS", True, True, True)
            self.view_object.start_row = self.view_object.start_row - self.view_object.rows_to_display
            if self.view_object.start_row < 0:
                self.view_object.start_row = 0
            self.view_object.repopulate_grid()
        #Refresh the state of sort buttons:
        self.enable_disable_buttons()		
		
    def debug_display_arrays(self):
        i = 0
        self.logobject.logit("self.meta_values:", True, True, True)
        for val in self.meta_values:
            self.logobject.logit(str(i) + "  " + str(val), True, True, True)
            i += 1

        i = 0
        self.logobject.logit("self.controls:", True, True, True)
        for control in self.controls:
            self.logobject.logit("%s) Row: %s, Col: %s, Name: %s, Type: %s" % ( i, control.row_index, control.col, control.ref_name, control.control_type ), True, True, True)
            i += 1

    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found

		
		
		
    #*********************************************************************************************
    def read_write_bigmatch_result_file(self, infile=None, outfile=None, write_which=None, write_what=None, read_into_meta_values_list=None, file_format="bigmatch", delimiter="|", columns_to_write=None):
        '''Parse the standard BigMatch result file, extracting key information such as the match weight, ID (sequence) fields, matched values, etc.
        All of this information is stored in self.meta_values. But NOTE: the simple match values stored in self.meta_values proved to be insufficient for a robust user assessment.
        So match values are stored separately in self.frame_and_its_labels, so that they can be displayed and re-displayed in color-coded segments. See below function populate_resultrow_frame()'''
        if infile is None:
            infile = self.matchreview_file_to_load_from
        if not infile:
            self.handle_error("No result file was specified")
            return
        if not outfile:
            outfile = self.exact_match_output_file
        if not outfile:
            self.handle_error("No target file was specified")
            return
        write_which = str(write_which).lower().strip()
        #Traverse the specified Match Results file, and optionally write parts to an outfile AND/OR extract parts of each row into a list.
        print("\n TOP OF FUNCTION read_write_bigmatch_result_file() -- file: %s" % (str(infile)) )
        count = blkpass_rowcount = meta_rowid = weight_pos = 0
        self.max_length_matching_text = 20   #Start out assuming a very narrow set of matching fields -- then use the maximum width to set a "justify" line so that the results appear less ragged.
        blkpass = holdpass = ""
        with open(infile, 'r') as infl:
            with open(outfile, 'w') as outf:
                for row in infl:
                    if len(row) == 0:
                        continue                         #Empty row
                    if str(row)[:4]=="****":             #Asterisk lines are placed in the file to denote the start of a new section of results (different blocking pass)
                        continue
                    #**************************************************************
                    meta_row = self.parse_resultfile_row(row, meta_rowid)
                    #**************************************************************
                    blkpass = meta_row[0]
                    if blkpass != holdpass:                    #Reset this counter when we encounter a new Blocking Pass section
                        blkpass_rowcount = 0
                        holdpass = blkpass
                    weight = meta_row[1]
                    recmatches = meta_row[2]
                    memmatches = meta_row[3]
                    id_rec = meta_row[4]
                    id_mem = meta_row[5]
                    #********************************************************************************************
                    #Processing depends on whether this row represents an EXACT MATCH or a probabilistic weight
                    write_this_row = store_row_to_meta_values = False
                    if recmatches == memmatches:       #EXACT matches (normally written to a separate file)
                        if write_which == "exact" or write_which == "all":
                            print("Exact match: %s -|- %s" % (recmatches, memmatches) ) 
                            write_this_row = True
                        #If specified, store this EXACT MATCH row into the META_VALUES list (not the default)
                        if read_into_meta_values_list=="exact" or read_into_meta_values_list=="all":
                            store_row_to_meta_values = True
                    else:                              #NOT EXACT MATCH - a probabilistic weight has been assigned by BigMatch, so the user will review all rows and decide where the best weight threshold is for ACCEPTANCE
                        if write_which == "non_exact":
                            write_this_row = True
                        if read_into_meta_values_list=="non_exact" or read_into_meta_values_list=="all":
                            store_row_to_meta_values = True
                    if write_this_row:
                        if self.no_delimiters_in_result_file:
                            outf.write("%s %s %s %s %s %s \n" % (blkpass, weight.rjust(9), id_rec, recmatches.ljust(self.max_length_matching_text+10), id_mem, memmatches.ljust(self.max_length_matching_text+10)) )
                        else:
                            #outf.write("%s %s %s %s %s: %s %s %s: %s \n" % (blkpass, " | ", weight.rjust(9), " | ", id_rec, recmatches.ljust(self.max_length_matching_text+10), " | ", id_mem, memmatches.ljust(self.max_length_matching_text+10)) )
                            outf.write("%s | %s | %s | %s | %s | %s \n" % (blkpass, weight.rjust(9), id_rec, recmatches.ljust(self.max_length_matching_text+10), id_mem, memmatches.ljust(self.max_length_matching_text+10) ) )
                    if read_into_meta_values_list:
                        if self.debug: print("Adding row to meta_values: %s, %s, %s, %s" % (blkpass, weight, recmatches, memmatches) )
                        #**************************************************************************************************************
                        #Populate the META_VALUES list (list of lists) that will be used to populate the Entry Grid
                        self.meta_values.append(meta_row)		          #meta_values is a LIST of LISTS, consisting of one "outer" list representing all the rows from the data dictionary, and an "inner" list consisting of the cell values for a single row.\
                        #**************************************************************************************************************
                    #if self.debug:
                        #print("\n -- ROW %s" % (count) )
                        #print("rec: %s" % (recmatches) )
                        #print("mem: %s" % (memmatches) )
                    meta_rowid += 1                   #Count this as a row that will be added to self.meta_values
                    count += 1
                #Close files:
                outf.close()
            infl.close()
        self.matchfile_rows = count
        self.logobject.logit("\n At end of read_write_bigmatch_result_file(), meta_values has %s rows, and the matchfile has %s rows." % (len(self.meta_values) , self.matchfile_rows), True, True, True )  
        self.sort_list()


#******************************************************************************
# NEW CLASS SECTION
#******************************************************************************
class MatchReview_View(Frame):
    debug = False
    container = None
    model = None
    logobject = None
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
    vert_position_of_1st_gridrow = None   #The Tkinter grid row of the first Match Values Comparison row (which is needed every time we re-render the comparison values)
    pass_index = 0
    meta_rowid = None       #Meta_rowid is a unique identifier (autonum) for each row of self.meta_values, the main array.  It is stored in column 4 (fifth column) in the list.
    kw_fresult = {}         #Configuration for the frames that display comparison values
    resultrow_frames_initialized = None
    jump_to_weight = None

    def __init__(self, container, model=None, pass_index=None, show_view=None):
        Frame.__init__(self, container)
        if container:
            self.container = container
        if model is None:
            model = BlockingPass_Model()				#Normally this VIEW object will be called by an already-instantiated MODEL object.  But this line is there to catch any direct instantiations of the VIEW.		
        self.model = model                              #Instance of the MatchReview_Model class (see aboove) 
        self.debug = self.model.debug
        self.logobject = self.model.logobject
        self.pass_index = pass_index                    #Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
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
        self.model.logobject.logit("\n In matchreview_view.initUI: About to display main MatchReview frame title", True, True, True)
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
        #***********************************************************************
        #Display the first page of results:  
        self.display_review_page(0)
        #***********************************************************************
        #for control in self.model.controls:      #DEBUG CHECK THE CONTROLS LIST
        #    if self.debug: self.model.logobject.logit("Control-- Gridrow: %s Row: %s OR %s, Col: %s, meta_rowid: %s, control_type %s, ref_name=%s, Current value: %s, " % (control.gridrow, control.row_index, control.control_index, control.col, control.meta_rowid, control.control_type, control.ref_name, control.value_object.get() ), True, True, True )
		
    def display_review_page(self, start_row=None):
        #*************************************
        #Display the match values:
        #*************************************
        if start_row is not None:
            self.start_row = start_row
        if self.start_row is None:
            self.start_row = 0
        self.model.logobject.logit("\n In matchreview_view.display_review_page(), start_row=%s" % (self.start_row), True, True )
        self.row_index = 0				
        curvalue = 0 
        data_column_name = ""
        chk_kw = {"width":6, "borderwidth":1, "font_size":11, "text":data_column_name}
        kw_txtbox = {"width":20, "background":self.bgcolor, "foreground":"black", "borderwidth":1, "font":("Arial", 10, "normal")}  #, "data_column_name":data_column_name, "text":data_column_name}
        vert_position = self.get_widgetstack_counter()
        self.vert_position_of_1st_gridrow = vert_position
        self.rowtype = "matchreview"         #Each row in the CONTROLS list must be stamped with its row type (e.g., "blocking_fields", "matching_fields", etc.
        ix = 0                               #index of the current row
        countrow = 0                         #count the number of rows displayed
        holdweight = holdpass = ""
        bgcolor = "light grey"		
        weight_color = "dark slate blue"
        for item in self.model.meta_values:  #The entire contents of the BigMatch result file is loaded into self.model.meta_values. Display only 30 at a time. 
            if ix >= self.start_row and countrow < self.rows_to_display:
                self.meta_rowid = item[6]    #The Row index number of the current row in meta_values
                if self.debug: self.model.logobject.logit("Row %s is between %s and %s so it will be displayed. Meta_rowid=%s" % (ix, self.start_row, int(self.start_row) + int(self.rows_to_display), self.meta_rowid ), True, True )
                vert_position = self.get_widgetstack_counter()
                label_text = ""
                #(1) Checkbox to indicate that this field should be accepted as a match:
                gridcolumn = 0
                curvalue = 0
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
                self.recfile_values_for_current_row = str(item[2])        #This item from meta_values is a string of Matching Field values for the Record file
                self.memfile_values_for_current_row = str(item[3])        #This item from meta_values is a string of Matching Field values for the Memory file
                #kw_fresult = {"background":self.bgcolor, "borderwidth":1, "height":1, "padx":4, "pady":2}              #, "data_column_name":data_column_name, "text":data_column_name, "font":("Arial", 10, "normal") }
                self.kw_fresult = {"background":"yellow", "height":1, "borderwidth":1, "padx":4, "pady":2}              # " "data_column_name":data_column_name, "text":data_column_name, "font":("Arial", 10, "normal") }
                kw_fresult = self.kw_fresult
                #******************************************************************************
                #Display the Record file and Memory file matching field values, side by side - Record values in one frame object, Memory values in a second frame object.
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "rec", vert_position, gridcolumn, **kw_fresult)             #RECORD FILE matching fields are contained in item[2]
                kw_fresult["background"] = "white"
                gridcolumn +=1
                frame = self.create_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "mem", vert_position, gridcolumn, **kw_fresult)             #MEMORY FILE matching fields are contained in item[3]
                countrow += 1
                ix += 1
                self.row_index += 1 
                
        #Display a temporary message notifying the user that their file was created.
        self.model.update_message_region("NOTE: exact matches are not displayed here, but have been saved to a file ending with _EXACT.dat")
        self.grid_initialized = True
        self.container.refresh_canvas()
        if self.debug: self.model.debug_display_arrays()   #View the Meta_Values and Controls arrays

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
        '''The grid of checkboxes and textboxes is independent of the data values stored in meta_values. 
        Each control is set up with a Tkinter StringVar to hold the current value of that control (text in a textbox, etc.) 
        Each StringVar variable can be updated whenever the grid is refreshed.'''
        if self.model.controls:
            for control in self.model.controls:
                col = control.col
                row = control.row_index
                control_type = str(control.control_type).lower().strip()		
                #if self.debug: print("CLEARING: Col: %s Row: %s Type: %s" % ( str(control.col), str(control.row_index), control_type ) )
                control.meta_rowid = None         #Important because if associated with a row in Meta_Values, this control will take on the ACCEPTED status of that row in Meta_Values -- if that Meta row has a weight above the current user-specified threshold, then the checkbox will remain checked even if all the controls' displays for this row have been set to blanks.
                control.blocking_pass = ""				
                value = ""
                if control_type == "checkbox":
                    control.object.deselect()     #Un-check the checkbutton object
                else:
                    value = control.value_object.get()
                    control.value_object.set('')
                #print("CLEARED: Col: %s Row: %s Type: %s, Current control value: %s" % ( str(control.col), str(control.row_index), str(control.control_type), value ) ) 
                #control.object.grid(column=col, row=row)       #We don't need to re-create or re-position the control
        #The actual comparison values to be reviewed are NOT included in self.model.controls, because they are complex frame objects different from simple text boxes.
        for frame_and_its_labels in self.model.result_comparison_frames_in_grid:        #frame_and_its_labels = [frame, mem_or_rec, gridrow, gridcolumn, labels_and_stringvars_for_frame]
            #if self.debug: self.model.logobject.logit("In clear_grid, gridrow=%s, gridcolumn=%s, mem_or_rec=%s" % (frame_and_its_labels[2], frame_and_its_labels[3], frame_and_its_labels[1]), True, True, True )
            for lblpair in frame_and_its_labels[4]:             #frame_and_its_labels[4] holds 10 Tkinter label objects plus the 10 StringVars that hold the labels' values
                stringvar = lblpair[1]                          #lblpair[1] is the StringVar that holds the Label object's value
                if lblpair[1].get():
                    if self.debug: self.model.logobject.logit("In clear_grid, current label=%s, will be set to blank" % (lblpair[1].get()), True, True, True )
                    stringvar.set("")
        self.container.refresh_canvas()

    def update_control_in_grid(self, row, col, newvalue, meta_rowid, fontcolor=None, controltype=None):
        #Find the correct element in self.controls where COL attribute = col, and the ROW_INDEX attribute = row.
        #if self.debug: self.logobject.logit("In update_control_in_grid(), Seeking row=%s and col=%s ... new value is %s" % (str(row), str(col), newvalue ), True, True, True )
        found = False
        for control in self.model.controls:
            #When we find the correct Entry object in the self.controls list, update its value to reflect the newly-submitted meta_values.
            #if self.debug: self.model.logobject.logit("NEXT UP: ROW: %s, COL: %s, Current value: %s, New value: %s" % (control.row_index, control.col, control.value_object.get(), newvalue), True, True, True )
            if str(control.col) == str(col) and str(control.row_index) == str(row):
                if self.debug: self.model.logobject.logit("Control FOUND: Col: %s Row: %s Current value: %s, New value: %s" % (control.col, control.row_index, control.value_object.get(), newvalue), True, True, True )
                control.meta_rowid = meta_rowid
                control.value_object.set(newvalue)
                #control.object.grid(column=col, row=row)          #We don't need to re-create or re-position the control
                control.object.config(foreground=fontcolor)       
                if self.debug: self.model.logobject.logit("Control AFTER update: Col: %s Row: %s control value: %s" % (str(control.col), str(control.row_index), str(control.value_object.get())), True, True, True)
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
        self.model.add_control_to_list(entry, var, blocking_pass=self.pass_index, ref_name=textbox_name, row_index=self.row_index, gridrow=gridrow, col=gridcolumn, control_type="textbox", meta_rowid=self.meta_rowid)

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
        self.model.add_control_to_list(chk, var, blocking_pass=self.pass_index, ref_name=chkbox_name, row_index=self.row_index, gridrow=gridrow, col=gridcolumn, control_type="checkbox", meta_rowid=self.meta_rowid)

    def create_resultrow_frame(self, matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw):
        '''Create and display a Tkinter frame object, populated with labels representing matching-field values for the user's clerical review process.
        The frame objects are created ONCE, and then later the StringVar values are updated as the user scrolls or sorts the display rows. (See function populate_resultrow_frame()).
        Pass both the RECORD and MEMORY matching fields values to this function, so that we can compare each segment of those values and highlight differences
        Note that this function creates and displays a single frame object, containing a string of matching-field values for EITHER the Record File or the Memory File. 
        This function will be called twice (Record File, then Memory File) for each row that is being displayed in the grid -- so once for every row in the specified number of rows per page.
        List labels_and_stringvars_for_frame[] stores label OBJECTS and the StringVar OBJECTS that store their values. This is so that the grid can be refreshed as often as needed. 
        We can't keep creating an infinite number of label objects, so we create them one time and update their StringVar values as often as needed.'''
        if self. debug: self.model.logobject.logit("In create_resultrow_frame(), mem_or_rec: %s, matchvals_rec: %s, matchvals_mem: %s, gridcolumn: %s" % (mem_or_rec, matchvals_rec, matchvals_mem, gridcolumn), True, True, True )
        mem_or_rec = str(mem_or_rec).lower().strip()
        frame = Frame(self)
        frame.grid(row=gridrow, column=gridcolumn, sticky=EW)
        if not self.model.check_key_exists("background", **kw):
            kw["background"] = self.bgcolor
        #if not self.model.check_key_exists("width", **kw):
        #    kw["width"] = 80
        frame.configure(**kw)
        frame.configure(width=80)
        labels_and_stringvars_for_frame = []        #List of labels that will be displayed within this frame, along with the StringVar variables to hold the values that are displayed in the labels.
        var0 = StringVar(self)
        var0.set("")
        lbl0 = Label(frame, textvariable=var0)
        lblpair_0 = [lbl0, var0]
        labels_and_stringvars_for_frame.append(lblpair_0)
        var1 = StringVar(self)
        var1.set("")
        lbl1 = Label(frame, textvariable=var1)
        lblpair_1 = [lbl1, var1]
        labels_and_stringvars_for_frame.append(lblpair_1)
        var2 = StringVar(self)
        var2.set("")
        lbl2 = Label(frame, textvariable=var2)
        lblpair_2 = [lbl2, var2]
        labels_and_stringvars_for_frame.append(lblpair_2)
        var3 = StringVar(self)
        var3.set("")
        lbl3 = Label(frame, textvariable=var3)
        lblpair_3 = [lbl3, var3]
        labels_and_stringvars_for_frame.append(lblpair_3)
        var4 = StringVar(self)
        var4.set("")
        lbl4 = Label(frame, textvariable=var4)
        lblpair_4 = [lbl4, var4]
        labels_and_stringvars_for_frame.append(lblpair_4)
        var5 = StringVar(self)
        var5.set("")
        lbl5 = Label(frame, textvariable=var5)
        lblpair_5 = [lbl5, var5]
        labels_and_stringvars_for_frame.append(lblpair_5)
        var6 = StringVar(self)
        var6.set("")
        lbl6 = Label(frame, textvariable=var6)
        lblpair_6 = [lbl6, var6]
        labels_and_stringvars_for_frame.append(lblpair_6)
        var7 = StringVar(self)
        var7.set("")
        lbl7 = Label(frame, textvariable=var7)
        lblpair_7 = [lbl7, var7]
        labels_and_stringvars_for_frame.append(lblpair_7)
        var8 = StringVar(self)
        var8.set("")
        lbl8 = Label(frame, textvariable=var8)
        lblpair_8 = [lbl8, var8]
        labels_and_stringvars_for_frame.append(lblpair_8)
        var9 = StringVar(self)
        var9.set("")
        lbl9 = Label(frame, textvariable=var9)
        lblpair_9 = [lbl9, var9]
        labels_and_stringvars_for_frame.append(lblpair_9)
        #Add a row to the result_comparison_frames_in_grid list. Each row consists of a single frame object and the StringVars and Label objects associated with that frame object.
        frame_and_its_labels = [frame, mem_or_rec, gridrow, gridcolumn, labels_and_stringvars_for_frame]    #lblpair_0, lblpair_1, lblpair_2, lblpair_3, lblpair_4, lblpair_5, lblpair_6, lblpair_7, lblpair_8, lblpair_9]
        framerow_index = len(self.model.result_comparison_frames_in_grid)                            #The frame will be added to this list soon
        #Configure each Label that was just added to the list.
        color = "black"
        #Item[0] in this list-row is the frame object itself, item[1] is mem_or_rec, item[2] is the grid row index, item[3] is the grid column index. 
        #For each label, call GRID() and CONFIG() to format the Label object within this Frame object		
        lbl_count = 0
        for lbl_pair in frame_and_its_labels[4]:    #Item[4] in this list is a list of 10 2-member lists, each consisting of a Tkinter Label0 and its designated StringVar textvariable.
            lbl = lbl_pair[0]
            #self.model.logobject.logit("Type of ResltComprFrm row %s item %s: %s. Type of item[0]: %s. Type of item[1]: %s. Stringvar value: '%s'" % (framerow_index, lbl_count, type(lbl_pair), type(lbl_pair[0]), type(lbl_pair[1]), str(lbl_pair[1].get())  ), True, True  )
            lbl.grid(row=0, column=lbl_count, sticky=W)
            lbl.config(**kw)    #**kw is meant to configure the FRAME, not the individual labels within that frame. Make sure that the frmae attributes like "width" are removed before we apply them to the Labels.
            lbl.config(anchor=W, font=("Arial", 10, "normal"))
            lbl.config(foreground=color)                        #Font color will be set according to whether the current segments match (rec matches mem)
            lbl_count += 1
        
        #Append this frame object and its labels into a List that can be accessed later, so that the values can be refreshed when the user scrolls or sorts.
        self.model.result_comparison_frames_in_grid.append(frame_and_its_labels)     #A list of grid frames, each accompanied by its collection of text segments embedded in TKinter Label objects.
		#Display this frame object in the grid:
        self.populate_resultrow_frame(matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw)          #Display the comparison values
        self.resultrow_frames_initialized = True
        self.container.refresh_canvas()

    def populate_resultrow_frame(self, matchvals_rec, matchvals_mem, mem_or_rec, gridrow, gridcolumn, **kw):
        '''Display the comparison text (matching-field values) in the Record File or Memory File frame. First, split the values-string into segments separated by blanks. 
        Each segment in the Record File matching-values-string will be compared to each segment in the Memory File matching-values-string.
        Differences are highlighted by color.
        First, we need to locate the correct set of Label controls, which are stored in a list. The list is searchable by GridRow and GridColumn, which is how we locate the correct Label Widget set.
        Of course, we could avoid this search process when the frame is initially created, because the creating object already has a reference to the array that needs to be displayed (StringVars need to be updated).
        But for simplicity, this function needs to be generic enough to handle cases where the information is not known, aside from row and column indices in the master list of frames with their Label widgets.'''
        frmx = 0
        for frame_and_its_labels in self.model.result_comparison_frames_in_grid:
            #if self.debug: self.logobject.logit("In populate_resultrow_frame(), seeking gridrow %s, found %s, seeking gridcolumn %s, found %s" % (gridrow, frame_and_its_labels[2], gridcolumn, frame_and_its_labels[3] ), True, True, True )
            if frame_and_its_labels[2] == gridrow and frame_and_its_labels[3] == gridcolumn:      #The row and column indices match - so we have found the correct Frame and its Labels.
                if self.debug: self.model.logobject.logit("In populate_resultrow_frame(), framerow (%s) mem_or_rec: '%s', matchvals_rec: '%s', matchvals_mem: '%s', gridcolumn: %s" % (frmx, mem_or_rec, matchvals_rec, matchvals_mem, gridcolumn), True, True, True )
                matchsegs_rec = matchvals_rec.split(" ")
                matchsegs_mem = matchvals_mem.split(" ")
                max_num_segments = len(matchsegs_rec)
                min_num_segments = len(matchsegs_rec)
                if len(matchsegs_mem) < len(matchsegs_rec):         #MAKE SURE we set num_segments to the SMALLER number of segments between REC and MEM.  Otherwise an error occurs because the array index exceeds the number of items in the array.
                    min_num_segments = len(matchsegs_mem)
                elif len(matchsegs_mem) > len(matchsegs_rec):
                    max_num_segments = len(matchsegs_mem)
                #Item[0] is the Frame widget, item[1] is "mem_or_rec", item[2] is gridrow, item[3] is the gridcolumn, item[4] is the list of StringVars and associated Label widgets within the Frame.
                #Item[4] is "labels_and_stringvars_for_frame", a list of 10 lists, each having 2 elements: [0] is a Tkinter Label object and [1] is its associated StringVar to hold the label's text value.
                lblx = 0
                for lbl_pair in frame_and_its_labels[4]:         #should be 10 label pairs per frame (each label pair is a Label object and its Stringvar object)
                    #Debug - view all of this frame's child labels (which are stored in the list that appears in position 4 [5th item] in each row of result_comparison_frames_in_grid.
                    #self.model.logobject.logit("Framerow %s, segment %s). Type of frame-labels: %s. Type of frame-labels[0]: %s. Type of frame-labels[1]: %s. Type of frame-labels[2]: %s. Type of frame-labels[3]: %s. Type of frame-labels[4]: %s. Type of frame-labels[4][0]: %s. Type of frame-labels[4][1]: %s." % (frmx, lblx, type(frame_and_its_labels), type(frame_and_its_labels[0]), type(frame_and_its_labels[1]), type(frame_and_its_labels[2]), type(frame_and_its_labels[3]), type(frame_and_its_labels[4]), type(frame_and_its_labels[4][0]), type(frame_and_its_labels[4][1])  ), True, True )
                    #IMPORTANT! Set the StringVar value to nothing -- that is, erase existing values that were previously displayed in the label widget.
                    frame_and_its_labels[4][lblx][1].set("")     #StringVar is frame_and_its_labels[4][x][1] -- but it is technically a list, and only segment[1] is an object that can execute the Get()
                    lblx +=1
                #Traverse the Labels and set their StringVar values to the segments found in the Record File or Memory File matching-field-values.
                color = "black"
                recseg = memseg = text = ""
                ix = 0
                #max_num_segments is the largest number of segments found for this row (the larger of the two: record or memory file matchvalues)
                for ix in range(0, max_num_segments):               #match_segs_rec is a list of text segments in the RECORD file matchvalues
                    text = memseg = recseg = ""
                    if len(matchsegs_rec) > ix:
                        recseg = str(matchsegs_rec[ix])
                    if len(matchsegs_mem) > ix:                     #match_segs_mem is a list of text segments in the MEMORY file matchvalues
                        memseg = str(matchsegs_mem[ix])
                    if len(matchsegs_rec) > ix and len(matchsegs_mem) > ix:       #Both RECORD and MEMORY matching field values have at least this many segments -- compare them to see whether they match.
                        if recseg.lower().strip() == memseg.lower().strip():     
                            color = "black"                                       #This segment is identical between the RECORD FILE and the MEMORY FILE
                        else:                                                    
                            color = "red"                                         #This segment is NOT identical between the RECORD FILE and the MEMORY FILE
                    else:                                                        
                        color = "gray"                                            #RECORD and MEMORY matching field values might have a different number of segments
                    if mem_or_rec == "mem":
                        text = memseg
                    elif mem_or_rec == "rec":
                        text = recseg
                    #if text: 
                    #    self.model.logobject.logit("Seg text for framerow %s, segment %s: %s" % (frmx, ix, text), True, True )
                    #***************************************************************************************************************
                    #SET THIS SEGMENT'S FONT TO THE INDICATED COLOR:
                    frame_and_its_labels[4][ix][0].config(foreground=color)
                    #SET THE LABEL'S VALUE TO THIS SEGMENT FROM THE MATCHING-FIELD-VALUES-STRING WE ARE DISPLAYING:
                    frame_and_its_labels[4][ix][1].set(text)
                    #***************************************************************************************************************
                    ix +=1
                break          #We found the specified row, so exit the loop
            frmx +=1
			
    def repopulate_grid(self):
        '''repopulate_grid() is called when the frame-grid is re-drawn with new values.  This happens all the time, because the user displays a small number of rows at a time.
		It would be convenient to simply re-call the function that created the frames in the first place, but that would create hundreds or thousands of frame objects as the user scrolls and sorts iteratively.'''
        #print("\n ARRAYS before clear:")
        #self.model.debug_display_arrays()
        self.clear_grid()    #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_arrays() deletes these class properties.
        #print("\n ARRAYS after clear:")
        #self.model.debug_display_arrays()
		
        #NOTE: each item in self.meta_values is itself a list of cell values - so each item represents a row of cells.
        self.model.logobject.logit("\n *********************************************************************", True, True)
        self.model.logobject.logit("RE-POPULATING self.model.controls LIST FROM self.model.meta_values", True, True)
        self.model.logobject.logit("StartRow: %s EndRow: %s" % (self.start_row, int(self.start_row) + int(self.rows_to_display) ), True, True )
        ix = 0                              #index of the current row
        countrow = 0                        #count the number of rows displayed
        holdweight = ""
        weight_color = "dark slate blue"
        for item in self.model.meta_values:
            #self.model.logobject.logit("In Repopulate, row %s" % (ix), True, True )
            if ix >= self.start_row and countrow < self.rows_to_display:          #This row of meta_values falls within the start and end row for the chunk we are displaying.
                #Memfile_values and Recfile_values are BOTH passed to the display function, because we need to compare them against each other to determine the colors to be used in displaying the values.
                self.recfile_values_for_current_row = ""                           
                self.memfile_values_for_current_row = ""
                self.meta_rowid = item[6]              #RowId is the 7th item in the list
                if self.debug: self.model.logobject.logit("Repopulating: Row %s is between %s and %s so it will be displayed. Meta_rowid=%s, bp=%s, weight=%s, recvalues=%s, memvalues=%s" % (ix, self.start_row, ( int(self.start_row) + int(self.rows_to_display) ), self.meta_rowid, str(item[0]), str(item[1]), str(item[2]), str(item[3]) ), True, True, True )
                #Checkbox:
                col = 0
                newvalue = 0                           #Un-check the boxes when we re-draw the page
                #if self.debug: self.model.logobject.logit("Calling Update_control_in_grid() (chkbx) with row %s, col %s, newvalue %s" % (countrow, col, newvalue), True, True, True )
                self.update_control_in_grid(countrow, col, newvalue, self.meta_rowid)
				
                #Blocking Pass:
                col = 1
                newvalue = str(item[0]).strip()        #Weights and unique IDs
                #newvalue = newvalue.split(" ")[0]     #Just get the weight, discard the unique key values for now
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                #if self.debug: self.model.logobject.logit("Calling Update_control_in_grid() (blkps) with row %s, col %s, newvalue %s" % (countrow, col, newvalue), True, True, True )
                self.update_control_in_grid(countrow, col, newvalue, self.meta_rowid)
				
                #Weight:
                col = 2
                newvalue = str(item[1]).strip()        #Weights and unique IDs
                if newvalue != holdweight:             #Don't use the alternating weight colors here - get colors from the function instead
                    holdweight = newvalue
                weight_color = self.get_weight_color(newvalue, holdweight)
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                #if self.debug: self.model.logobject.logit("Calling Update_control_in_grid() (weight) with row %s, col %s, newvalue %s" % (countrow, col, newvalue), True, True, True )
                self.update_control_in_grid(countrow, col, newvalue, self.meta_rowid, weight_color)

                #Text box to display the row number
                col = 3
                newvalue = str(ix)                     #Row number within the list (index)
                #Find the correct element in self.controls where the COL attribute = col, and the ROW attribute = row.
                #if self.debug: self.model.logobject.logit("Calling Update_control_in_grid() (rownm) with row %s, col %s, newvalue %s" % (countrow, col, newvalue), True, True, True )
                self.update_control_in_grid(countrow, col, newvalue, self.meta_rowid)
				
                #*************************************************************************************************************                
                #Re-render the comparison frames for the user to review.
                ##DO NOT RE-CREATE THE FRAME OBJECTS EVERY TIME THE USER SCROLLS OR SORTS! that would create hundreds or thousands of frame objects as the user scrolls and sorts iteratively.
                vert_position = countrow +3              #Column labels are at row 0, blank space at row 1 - so add 3 to the counter to assign vertical position for this grid display row.
                kw_fresult = self.kw_fresult
                #Re-display the Matching Field Values frame for the current row of meta_values
                self.recfile_values_for_current_row = str(item[2])        #This item from meta_values is a string of Matching Field values for the Record file
                self.memfile_values_for_current_row = str(item[3])        #This item from meta_values is a string of Matching Field values for the Memory file
                gridcolumn = 4		
                if self.debug: self.logobject.logit("Calling populate_resultrow_frame with 'rec', %s" % (self.recfile_values_for_current_row), True, True, True)
                self.populate_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "rec", vert_position, gridcolumn, **kw_fresult)          #Display the comparison values
                gridcolumn = 5
                if self.debug: self.logobject.logit("Calling populate_resultrow_frame with 'mem', %s" % (self.recfile_values_for_current_row), True, True, True)
                self.populate_resultrow_frame(self.recfile_values_for_current_row, self.memfile_values_for_current_row, "mem", vert_position, gridcolumn, **kw_fresult)          #Display the comparison values
                #******************************************************************************************************************
                countrow += 1
            ix += 1
        #Now that the grid has been cleared and re-displayed, we need to update the checkboxes to reflect the user's current weight threshold for acceptance - any weight above the specified threshold triggers a checkbox CHECKED. Below the threshold triggers a checkbox DESELECT.
        self.model.spinhandler()
        #self.debug_display_arrays()
        self.container.refresh_canvas()

    '''def get_color_for_match_segment(self, matchvals1, matchvals2):
        color = ""
        ix = 1
        for seg in matchsegs1:
            if len(matchsegs2) >= ix:
                if seg == matchsegs2[ix]:        #This segment is identical between the RECORD FILE and the MEMORY FILE
                    color = "black"
                else:                            #This segment is identical between the RECORD FILE and the MEMORY FILE
                    color = "red"
            ix +=1
        return color'''

        
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
    #value = None          #Actual string value, accessed as StringVar().get()
    gridrow = None         #Position in the grid (controls start at row 3 because labels and other such things appear in grid rows 0,1,2)
    col = None             #Horizontal position in the grid 
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
        #if self.model.check_key_exists("value", **kw):
        #    self.value = kw["value"]
        if self.model.check_key_exists("gridrow", **kw):
            self.gridrow = kw["gridrow"]
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

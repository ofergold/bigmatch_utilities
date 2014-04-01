#!C:\Python33\python.exe -u
#!/usr/bin/env python

import sys
import os
from FilePath import *

gl_frame_color = "lightblue"
gl_frame_width = 500
gl_frame_height = 100


'''Class BigmatchParmfile() currently handles only the loading of variables FROM a saved Parmf.txt parameter file.
The loaded variables are to be displayed in the Blocking Pass entry forms, rendered by the class BlockingPass_Model'''

'''NOTE: the original structure of the objects defined below was to have a ParmFile object with a collection of child BlockingPass objects.
Each child BlockingPass object had a collection of child ParmRows.
Each ParmRow object had a collection of child Parms.  
For some unknown reason, the grandchild object collections all showed the exact same elements.  
I researched this for a whole day and then opted to revert to using old-fashioned Lists of Dictionaries.
The intention is still to correct the problem with the earlier strategy. 
But for now there are many arrays with redundant information scattered around the code, as a result of quickly trying various arrangements of lists and dicts.
'''


#******************************************************************************
class BigmatchParmfile():
    file_path = None
    file_name = None
    filename_with_path = None
    parmfile_rowcount = None
    row_index = None
    file_rows = []
    file_row_objects = []
    recfile_datadict = None
    memfile_datadict = None
    blocking_pass_count = None
    blocking_passes = []
    blkpass_row_index = None	
    dedupe_single_file = None
    recfile_record_length = 950
    memfile_record_length = 950
    parm_counter = None	
    parms = []	

    def __init__(self, filename_with_path=None):
        if filename_with_path:
            self.filename_with_path = filename_with_path
        print("\n filename_with_path: %s" % (self.filename_with_path) )
        self.row_index = 0
        with open(filename_with_path, 'rt') as f:
            self.file_rows = f.readlines()                      #Copy the text into a space-delimited list called file_rows
            self.parmfile_rowcount = len(self.file_rows)
            for row in self.file_rows:                          #Iterate thru the rows of text, and for each row create a ParmRow object
                print("\n Row %s: %s" % (self.row_index, row) )
                row = row.replace("\t", "     ")    #Get rid of tabs
                #Instantiate a BigmatchParmRow, populate it and add it to the file_row_objects list. 
                parmrow = BigmatchParmRow(self, self.row_index, row)
                #************************************************************************************
                #After parsing the 3rd row (row index 2), we have everything we need to populate "n" instances of the Parmfile_BlockingPass class (one instance for every Blocking Pass defined by the user). 
                #These instances were instantiated by function parse_2nd_row() and further populated by function parse_3rd_row(). But they still need to be fully fleshed out, so call populate_blocking_passes().
                if self.row_index == 2:
                    self.populate_blocking_passes()
                elif self.row_index > 2 and self.row_index < len(self.file_rows):       #Get all the Blocking Pass rows, but exclude the very last row, which is for Sequence Field info.
                    #All rows after row 3 (index 2) belong to a Blocking Pass (other than the very last row, which handles sequence fields).
                    #For these rows, we need to determine which blocking pass the belong to, and whether they are Blocking Fields, Matching Fields or Cutoff Fields.
                    parmlist= []
                    rowattribs = self.situate_parmrow_in_blocking_pass()   #Returns a dictionary of parmrow attributes
                    if rowattribs:
                        print("\n RowAttribs:")
                        print(rowattribs)
                        blkpass_index = rowattribs["blocking_pass"]       
                        parmrow.blocking_pass = rowattribs["blocking_pass"]             #Which BlockingPass does this row belong to?
                        parmrow.blkpass_row_index = rowattribs["blkpass_row_index"]     #blkpass_row_index is the index of this row WITHIN its BlockingPass
                        parmrow.row_type = rowattribs["row_type"]
                        #For rows within a BlockingPass (all rows between row 3 and the Final row), we create a child collection of Parameters within the Row Object.
                        parmlist = []
                        if parmrow.row_type == "blocking_fields":
                            parmlist = parmrow.parse_blocking_field_row()    #Returns a list of parm-dicts for the current row
                            
                        if parmrow.row_type == "matching_fields":
                            parmlist = parmrow.parse_matching_field_row()
                        if parmrow.row_type == "cutoff_fields":
                            parmlist = parmrow.parse_cutoff_field_row()
                        if parmrow.row_type == "prcutoff_fields":
                            parmlist = parmrow.parse_printcutoff_field_row()
                        '''ix = 0
                        for parm in parmrow.parm_values:
                            cntr = self.get_parm_counter()
                            ptyp = ""
                            if parmlist:
                                ptyp = parmlist[ix]["parm_type"]
                            ix += 1
                        '''
                        if parmlist:
                            #GMS alternate #1, since storing object lists seems to result in unexpected behaviors - store all parm rows in a list in each BlockingPass object
                            rowattribs["parmlist"] = parmlist
                            self.blocking_passes[blkpass_index].parmrow_attribs.append(rowattribs)
                            for parm in parmlist:
                                cntr = self.get_parm_counter()
                                #print("\n parms after parse_xx_row: row_index: %s, row_type: %s, parms in row: %s, parm_type: %s, parm_value: %s" % (parm["row_index"], parm["row_type"], parm["num_parms_in_row"], parm["parm_type"], parm["parm_value"] ) )
                                #for list in parm["whole_row"]:
                                #    print("   ++" + list)
                                first_parm_in_row = parm["whole_row"][0]        #This is important because it gives us the RecordFile Fieldname. Without that, parms like the BlankFlag cannot be uniquely identified by RowType, ParmType and ParmValue.  
                                parmstuff = {"blocking_pass": blkpass_index, "row_index": self.row_index, "row_type": parmrow.row_type, "num_parms_in_row": parm["num_parms_in_row"], "parm_index": parm["parm_index"], "parm_counter":cntr, "parm_value": parm["parm_value"], "parm_type": parm["parm_type"], "first_parm_in_row": first_parm_in_row}
                                #--> GMS alternate #2, since storing object lists seems to result in unexpected behaviors - store all parm rows to a list in this class (BigmatchParmfile)
                                self.parms.append(parmstuff)
                                #GMS alternate #3, since storing object lists seems to result in unexpected behaviors - store all parm rows to a list in the ParmRow class
                                #parmrow.yak.append(parmstuff)
                            #GMS alternative #4: store the Row Objects in a list within the BlockingPass 
                            self.blocking_passes[blkpass_index].whistle.append(parmrow)
                    #**********************************************************************************							
                    self.file_row_objects.append(parmrow)
                    #**********************************************************************************
                    #Add this Row to the Parm_Rows collection of its proper Blocking Pass
                    #self.blocking_passes[blkpass_index].add_parm_row_to_blocking_pass(parmrow)
                    print("In main INIT, adding ParmRow %s to BlockingPass #%s object's ParmRows collection (row has type '%s')." % (self.row_index, blkpass_index, parmrow.row_type) )
                    self.add_parm_row_to_blocking_pass(blkpass_index, parmrow)
                    #**********************************************************************************
                self.row_index += 1
            f.close()
        #Display the values for testing purposes
        print("\n ******************************************************")
        print("\n Parm row tree:")
        print("\n Number of Blocking Passes: %s" % (len(self.blocking_passes)) )
        self.display_blocking_passes_and_rows()

    def populate_blocking_passes(self):
        #We populate the starting and ending rows for various sections of each Blocking Pass by reading the contents of the ParmF.txt parameter file, which explicitly specifies the number of blocking and matching fields that we can expect for each Blocking Pass.
        first_row_of_pass = 3                                          #Row index for the first row of the current blocking pass; the 1st Blocking Pass always starts at row 4 (index 3).
        blkpass_index = 0
        for blkpass in self.blocking_passes:
            #print("\n BlockPass initial attributes-- blkpass_index: %s, num_blocking_fields: %s, num_matching_fields: %s " % (blkpass.blkpass_index, blkpass.num_blocking_fields, blkpass.num_matching_fields ) )
            #Based on the num_blocking_fields and num_matching_fields for each Blocking Pass object, we can calculate start and end positions of each section within the pass.
            blkpass.startrow = first_row_of_pass   	                                #First row of pass IS THE FIRST of the blocking_field rows
            blkpass.startrow_for_blkpass_blkfields = first_row_of_pass   	                                #First row of pass IS THE FIRST of the blocking_field rows
            blkpass.endrow_for_blkpass_blkfields = blkpass.startrow_for_blkpass_blkfields + blkpass.num_blocking_fields -1  #Minus one because if start_row is 3 and there is 1 row, then end row is 3 (3+1-1), not 4 (3+1)
            blkpass.startrow_for_blkpass_matchfields = blkpass.endrow_for_blkpass_blkfields + 1
            blkpass.endrow_for_blkpass_matchfields = blkpass.startrow_for_blkpass_matchfields + blkpass.num_matching_fields -1
            blkpass.startrow_for_blkpass_cutoffs = blkpass.endrow_for_blkpass_matchfields + 1
            blkpass.endrow_for_blkpass_cutoffs = blkpass.startrow_for_blkpass_cutoffs + 1
            blkpass.endrow = blkpass.endrow_for_blkpass_cutoffs
            print("\n Blocking Pass: %s, Startrow: %s, Endrow: %s, first_row_of_pass: %s, num_blocking_fields: %s, num_matching_fields: %s, startrow_for_blkpass_blkfields: %s, endrow_for_blkpass_blkfields: %s, startrow_for_blkpass_matchfields: %s, endrow_for_blkpass_matchfields: %s" % ( blkpass.blkpass_index, blkpass.startrow, blkpass.endrow, first_row_of_pass, blkpass.num_blocking_fields, blkpass.num_matching_fields, blkpass.startrow_for_blkpass_blkfields, blkpass.endrow_for_blkpass_blkfields, blkpass.startrow_for_blkpass_matchfields, blkpass.endrow_for_blkpass_matchfields  ) )
            #Now we can ascertain that the file rows are describing a new Blocking Pass.
            first_row_of_pass = blkpass.endrow_for_blkpass_cutoffs + 1 
            blkpass_index +=1

    def add_blocking_pass(self, **kw):
        #Create a new instance of the Parmfile_BlockingPass class, and add it to the master.blocking_passes list.
        print("\n About to CREATE A NEW BlockingPass.")
        blkpass = Parmfile_BlockingPass(self, **kw)
        self.blocking_passes.append(blkpass)
        print("\n CREATED A NEW BlockingPass. Current number of blocking passes is %s" % (len(self.blocking_passes)) )
        for blkpass in self.blocking_passes:
            print("BlkPass #%s has num_blocking_fields %s and num_matching_fields %s" % (blkpass.blkpass_index, blkpass.num_blocking_fields, blkpass.num_matching_fields) )

    def situate_parmrow_in_blocking_pass(self):
        #A Blocking Pass object was instantiated for each parameter value found in the 2nd row (index 1), because the 2nd row specifies the number of Blocking Fields found for each Blocking Pass -- so we know it exists and we know one important thing about it. Additional BlockingPass-level information is populated by function "populate_blocking_passes()".
        #Important: we determine the row_type and other row-level information by accessing information from the Blocking Pass that this row belongs to.
        rowattribs = {}		
        blkpass_index = 0
        self.blkpass_row_index = 0
        #print("\n In function Situate(), number of blocking passes so far is: %s" % (len(self.blocking_passes)) )
        found = False
        for blkpass in self.blocking_passes:
            print("\n In Situate(), now on blocking pass %s, which has startrow %s and endrow %s" % (blkpass.blkpass_index, blkpass.startrow, blkpass.endrow) )
            if self.row_index >= blkpass.startrow and self.row_index <= blkpass.endrow:         #This row falls within the current Blocking Pass section of the text file
                print("ROW %s IS WITHIN BOUNDS FOR BlockingPass %s" % (self.row_index, blkpass.blkpass_index) )
                rowattribs["blocking_pass"] = blkpass.blkpass_index
                rowattribs["blkpass_row_index"] = blkpass.increment_parmrow_counter()
                rowattribs["row_index"] = self.row_index
                #Determine where the current row fits into the Blocking Pass we are currently evaluating. (Is it within the Blocking Fields rows? Is it within the Matching Fields rows?)
                if self.row_index in range(blkpass.startrow_for_blkpass_blkfields, blkpass.endrow_for_blkpass_blkfields +1):          #This range of ParmF rows consists of Blocking Field rows for the first blocking pass (index 0)
                    rowattribs["row_type"] = "blocking_fields"
                    print("\n Row %s is within the range of Blocking Fields for Blocking Pass %s because row index is between %s and %s (blkpass_row_index=%s)" % (str(self.row_index), str(blkpass.blkpass_index), str(blkpass.startrow_for_blkpass_blkfields), str(blkpass.endrow_for_blkpass_blkfields), str(self.blkpass_row_index) ) )
                    found = True
                elif self.row_index in range(blkpass.startrow_for_blkpass_matchfields, blkpass.endrow_for_blkpass_matchfields +1):          #This range of ParmF rows consists of Blocking Field rows for the first blocking pass (index 0)
                    rowattribs["row_type"] = "matching_fields"				
                    print("\n Row %s is within the range of Matching Fields for Blocking Pass %s because row index is between %s and %s (blkpass_row_index=%s)" % (str(self.row_index), str(blkpass.blkpass_index), str(blkpass.startrow_for_blkpass_matchfields), str(blkpass.endrow_for_blkpass_matchfields), str(self.blkpass_row_index) ) )
                    found = True
                elif self.row_index in range(blkpass.startrow_for_blkpass_cutoffs, blkpass.endrow_for_blkpass_cutoffs +1):          #This range of ParmF rows consists of Blocking Field rows for the first blocking pass (index 0)
                    if self.row_index == blkpass.startrow_for_blkpass_cutoffs:
                        rowattribs["row_type"] = "cutoff_fields"             #Cutoff fields row
                    if self.row_index == blkpass.endrow_for_blkpass_cutoffs:
                        rowattribs["row_type"] = "prcutoff_fields"           #Print Cutoff fields row
                    print("\n Row %s is within the range of Cutoff Fields for Blocking Pass %s because row index is between %s and %s (blkpass_row_index=%s)" % (str(self.row_index), str(blkpass.blkpass_index), str(blkpass.startrow_for_blkpass_cutoffs), str(blkpass.endrow_for_blkpass_cutoffs), str(self.blkpass_row_index) ) )
                    found = True
                #Append this row to the parm_rows list for the current BlockingPass:
                if found:
                    self.blkpass_row_index += 1
                    #print("\n Adding Parm_row %s to BlockingPass #%s" % (self.row_index, blkpass_index) ) 
                    #self.master.blocking_passes[blkpass_index].parm_rows.append(self)    #Append this row into the parm_rows[] list for the current Blocking Pass:
                    '''self.blocking_passes[blkpass_index].add_parm_row_to_blocking_pass(parmrow_obj) '''
                    #print("\n Parm_rows for BlockingPass #%s now appears like this:" % (blkpass.blkpass_index) ) 
                    #for row in self.master.blocking_passes[blkpass_index].parm_rows:
                    #    print(row.parm_values)
                    #print("\n") 
                    break
            else:
                print("ROW %s IS OUTSIDE THE BOUNDS FOR BlockingPass %s" % (self.row_index, blkpass.blkpass_index) )
            self.blkpass_row_index = 0
        return rowattribs
			
    def add_parm_row_to_blocking_pass(self, blkpass_index, parmrow_obj):
        #print("\n About to add a Parmrow to list of BlockPass #%s ... total parmrows is now %s" % (blkpass_index, len(self.blocking_passes[blkpass_index].parm_rows) ) )
        #if blkpass_index == 0:
        #    print("\n Total parmrows for BockingPass #1 is now %s" % (len(self.blocking_passes[1].parm_rows) ) )
        self.blocking_passes[blkpass_index].parm_rows.append(parmrow_obj)
        #print("\n After adding Parmrow to list of BlockingPass #%s ... total parmrows is now %s" % (blkpass_index, len(self.blocking_passes[blkpass_index].parm_rows) ) )
        #if blkpass_index == 0:
        #    print("\n Total parmrows for BockingPass #1 is now %s" % (len(self.blocking_passes[1].parm_rows) ) )
        #print(self.blocking_passes[blkpass_index].parm_rows)
        
    def check_key_exists(self, keyvalue, **kw):
        found = False
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found
            
    def add_parmrow(self, parmrow, blockblkpass_index):
        pass

    def get_parm_counter(self):
        if self.parm_counter is None:
            self.parm_counter = 0 
        else:
            self.parm_counter += 1
        return self.parm_counter
        

    def display_blocking_passes_and_rows(self):
        for blkpass in self.blocking_passes:
            print("\n !!*** Blocking Pass #%s has %s blocking fields and %s matching fields. Startrow is %s and Endrow is %s" % (blkpass.blkpass_index, blkpass.num_blocking_fields, blkpass.num_matching_fields, blkpass.startrow, blkpass.endrow ) )
            #Same problem here. ALL parmrows appear in the collection of EVERY blocking pass.
            #for w in blkpass.whistle:
            #    print("Whistle %s, BlkPass: %s, BlkPass row: %s -- row_type: %s, parm_values: %s" % (w.row_index, w.blocking_pass, w.blkpass_row_index, w.row_type, w.parm_values) )
            #for parmrow in blkpass.parm_rows:
            #    print("File row %s, BlkPass: %s, BlkPass row: %s -- row_type: %s, parm_values: %s" % (parmrow.row_index, parmrow.blocking_pass, parmrow.blkpass_row_index, parmrow.row_type, parmrow.parm_values) )
            #The following works, but has only simple values for parameters (does not store parameter name)
            for parmrow in blkpass.parm_rows:
                #THIS WORKS OKAY: 
                print("\n ~~File row %s, BlkPass: %s, BlkPass row: %s -- row_type: %s, parm_values: %s" % (parmrow.row_index, parmrow.blocking_pass, parmrow.blkpass_row_index, parmrow.row_type, parmrow.parm_values) )
                #All of the lists of objects (even lists of dicts) seem to include all elements added to ALL instances of the class.  
                #But primitive types (strings, ints), and lists of primitive types seem to be fine.
                #print(" ~- Parms for row %s:" % (parmrow.row_index) )
                #for attrib in parmrow.parm_attribs:
                #for attrib in parmrow.yak:
                #    print("Parm--row_index: %s, parm_type: %s, parm_value: %s" % ( attrib["row_index"], attrib["parm_type"], attrib["parm_value"] ) )      #attrib["row_index"], attrib["row_type"], 
                #for elf in parmrow.yak2:
                #    print(elf)
            #The following also has ALL rows in EVERY blocking pass. It is a list of dicts stored at the Child level (BlockingPass) rather than the Grandchild level (ParmRow)
            #for row in blkpass.parmrow_attribs:
            #    print("\n __ParmRow Attributes for BlockingPass %s, Row %s:" % (blkpass.blkpass_index, row["row_index"] ) )
            #    print("BlockingPass: %s, blkpass_row_index: %s, row_index: %s, row_type: %s" % ( row["blocking_pass"], row["blkpass_row_index"], row["row_index"], row["row_type"]  ) )
            #    for parm in row["parmlist"]:
            #        print("\n   ==  %s" % (parm) )
        #print("\n Blocking Pass #0 has %s blocking fields and %s matching fields. Startrow is %s and Endrow is %s" % (self.blocking_passes[0].num_blocking_fields, self.blocking_passes[0].num_matching_fields, self.blocking_passes[0].startrow, self.blocking_passes[0].endrow ) )
        #for parmrow in self.blocking_passes[0].parm_rows:
        #    print("File row %s, BlkPass: %s, BlkPass row: %s -- row_type: %s, parm_values: %s" % (parmrow.row_index, parmrow.blocking_pass, parmrow.blkpass_row_index, parmrow.row_type, parmrow.parm_values) )
        #print("\n Blocking Pass #1 has %s blocking fields and %s matching fields. Startrow is %s and Endrow is %s" % (self.blocking_passes[1].num_blocking_fields, self.blocking_passes[1].num_matching_fields, self.blocking_passes[1].startrow, self.blocking_passes[1].endrow ) )
		
        #Intention was to always store Parameter Rows as children in a collection within each BlockingPass object.  For unknown reason, each BlockingPass's collection of child Rows contained ALL Rows, not just those within that BlockinPass.
        #So this collection of ALL Parameter Rows will have to suffice as a workaround.  --GMS February 2014
        #for parmrow in self.blocking_passes[1].parm_rows:
        #    print("File row %s, BlkPass: %s, BlkPass row: %s -- row_type: %s, parm_values: %s" % (parmrow.row_index, parmrow.blocking_pass, parmrow.blkpass_row_index, parmrow.row_type, parmrow.parm_values) )
        #print("\n SELF.FILE_ROW_OBJECTS (count is %s)" % (len(self.file_row_objects)) ) 
        #The following works, but has only simple values for parameters (does not store parameter name)
        for row in self.file_row_objects:
            print("\n **Rowindex: %s, BlockingPass: %s, Blkpass_row_index: %s, RowType: %s, RowText: %s" % (row.row_index, row.blocking_pass, row.blkpass_row_index, row.row_type, row.rowtext) )
            for parm in row.parm_values:
                print(parm)
            #print("CHILD PARMS--")
            #for parmobj in row.parm_objects:
            #    print("...row-index: %s, row_type: %s, parm_type: %s, parm_value: %s" % (parmobj.row_index, parmobj.row_type, parmobj.parm_type, parmobj.parm_value) )
            '''print("CHILD PARM ATTRIBS--")
            print("0 row_index: %s, row_type: %s, parm_type: %s, parm_value: %s" % ( row.parm_attribs[0]["row_index"], row.parm_attribs[0]["row_type"], row.parm_attribs[0]["parm_type"], row.parm_attribs[0]["parm_value"] ) )
            print("1 row_index: %s, row_type: %s, parm_type: %s, parm_value: %s" % ( row.parm_attribs[1]["row_index"], row.parm_attribs[1]["row_type"], row.parm_attribs[1]["parm_type"], row.parm_attribs[1]["parm_value"] ) )
            print("2 row_index: %s, row_type: %s, parm_type: %s, parm_value: %s" % ( row.parm_attribs[2]["row_index"], row.parm_attribs[2]["row_type"], row.parm_attribs[2]["parm_type"], row.parm_attribs[2]["parm_value"] ) )
            print("3 row_index: %s, row_type: %s, parm_type: %s, parm_value: %s" % ( row.parm_attribs[3]["row_index"], row.parm_attribs[3]["row_type"], row.parm_attribs[3]["parm_type"], row.parm_attribs[3]["parm_value"] ) )
            '''		
            #Same thing for the following - EVERY parm appears under EVERY ROW.			
            #for attrib in row.parm_attribs:
            #    print(":::parm_type: %s, parm_value: %s" % ( attrib["parm_type"], attrib["parm_value"] ) )    #"row_index: %s, row_type: %s,   attrib["row_index"], attrib["row_type"], 
        #THIS IS THE ONLY OPTION THAT WORKS FOR STORING DETAILED PARAMETER-LEVEL INFORMATION.  IT IS STORED AS A LIST IN THE TOP-LEVEL OBJECT CALLED "PARMS".
        for parm in self.parms:
            print("\n^^PARM: blkpass: %s, row_index: %s, row_type: %s, parms in row: %s, parm_index: %s, parm_type: %s, parm_value: %s, first_parm_in_row: %s" % (parm["blocking_pass"], parm["row_index"], parm["row_type"], parm["num_parms_in_row"], parm["parm_index"], parm["parm_type"], parm["parm_value"], parm["first_parm_in_row"] ) )

#End of class


#******************************************************************************
#******************************************************************************
class Parmfile_BlockingPass():
    master = None
    blkpass_index = None
    num_blocking_fields = None
    num_matching_fields = None
    startrow = None
    endrow = None
    startrow_for_blkpass_blkfields = None
    endrow_for_blkpass_blkfields = None  #Minus one because if start_row is 3 and there is 1 row, then end row is 3 (3+1-1), not 4 (3+1)
    startrow_for_blkpass_matchfields = None
    endrow_for_blkpass_matchfields = None
    startrow_for_blkpass_cutoffs = None
    endrow_for_blkpass_cutoffs = None
    parmrow_counter = None
    parm_rows = []
    parmrow_attribs = []
    whistle = []

    def __init__(self, master, **kw):
        self.master = master
        print("\n Keyword args in Parmfile_BlockingPass.init():")
        for key, value in kw.items():
            #if key.lower() == "blkpass_index":
            #    self.blkpass_index = value
            print("%s = %s" % (key, value) )
        self.blkpass_index = int(kw["blkpass_index"])
        self.num_blocking_fields = int(kw["num_blocking_fields"])
        self.num_matching_fields = int(kw["num_matching_fields"])

    def increment_parmrow_counter(self):
        if self.parmrow_counter is None:
            self.parmrow_counter = 0
        else:
            self.parmrow_counter += 1
        return self.parmrow_counter

    def add_parm_row_to_blocking_pass(self, parmrow_obj):
        print("\n In BlockPass object %s, about to add a new Parmrow object to list... total parmrows is now %s" % (self.blkpass_index, len(self.parm_rows)) )
        self.parm_rows.append(parmrow_obj)
        print(self.parm_rows)

    def add_row_attribs_to_blocking_pass(self, row_attribs):
        self.parmrow_attribs.append(row_attribs)
		
#End of class


#******************************************************************************
#******************************************************************************
class BigmatchParmRow():
    row_index = None
    blocking_pass = None
    blkpass_row_index = None
    row_type = None
    rowtext = None
    parm_values = []                #This is a list of Parameter Values
    parm_objects = []               #This is a list of Parameter Objects, not values (type BigMatchParm)
    parm_attribs = []
    yak = []
    yak2 = []
    def __init__(self, master, row_index, rowtext=None, row_type=''):
        self.master = master
        self.row_index = row_index
        if rowtext:
            self.rowtext = rowtext.strip()
            self.rowtext = self.rowtext.replace("      ", " ")
            self.rowtext = self.rowtext.replace("     ", " ")
            self.rowtext = self.rowtext.replace("    ", " ")
            self.rowtext = self.rowtext.replace("   ", " ")
            self.rowtext = self.rowtext.replace("  ", " ")
        self.parm_values = self.rowtext.split(" ")
        #print("parm_values for row %s: %s" % (self.row_index, self.parm_values) )
        '''parm_attrib = {}
        for val in self.parm_values:
            parm_attrib["row_index"] = self.row_index
            parm_attrib["row_type"] = ""
            parm_attrib["parm_value"] = val
            parm_attrib["parm_type"] = ""
            if parm_attrib:
                self.parm_attribs.append(parm_attrib)
        '''
        parmstuff = {"blocking_pass": "not sure yet", "row_index": self.row_index, "row_type": "unknown", "num_parms_in_row": "Many", "parm_index": "Some index", "parm_counter":self.row_index * 3, "parm_value": "Empty", "parm_type": "Nuttin"}
        self.yak.append(parmstuff)
        self.yak2.append("row_index=" + str(self.row_index))
        self.yak2.append("row_text=" + self.rowtext)
        #*****************************************************
        #ParseRow() functions populate this instance and also populates Parmfile_BlockingPass instances. 
        self.parse_row()
        #*****************************************************
		
    def parse_row(self):
        if self.row_index == 0:
            self.parse_1st_row()
        elif self.row_index == 1:
            self.parse_2nd_row()
        elif self.row_index == 2:
            self.parse_3rd_row()
        elif self.row_index == self.master.parmfile_rowcount -1:
            self.parse_final_row()
        else:
            #All rows that do not fall into the above categories (row_index less than 3 or very last row) IS A ROW WITHIN A BLCOKING PASS.
            #A Blocking Pass object was instantiated for each parameter value found in the 2nd row (row_index 1), because the 2nd row specifies the number of Blocking Fields found for each Blocking Pass -- so we know it exists and we know one important thing about it. Additional BlockingPass-level information is populated by function "populate_blocking_passes()".
            pass
					
    def parse_1st_row(self):
        self.master.blocking_pass_count = self.parm_values[0]
        self.master.dedupe_single_file = self.parm_values[5]
        self.recfile_record_length = self.parm_values[7]
        self.memfile_record_length = self.parm_values[8]
        print("\n blocking_pass_count: %s, dedupe_single_file: %s, recfile_record_length: %s, memfile_record_length: %s"  % (self.master.blocking_pass_count, self.master.dedupe_single_file, self.master.recfile_record_length, self.master.memfile_record_length) )

    def parse_2nd_row(self):                              #Each value in 2nd row (index 1) is an integer showing the number of Blocking Fields for a blocking pass.  The first integer is number of blocking fields in first blocking pass, 2nd integer is number of blocking fields in 2nd blocking pass, etc.
        i = 0
        for parmval in self.parm_values:                      #Each value in 2nd row (index 1) is an integer showing the number of Blocking Fields for a blocking pass.  The first integer is number of blocking fields in first blocking pass, 2nd integer is number of blocking fields in 2nd blocking pass, etc.
            num_blocking_fields = parmval
            #Create a new instance of the Parmfile_BlockingPass class, and add it to the master.blocking_passes list.
            blkpass_kw = {"blkpass_index":i, "num_blocking_fields":int(parmval), "num_matching_fields":0}       #The Number of matching fields will be loaded up from the line following this present line (Line 3, index 2) of the ParmF.txt file.
            self.master.add_blocking_pass(**blkpass_kw)
            #blkpass = Parmfile_BlockingPass(self.master, **blkpass_kw)
            #self.master.blocking_passes.append(blkpass)
            #print("\n blocking_pass index: %s, num_blocking_fields: %s, num_matching_fields: %s"  % (str(blkpass.blkpass_index), str(blkpass.num_blocking_fields), str(blkpass.num_matching_fields) ) )
            i +=1 

    def parse_3rd_row(self):                              #Each value in 3rd row (index 2) is an integer showing the number of Matching Fields for a blocking pass.  The first integer is number of matching fields in first blocking pass, 2nd integer is number of matching fields in 2nd blocking pass, etc.
        i = 0
        for parmval in self.parm_values:                      #Each value in 3rd row (index 2) is an integer showing the number of Matching Fields for a blocking pass.  The first integer is number of matching fields in first blocking pass, 2nd integer is number of matching fields in 2nd blocking pass, etc.
            num_matching_fields = parmval
            #Update the instance of the Parmfile_BlockingPass class that corresponds to this Blocking Pass, by populating the num_matching_fields property.
            #self.master.blocking_passes[i]["num_matching_fields"] = parmval                                #Number of matching fields for this blocking pass
            self.master.blocking_passes[i].num_matching_fields = int(parmval)                                    #Number of matching fields for this blocking pass
            print("\n blocking_pass index: %s, num_blocking_fields: %s, num_matching_fields: %s"  % ( str(self.master.blocking_passes[i].blkpass_index), str(self.master.blocking_passes[i].num_blocking_fields), str(self.master.blocking_passes[i].num_matching_fields) ) )
            i +=1 

    def parse_blocking_field_row(self):
        i = 0
        parms = []
        for parm in self.parm_values:
            parm_value = self.parm_values[i]    #The text value for this item of the row
            if i == 0:
                parm_type = "recfile_field"     #First item in a Blocking Field row is the name of the field within the Record File.
            elif i == 1:
                parm_type = "recfile_startpos"  #Second item in a Blocking Field row is the Starting Position of the field within the Record File.
            elif i == 2:
                parm_type = "recfile_width"     #Third item in a Blocking Field row is the Width of the field within the Record File.
            elif i == 3:
                parm_type = "memfile_startpos"  #Fourth item in a Blocking Field row is the Starting Position of the field within the Memory File.
            elif i == 4:
                parm_type = "memfile_width"     #Fifth item in a Blocking Field row is the Width of the field within the Memory File.
            elif i == 5:
                parm_type = "blank_flag"        #Sixth item in a Blocking Field row is the Blank Flag (how to handle blanks in the data).
            else:
                self.master.error_message = "Invalid parameter index for Blocking Field row: " + str(i)
                return False
            kw_parm = {"whole_row": self.parm_values, "num_parms_in_row": len(self.parm_values), "parm_index": i, "parm_type": parm_type, "parm_value": parm_value, "row_index": self.row_index, "row_type": self.row_type}		
            parms.append(kw_parm)
            #Instantiate the BigmatchParm() class and populate its properties
            #parm = BigmatchParm(**kw_parm)
            #self.parm_objects.append(parm)
            #Storing a list of object references does not seem to work.  Try an old-fashioned List of Dicts instead.
            self.add_parm_attribs(**kw_parm)
            '''parm_attrib = {}
            parm_attrib["row_index"] = kw_parm["row_index"]
            parm_attrib["row_type"] = kw_parm["row_type"]
            parm_attrib["parm_type"] = kw_parm["parm_type"]
            parm_attrib["parm_value"] = kw_parm["parm_value"]
            if parm_attrib:
                self.parm_attribs.append(parm_attrib)'''
            i +=1 
			
        return parms

    def parse_matching_field_row(self):
        parms = []		
        i = 0
        for parm in self.parm_values:
            parm_value = self.parm_values[i]    #The text value for this item of the row
            if i == 0:
                parm_type = "recfile_field"     #First item in a Matching Field row is the name of the field within the Record File.
            elif i == 1:
                parm_type = "recfile_startpos"  #Second item in a Matching Field row is the Starting Position of the field within the Record File.
            elif i == 2:
                parm_type = "recfile_width"     #Third item in a Matching Field row is the Width of the field within the Record File.
            elif i == 3:
                parm_type = "memfile_startpos"  #Fourth item in a Matching Field row is the Starting Position of the field within the Memory File.
            elif i == 4:
                parm_type = "memfile_width"     #Fifth item in a Matching Field row is the Width of the field within the Memory File.
            elif i == 5:
                parm_type = "non_operational"   #Sixth item in a Matching Field row is always a Zero (non-operational)
            elif i == 6:
                parm_type = "comparison_method" #Seventh item in a Matching Field row is the Comparison Method (string, date, etc.)
            elif i == 7:
                parm_type = "m-value"           #Eighth item in a Matching Field row is M-Value (weight cutoff for inclusion as a match)
            elif i == 8: 
                parm_type = "u-value"           #Ninth item in a Matching Field row is U-Value (weight cutoff for exclusion as a match)
            else:
                self.master.error_message = "Invalid parameter index for Matching Field row: " + str(i)
                return False
            #Instantiate the BigmatchParm() class and populate its properties
            kw_parm = {"whole_row": self.parm_values, "num_parms_in_row": len(self.parm_values), "parm_index": i, "parm_type": parm_type, "parm_value": parm_value, "row_index": self.row_index, "row_type": self.row_type}		
            parms.append(kw_parm)
            #parm = BigmatchParm(**kw_parm)
            #self.parm_objects.append(parm)
            self.add_parm_attribs(**kw_parm)
            i +=1 

        return parms
		
    def parse_cutoff_field_row(self):
        i = 0
        parms = []
        for parm in self.parm_values:
            parm_value = self.parm_values[i]    #The text value for this item of the row
            if i == 0:
                parm_type = "cutoff_hi"         #First item in a Cutoff Field row is the High value for inclusion in output file.
            elif i == 1:
                parm_type = "cutoff_low"        #Second item in a Cutoff Field row is the Low value for inclusion in output file.
            else:
                self.master.error_message = "Invalid parameter index for Cutoff Field row: " + str(i)
                return False
            #Instantiate the BigmatchParm() class and populate its properties
            kw_parm = {"whole_row": self.parm_values, "num_parms_in_row": len(self.parm_values), "parm_index": i, "parm_type": parm_type, "parm_value": parm_value, "row_index": self.row_index, "row_type": self.row_type}		
            parms.append(kw_parm)
            #parm = BigmatchParm(**kw_parm)
            #self.parm_objects.append(parm)  
            self.add_parm_attribs(**kw_parm)
            i +=1 
        return parms
		
    def parse_printcutoff_field_row(self):
        i = 0
        parms = []
        for parm in self.parm_values:
            parm_value = self.parm_values[i]    #The text value for this item of the row
            if i == 0:
                parm_type = "prcutoff_hi"         
				#First item in a PrintCutoff Field row is the High value for inclusion in output file.
            elif i == 1:
                parm_type = "prcutoff_low"        #Second item in a PrintCutoff Field row is the Low value for inclusion in output file.
            else:
                self.master.error_message = "Invalid parameter index for PrintCutoff Field row: " + str(i)
                return False
            #Instantiate the BigmatchParm() class and populate its properties
            kw_parm = {"whole_row": self.parm_values, "num_parms_in_row": len(self.parm_values), "parm_index": i, "parm_type": parm_type, "parm_value": parm_value, "row_index": self.row_index, "row_type": self.row_type}		
            parms.append(kw_parm)
            #parm = BigmatchParm(**kw_parm)
            #self.parm_objects.append(parm)
            self.add_parm_attribs(**kw_parm)
            i +=1 
        return parms

    def parse_final_row(self):
        print("\n The final row looks like this: %s" % (self.parm_values) )

    def add_parm_attribs(self, **kw):
        #parm_attribs is a list of dicts:
        parm_attrib = {}
        if self.master.check_key_exists("row_index", **kw): 
            parm_attrib["row_index"] = kw["row_index"]
        if self.master.check_key_exists("row_type", **kw): 
            parm_attrib["row_type"] = kw["row_type"]
        if self.master.check_key_exists("parm_type", **kw): 
            parm_attrib["parm_type"] = kw["parm_type"]
        if self.master.check_key_exists("parm_value", **kw): 
            parm_attrib["parm_value"] = kw["parm_value"]
        if parm_attrib:
            self.parm_attribs.append(parm_attrib)


#End of class

#******************************************************************************
#******************************************************************************
class BigmatchParm():
    row_index = None
    row_type = None
    parm_type = None
    parm_value = None
    
    def __init__(self, **kw):
        if self.check_key_exists("row_index", **kw):
            self.row_index = kw["row_index"]
        if self.check_key_exists("row_type", **kw):
            self.row_type = kw["row_type"]
        if self.check_key_exists("parm_type", **kw):
            self.parm_type = kw["parm_type"]
        if self.check_key_exists("parm_value", **kw):
            self.parm_value = kw["parm_value"]

    def check_key_exists(self, keyvalue, **kw):
        found = False
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        return found
            
		
#End of class

'''FROM bvdet at http://bytes.com/topic/python/answers/882126-grid-view-table-list-tkinter '''
from tkinter import *
from time import sleep

textFont1 = ("Arial", 10, "bold italic")
textFont2 = ("Arial", 16, "bold")
textFont3 = ("Arial", 8, "bold")
gl_colwidth = 16
 
class LabelWidget(Entry):
    def __init__(self, master, x, y, text, **kw):
        self.text = StringVar()
        self.text.set(text)
        self.value = ''   #GMS this is just so that LabelWidget has the same properties as EntryWidget.
        Entry.__init__(self, master=master)
        self.config(textvariable=self.text)
        self.config(relief="ridge", font=textFont1, justify='center')
        kw["width"] = self.master.get_column_width(self.master.widget_type, **kw)
        self.config(**kw)
        self.grid(column=x, row=y)
        print("LabelWidget %s, %s has width: %s and type: %s" % (x, y, kw["width"], self.master.widget_type ) )
        #master.cell_widgets.append(self)   #DO NOT add the read-only labels (column header captions and line number labels) in the cell_widgets list.  They do not have user-entered values.
 
class EntryWidget(Entry):
    def __init__(self, master, x, y, cellvalue="", **kw):
        Entry.__init__(self, master=master)
        self.value = StringVar()
        self.config(textvariable=self.value, relief="ridge", font=textFont1, justify='center')
        kw["width"] = self.master.get_column_width(self.master.widget_type, **kw)
        self.config(**kw)
        self.grid(column=x, row=y)
        self.value.set(cellvalue)
        #print("In EntryWidget(), colwidth=%s, x=%s, y=%s, cellvalue=%s, self.value=%s" % (colwidth, x, y, str(cellvalue), str(self.value) ) )
        #Keep a list of all grid cells (Entry widgets) and their positions:
        cell_attribs = { "object":self, "x":x, "y":y, "orig_value":cellvalue, "StringVar":str(self.value) }
        master.cell_widgets.append(cell_attribs)                  #Keep a list of grid cells so that we can interrogate it later.
        #print("EntryWidget %s, %s has width: %s" % (x, y, kw["width"] ) )

class EntryGrid(Frame):
    ''' Dialog box with Entry widgets arranged in columns and rows.'''
    debug = True
    error_message = ""
    initialized = False	
    parent = None
    col_list = None
    row_list = None
    values_list = None
    column_width = None
    rowlabel_column_width = None      #Width of the left-most column, which typically displays row numbers.  Calculated by function calc_rowlabel_column_width().
    cell_widgets = []                 #List of Entry widget objects, which can later be traversed to retrieve their values.
    meta_values_after_edit = []       #List of values read from the Entry Grid, AFTER the user has made changes. Populated by function retrieve_grid_values().
    grid_values = {}
    num_initial_rows = 26
    label_bgcolor = "#FBFCCA"
    label_fontcolor = "#031665"
    entry_bgcolor = "#E2E4E3"
    entry_fontcolor = "#020D3E" 
    previous_row_count = None
    previous_column_count = None
    widget_type = None                #At any given time when the grid is being populated, widget_type tells us what kind of grid cell is currently being worked on (examples: 'row_labels' 'column_labels', 'entry')
    grid_config_dict = None
    #logobject = None

    def __init__(self, parent, col_list, row_list, values_list=[], show_grid=False, **kw):
        '''col_list is a list of column labels that are displayed along the top of the grid.
        row_list is a list of row numbers to be displayed along the left side of grid for user convenience.
        values_list is a list that holds the actual data to populate the grid.
		'''
        Frame.__init__(self, parent) 
        self.parent = parent
        print("\n In EntryGrid._init_():")
        if self.check_key_exists("width", **kw):
            self.column_width = int(kw["width"])
        else:
            self.column_width = gl_colwidth
        kw["width"]=self.column_width
        #GMS don't display the grid	in INIT. Rather, call the initialize_grid() function explicitly and pass arrays to populate the grid.
        if show_grid:		
            self.initialize_grid(col_list, row_list, values_list, **kw)
		
    def initialize_grid(self, col_list, row_list, values_list=[], **kw):
        self.clear_arrays()    #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_arrays() deletes these class properties.
        self.clear_grid()      #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_grid() deletes cell values.
        self.cell_widgets = [] #This must be reset or subsequent loadings start appending new rows onto the old (why?)		
        self.col_list = col_list[:]
        self.col_list.insert(0, "")
        print("Column and Row lists:")
        print(self.col_list)
        self.row_list = row_list[:]
        print(self.row_list)
        self.config(padx='3.0m', pady='3.0m')
        self.values_list = values_list[:]          #The grid values that have been passed in from the calling object
        print("\n In EntryGrid._initialize_grid():")
        if self.check_key_exists("width", **kw):
            self.column_width = int(kw["width"])
        else:
            self.column_width = gl_colwidth
        kw["width"]=self.column_width
        self.grid()
        #Create row and column headers along top and left:		
        #print ("\n In TkEntry.initialize_grid(), ABOUT TO CALL Make_Header():  len(col_list)=" + str(len(self.col_list)) + ", len(row_list)=" + str(len(self.row_list)) + ", len(values_list)=" + str(len(self.values_list)) + "\n")
        #self.debug_display_arrays()
        self.make_header()
        if self.debug:
            print ("\n In TkEntry.initialize_grid(), AFTER Make_Header, about to loop thru arrays: len(col_list)=" + str(len(self.col_list)) + ", len(row_list)=" + str(len(self.row_list)) + ", len(values_list)=" + str(len(self.values_list)) + "\n")
            self.debug_display_arrays()
        #Display in grid cells any values that were passed in as values_list[].
        self.grid_values = {}
        self.widget_type = "entry"
        kw["width"] = self.get_column_width(self.widget_type, **kw)
        #for c in range(1, len(self.col_list)):
            #for r in range(len(self.row_list)):
        for r in range(0, len(self.row_list)):
            for c in range(1, len(self.col_list)):
                cellvalue = StringVar()
                if len(values_list) > 0:
                    cellvalue = values_list[r][c-1]			#The values that will be copied into this cell from the "values_list" LIST OF LISTS.
                else:
                    cellvalue = ""
                cellvalue = cellvalue.replace("\n", "")
                cellvalue = cellvalue.replace(chr(10), "")
                cellvalue = cellvalue.replace(chr(13), "")
                #print ("c: %s, r: %s ... cell value: %s" % (str(c), str(r), str(cellvalue) ) )
                #Create the Entry widget which will display the value:
                w = EntryWidget(self, c, r+1, cellvalue, background=self.entry_bgcolor, fg=self.entry_fontcolor, **kw)
                self.grid_values[(c-1, r)] = w.value
        #Copy the grid cell config dict to a property of this class.
        self.grid_config_dict = kw
        #Important: Register the fact that this Entry Grid has been initialized.  
        #Otherwise the calling object will re-draw the grid, which will work fine except that it'll create dozens of new StringVars each time it is re-populated, and we won't have any way to interrogate those StringVars later to retrieve their values.
        self.initialized = True
        
        print("\n Length of self.cell_widgets: %s" % (len(self.cell_widgets) ) )
        #***************************
        if __name__ == "__main__":
            self.mainloop()

    def has_been_initialized(self):
        return self.initialized

    #******************************************************************************************************************************
    def repopulate_grid(self, col_list, row_list, values_list=[]):
        '''Function repopulate_grid() is called when the Entry grid is re-drawn with new values.  This happens all the time, because the grid is first drawn with empty cells, which are over-written after the user chooses a Data Dictionary file.
        NOTE: repopulate_grid() is typically called by the CALLING OBJECT.'''	
        self.clear_arrays()    #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_arrays() deletes these class properties.
        self.clear_grid()    #This must be executed BEFORE the row and column lists are loaded in as class properties, because clear_arrays() deletes these class properties.
        self.col_list = col_list[:]
        self.col_list.insert(0, "")  
        self.row_list = row_list[:]
        self.values_list = values_list[:]
		#Note: the row_list contains one row for every CURRENTLY POPULATED row in the grid. But the user might populate additional rows, which will NOT be reflected in row_list (or any updates) unless row_list AND cell_widgets are expanded to encompass all the rows that are at the user's disposal.
        print("\nRow_list has %s items. values_list has %s items. Num_initial_rows is %s" % (len(self.row_list), len(values_list), self.num_initial_rows))
        if len(self.row_list) < self.num_initial_rows:
            if self.debug: print("ADDING rows to self.row_list.")
            ir = 0
            for ir in range(len(self.row_list), self.num_initial_rows-1):
                if self.debug: print("Adding to row_list: %s" % (ir +1))
                self.row_list.append(ir)
        if len(self.values_list) < self.num_initial_rows:
            print("ADDING rows of lists to self.values_list.")
            tmpvals = []
            for col in self.col_list:
                tmpvals.append('')
            ir = 0
            for ir in range(len(self.values_list), self.num_initial_rows-1):
                if self.debug: print("Adding to values_list: %s" % (ir +1))
                self.values_list.append(tmpvals)

        #Make sure self.cell_widgets is expanded if necessary to hold the values passed in as self.values_list
        print(\n\nLen(cell_widgets): %s, Len(self.col_list): %s, num_initial_rows: %s, Len(col_list) * num_initial_rows: %s:" % (len(cell_widgets), len(self.col_list), self.num_initial_rows, (len(col_list) * num_initial_rows)   ) )
        if len(self.cell_widgets) < (len(self.col_list) * self.num_initial_rows):
            if self.debug: print("ADDING cells to self.cell_widgets.")
            for r in range(0, len(self.row_list)):
                for c in range(1, len(self.col_list)):
                    cellvalue = StringVar()
                    cellvalue = ""
                    #if len(values_list) > 0:
                    #    cellvalue = values_list[r][c-1]			#The values that will be copied into this cell from the "values_list" LIST OF LISTS.
                    #else:
                    #    cellvalue = ""
                    #cellvalue = cellvalue.replace("\n", "")
                    #cellvalue = cellvalue.replace(chr(10), "")
                    #cellvalue = cellvalue.replace(chr(13), "")
                    #print ("c: %s, r: %s ... cell value: %s" % (str(c), str(r), str(cellvalue) ) )
                    #Create the Entry widget which will display the value:
                    w = EntryWidget(self, c, r+1, cellvalue, background=self.entry_bgcolor, fg=self.entry_fontcolor, self.grid_config_dict)
                    self.grid_values[(c-1, r)] = w.value
        if self.debug: 
            print("\n Column list:")
            print(self.col_list)
            print("\n Row list:")
            print(self.row_list)
        #Create row and column headers along top and left:		
        print ("\n In TkEntry.repopulate_grid(), ABOUT TO CALL repopulate_column_headings():  len(col_list)=" + str(len(self.col_list)) + ", len(row_list)=" + str(len(self.row_list)) + ", len(values_list)=" + str(len(self.values_list)) + "\n")
        self.repopulate_column_headings()
        #Import the values submitted as values_list, and use those values to update the Entry objects referenced in the cell_widgets list. 
        #NOTE: each item in the values_list is itself a list of cell values - so the item represents a row of cells.
        print("\n **********************************************")
        print("RE-POPULATING CELL_WIDGETS LIST FROM values_list")
        #Note that the re-population is based on rows and columns in the NEW array.  But this can leave old cells still populated OUTSIDE the bounds of the new array, so clear them first with clear_arrays().
        #Also, if the new array is wider than the old, but not as deep, it will create new columns on the right, but populate them for only as many rows as the NEW array requires.  This can leave holes in the grid, which is distracting to the user, if nothing else.
        #So it's best to make note of how many Entry widget rows and columns were created by the PREVIOUS run, so we can fill in the gaps if needed.
        r = 1      #cell_widgets list starts at 1 for both rows and columns (x and y) because row 0 is headers and column 0 is rownums.
        for newrow in self.values_list:
            c = 1
            for newcol in newrow:
                newvalue = str(newcol)
                #Find the correct element in cell_widgets where the X attribute = c, and the Y attribute = r.
                #print("Seeking x=%s and y=%s ... new value is %s" % (str(r), str(c), newvalue ) )
                found = False
                for cell in self.cell_widgets:
                    #When we find the correct Entry object in the cell_widgets list, update its value to reflect the newly-submitted values_list.
                    #print("FOUND: X: %s Y: %s Current cell value: %s, new cell value: %s" % (str(cell["x"]), str(cell["y"]), str(cell["object"].value.get()), newvalue  ) )
                    if str(cell["x"]) == str(c) and str(cell["y"]) == str(r):
                        #if self.debug: print("FOUND: X: %s Y: %s Current cell value: %s, New cell value: %s" % (str(cell["x"]), str(cell["y"]), str(cell["object"].value.get()), newvalue ) )
                        cell["object"].value.set(newvalue)
                        cell["object"].grid(column=c, row=r)
                        w = cell["object"]
                        self.grid_values[(c-1, r)] = w.value
                        if self.debug: print("AFTER: X: %s Y: %s Cell value: %s" % (str(cell["x"]), str(cell["y"]), str(cell["object"].value.get())))
                        found = True
                        break
                if found == False:
                    #Create the Entry widget which will display the value:
                    #print("\n New grid value '%s' not found. Creating a new cell to hold this value at %s, %s" % (newvalue, c, r) )
                    w = EntryWidget(self, c, r, newvalue, background=self.entry_bgcolor, fg=self.entry_fontcolor)
                    self.grid_values[(c,r)] = w.value
                c += 1
            r += 1
        print("\n Display Arrays:")
        self.debug_display_arrays()

    def make_header(self):
        self.hdrDict = {}
        if self.debug: print ("\n In TkEntry.make_header(), len(col_list)=" + str(len(self.col_list)) + ", len(row_list)=" + str(len(self.row_list)) + ", len(values_list)=" + str(len(self.values_list)) + "\n")
        kw_hdr = {"readonlybackground":self.label_bgcolor, "background":self.label_bgcolor, "fg":self.label_fontcolor }
        #Create column labels along top of grid
        for i, label in enumerate(self.col_list):
            if i == 0:
                self.widget_type = "row_label"               #Width of the first column (which usually displays row numbers) is different from the remaining columns.
                kw_hdr["width"] = self.get_column_width(self.widget_type, **kw_hdr)
            else:
                self.widget_type = "column_label"
            kw_hdr["width"] = self.get_column_width(self.widget_type, **kw_hdr)
            w = LabelWidget(self, i, 0, label, **kw_hdr)
            self.hdrDict[(i,0)] = w
            if i == 0:                                       #Done with the first cell (0,0) which needs to be only as wide as the other Row Label cells.
                kw_hdr["width"] = None                       #If a "width" key occurs in the **kwargs, get_column_width() accepts it as the valid width--so reset the Width in **kwargs
            #w.bind(sequence="<KeyRelease>", func=handler)

        #Now create row labels along left side of grid
        self.widget_type = "row_label"
        kw_hdr["width"] = self.get_column_width(self.widget_type, **kw_hdr)
        for i, label in enumerate(self.row_list):
            w = LabelWidget(self, 0, i+1, label, **kw_hdr)          #width=max_rowlabel_width, readonlybackground=self.label_bgcolor, background=self.label_bgcolor, fg=self.label_fontcolor
            self.hdrDict[(0,i+1)] = w
            #w.bind(sequence="<KeyRelease>", func=handler)

    def get_column_width(self, coltype=None, **kw):
        ''' ''' 
        colwidth = 0
        if str(coltype).lower().strip() == "row_label":
            if not self.rowlabel_column_width:
                self.rowlabel_column_width = self.calc_rowlabel_column_width()
            colwidth = self.rowlabel_column_width
        else:
            found_in_kwargs = False
            if self.check_key_exists("width", **kw):
                if kw["width"]:
                    found_in_kwargs = True
            if found_in_kwargs:
                colwidth = kw["width"]
            elif self.column_width:
                colwidth = self.column_width
            else: 
                colwidth = gl_colwidth
        return colwidth

    def calc_rowlabel_column_width(self):
        '''The left-most column is typically reeserved for a row label, such as the row number. It should be no wider than necessary.'''
        max_width = 0
        for i, label in enumerate(self.row_list):
            label_width = len(str(label).strip())
            if label_width > max_width:
                max_width = label_width
        self.rowlabel_column_width = max_width + 4
        return max_width + 4        

    def repopulate_column_headings(self):
        kw_hdr = {"readonlybackground":self.label_bgcolor, "background":self.label_bgcolor, "fg":self.label_fontcolor }
        for i, label in enumerate(self.col_list):
            if i == 0:
                self.widget_type = "row_label"               #Width of the first column (which usually displays row numbers) is different from the remaining columns.
                kw_hdr["width"] = self.get_column_width(self.widget_type, **kw_hdr)
            else:
                self.widget_type = "column_label"
            kw_hdr["width"] = self.get_column_width(self.widget_type, **kw_hdr)

            #The array used to re-populate the grid might be larger than the existing grid -- in which case we need to enlarge the grid.
            if len(self.hdrDict) < i:   
                obj = self.hdrDict[(i,0)]
                obj.delete(0, END)
                obj.text.set(label)
            else:                                    #The array used to store header values is NOT long enough to accommodate the next column - so create a new cell
                w = LabelWidget(self, i, 0, label, **kw_hdr) 
                self.hdrDict[(i,0)] = w
            if i == 0:                                       #Done with the first cell (0,0) which needs to be only as wide as the other Row Label cells.
                kw_hdr["width"] = None                       #If a "width" key occurs in the **kwargs, get_column_width() accepts it as the valid width--so reset the Width in **kwargs

    def retrieve_grid_values(self):
        '''Traverse the cells of this Tkinter Entry grid and copy the values of each cell into an array.
        NOTE: this function is typically called by the CALING OBJECT.'''
        print("\n **********************************************")
        print("CELL WIDGET TEXT PROPERTIES:")
        row_values = []
        y_row = 1
        for y_row in range(1, self.num_initial_rows):
        #for y_row in range(1, len(self.row_list)+1):
        #for cell in self.cell_widgets:
            #print("X: %s Y: %s Cell value: %s" % (str(cell["x"]), str(cell["y"]), str(cell["object"].value.get())))
            row_values = []								#Populate another list with all values from this ROW.
            x_col = 1
            for x_col in range(1, len(self.col_list)):
                cell_value = self.get_cell_value(x_col, y_row)
                if self.debug: print("X: %s Y: %s Cell value: %s" % (x_col, y_row, cell_value) )
                row_values.append(cell_value)
                x_col += 1
            y_row += 1
            self.meta_values_after_edit.append(row_values)
        #View the results:
        for row in self.meta_values_after_edit:
            #pass
            print("\n Next row:")
            for col in row:
                print(col)
        
        return self.meta_values_after_edit

    def get_cell_value(self, x, y):
        return_value = ''
        for cell in self.cell_widgets:
            #print("Seeking %s, %s... cell.X: %s cell.Y: %s Cell value: %s ...Orig value: %s ... StringVar: %s" % (str(x), str(y), str(cell["x"]), str(cell["y"]), str(cell["object"].value.get()), str(cell["orig_value"]), str(cell["StringVar"]) ))
            if int(cell["x"]) == x:
                if int(cell["y"]) == y:
                    return_value = str(cell["object"].value.get())
                    if self.debug: print("return value: %s" % (return_value))
                    break
        return return_value

    def count_previous_grid_cells(self):
        max_x = max_y = 0
        for cell in self.cell_widgets:
            max_x = x
            max_y = y
        previous_row_count = max_y + 1
        previous_column_count = max_x + 1
        max = {"x":max_x, "y":max_y}
        return max

    def clear_all(self):
        self.clear_arrays()
        self.clear_grid()

    def clear_arrays(self):
        if self.col_list is not None and self.row_list is not None and self.values_list is not None:
            colcount = 0
            rowcount = 0
            if self.col_list: 
                colcount = len(self.col_list)
                self.col_list = []
                for i in range(0, colcount):
                    self.col_list.append('')
            if self.row_list:
                rowcount = len(self.row_list)
                self.row_list = []				
                for i in range(0, rowcount):
                    self.row_list.append('')
            #NOTE: values_list is a LIST OF LISTS, so each member has TWO subscripts: [0],[0],  [0],[1], etc.
            if self.values_list:
                self.values_list = []
                for j in range(0, rowcount):
                    meta_temp = []
                    for i in range(0, colcount):
                        meta_temp.append('')
                    self.values_list.append(meta_temp)

            print ("\n At END of TkEntry.clear_arrays(), before initialize_grid is called, len(col_list)=" + str(len(self.col_list)) + ", len(row_list)=" + str(len(self.row_list)) + ", len(values_list)=" + str(len(self.values_list)) + "\n")
            #self.debug_display_arrays()
            #self.initialize_grid(self.col_list, self.row_list, self.values_list)


    def clear_grid(self):
        if self.cell_widgets:
            for cell in self.cell_widgets:
                x = cell["x"]
                y = cell["y"]
                #print("CLEARING: X: %s Y: %s Current cell value: %s" % (str(cell["x"]), str(cell["y"]), str(cell["object"].value.get()) ) )
                cell["object"].value.set('')
                cell["object"].grid(column=x, row=y)

    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found

    '''def __entryhandler(self, col, row):
        #pass
        s = self.grid_values[(col,row)].get()
        if s.upper().strip() == "EXIT":
            self.destroy()
        elif s.upper().strip() == "DEMO":
            self.demo()
        elif s.strip():
            print(s) '''
 
    '''def demo(self):
        #pass
        enter a number into each Entry field 
        for i in range(len(self.cols)):
            for j in range(len(self.row_list)):
                sleep(0.25)
                self.set(i,j,"")
                self.update_idletasks()
                sleep(0.1)
                self.set(i,j,i+1+j)
                self.update_idletasks()
        '''
    def debug_display_arrays(self):
        i = 0
        print("col_list:")
        for col in self.col_list:
            print(str(i) + "  " + str(col))
            i += 1

        i = 0
        print("row_list:")
        for int in self.row_list:
            print(str(i) + "  " + str(int))
            i += 1

        i = 0
        print("values_list:")
        for childarray in self.values_list:
            print(str(i) + "  " + str(childarray))
            i += 1

        i = 0
        #print("cell_widgets:")
        #for cell in self.cell_widgets:
        #    print("(%s)  cell_widgets -- x: %s  y: %s  value: %s" % (str(i), str(cell["x"]), str(cell["y"]), str(cell["object"].value.get()) ) )   #%s   , str(cell)
        #    i += 1
		
		
    #def __headerhandler(self, col, row, text):
    #    ''' has no effect when Entry state=readonly '''
    #    self.hdrDict[(col,row)].text.set(text)
 
    def get(self, x, y):
        return self.grid_values[(x,y)].get()
 
    def set(self, x, y, v):
        self.grid_values[(x,y)].set(v)
        return v
 
if __name__ == "__main__":
    root = Tk()
    show_grid = True
    kw_grid = {}
    cols = ['A', 'B', 'C', 'D']
    rows = ['1', '2', '3', '4']
    app = EntryGrid(root, cols, rows, show_grid, **kw_grid)

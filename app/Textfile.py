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
import shutil
from os import path
from FilePath import *
from DataDict import *

gl_frame_color = "ivory"

#******************************************************************************************
class TextFile():
    debug = True
    error_message = None
    controller = None                       #Controller is the BigMatchController class in main.py 
    csv_file = None
    text_file = None
    text_file_datadict_list = None
    text_file_datadict_file = None
    datadict_column_headers = None
    csv_column_headers = []
    startpos_of_current_textfile_column = None    #This is used to continuously update the starting position of the next data column
    columns_to_widen = []
    spaces_added_so_far = 0
    max_linewidth = 0

    def __init__(self):
        self.debug = True

    def convert_csv_to_flat_text(self, csv_file, output_file):
        if not csv_file:
            self.error_message = "No CSV file was specified"
            print("\n\n ERROR: " + self.error_message)
            return self.error_message
        self.csv_file = csv_file
        self.text_file = output_file
        with open(csv_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')  #, quotechar='')
            count = 0
            for row in csvreader:
                if count == 0:
                    self.build_column_header_list(row)
					
                print(row[0] + " " +row[7] + " " +row[8] + " " +row[9] + " " +row[10] + " " +row[11] + " " +row[12] + " " +row[13] + " " +row[14] + " " +row[15] + " " +row[16] + " " +row[17] + " " +row[18] + " " +row[19] + " " +row[20] + " " +row[21] )
                count += 1
                if count > 50:
                    break
            csvfile.close()

        self.get_max_widths_for_columns()

        #print("\n Column Headers AFTER max called:")
        #for col in self.csv_column_headers:
        #    print(col)

        self.write_flat_text_file(output_file)

        self.create_data_dict_for_text_file()

    def build_column_header_list(self, hdr_row):
        checked = 0
        col_index = 0
        for col_hdr in hdr_row:
            #In this test case, explicitly choose specific columns to be included in the export.  But in future, give the user a way to select the columns they want to export.
            if col_index < 23:
                checked = 1
            else:
                checked = 0
            col_hdr = col_hdr.strip()
            print("(%s) col_hdr: %s" % (col_index, col_hdr) )
            temp = {"col_index":col_index, "col_hdr":col_hdr, "max_width":0, "start_pos":0, "data_type":"", "selected":checked}
            self.csv_column_headers.append(temp)
            col_index += 1
            

    def get_max_widths_for_columns(self):
        col_index = 0
        max_width = 0
        self.startpos_of_current_textfile_column = 1
        for col in self.csv_column_headers:
            if str(col["selected"]) == "1":
                col_index = col["col_index"]
                #BEFORE we move on to the next selected column, calculate its STARTING POSITION, based on the summed column-widths of all previous columns.
                self.csv_column_headers[col_index]["start_pos"] = self.startpos_of_current_textfile_column    #Update the master list of Columns -- ADD A SPACE AT END OF EACH COLUMN FOR READABILITY
                #Now get the max_width of the current column:				
                max_width = self.get_max_width_for_column(col_index)
                max_width = max_width +1                                          #ADD A SPACE AT END OF EACH COLUMN FOR READABILITY
                self.csv_column_headers[col_index]["max_width"] = max_width       #Update the master list of Columns 
                txt = col["col_hdr"].ljust(20)
                print("ColIndex: %s Caption: %s Width: %s, Startpos: %s" % (col_index, txt, max_width, self.startpos_of_current_textfile_column))
                self.startpos_of_current_textfile_column += (max_width)
            
    def get_max_width_for_column(self, col_index):
        max_width = 0
        with open(self.csv_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',') 
            count = 0
            for row in csvreader:
                if count > 0:
                    cell = str(row[col_index]).strip()
                    if len(cell) > max_width:
                        max_width = len(cell)
                count += 1
            csvfile.close()
        return max_width           
	
    def write_flat_text_file(self, output_file):
        with open(self.csv_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')  #, quotechar='')
            count = 0
            with open(output_file, 'w') as textfile:
                for row in csvreader:
                    #print("ROW %s" % (count) )
                    textrow = ""
                    if count > 0:   #Exclude the header row
                        for col in self.csv_column_headers:
                            if str(col["selected"]) == "1":
                                col_index = col["col_index"]
                                max_width = int(col["max_width"])
                                val = str(row[col_index]).strip()
                                #print("Writing column %s of row %s, value %s" % (col_index, count, val) )
                                #textfile.write(val.ljust(max_width))
                                textrow = textrow + val.ljust(max_width)
                        textfile.write(textrow + "\n")
                        #textfile.write("\n")
                    count += 1
                textfile.close()
            csvfile.close()


    def create_data_dict_for_text_file(self):
        self.text_file_datadict_list = []       #text_file_datadict_list is the list of lists (a list of CSV rows comprising the Data Dictionary for the text file being created).  It can be written to the CSV file using csvwriter.writerows(list)
        datadict = DataDict_Model(self, self)   #BigMatch DataDict class
        hdr_list = datadict.load_standard_datadict_headings()    #Make sure we are using the standard, updated list of column headings for the Data Dictionary
        datadict = None                         #Erase the class instantiation when done to release memory
        #Check our assumptions about which Data Dictionary column headings are in the standard:		
        if not "column_name" in hdr_list:
            self.error_message = "Expected item 'column_name' to be in Data Dictionary header row"
        if not "start_pos" in hdr_list:
            self.error_message = "Expected item 'start_pos' to be in Data Dictionary header row"
        if not "width" in hdr_list:
            self.error_message = "Expected item 'width' to be in Data Dictionary header row"
        if not "unique_id" in hdr_list:
            self.error_message = "Expected item 'unique_id' to be in Data Dictionary header row"
        if not "bigmatch_format" in hdr_list:
            self.error_message = "Expected item 'bigmatch_format' to be in Data Dictionary header row"
        if self.error_message:
            print("\n \n ERROR: " + self.error_message)
        self.build_dict_of_datadict_column_headers(hdr_list)
        for col in self.csv_column_headers:
            if str(col["selected"]) == "1":        #The user has selected this column in the data CSV being converted to flat text file.
                row = []                           #List of value for the data dict CSV row
                for ix in range(0, len(self.datadict_column_headers)):      #Starting with 0, find the values for each column in this data dict ROW.
                    colhdr_name = self.datadict_column_headers[ix]          #Get the name of the next data dict column header in the standard arrangement
                    #Find the value for this row:
                    if colhdr_name == "column_name":
                        row.append(col["col_hdr"])
                    elif colhdr_name == "start_pos":
                        row.append(col["start_pos"])
                    elif colhdr_name == "width":
                        row.append(col["max_width"])
                    elif colhdr_name == "unique_id":
                        row.append("")
                    elif colhdr_name == "bigmatch_format":
                        row.append("uo")
                    elif colhdr_name == "data_format":
                        row.append("")
                    elif colhdr_name == "comments":
                        row.append("")
                self.text_file_datadict_list.append(row)
                    
        #Write the Data Dictionary attributes to a CSV file:
        if not self.text_file_datadict_file:
            self.text_file_datadict_file = self.csv_file.replace(".csv", ".dict.csv")
        with open(self.text_file_datadict_file, 'w') as dictfile:
            csvwriter = csv.writer(dictfile, delimiter=',')
            #csvwriter.writerows(self.text_file_datadict_list)
            #First write the data dict column headers:
            csvwriter.writerow(hdr_list)
            #Now write out one ROW for every selected COLUMN from the CSV being converted.
            for dictrow in self.text_file_datadict_list:
                csvwriter.writerow(dictrow)
            print("\n Data Dictionary:")
            for col in self.text_file_datadict_list:
                print(col)
            dictfile.close()

    def build_dict_of_datadict_column_headers(self, hdr_list):
        self.datadict_column_headers = {}
        for hdr in hdr_list:
            index = hdr_list.index(hdr)
            self.datadict_column_headers[index] = hdr
        print("DataDict headers columns:")
        for hdrcol in self.datadict_column_headers:
            print(hdrcol)
 
    def widen_columns_in_fixed_width_textfile(self, columns_to_widen=None, text_file=None, data_dict=None, output_file=None):
        print("\n Top of function widen_columns_in_fixed_width_textfile()... Type of columns_to_widen=%s, length is %s" % (str(type(columns_to_widen)), len(columns_to_widen) ) )
        if columns_to_widen is None:
            columns_to_widen = self.columns_to_widen
        else:
            self.columns_to_widen = columns_to_widen
        if text_file is None:
            text_file = self.text_file
        if output_file is None:
            ext = text_file.strip().lower()[-4:]
            print("\n EXT is: " + ext)
            output_file = text_file.strip().lower().replace(ext, "_newfldwidths" + ext)
        if data_dict is None:
            data_dict = self.text_file_datadict_file
        else:
            if self.text_file_datadict_file	is None:
                self.text_file_datadict_file = data_dict

        #TO DO: check that all required file names and column attributes are provided before proceeding. Raise error if not.
        #For every column specified, call the function to widen it:
        self.spaces_added_so_far = 0
        for col in self.columns_to_widen:
            print(col)
            self.widen_column_in_fixed_width_textfile(col["column_name"], col["num_chars_to_add"], col["startpos"], col["width"], text_file, output_file)
        if self.error_message:
            print("\n \n ERROR: %s" % (self.error_message) )
 
    def widen_column_in_fixed_width_textfile(self, column_name, num_chars_to_add, start_pos=None, width=None, text_file=None, data_dict=None, output_file=None):
        if text_file is None:
            text_file = self.text_file
        ext = text_file.strip().lower()[-4:]
        temp_file = text_file.strip().lower().replace(ext, "_temp" + ext)
        if output_file is None:
            output_file = text_file.strip().lower().replace(ext, "_newfldwidths" + ext)
        if start_pos is None or width is None:
            column_attribs = self.get_column_startpos_and_length(column_name, data_dict)
            start_pos = column_attribs["startpos"]
            width = column_attribs["width"]
        print("\n In widen_column_in_fixed_width_textfile(), widening '%s' by %s columns... spaces_added_so_far: %s" % (column_name, num_chars_to_add, self.spaces_added_so_far) )
        #Widen the field.  
        #NOTE: This function triggers a CREATION or OVERWRITE of the output file.  To support multiple column widenings, we need to save the changes each time to a temp file which reflects all changes made to date--and then copy the temp file contents into the output file.
        if self.spaces_added_so_far == 0:                  #This is the first column to be widened
            shutil.copyfile(text_file, output_file)        #Copy the source (original) data file to output file
        count = 1
        self.max_linewidth = 0
        with open(output_file, 'rb') as outputfile:
            with open(temp_file, 'w', newline='', encoding='utf8') as tempfile:
                for line in outputfile:
                    #if count > 1000:
                    #    break
                    textrow_start = str(line)[:start_pos + self.spaces_added_so_far + 1]
                    colvalue = str(line)[start_pos + self.spaces_added_so_far + 1 : start_pos + self.spaces_added_so_far + width].strip().ljust(width + num_chars_to_add)
                    textrow_end = str(line)[start_pos + self.spaces_added_so_far + 1 + width : ]
                    #WRITE THE OUTPUT ROW:
                    newrow = str(textrow_start) + str(colvalue) + str(textrow_end)
                    newrow = str(newrow).replace("b'", "")
                    newrow = str(newrow).replace('b"', '')
                    if len(newrow) > self.max_linewidth:
                        self.max_linewidth = len(newrow)
                    tempfile.write(newrow)     #.encode('utf-8')
                    tempfile.write("\n")
                    #print("ROW %s:   %s" % (count, newrow) )
                    if str(count)[-2:] =="00":
                        print("ROW %s" % (count) )
                    count += 1
                outputfile.close()
                shutil.copyfile(temp_file, output_file)        #Copy the temp data file to output file (which is the final result the user will now resume processing)
                tempfile.close()
        os.remove(temp_file)
        self.spaces_added_so_far += num_chars_to_add

    def get_column_startpos_and_length(self, column_name, data_dict=None):
        column_name = str(column_name).lower().strip()
        if data_dict is None:
            data_dict = self.text_file_datadict_file
        #Get the column indices for column_name, start_pos and width in the data dict
        coldict = self.locate_crucial_datadict_columns(data_dict)
        column_attribs = {}
        with open(data_dict, 'rt') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            row_index = 0
            for row in csvreader:
                columnname_text = str(row[coldict["column_name"]]).lower().strip()
                if columnname_text == column_name:     #We found the correct row in the data dict, the row that specifies information about the requested Column_Name
                    column_attribs["startpos"] = row[coldict["startpos"]]
                    column_attribs["width"] = row[coldict["width"]]
                    break
            csvfile.close()
        print("At end of get_column_startpos_and_length(), column_attribs:")
        print(column_attribs)
        return column_attribs

    def locate_crucial_datadict_columns(self, data_dict=None):
        '''docstring '''
        if data_dict is None:
            data_dict = self.text_file_datadict_file
        else:
            if self.text_file_datadict_file	is None:
                self.text_file_datadict_file = data_dict
        coldict = {}
        #Traverse header columns of the Data Dictionary until we locate the column_name, start_pos, and width columns--then return their column indices.
        with open(data_dict, 'rt') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            row_index = 0
            column_index = 0
            colname_column = None
            startpos_column = None
            width_column = None
            for row in csvreader:
                if(row_index == 0):       #Top (header) row in the Data Dictionary CSV
                    print("*****locate_crucial_datadict_columns(): row[0] = " + str(row[0]) + " mem_or_rec: " + mem_or_rec + "***")
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
                        column_index += 1
                        break         #Automatically break after the first ROW in the file
            csvfile.close()
        coldict["column_name"] = colname_column
        coldict["startpos"] = startpos_column
        coldict["width"] = width_column
        print("\n colname_column: %s, startpos_column: %s, width_column: %s, uniqid_column: %s" % (colname_column, startpos_column, width_column) )
        if coldict["column_name"] is not None and coldict["startpos"] is not None and coldict["width"] is not None:
            success = True
        else:
            self.error_message = "Data dictionary attributes were not successfully populated."
        if self.error_message is not None:
            print("\n Error: %s \n" % (self.error_message))

        return coldict


#******************************************************************************************		
#******************************************************************************************		
def main():
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    '''Geometry for all windows in this app is set by main.py '''
    master = TextFile()
    columns_to_widen = []	
    coldict={"column_name":"street_number", "startpos":112, "width":6, "num_chars_to_add":3}
    columns_to_widen.append(coldict)
    coldict={"column_name":"street_direction", "startpos":118, "width":2, "num_chars_to_add":3}
    columns_to_widen.append(coldict)
    coldict={"column_name":"street_name", "startpos":120, "width":20, "num_chars_to_add":6}
    columns_to_widen.append(coldict)
    coldict={"column_name":"suffix", "startpos":140, "width":5, "num_chars_to_add":7}
    columns_to_widen.append(coldict)
    master.widen_columns_in_fixed_width_textfile(columns_to_widen, "C:\\Greg\\Data\\Building_Permits_0_5k_Test.txt", "C:\\Greg\\Data\\Building_Permits_0_5k.dict.csv")
    #master.convert_csv_to_flat_text("c:\greg\data\Building_Permits_0_5k.csv", "c:\greg\data\Building_Permits_0_5k.txt")

if __name__ == "__main__":
    main()  

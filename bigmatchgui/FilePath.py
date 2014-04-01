#!C:\Python33\python.exe -u
#!/usr/bin/env python
'''http://stackoverflow.com/questions/16429716/opening-file-tkinter '''
''' python c:\greg\code\python\Gms_TkFileSystem5_try_button.py '''  
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from TkEntry import EntryGrid
import os 
from os import path

gl_frame_color = "ivory"
gl_frame_width = 400
gl_frame_height = 100
gl_file_textbox_width = 110

#*****************************************************************************************		
class FilePath_Model():
    debug = True
    error_message = None
    parent_window = None	
    controller = None          #Controller is the BigMatch MAIN class file
    master = None              #Master is the object needing to locate a file.  This might be the DataDict class, the BlockingPass class or another object.
    file_types = []
    file_name = None
    file_path = None
    file_name_with_path = None
    view_object = None
    initial_dir = None
    title = ''
    bgcolor = ''
    frame_width = None
    frame_height = None
    show_view = None
    open_or_save_as = 'open'   #open_or_save_as specifies whether this FilePath dialog will open an existing file (tkinter "askopenfilename"), or prompt user to "Save As..." (tkinter "asksaveasfilename")
    file_category = None       #Examples: 'DataDict', 'ParmFile', 'MatchResult'
    alias = ''                 #Many instances of this class might be visible at any given time, and it's difficult to tell which one is executing what code without some kind of label that can be output for debugging.

    def __init__(self, parent_window, master, controller, title='', open_or_save_as='open', alias='', file_types=[('All files', '*'),('Text files', '*.csv;*.txt;*.dat')], **kw):      #bgcolor=gl_frame_color, file_types=[('All files', '*'),('Text files', '*.csv;*.txt')], frame_width=gl_frame_width, frame_height=gl_frame_height
        if parent_window:
            self.parent_window = parent_window
        if master:
            self.master = master            #Master is the object needing to locate a file.  This might be the DataDict class, the BlockingPass class or another object.
        if controller:
            self.controller = controller    #Controller is the BigMatchController class in main.py 
        if title:
            self.title = title
        if open_or_save_as:
            self.open_or_save_as = open_or_save_as    #open_or_save_as specifies whether this FilePath dialog will open an existing file (tkinter "askopenfilename"), or prompt user to "Save As..." (tkinter "asksaveasfilename")
        if alias:
            self.alias = alias
        if not self.file_types:
            self.file_types = [('All files', '*'), ('Text files', '*.csv;*.txt;*.dat')]
        #kwargs:
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
        if self.check_key_exists("initial_dir", **kw):
            self.initial_dir = str(kw["initial_dir"])
        if self.initial_dir is None:
            if self.controller.dir_last_opened:
                self.initial_dir = self.controller.dir_last_opened
            else:
                self.initial_dir = os.path.dirname(os.path.realpath(__file__))       #Do not leave initial_dir empty because it causes an error in the open_file dialogs
        if self.check_key_exists("file_category", **kw):
            self.file_category = kw["file_category"]
        print("\n FILE TYPES FOR OPEN FILE DIALOG: (type is: %s" % (str(type(self.file_types)) ) )
        print(self.file_types)

    def update_filepath_display(self, file_name_with_path):
        '''When the user selects a file, display the file name and path in the Tk Entry box '''
        self.file_name_with_path = file_name_with_path
        self.view_object.textbox.configure(state=NORMAL)                    #Entry widget's state must be NORMAL in order to write or delete.  But we need it to stay in "readonly" mode at all other times.  This is because if we allow the user to enter in a file name, this does not trigger the events that are triggered by the "Browse" button, and those events are crucial.
        self.view_object.textbox.delete(0, END)   #does not seem to work?
        self.view_object.textbox.insert(END, self.file_name_with_path)
        self.view_object.textbox.configure(state="readonly")                #Entry widget's state must be NORMAL in order to write or delete.  But we need it to stay in "readonly" mode at all other times.  This is because if we allow the user to enter in a file name, this does not trigger the events that are triggered by the "Browse" button, and those events are crucial.

    def locate_file(self, file_types=[('All files', '*'), ('Text files', '*.csv;*.txt')], notify_master=True, callback_string=''):
        '''See display_user_buttons() below in View.  The buttons call either locate_file() or save_as_file(), depending on whether the user is loading or saving to a file. '''
        #file_types = [('All files', '*'), ('Data files', '*.dat'), ('Text files', '*.csv;*.txt')]
        file_name_with_path = tkinter.filedialog.askopenfilename(parent=self.parent_window, filetypes=self.file_types, title='Choose a file', initialdir=self.initial_dir)    #initialdir=self.current_dir
        if file_name_with_path != '' and file_name_with_path is not None:
            self.file_name_with_path = file_name_with_path
            print("\n" + "In locate_file, file_name_with_path = '" + file_name_with_path + "'")
            if self.view_object is None:
                self.display_view() 
            self.update_filepath_display(file_name_with_path)    #Refresh the textbox displaying the selected file
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head               #Store the path last opened by the user and set this as a default starting point for FileOpen dialogs
            if notify_master:                #A FileOpen dialog normally serves the purposes of another class, such as Data Dict or BlockingPass. The Master class needs to know when the user selects a file.
                print("Notifying the master object that the user has selected a new file: %s" % (file_name_with_path) )
                if callback_string == '':
                    callback_string = "load, " + self.alias 
                self.master.update_filepath(file_name_with_path, callback_string, self.alias)
        return file_name_with_path

    def save_as_file(self, file_types=[('All files', '*'), ('Text files', '*.csv;*.txt')], notify_master=True, callback_string=''):
        '''See display_user_buttons() below in View.  The buttons call either locate_file() or save_as_file(), depending on whether the user is loading or saving to a file. '''
        file_name_with_path = tkinter.filedialog.asksaveasfilename(parent=self.parent_window, filetypes=self.file_types, title='Choose a file', initialdir=self.initial_dir)    #initialdir=self.current_dir
        if file_name_with_path != '' and file_name_with_path is not None:
            self.file_name_with_path = file_name_with_path
            print("\n" + "In save_as_file, self.file_name_with_path = '" + self.file_name_with_path + "'")
            if self.view_object is None:
                self.display_view()  
            self.update_filepath_display(self.file_name_with_path)  #Refresh the textbox displaying the selected file
            head, tail = os.path.split(file_name_with_path)
            self.controller.dir_last_opened = head               #Store the path last opened by the user and set this as a default starting point for FileOpen dialogs
            if notify_master:                #A FileOpen dialog normally serves the purposes of another class, such as Data Dict or BlockingPass. The Master class needs to know when the user selects a file.
                print("Notifying the master object that the user has selected a new file: %s" % (file_name_with_path) )
                if callback_string == '':
                    callback_string = "save_as, " + self.alias 
                self.master.update_filepath(file_name_with_path, callback_string, self.alias)      #Alert the parent module (datadict, blockingpass, etc.) that a file name/path was changed!
        return file_name_with_path

    def clear_file(self):
        self.file_name_with_path = ""
        self.update_filepath_display("")         #Refresh the textbox displaying the selected file
        callback_string = self.open_or_save_as
        self.master.update_filepath("", callback_string)   #Alert the parent module (datadict, blockingpass, etc.) that a file name/path was changed!

    def instantiate_view_object(self, container):
        self.view_object = FilePath_View(container, self) 

    def display_view(self, container=None, open_or_save_as=None):
        #open_or_save_as specifies whether this FilePath dialog will open an existing file (tkinter "askopenfilename"), or prompt user to "Save As..." (tkinter "asksaveasfilename")
        if open_or_save_as:
            self.open_or_save_as = open_or_save_as
        else:
            open_or_save_as = self.open_or_save_as
        if open_or_save_as is None:
            open_or_save_as = "open"
            self.open_or_save_as = open_or_save_as
        if container == None:
            container = self.controller.bigcanvas.bigframe			#default objects on which other widgets are displayed.
        if self.view_object is None:
            self.instantiate_view_object(container)
        self.view_object.initUI(open_or_save_as, background=self.bgcolor, borderwidth=2, padx=0, pady=0)   #DISPLAY THE FRAME OBJECT ON SCREEN
		
    def check_key_exists(self, keyvalue, **kw):
        found = False
        #print("Checking for key '%s' in **Kwargs" % (keyvalue) ) 
        for key, value in kw.items():
            if str(key).lower() == str(keyvalue).lower():
                found = True
                break
        #print("Checking for key '%s' in **Kwargs -- Found? %s" % (str(keyvalue), str(found) ) ) 
        return found

	
#*****************************************************************************************	
class FilePath_View(Frame):
    debug = True
    container = None
    model = None
    label_object = None
    textbox = None

    def __init__(self, container, model):      #title='File location: ', bgcolor=gl_frame_color, file_name_with_path='', frame_width=gl_frame_width, frame_height=gl_frame_height):
        Frame.__init__(self, container)
        self.container = container		
        self.model = model
        self.file_textbox_width = gl_file_textbox_width
        #Display the frame:
        #if self.model.show_view:		
        #    self.initUI()
        
    def initUI(self, open_or_save_as='open', **kw):
        #This FRAME object will be placed into the parent container (window, canvas or frame), directly below any previous widgets. The grid() ROW designators refer to the container's Grid and determine which order the widgets will be displayed in.
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "FilePath_View")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=W)                    #position the Frame within the Parent Window
        self.config(width=self.model.frame_width) 
        self.config(**kw)
        self.columnconfigure(0, weight=1, pad=3)
        self.rowconfigure(0, pad=3)
        fg="#000000fff"
        #Label for the filepath textbox:
        self.label_object = Label(self, text=self.model.title)
        self.label_object.grid(row=0, column=0, sticky=W) 
        self.label_object.config(font=("Arial", 10, "bold"), width=26, anchor=E, justify="left")
        self.label_object.config(**kw)
        #Textbox:
        self.textbox = Entry(self)
        self.textbox.grid(row=0, column=1, sticky=W) 
        self.textbox.config(state="readonly", relief="ridge", font=("Arial", 9, "normal"), fg=fg, background=self.model.bgcolor, readonlybackground=self.model.bgcolor, width=self.file_textbox_width, justify="left")
        self.textbox.focus_set()
		#Add buttons to the frame:
        self.display_user_buttons(open_or_save_as)
        #Spacer for the filepath textbox:
        '''self.spacer_object = Label(self, text="  ")
        self.spacer_object.grid(row=0, column=2, sticky=W) 
        self.spacer_object.config(width=self.file_textbox_width, font=("Arial", 10, "bold"), anchor=E, justify="left")
        self.spacer_object.config(**kw)
        '''
		
    def display_user_buttons(self, open_or_save_as='open'):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to contantly hit the system menus.
        open_or_save_as specifies whether this FilePath dialog will open an existing file (tkinter "askopenfilename"), or prompt user to "Save As..." (tkinter "asksaveasfilename") '''
        print("In FilePath_View.display_buttons (open_or_save_as = %s)", (open_or_save_as) )
        #self.btnOpen = Button(self, text="Browse", width=20, command=self.model.locate_file)
        #The button click will call function locate_file() OR save_as_file(), and will let this function know that it should notify the Master object (a DataDict, BlockingPass or other class instance) when the user has selected a file.
        callback_string = 'Testing123'
        alert_master = True
        file_types=[('All files', '*'), ('Text files', '*.csv;*.txt')]
        open_or_save_as = open_or_save_as.lower().strip()
        if open_or_save_as == "open":
            self.btnOpen = Button(self, text="Browse", width=14, command=self.model.locate_file)
        elif open_or_save_as == "save_as":
            self.btnOpen = Button(self, text="Save As", width=14, command=self.model.save_as_file)
        #self.btnOpen = Button(self, text="Browse", width=20, command=lambda x:self.model.locate_file(file_types, alert_master, callback_string) )  #Throws error "TypeError: <lambda>() missing 1 required positional argument: 'x'"
        #                                                        command=lambda x:self.capture_menu_click(optmenu_name, var)
        self.btnOpen.grid(row=0, column=2, sticky=W)
        self.btnClear = Button(self, text="Clear", width=14, command=self.model.clear_file )
        self.btnClear.grid(row=0, column=3, sticky=W)
        

#******************************************************************************************		
def main():
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    root = Tk()
    root.geometry("900x600+100+100")
    master = FilePath_Model(root)
    master.display_view(root)	
    root.mainloop()

if __name__ == '__main__':
    main()  
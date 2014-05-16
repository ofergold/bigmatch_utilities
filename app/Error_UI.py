#!C:\Python33\python.exe -u
#!/usr/bin/env python
'''http://stackoverflow.com/questions/16429716/opening-file-tkinter '''
''' python c:\greg\code\python\Gms_TkFileSystem5_try_button.py '''  
from tkinter import *
import tkinter.filedialog 
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import *     #showerror
import sys
import traceback
import os
import csv
import datetime, time, sched
from CHLog import *

gl_frame_color = "ivory"
gl_frame_width = 700
gl_frame_height = 100

#******************************************************************************
class Error_UI_Model():
    debug = True
    error_message = None                    #Plain text error message
    error_list = []                         #List of errors that have been logged by the controller (LIST OF DICTS - EACH DICT CONTAINS AN ERROR MESSAGE AND EXCEPTION OBJECTS)
    error_dict = None                       #The ERROR DICT currently being processed
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

    def __init__(self, parent_window, controller, error_list=["Unspecified error (ui model parm)"], title="Error", bgcolor=gl_frame_color, frame_width=gl_frame_width, frame_height=gl_frame_height):	
        self.parent_window = parent_window  #Parent_wiondow is the TKinter object itself (often known as "root"
        self.controller = controller		#Controller is the BigMatchController class in main.py 
        self.error_list = error_list        #Error_list is a list of DICTS - each dict contains a plain text error message and exception objects)
        now = datetime.datetime.now()
        self.init_time = str(now.year) + str(now.month).rjust(2,'0') + str(now.day).rjust(2,'0') + ' ' + str(now.hour).rjust(2,'0') + ':' + str(now.minute).rjust(2,'0')
        self.logobject = CHLog(self.controller.enable_logging)
        self.logobject.logit("\n\n____________________________________________________________________", True, True )
        self.logobject.logit("%s In Error_UI_Model._init_: title=%s" % (self.init_time, title), True, True )
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
        if self.error_message is not None:
            self.logobject.logit("\nCalling handle_error with message '%s'" % (self.error_message) )
            return
    
        
    #*****************************************************************************************************************************************
    #ERROR VIEW OBJECT(S)
    #NOTE: VIEWS are typically invoked by calling this MODEL object. The following methods are handlers for instantiating VIEWS.
    def instantiate_view_object(self, container, index):
        #Instantiate VIEWS here.  
        error_view = Error_UI_View(container, self, index)
        return error_view

    def display_view(self, container, index, **kw):
        error_view = self.instantiate_view_object(container, index)
        print("Kwargs for error_view.display_view(): ")
        self.logobject.logit(str(kw), True, True)
        for key, value in kw.items():
            self.logobject.logit("%s = %s" % (key, value), True, True )
        self.logobject.logit("\n In error_ui_model.display_view(), calling error_view.initUI().", True, True)
        error_view.initUI(**kw)   #DISPLAY THE FRAME OBJECT ON SCREEN
        return error_view

    def display_views(self, container=None, howmany_views=None):
        #Instantiate VIEWS here.  
        print("\n Top of error_view.display_views()")
        if container is None:
            container = self.controller.bigcanvas.bigframe
        if not self.error_list:
            self.error_list = ["Unspecified error (ui model display views)"]
        if howmany_views is None:
            howmany_views = len(self.error_list)
        self.logobject.logit("\n Top of error_view.display_views()", True, True)
        if True:    #to do: validate the existence of error message before launching UI
            for i in range(0, howmany_views):
                bgcolor = self.bgcolors[i]    #bgcolor = "#FDFFDF"   
                print("\n In Error_UI_Model.display_views(), calling display_view() for iteration #" + str(i) +". BgColor=" + bgcolor)
                #DISPLAY THE ERROR DISPLAY SCREEN HERE:
                self.display_view(container, i, width=self.frame_width, background=bgcolor, borderwidth=2, padx=3, pady=3)
        else:
            pass #

    def display_user_buttons(self, container):
        '''Function display_user_buttons shows one or more buttons near top of page for common user functions, so the user doesn't need to constantly hit the system menus. '''
        self.button_frame = Frame(container)
        if str(type(container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = container.get_widget_position(self.button_frame, "error_view.display_user_buttons()")
        else:
            stackslot = 0
        #Testing: show a button that will dump to the command window the current contents of all the screen CONTROLS.
        self.button_frame.grid(row=stackslot, column=0, sticky=EW)
        self.button_frame.config(background=self.bgcolor)

    def update_message_region(self, text='', clear_after_ms=4000, **kw):
        #if not text:
        #    text = "Uh-oh"
        self.message_region.configure(text=text)
        self.message_region.after(clear_after_ms, self.clear_message_region)
		
    def clear_message_region(self):
        self.message_region.configure(text="")

        
#End of class Error_UI_Model

#******************************************************************************
#******************************************************************************
class Error_UI_View(Frame):
    debug = True
    container = None
    model = None
    widgetstack_counter = None
    bgcolors = []
    bgcolor = None	
    row_index = 0
    rowtype = None	
    show_view = None
    error_dict = None
	
    def __init__(self, container, model=None, view_index=None, error_dict=None, show_view=None):
        Frame.__init__(self, container)
        if container:
            self.container = container
        if model is None:
            model = Error_UI_Model()                     #Normally this VIEW object will be called by an already-instantiated MODEL object.  But this line is there to catch any direct instantiations of the VIEW.		
        self.model = model 
        self.view_index = view_index                     #Typically we display 6 or 7 blocking pass views on the screen at one time. The blockpassview_index is a counter (index) for these different views.
        if error_dict:
            self.error_dict = error_dict
        else:
            if not self.view_index:
                self.view_index = 0                      #Which item in the error_list is to be displayed?
            self.error_dict = self.model.error_list[self.view_index]      #Display the error_dict with the nth index in self.model.error_list
        self.show_view = show_view
        #Display the frame:
        print("\n In Error_UI_Model._init_: self.show_view=" + str(self.show_view))
        if self.show_view:		                         #Normally this does NOT trigger the screen display, because the class is instantiated and THEN displayed later.
            self.initUI()
        
    def initUI(self, **kw):
        #This FRAME object will be placed into the container (usually a frame, but could be canvas or the container window), directly below any previous widgets. 
        print("\n Type Of Container: " + str(type(self.container)) )
        if str(type(self.container)).lower().find(".tk") == -1:							#For testing, we might display this object directly in the Tkinter main window.  If this is the case, then don't call get_widget_position().
            stackslot = self.container.get_widget_position(self, "Error_UI_Model.Init")
        else:
            stackslot = 0		
        self.grid(column=0, row=stackslot, sticky=W)                    #position the Frame within the container Window
        self.config(**kw)
        self.bgcolor = kw["background"]
        self.config(background=self.bgcolor)
        print("In initUI(), background=" + str(self.bgcolor))
        #Frame Title:
        print("\n In Error_UI_Model.initUI: About to display main frame title")
        widgetspot = self.get_widgetstack_counter()
        #self.column_header_label1 = Label(self, text=self.model.title + " #" + str(self.view_index +1))
        #self.column_header_label1.grid(row=widgetspot, column=0, columnspan=4, sticky=W) 
        #self.column_header_label1.config(background=self.bgcolor, font=("Arial", 18, "bold"), borderwidth=1, width=30, anchor=CENTER, justify=tkinter.LEFT)

        #Display column headers but ONLY for the first error:
        vert_position = self.get_widgetstack_counter()
        lbl_kw = {"width":20, "background":self.bgcolor, "borderwidth":1, "font":("Arial", 12, "bold") }
        if self.view_index == 0:
            lbl = self.create_label("Error message", vert_position, 0, **lbl_kw)
            lbl = self.create_label("Exception type", vert_position, 1, **lbl_kw)
            lbl = self.create_label("Exception value", vert_position, 2, **lbl_kw)
            lbl = self.create_label("Line number", vert_position, 3, **lbl_kw)
        #self.row_index = 0				
        #curvalue = 0 
		
        #*************************************
        #Display the error labels:
        lbl_config = {"font": ("Arial", 10, "normal"), "background": "#FEF0A0", "fg": "#024CC6", "borderwidth":2, "width":30, "anchor":W}
        vert_position = self.get_widgetstack_counter()
        error_message = self.error_dict["error_message"]
        lbl = self.create_label(error_message, vert_position, 0, 212, **lbl_config)
        #Exception details:
        xcp_typ = xcp_val = xcp_tracebk=None
        if "exc_type" in self.error_dict:
            xcp_typ = self.error_dict["exc_type"]
            print("\nType of exc_type: %s" % ( type(xcp_typ) ) )
            lbl = self.create_label(str(xcp_typ), vert_position, 1, 212, **lbl_config)
        if "exc_value" in self.error_dict:
            xcp_val = self.error_dict["exc_value"]
            print("\nType of exc_value: %s" % ( type(xcp_val) ) )
            lbl = self.create_label(str(xcp_val), vert_position, 2, 212, **lbl_config)
        lbl_config["width"] = 60
        if "exc_traceback" in self.error_dict:
            xcp_tracebk = self.error_dict["exc_traceback"]
            print("\nType of exc_traceback: %s" % ( type(xcp_tracebk) ) )
            tb_list = traceback.extract_tb(xcp_tracebk, 4)
            tb_index = 0
            for tb in tb_list:
                lbl = self.create_label("Traceback: " + str(tb), vert_position, 3+tb_index, 424, **lbl_config)
                tb_index += 1

    def get_widgetstack_counter(self, who_called=''):
        if(self.widgetstack_counter == None):
            self.widgetstack_counter = 0
        else:  
            self.widgetstack_counter += 1
        #print("\n" + "widgetstack_counter: " + str(self.widgetstack_counter) + "  " + who_called )
        return self.widgetstack_counter

    def create_label(self, text, gridrow, gridcolumn, wraplength=0, **kw):
        lbl = Label(self, text=text, anchor=W, justify=LEFT)
        lbl.grid(row=gridrow, column=gridcolumn, sticky=W) 
        lbl.config(**kw)
        lbl.config(wraplength=wraplength)

 # End of class Error_UI_View

#******************************************************************************************		
#******************************************************************************************		
def main():
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    '''Geometry for all windows in this app is set by main.py '''
    root = Tk()
    root.geometry("500x500+80+80")
    master = Error_UI_Model()
    master.display_view(root)
    root.mainloop()

if __name__ == '__main__':
    '''This is only for testing.  Normally this class is instantiated by some other class, located in some other module.'''
    main()  

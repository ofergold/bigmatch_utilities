#!C:\Python33\python.exe -u
#!/usr/bin/env python

import sys

#******************************************************************************
class TkErrorHandler():
    message = None

    def __init__(self, message):
        self.message = message
        self.init_UI()

    def show_error():
        tkMessageBox.showerror(self.message)
        return

    def show_warning():
        tkMessageBox.showwarning(self.message)
        return

#End class

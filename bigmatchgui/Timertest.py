class Timertest():
    def __init__(self):
        self.locked = False

    def text_next(self, event):
        if not self.locked:
            #<do the "next" logic>
            self.lock(10) # lock for 10 seconds

    def text_previous(self, event):
        if not self.locked:
            #<do the "previous" logic>
            self.lock(10) # lock for 10 seconds

    def lock(self, n):
        if n == 0:
            self.locked = False
            self.status.config(text="")
        else:
            self.locked = True
            self.status.config(text="Locked for %s more seconds" % n)
            self.status.after(1000, lambda n=n-1: self.lock(n))
import tkinter as tk
import threading

class MyTkApp(threading.Thread):
    def __init__(self):
        self.root=tk.Tk()
        self.s = tk.StringVar()
        self.s.set('Foo')
        l = tk.Label(self.root,textvariable=self.s)
        l.pack()
        threading.Thread.__init__(self)

    def run(self):
        self.root.mainloop()


app = MyTkApp()
app.start()

# Now the app should be running and the value shown on the label
# can be changed by changing the member variable s.
# Like this:
app.s.set('Bar')
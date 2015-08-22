#!/usr/bin/python
# -*- coding: utf-8 -*-

# python 2.x
#from Tkinter import Tk, Frame, Menu, Entry, Label, E, W, N, S
import Tkinter as tk


def button_callback():
    pass


class SmartWheelMain(tk.Frame):
  
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)   
         
        self.parent = parent
        
        self.init_ui()
        
    def init_ui(self):
        self.parent.title("SmartWheel controller")

        # menu
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        
        file_menu = tk.Menu(menubar)       
        
        submenu = tk.Menu(file_menu)
        submenu.add_command(label="command 1")
        submenu.add_command(label="command 2")
        submenu.add_command(label="coomand 3")
        file_menu.add_cascade(label='Import', menu=submenu, underline=0)
        
        file_menu.add_separator()
        
        file_menu.add_command(label="Exit", underline=0, command=self.on_exit)
        menubar.add_cascade(label="File", underline=0, menu=file_menu)        
              
        # window content

        # connect
        self.connect_button = tk.Button(self.parent, text="connect", command=button_callback)
        self.connect_button.grid(row=0)

        # test state
        var = tk.IntVar()
        c = tk.Checkbutton(self.parent, text="state", variable=var)
        c.grid(row=0, column=1)

        # com port
        label1 = tk.Label(self.parent, text="COM1")
        label1.grid(row=0, column=2)

        # big name
        label2 = tk.Label(self.parent, text="Wheel front left")
        label2.grid(row=1, column=0, columnspan=3)

        # enable
        b = tk.Button(self.parent, text="enable", command=button_callback)
        b.grid(row=2, column=0)

        # test state
        var = tk.IntVar()
        c = tk.Checkbutton(self.parent, text="on", variable=var)
        c.grid(row=2, column=1)

        # ok
        b = tk.Button(self.parent, text="ok", command=button_callback)
        b.grid(row=2, column=2)

        # reset
        b = tk.Button(self.parent, text="reset", command=button_callback)
        b.grid(row=3, column=0)

        # config
        b = tk.Button(self.parent, text="config", command=button_callback)
        b.grid(row=3, column=2)


        label1 = tk.Label(self.parent, text="speed")
        label1.grid(row=5, column=1)
        w = tk.Scale(
            self.parent, 
            from_=-100, to=100,
            resolution=1, 
            orient=tk.VERTICAL, 
            borderwidth=0)
        w.grid(row=4, column=2)

        label1 = tk.Label(self.parent, text="steer")
        label1.grid(row=7, column=0)
        w = tk.Scale(
            self.parent, 
            from_=-100, to=100,
            resolution=1, 
            orient=tk.HORIZONTAL, 
            borderwidth=0)
        w.grid(row=8, columnspan=3)


        """
        label1 = tk.Label(self.parent, text="First").grid(row=0, sticky=tk.W)
        label2 = tk.Label(self.parent, text="Second").grid(row=1, sticky=tk.W)

        entry1 = tk.Entry(self.parent)
        entry2 = tk.Entry(self.parent)

        entry1.grid(row=0, column=1)
        entry2.grid(row=1, column=1)

        #label1.grid(sticky=E)
        #label2.grid(sticky=E)

        entry1.grid(row=0, column=1)
        entry2.grid(row=1, column=1)

        #checkbutton.grid(columnspan=2, sticky=W)

        #image.grid(row=0, column=2, columnspan=2, rowspan=2,
        #           sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=5)

        #button1.grid(row=2, column=2)
        #button2.grid(row=2, column=3)
        b = tk.Button(self.parent, text="OK ik ben een brede knop", command=button_callback)
        b.grid(row=3, columnspan=3)

        w = tk.Scale(
            self.parent, 
            from_=-100, to=100,
            resolution=1, 
            orient=tk.HORIZONTAL, 
            borderwidth=0)
        w.grid(row=4, columnspan=3)

        listbox = tk.Listbox(self.parent)
        listbox.grid(row=5, rowspan=10, column=1, columnspan=3)
        listbox.insert(tk.END, "a list entry")

        for item in ["one", "two", "three", "four"]:
            listbox.insert(tk.END, item)
  
        #n = tk.ttk.Notebook(self.parent)
        #f1 = tk.ttk.Frame(n); # first page, which would get widgets gridded into it
        #f2 = tk.ttk.Frame(n); # second page
        #n.add(f1, text='One')
        #n.add(f2, text='Two')

        var = tk.IntVar()
        c = tk.Checkbutton(self.parent, text="Expand", variable=var)
        c.grid(row=10, column=1)
        """

    def on_exit(self):
        self.quit()


def main():
  
    root = tk.Tk()
    root.geometry("600x500+300+300")  # +300+300 indicate 300,300 from upper left.
    app = SmartWheelMain(root)
    root.mainloop()  


if __name__ == '__main__':
    main()  

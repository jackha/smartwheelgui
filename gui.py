#!/usr/bin/python
# -*- coding: utf-8 -*-

# python 2.x
import Tkinter as tk
from Tkinter import *
import ttk
import json
import sys
import json

from serial_object import SerialObject


class Interface(object):
    def __init__(self, root, smart_wheels):
        """Interface for SmartWheels, 

        makes an interface for a list of sw_configs
        """
        self.root = root
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        note = ttk.Notebook(mainframe)
        note.grid(row=0, column=0)

        self.tabs = []
        for i, smart_wheel in enumerate(smart_wheels):
            new_tab = ttk.Frame(note)
            row = 0
            ttk.Label(new_tab, text=smart_wheel.name).grid(row=row, column=0, columnspan=3)

            row += 1
            ttk.Button(
                new_tab, text="Connect", 
                command=lambda: self.button(smart_wheel, new_tab, 'connect')
                ).grid(row=row, column=0)
            ttk.Checkbutton(new_tab, text="State").grid(row=row, column=1)
            ttk.Entry(new_tab, text="COMX").grid(row=row, column=2)

            row += 1
            ttk.Button(
                new_tab, text="Reset", 
                command=lambda: self.button(smart_wheel, new_tab, 'reset')
                ).grid(row=row, column=0)
            ttk.Button(
                new_tab, text="Config", 
                command=lambda: self.button(smart_wheel, new_tab, 'config')
                ).grid(row=row, column=2)

            row += 1
            ttk.Scale(new_tab, 
                from_=-100, to=100, 
                orient=tk.VERTICAL).grid(row=row, column=2)

            row += 1
            ttk.Label(new_tab, text="Speed").grid(row=row, column=0)
            ttk.Label(new_tab, text="200").grid(row=row, column=1)

            row += 1
            ttk.Label(new_tab, text="Steer").grid(row=row, column=0)
            ttk.Label(new_tab, text="200").grid(row=row, column=1)

            row += 1
            ttk.Scale(new_tab, 
                from_=-100, to=100,
                orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3)

            self.tabs.append(new_tab)
            note.add(new_tab, text="%d %s" % (i, smart_wheel.name))

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def button(self, smart_wheel, tab, action):
        """Do the appropriate action for the current SmartWheel"""
        print("button: %s for SmartWheel[%s]" % (action, str(smart_wheel)))
        if action == 'reset':
            smart_wheel.reset()
        elif action == 'connect':
            smart_wheel.connect()
        elif action == 'config':
            # some config dialog, then save to smart_wheel
            print("config")
        elif action == 'enable':
            # check the status, then enable or disable
            if smart_wheel.enabled:
                smart_wheel.disable()
            else:
                smart_wheel.enable()
            # update GUI
            # TODO


def main():
    root = tk.Tk()
    root.title("SmartWheel")

    smart_wheels = []
    for filename in ['config.json', 'serialconfig.txt']:
        new_so = SerialObject(filename=filename, name='SmartWheel [%s]' % filename)
        smart_wheels.append(new_so)

    interface = Interface(root, smart_wheels)
    root.mainloop()


if __name__ == '__main__':
    main()  

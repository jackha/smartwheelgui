#!/usr/bin/python
# -*- coding: utf-8 -*-

# python 2.x
try:
    import Tkinter as tk
    # from Tkinter import *
    import ttk
except ImportError:
    import tkinter as tk
    import tkinter.ttk as ttk
import json
import sys
# from listports import serial_ports
from serial.tools.list_ports import comports


BAUDRATES = ('9600', '19200' , '38400', '57600','115200', '230400', '250000')  # possible baudrates


class Interface(object):
    def __init__(self, root, com_ports=[], baud_rates=[]):
        self.root = root
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        ttk.Label(mainframe, text="port").grid(row=0, column=0)
        ttk.Label(mainframe, text="baudrate").grid(row=1, column=0)

        self.ports = ttk.Combobox(mainframe)
        self.ports['values'] = com_ports
        self.ports.current(0)
        self.ports.grid(row=0, column=1)

        self.baud = ttk.Combobox(mainframe)
        self.baud['values'] = baud_rates
        self.baud.current(0)
        self.baud.grid(row=1, column=1)

        ttk.Button(mainframe, text="Save & Quit", command=self.save).grid(row=2, column=1, sticky=tk.W)

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def save(self):
        with open('config.json', 'w') as config_file:
            json.dump({'comport': self.ports.get(), 'baudrate': self.baud.get()}, config_file)
        sys.exit(0)


def main():
    root = tk.Tk()
    root.title("SmartWheel")

    com_ports = comports()
    if not com_ports:
        com_ports.append('dummy')
    interface = Interface(root, com_ports=com_ports, baud_rates=BAUDRATES)
    root.mainloop()


if __name__ == '__main__':
    main()  

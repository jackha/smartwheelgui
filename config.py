#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Connection config program
"""

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
import connection
import logging

# from listports import serial_ports
from serial.tools.list_ports import comports


class ConfigGUI(object):
    def __init__(self, root, com_ports=[], baud_rates=[]):
        self.root = root

        mainframe = ttk.Frame(self.root, padding="5 5 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        mainframe.columnconfigure(0, weight=0)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(0, weight=0)

        row = 0
        ttk.Label(mainframe, text="port").grid(row=row, column=0)
        self.ports = ttk.Combobox(mainframe)
        self.ports['values'] = [c[0] for c in com_ports]
        self.ports.current(0)
        self.ports.grid(row=row, column=1)

        row += 1
        ttk.Label(mainframe, text="baudrate").grid(row=row, column=0)
        self.baud = ttk.Combobox(mainframe)
        self.baud['values'] = baud_rates
        self.baud.current(0)
        self.baud.grid(row=row, column=1)

        row += 1
        ttk.Label(mainframe, text="conn type").grid(row=row, column=0)
        self.conn_type = ttk.Combobox(mainframe)
        self.conn_type['values'] = connection.ConnectionConfig.CONNECTION_TYPES
        self.conn_type.current(0)
        self.conn_type.grid(row=row, column=1)

        row += 1
        ttk.Button(mainframe, text="Save & Quit", command=self.save).grid(row=row, column=1, sticky=tk.W)

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def save(self):
        config = connection.ConnectionConfig()
        config.set_var('comport', self.ports.get())
        config.set_var('baudrate', self.baud.get())
        config.set_var('connection_type', self.conn_type.get())
        filename = 'testconf1.json'
        config.save(filename)
        logging.info("Saved file: %s" % filename)
        logging.info("Quitting...")
        sys.exit(0)


def main():
    #logging.basicConfig(filename='config.log', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)  # no file, only console

    logging.info("Connection config tool")
    root = tk.Tk()
    root.title("Connection config")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # we get a list of: [port, desc, hwid], desc and hwid is seen as 'n/a'
    com_ports = comports()  
    if not com_ports:
        com_ports.append(['dummy', 'n/a', 'n/a'])
    interface = ConfigGUI(
        root, com_ports=com_ports, 
        baud_rates=connection.BAUDRATES)
    root.mainloop()


if __name__ == '__main__':
    main()  

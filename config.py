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
    from Tkinter import filedialog
except ImportError:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import filedialog
import json
import sys
import connection
import logging

# from listports import serial_ports
from serial.tools.list_ports import comports


class ConfigGUI(tk.Toplevel):


    def __init__(
        self, root, parent=None, smart_wheel=None, com_ports=[], baud_rates=[], 
        connection_config=None):
        """
        Optionally set initial state to given connection_config
        """
        self.root = root
        self.parent = parent  # parent window, or None
        self.smart_wheel = smart_wheel  # either a SWM object, or None

        mainframe = ttk.Frame(self.root, padding="5 5 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        mainframe.columnconfigure(0, weight=0)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(0, weight=0)

        # a notebook is the base for tabs 
        self.note = ttk.Notebook(mainframe)
        self.note.grid(row=0, column=0, columnspan=5)

        self.note_idx = {}  # keep track of connection_type -> notebook index
        note_idx_counter = 0

        # a frame is a tab
        self.serial_frame = ttk.Frame(self.note)

        # filename
        row = 0
        ttk.Label(self.serial_frame, text="port").grid(row=row, column=0)
        self.ports = ttk.Combobox(self.serial_frame)
        self.ports['values'] = [c[0] for c in com_ports]
        self.ports.current(0)
        self.ports.grid(row=row, column=1)

        row += 1
        ttk.Label(self.serial_frame, text="baudrate").grid(row=row, column=0)
        self.baud = ttk.Combobox(self.serial_frame)
        self.baud['values'] = baud_rates
        self.baud.current(0)
        self.baud.grid(row=row, column=1)

        # row += 1
        # ttk.Label(self.serial_frame, text="conn type").grid(row=row, column=0)
        # self.conn_type = ttk.Combobox(self.serial_frame)
        # self.conn_type['values'] = connection.ConnectionConfig.CONNECTION_TYPES
        # self.conn_type.current(0)
        # self.conn_type.grid(row=row, column=1)

        self.note.add(self.serial_frame, text=connection.ConnectionConfig.CONNECTION_TYPE_SERIAL)
        self.note_idx[connection.ConnectionConfig.CONNECTION_TYPE_SERIAL] = note_idx_counter

        # ethernet tab
        note_idx_counter += 1

        self.ethernet_frame = ttk.Frame(self.note)

        row = 0
        ttk.Label(self.ethernet_frame, text="ip address").grid(row=row, column=0)
        self.ip_address_var = tk.StringVar()
        self.ip_address_var.set("127.0.0.1")

        self.ip_address = ttk.Entry(self.ethernet_frame, textvariable=self.ip_address_var)
        self.ip_address.grid(row=row, column=1)

        row += 1
        ttk.Label(self.ethernet_frame, text="port").grid(row=row, column=0)
        self.ethernet_port_var = tk.StringVar()
        self.ethernet_port_var.set("5000")

        self.ethernet_port = ttk.Entry(self.ethernet_frame, textvariable=self.ethernet_port_var)
        self.ethernet_port.grid(row=row, column=1)

        self.note.add(self.ethernet_frame, text=connection.ConnectionConfig.CONNECTION_TYPE_ETHERNET)
        self.note_idx[connection.ConnectionConfig.CONNECTION_TYPE_ETHERNET] = note_idx_counter

        # mock tab
        note_idx_counter += 1
        self.mock_frame = ttk.Frame(self.note)

        row = 0

        self.note.add(self.mock_frame, text=connection.ConnectionConfig.CONNECTION_TYPE_MOCK)
        self.note_idx[connection.ConnectionConfig.CONNECTION_TYPE_MOCK] = note_idx_counter

        # lower part
        row = 1
        ttk.Label(mainframe, text="connection name").grid(row=row, column=0)
        self.name_var = tk.StringVar()
        self.name_var.set("connection name")

        self.name = ttk.Entry(mainframe, textvariable=self.name_var)
        self.name.grid(row=row, column=1)

        # row = 1
        # ttk.Label(mainframe, text="filename").grid(row=row, column=0)
        # self.filename_var = tk.StringVar()
        # self.filename_var.set("testconf1.json")

        # self.filename = ttk.Entry(mainframe, textvariable=self.filename_var)
        # self.filename.grid(row=row, column=1)

        row += 1
        ttk.Button(mainframe, text="Revert", command=self.revert).grid(row=row, column=0, sticky=tk.E)
        ttk.Button(mainframe, text="Load from file...", command=self.load).grid(row=row, column=1, sticky=tk.E)
        ttk.Button(mainframe, text="Save to file...", command=self.save).grid(row=row, column=2, sticky=tk.E)
        ttk.Button(mainframe, text="OK", command=self.close).grid(row=row, column=3, sticky=tk.E)
        ttk.Button(mainframe, text="Cancel", command=self.cancel).grid(row=row, column=4, sticky=tk.E)

        #for child in mainframe.winfo_children(): 
        #    child.grid_configure(padx=5, pady=5)
        self.config_backup = connection_config

        if connection_config is not None:
            self.state_from_config(connection_config)

        # TODO: make this window modal
        # mainframe.grab_set()
        # mainframe.wait_window(mainframe)

    def state_from_config(self, config):
        """Set current state from connection_config object"""
        self.name_var.set(config.name)
        self.note.select(self.note_idx[config.connection_type])
        # config.timeout
        if config.connection_type == connection.ConnectionConfig.CONNECTION_TYPE_SERIAL:
            self.baud.set(config.baudrate)
            self.ports.set(config.comport)
        elif config.connection_type == connection.ConnectionConfig.CONNECTION_TYPE_ETHERNET:
            self.ip_address_var.set(config.ip_address)
            self.ethernet_port_var.set(config.ethernet_port)
        elif config.connection_type == connection.ConnectionConfig.CONNECTION_TYPE_MOCK:
            pass

    def config_from_state(self):
        """Return config object from current window state"""
        config = connection.ConnectionConfig()
        connection_type = self.note.tab(self.note.select(), "text")
        config.set_var('connection_type', connection_type)

        config.set_var('name', self.name.get())

        if connection_type == connection.ConnectionConfig.CONNECTION_TYPE_SERIAL:
            config.set_var('comport', self.ports.get())
            config.set_var('baudrate', self.baud.get())
        elif connection_type == connection.ConnectionConfig.CONNECTION_TYPE_ETHERNET:
            config.set_var('ip_address', self.ip_address.get())
            config.set_var('ethernet_port', self.ethernet_port.get())
        elif connection_type == connection.ConnectionConfig.CONNECTION_TYPE_MOCK:
            pass
        return config

    def revert(self):
        if self.config_backup is not None:
            self.state_from_config(self.config_backup)

    def save(self):
        """Save settings to config"""
        config = self.config_from_state()

        save_file_options = dict(
            initialdir='./', 
            initialfile='wheel_config.json',  #  d
            parent=self.root, title='Save...',
            confirmoverwrite=True,
            filetypes=[('json', '*.json'), ])

        filename = filedialog.asksaveasfilename(**save_file_options)

        if not filename:  # user probably clicked cancel
            return
        config.save(filename)
        logging.info("Saved file: %s" % filename)
        # logging.info("Quitting...")
        # sys.exit(0)
        if self.app is not None and self.smart_wheel is not None:
            # callback in parent window
            self.app.set_config(self.smart_wheel, self.config_from_state())  # we want to remember it

    def load(self):
        """
        Load config and set GUI to match the config
        """
        load_file_options = dict(
            initialdir='./', 
            parent=self.root, title='Load...',
            filetypes=[('json', '*.json'), ])

        filename = filedialog.askopenfilename(**load_file_options)

        if not filename:  # user probably clicked cancel
            return
        config = connection.ConnectionConfig.from_file(filename)
        self.config_backup = config
        logging.info("Loaded file: %s" % filename)

        self.state_from_config(config)

    def close(self):
        if self.parent is not None and self.smart_wheel is not None:
            # callback in parent window
            self.parent.set_config(self.smart_wheel, self.config_from_state())  # we want to remember it
            # self.parent.close_me(self)

        self.root.destroy()

    def cancel(self):
        self.root.destroy()


def config_gui(root, parent=None, smart_wheel=None, connection_config=None):
    """Create config gui, root is tk frame"""
    root.title("Connection config")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # we get a list of: [port, desc, hwid], desc and hwid is seen as 'n/a'
    com_ports = comports()  
    if not com_ports:
        com_ports.append(['no ports found', 'n/a', 'n/a'])
    gui = ConfigGUI(
        root, parent=parent,
        smart_wheel=smart_wheel,
        com_ports=com_ports, 
        baud_rates=connection.BAUDRATES,
        connection_config=connection_config) 

    
if __name__ == '__main__':
    # TODO: read filename from command line arguments.
    #logging.basicConfig(filename='config.log', level=logging.DEBUG)
    root = tk.Tk()
    logging.basicConfig(level=logging.DEBUG)  # no file, only console
    config_gui(root)  
    root.mainloop()
    
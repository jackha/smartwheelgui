#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    # python3: default
    import tkinter as tk
    import tkinter.ttk as ttk
except ImportError:
    # python 2.x
    import Tkinter as tk
    # from Tkinter import *
    import ttk

import json
import sys
import json
import time
import threading

from serial import Serial
from mock_serial import MockSerial

from smart_module import SmartModule
from connection import NotConnectedException


class Interface():
    TEXT_CONNECT = 'Connect'
    TEXT_DISCONNECT = 'Disconnect'

    def __init__(self, root, smart_wheels):
        """Interface for SmartWheels, 

        makes an interface for a list of sw_configs
        """
        # super(Interface, self).__init__(root)
        self.i_wanna_live = True

        self.root = root
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        note = ttk.Notebook(mainframe)
        note.grid(row=0, column=0)

        self.gui_elements = {}
        self.tabs = {}

        #self.tabs = []
        for i, smart_wheel in enumerate(smart_wheels):  # every smart_wheel must have a unique name
            self.gui_elements[smart_wheel.name] = {}
            new_tab = ttk.Frame(note)
            self.tabs[smart_wheel.name] = new_tab

            row = 0
            ttk.Label(new_tab, text=smart_wheel.name).grid(row=row, column=0, columnspan=3)

            row += 1
            connect_btn = ttk.Button(
                new_tab, text=self.TEXT_CONNECT, 
                command=self.button_fun(smart_wheel, new_tab, 'connect')
                )
            connect_btn.grid(row=row, column=0)
            self.gui_elements[smart_wheel.name]['connect_btn'] = connect_btn

            check = ttk.Checkbutton(
                new_tab, text="State", 
                command=self.button_fun(smart_wheel, new_tab, 'enable')
                )
            check.grid(row=row, column=1)
            self.gui_elements[smart_wheel.name]['enable_checkbutton'] = check

            ttk.Entry(new_tab, text="COMX").grid(row=row, column=2)

            row += 1
            ttk.Button(
                new_tab, text="Reset", 
                command=self.button_fun(smart_wheel, new_tab, 'reset')
                ).grid(row=row, column=0)
            ttk.Button(
                new_tab, text="Config", 
                command=self.button_fun(smart_wheel, new_tab, 'config')
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

            # self.tabs.append(new_tab)
            note.add(new_tab, text="%d %s" % (i, smart_wheel.name))

            print("new smart_wheel %s" % smart_wheel.name)

            # input command
            row += 1
            input_field = ttk.Entry(new_tab)
            input_field.grid(row=row, column=1, columnspan=3)
            self.gui_elements[smart_wheel.name]['input_field'] = input_field

            # command result
            row += 1
            output_field = tk.Text(new_tab)
            output_field.grid(
                row=row, column=1, columnspan=3, rowspan=3)
            self.gui_elements[smart_wheel.name]['output_field'] = output_field

            update_thread = threading.Thread(target=self.update_thread_fun(smart_wheel))
            update_thread.start()

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def button(self, smart_wheel, tab, action):
        """Do the appropriate action for the current SmartWheel"""
        print("button: %s for SmartWheel[%s]" % (action, str(smart_wheel)))
        try:
            if action == 'reset':
                sent = smart_wheel.reset()
                self.message(smart_wheel, '-> [%s]' % sent)
                # input_value = self.gui_elements[smart_wheel.name]['input_field'].get()
                # print("input field value = %s" % input_value)
                # self.gui_elements[smart_wheel.name]['output_field'].insert('end -1 chars', input_value + '\n')
            elif action == 'connect':
                smart_wheel.connect()
                self.message(smart_wheel, 'connected')
                # TODO: how to change button label
                # self.gui_elements[smart_wheel.name]['connect_btn'].textvariable = tk.StringVar(self.root, self.TEXT_DISCONNECT)
            elif action == 'config':
                # some config dialog, then save to smart_wheel
                print("config")
            elif action == 'enable':
                # check the status, then enable or disable
                sent = None                
                if 'selected' in self.gui_elements[smart_wheel.name]['enable_checkbutton'].state():
                    if not smart_wheel.enabled:
                        sent = smart_wheel.enable()
                    else:
                        self.message(smart_wheel, 'ignored: smart wheel already enabled')
                else:
                    if smart_wheel.enabled:
                        sent = smart_wheel.disable()
                    else:
                        self.message(smart_wheel, 'ignored: smart wheel already disabled')
                if sent:
                    self.message(smart_wheel, '-> [%s]' % sent)
                # update GUI
                # TODO
        except NotConnectedException as err:
            self.message(smart_wheel, 'Oops, there was an error: {}'.format(err))

    def update_thread_fun(self, smart_wheel):
        def update_thread():
            while self.i_wanna_live:
                while smart_wheel.incoming:
                    new_message = smart_wheel.incoming.pop(0)
                    self.message(smart_wheel, '<- [%s]' % new_message)
                time.sleep(0.001)
        return update_thread

    def button_fun(self, smart_wheel, tab, action):
        """
        return a button function without parameters with these parameters included 
        """
        def new_fun():
            return self.button(smart_wheel, tab, action)
        return new_fun

    def message(self, smart_wheel, msg):
        self.gui_elements[smart_wheel.name]['output_field'].insert('end -1 chars', msg + '\n')

    # def close_window(self):
    #     print("close!")
    #     super(Interface, self).close_window()


def main():
    root = tk.Tk()
    root.title("SmartWheel")

    # serial_wrapper = Serial
    # serial_wrapper = MockSerial

    smart_modules = []
    for filename in ['testconf1.json', 'testconf2.json']:
        new_sm = SmartModule.from_config(filename)
        smart_modules.append(new_sm)

    interface = Interface(root, smart_modules)

    def on_close():
        root.destroy()
        # shut down smart modules
        for sm in smart_modules:
            sm.shut_down()
        interface.i_wanna_live = False

    root.protocol("WM_DELETE_WINDOW", on_close)  # close window
    root.mainloop()


if __name__ == '__main__':
    main()  

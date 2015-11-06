#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: Jack Ha for Opteq
License: lgpl

Smart Wheel Module (SWM) main GUI program.

Usage: see README.rst

if GUI_STATE_FILENAME exists, it will try to load the gui state from the file.
if it fails, you can always delete this file and a new file will be generated.

The Interface class is instantiated with notes (tabs) created for each SWM.

SWMGuiElements is an extension on the SWM class, it provides GUI helper 
functions.

"""

try:
    # python3: default
    import tkinter as tk
    import tkinter.ttk as ttk
except ImportError:
    # python 2.x
    import Tkinter as tk
    # from Tkinter import *
    import ttk

import argparse
import json
import sys
import json
import time
import threading
import logging
import connection
import os

from swm import SWM
from connection import NotConnectedException
from config import config_gui
from wheel_gui import wheel_gui
from loghelper import setup_logging

logger = logging.getLogger(__name__)

GREY = '#777'

# 
UPDATE_TIME = 0.01
UPDATE_TIME_SLOW = 0.2

GUI_STATE_FILENAME = '_guistate.json'
SETTINGS_FILENAME = 'settings.json'

#LOG_PATH = './logs'

# SWM.incoming will get filled, the gui must pull the messages.
POPULATE_INCOMING = True

# these are the messages actually shown in the gui.
SHOW_MESSAGES = {'$0', '$1', '$8', '$9', '$15', '$29', '$50', '$60'}


def smart_wheels_from_state_file(filename):
    """
    Create and return SWM objects defined by state file.
    """
    smart_modules = []
    with open(GUI_STATE_FILENAME, 'r') as f:
        sm_config = json.load(f)
    for single_config in sm_config:
        conn = connection.Connection.from_dict(single_config['config'])
        new_sm = SWMGuiElements(connection=conn, populate_incoming=POPULATE_INCOMING)
        smart_modules.append(new_sm)
    return smart_modules


def state_file_from_smart_wheels(smart_wheels):
    """
    Write state file from current smart wheel instances.
    """
    tabs = []
    for swm in smart_wheels:
        tabs.append({'config': swm.connection.conf.as_dict()})
    with open(GUI_STATE_FILENAME, 'w') as state_file:
        json.dump(tabs, state_file, indent=2)


class SWMGuiElements(SWM):
    """
    Smart Wheel Module with Interface elements (with corresponding values).

    With tk, we need StringVar objects to actually store, recall and set field
    values.
    """

    def __init__(self, *args, **kwargs):
        """
        Set defaults
        """
        super(SWMGuiElements, self).__init__(*args, **kwargs)

        # organize elements by key
        self.elements = {}  

        # status slug. user updatable; for use in GUI
        self.state = self.STATE_NOT_CONNECTED  

        # the GUI where you can call handle_cmd_from_wheel, once initialized
        self.wheel_gui = None  

        self.tab_id = None  # the attached GUI tab

    def set_elem(self, elem_name, elem_value):
        """
        Set a GUI element

        Use this function when using other objects than create_label, 
        create_button, etc.
        """
        self.elements[elem_name] = elem_value

    def get_elem(self, elem_name):
        """
        Return the internally stored GUI element.
        """
        return self.elements[elem_name]

    def create_label(self, frame, elem_name, elem_value, label_args={}):
        """
        make a label with corresponding StringVar and return it

        StringVar: so we can change the contents
        """
        elem_var_name = '%s_var' % elem_name
        _var = tk.StringVar()
        _var.set(elem_value)
        self.elements[elem_var_name] = _var
        
        label = ttk.Label(
            frame, 
            textvariable=self.elements[elem_var_name],
            **label_args
            )
        self.elements[elem_name] = label
        return label

    def create_button(self, frame, elem_name, elem_value, command):
        """
        Create a button with a changeable label
        Namespace of elem_name is the same as for labels.
        """
        elem_var_name = '%s_var' % elem_name
        _var = tk.StringVar()
        _var.set(elem_value)
        self.elements[elem_var_name] = _var
        
        label = ttk.Button(
            frame, 
            textvariable=self.elements[elem_var_name],
            command=command
            )
        self.elements[elem_name] = label
        return label

    def create_entry(self, frame, elem_name, elem_value, elem_args={}):
        """
        Create an Entry with a changeable value
        Namespace of elem_name is the same as for labels.
        """
        elem_var_name = '%s_var' % elem_name
        _var = tk.StringVar()
        _var.set(elem_value)
        self.elements[elem_var_name] = _var
        
        obj = ttk.Entry(
            frame, 
            textvariable=self.elements[elem_var_name],
            **elem_args
            )
        self.elements[elem_name] = obj
        return obj

    def create_text(self, frame, elem_name, elem_args={}):
        """
        Create tk.Text object and return it. 
        """
        obj = tk.Text(frame, **elem_args)
        self.elements[elem_name] = obj
        return obj

    def set_label(self, elem_name, elem_value):
        """
        Set a new value for a label or button
        """
        elem_var_name = '%s_var' % elem_name
        # Only set the value if it was different: prevent all kinds of GUI updating
        if self.elements[elem_var_name].get() != elem_value:
            self.elements[elem_var_name].set(elem_value)

    def set_color(self, elem_name, color_value):
        """
        Set an elements color.

        color_value is something like '#356' 
        """
        self.elements[elem_name].configure(foreground=color_value)

    def get_label(self, elem_name):
        """
        Get value for a label
        """
        elem_var_name = '%s_var' % elem_name
        return self.elements[elem_var_name].get()


class Interface():
    """
    Interface for SmartWheels

    makes an interface for a list of SWMGuiElements objects.
    the result is a bunch of notes (tabs), each representing a SWM.

    self.smart_wheels must correspond to self.note.tabs().
    new_wheel and delete_wheel ensure this as well.
    """
    #GUI_CONNECT_BTN = 'connect_button'
    #GUI_DISCONNECT_BTN = 'disconnect_button'

    GUI_CONNECTION_NAME = 'connection_name_label'
    GUI_CONNECTION_STATUS = 'connection_status_label'
    GUI_CONNECTION_INFO = 'connection_info_label'

    GUI_STEER_SET_POINT = 'steer_set_point'
    GUI_STEER_ACTUAL = 'steer_actual'
    GUI_STEER_SCALE = 'steer_scale'
    GUI_STEER_0_BUTTON = 'steer_stop'

    GUI_SPEED_SET_POINT = 'speed_set_point'
    GUI_SPEED_ACTUAL = 'speed_actual'
    GUI_SPEED_SCALE = 'speed_scale'
    GUI_SPEED_0_BUTTON = 'speed_stop'

    GUI_CONNECT_BUTTON = 'connect_button'
    GUI_DISCONNECT_BUTTON = 'disconnect_button'
    GUI_RESET_BUTTON = 'reset_button'

    GUI_ENABLE_BUTTON = 'enable_button'
    GUI_DISABLE_BUTTON = 'disable_button'
    GUI_EDIT_BUTTON = 'edit_button'

    GUI_FIRMWARE = 'firmware'

    GUI_WHEEL_ENABLED = 'wheel_enabled'
    GUI_VIN = 'vin'
    GUI_COUNTERS = 'counters'

    GUI_INPUT_FIELD = 'input_field'
    GUI_OUTPUT_FIELD = 'output_field'

    PADDING = '10 2 10 4'

    def __init__(self, root, smart_wheels):
        """
        Init 

        Set defaults and create GUIs for each SWM provided.
        """
        # super(Interface, self).__init__(root)
        self.i_wanna_live = True
        # self.sub_window_open = False  # is set back to false from the sub window
        
        self.root = root
        mainframe = ttk.Frame(root)
        # mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        self.mainframe = mainframe
        #self.mainframe.bind("<Configure>", self.on_resize)

        # top menu
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        menu_file = tk.Menu(menu)
        menu.add_cascade(label='File', menu=menu_file)
        menu_file.add_command(label='New Wheel', command=self.new_wheel)
        menu_file.add_command(label='Delete selected wheel', command=self.delete_wheel)
        menu_file.add_command(label='Quit', command=self.quit)
        
        # tabs
        note = ttk.Notebook(mainframe)
        note.grid(row=0, column=0)
        self.note = note

        self.smart_wheels = smart_wheels
        
        self.steer_set_point = 0
        self.speed_set_point = 0
        
        for smart_wheel in smart_wheels:  # every smart_wheel must have a unique name
            self.make_gui_for_smart_wheel(smart_wheel)
            
        # for child in mainframe.winfo_children(): 
        #     child.grid_configure(padx=5, pady=5)
        self.last_slow_update = time.time()
        self.gui_message_queue = []  # (smart_wheel, msg)
        self.gui_set_label_queue = []  # (smart_wheel, label_name, text)
        self.gui_set_tab_name_queue = []  # tab, text
        self.update_me()

    def update_me(self):
        """ 
        main thread for updating GUI stuff. 

        all GUI changes must be done here.

        - SWM status -> GUI status (with interval UPDATE_TIME_SLOW)
        - SWM incoming messages -> display on screen with filter SHOW_MESSAGES
        - Display messages that come from using "def message"
        - Set labels that come from using "def set_label" 
          (config change, steer command, etc)
        - Set tab names (after config change)
        """
    
        check_time = time.time()
        if check_time - self.last_slow_update > UPDATE_TIME_SLOW:
            self.last_slow_update = check_time

            for smart_wheel in self.smart_wheels:
                if smart_wheel.wheel_gui is not None:
                    smart_wheel.wheel_gui.update_status_from_wheel()

                self.update_gui_from_wheel(smart_wheel)

                # # empty the smart wheel incoming and show on screen if wanted
                try_again = True
                while try_again:
                    try:
                        msg = smart_wheel.incoming.pop(0)
                        if msg[0] in SHOW_MESSAGES:
                            self._message(smart_wheel, ','.join(msg))
                    except IndexError:
                        # empty
                        try_again = False

                # update all enabled / disabled buttons
                self.update_gui_elements(smart_wheel)
                      
        # messages
        try:
            target, msg = self.gui_message_queue.pop(0)
            self._message(target, msg)
        except:
            # empty queue
            pass

        # set_label
        try:
            sw, label_name, txt = self.gui_set_label_queue.pop(0)
            sw.set_label(label_name, txt)
        except:
            pass

        # tab
        try:
            tab_id, txt = self.gui_set_tab_name_queue.pop(0)
            logger.info("tab name %r, %s" % (tab_id, txt))
            self.note.tab(tab_id, **dict(text=txt))
        except:
            pass

        self.mainframe.after(10, self.update_me)

    def make_gui_for_smart_wheel(self, smart_wheel, position="end"):
        """
        Create a GUI for given smart wheel and put it in self.note.

        The smart_wheel is subscribed to the function message 
        (means that some output will be seen in the message box)

        Afterwards the GUI is updated with the smart wheel state.

        kwarg Position is ttk.Notebooks index: either an integer or "end"
        """
        new_tab = ttk.Frame(self.note)
            
        row = 0

        label_frame_connection = ttk.Labelframe(new_tab, text='Connection', padding=self.PADDING)
        label_frame_connection.grid(row=row, column=0, columnspan=4, sticky="nsew")

        label_frame_row = 0
        sm_button = smart_wheel.create_button(
            label_frame_connection, 
            'connect_button', 
            'Connect', 
            self.button_fun(smart_wheel, new_tab, 'connect'))
        sm_button.grid(row=label_frame_row, column=0)
        sm_button = smart_wheel.create_button(
            label_frame_connection, 
            'disconnect_button', 
            'Disconnect', 
            self.button_fun(smart_wheel, new_tab, 'disconnect'))
        sm_button.grid(row=label_frame_row, column=1)

        reset = smart_wheel.create_button(
            label_frame_connection, 
            self.GUI_RESET_BUTTON, 
            'Reset', 
            self.button_fun(smart_wheel, new_tab, 'reset'))
        reset.grid(row=label_frame_row, column=2)
        ttk.Button(
            label_frame_connection, text='Config', 
            command=self.button_fun(smart_wheel, new_tab, 'config')
            ).grid(row=label_frame_row, column=3)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='name', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_CONNECTION_NAME, 
            smart_wheel.connection.conf.name)
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='config', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label2 = smart_wheel.create_label(
            label_frame_connection, self.GUI_CONNECTION_INFO, 
            str(smart_wheel.connection.conf))
        label2.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='firmware', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_FIRMWARE, 
            '')  # fill initially with empty
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='status', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_CONNECTION_STATUS, 
            '')  # fill initially with empty
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='wheel enabled', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_WHEEL_ENABLED, 
            '')  # fill initially with empty
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='vin', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_VIN, 
            '-')  # fill initially with empty
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_row += 1
        ttk.Label(
            label_frame_connection, text='counters', foreground=GREY).grid(
            row=label_frame_row, column=0, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_connection, self.GUI_COUNTERS, 
            '')  # fill initially with empty
        label.grid(row=label_frame_row, column=1, columnspan=10, sticky=tk.W)

        label_frame_connection.columnconfigure(0, weight=1)
        label_frame_connection.columnconfigure(1, weight=1)
        label_frame_connection.columnconfigure(2, weight=1)
        label_frame_connection.columnconfigure(3, weight=1)
        label_frame_connection.columnconfigure(4, weight=100)

        # Connection
        row += 1
        label_frame_wheel = ttk.Labelframe(new_tab, text='Wheel', padding=self.PADDING)
        label_frame_wheel.grid(row=row, column=0, columnspan=4, sticky="nsew")
        label_frame_wheel.columnconfigure(0, weight=1)
        label_frame_wheel.columnconfigure(1, weight=1)
        label_frame_wheel.columnconfigure(2, weight=1)
        label_frame_wheel.columnconfigure(3, weight=1)
        label_frame_wheel.columnconfigure(4, weight=100)

        button = smart_wheel.create_button(
            label_frame_wheel, 
            self.GUI_ENABLE_BUTTON, 
            'Enable', 
            self.button_fun(smart_wheel, new_tab, 'enable'))
        button.grid(row=0, column=0)
        button = smart_wheel.create_button(
            label_frame_wheel, 
            self.GUI_DISABLE_BUTTON, 
            'Disable', 
            self.button_fun(smart_wheel, new_tab, 'disable'))
        button.grid(row=0, column=1)
        button = smart_wheel.create_button(
            label_frame_wheel, 
            self.GUI_EDIT_BUTTON, 
            'Edit/Debug', 
            self.button_fun(smart_wheel, new_tab, 'wheel-gui'))
        button.grid(row=0, column=2)

        #####################################
        # speed
        row += 1
        ttk.Label(label_frame_wheel, text="actual").grid(row=row, column=1, sticky=tk.E)
        ttk.Label(label_frame_wheel, text="sent").grid(row=row, column=2, sticky=tk.E)
        ttk.Label(label_frame_wheel, text="control").grid(row=row, column=5)
        
        row += 1
        ttk.Label(label_frame_wheel, text="Speed").grid(row=row, column=0, sticky=tk.E)

        label = smart_wheel.create_label(
            label_frame_wheel, self.GUI_SPEED_ACTUAL, 
            '-')
        label.grid(row=row, column=1, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_wheel, self.GUI_SPEED_SET_POINT, 
            str(self.speed_set_point))
        label.grid(row=row, column=2, sticky=tk.E)

        button = smart_wheel.create_button(
            label_frame_wheel, 
            self.GUI_SPEED_0_BUTTON, 
            'stop', 
            self.button_fun(smart_wheel, new_tab, 'speed-0'))
        button.grid(row=row, column=4)
        
        speed_scale = ttk.Scale(label_frame_wheel, 
            from_=-200, to=200, 
            orient=tk.VERTICAL,
            command=self.set_speed_fun(smart_wheel))
        speed_scale.grid(row=row, column=5)
        smart_wheel.set_elem(self.GUI_SPEED_SCALE, speed_scale)

        # steer
        row += 1
        ttk.Label(label_frame_wheel, text="Steer").grid(row=row, column=0, sticky=tk.E)

        label = smart_wheel.create_label(
            label_frame_wheel, self.GUI_STEER_ACTUAL, 
            '-')
        label.grid(row=row, column=1, sticky=tk.E)
        label = smart_wheel.create_label(
            label_frame_wheel, self.GUI_STEER_SET_POINT, 
            str(self.steer_set_point))
        label.grid(row=row, column=2, sticky=tk.E)

        button = smart_wheel.create_button(
            label_frame_wheel, 
            self.GUI_STEER_0_BUTTON, 
            '0', 
            self.button_fun(smart_wheel, new_tab, 'steer-0'))
        button.grid(row=row, column=4)
        
        steer_scale = ttk.Scale(label_frame_wheel, 
            from_=-1800, to=1800,
            orient=tk.HORIZONTAL,
            command=self.set_steer_fun(smart_wheel))
        steer_scale.grid(row=row, column=5)
        smart_wheel.set_elem(self.GUI_STEER_SCALE, steer_scale)

        ############################################
        # console
        label_frame_console = ttk.Labelframe(new_tab, text='Console', padding=self.PADDING)
        label_frame_console.grid(row=row, column=0, columnspan=4, sticky="nsew")

        # input command label
        # !! width=80 strangely applies to all objects here, the input_field and output_field
        row += 1
        ttk.Label(
            label_frame_console, 
            text="Manual input command (see reference manual for commands), enter to send:",
            width=80).grid(row=row, column=0, sticky=tk.W)
        # input command
        row += 1
        # input_field = ttk.Entry(new_tab)
        input_field = smart_wheel.create_entry(label_frame_console, self.GUI_INPUT_FIELD, '', elem_args={})
        input_field.grid(row=row, column=0, columnspan=4, sticky=tk.NSEW)

        # <return> executes the command
        input_field.bind('<Return>', self.event_fun(smart_wheel))

        # output label
        row += 1
        ttk.Label(
            label_frame_console, 
            text="Output (see command prompt for more detail):").grid(row=row, column=0, columnspan=4, sticky=tk.W)
        
        # output to user
        row += 1

        scrollbar = tk.Scrollbar(label_frame_console)
        scrollbar.grid(row=row, column=5, sticky=tk.E)

        # output_field = tk.Text(new_tab, yscrollcommand=scrollbar.set)
        output_field = smart_wheel.create_text(
            label_frame_console, self.GUI_OUTPUT_FIELD, 
            elem_args=dict(yscrollcommand=scrollbar.set, height=10))
        output_field.grid(
            row=row, column=0, sticky=tk.NSEW)
        scrollbar.config(command=output_field.yview)

        ###################################
        # end of label frames

        self.note.insert(position, new_tab, text="%s" % (smart_wheel.name))

        # subscribe myself for back logging
        smart_wheel.subscribe(self.message)
        # self.update_gui_elements(smart_wheel)

        # TODO: how to better get tab_id?
        if position == 'end':
            tab_id = self.note.tabs()[-1]
        else:
            tab_id = self.note.tabs()[position]

        smart_wheel.tab_id = tab_id

    def new_wheel(self):
        """
        Add new wheel.

        self.smart_wheels, self.note are both updated
        """
        logger.info('Add new wheel')

        conn = connection.Connection()
        new_sm = SWMGuiElements(connection=conn, populate_incoming=POPULATE_INCOMING)

        all_tabs = self.note.tabs()
        if len(all_tabs) == 0:
            new_pos = 0
            new_pos_tk = "end"
        else:
            new_pos = self.note.index(self.note.select()) + 1  # new tab is after currently selected tab
            new_pos_tk = new_pos if new_pos < len(all_tabs) else "end"
        self.make_gui_for_smart_wheel(new_sm, position=new_pos_tk)
        self.smart_wheels.insert(new_pos, new_sm)

        self.note.select(new_pos)  # select by index

        # pop up config for initial configuration
        config_gui(
            tk.Toplevel(self.root), 
            parent=self, smart_wheel=new_sm, 
            connection_config=new_sm.connection.conf)

    def delete_wheel(self):
        """
        Delete wheel module from tabs

        Both self.smart_wheels as wel as self.note are updated.
        The SWM is first shut down before deleted.
        """
        selected_tab = self.note.select()
        idx = self.note.index(selected_tab)
        logger.info("Delete wheel from gui: %s, idx=%d" % (self.note.tab(selected_tab, "text"), idx))
        smw = self.smart_wheels.pop(idx)
        smw.shut_down()
        self.note.forget(selected_tab)

    def on_resize(self, event):
        """
        Resize event

        Testing
        """
        logger.info('Resizing...')

    def quit(self):
        """
        Quit the GUI
        """
        logger.info('Quit')
        self.i_wanna_live = False
        for swm in self.smart_wheels:
            if swm.connection.is_connected():
                swm.disconnect()
            swm.shut_down()
        self.root.quit()
        # store my config
        state_file_from_smart_wheels(self.smart_wheels)
        logger.info('GUI state saved.')

    def set_label(self, smart_wheel, label_name, text):
        """
        Set GUI label.

        Call this function from anywhere to set GUI labels, it is thread safe.
        """
        self.gui_set_label_queue.append((smart_wheel, label_name, text))

    def set_steer(self, smart_wheel, new_steer):
        """
        Set steer

        Read the steer scale, update the GUI and send the command to the SWM.
        """
        logger.info('Steer: %s, %s' % (smart_wheel, new_steer))
        self.steer_set_point = new_steer
        # smart_wheel.set_label(self.GUI_STEER_SET_POINT, str(self.steer_set_point))
        self.set_label(smart_wheel, self.GUI_STEER_SET_POINT, str(self.steer_set_point))
        cmd = '$2,%d,%d' % (self.speed_set_point, self.steer_set_point)
        self.message(smart_wheel, '-> [%s]' % cmd)
        smart_wheel.command(cmd)

    def set_steer_fun(self, smart_wheel):
        """
        Wrapper for set_steer to eliminate the smart_wheel option.
        """
        def fun(new_steer):
            return self.set_steer(smart_wheel, int(float(new_steer)))
        return fun

    def set_speed(self, smart_wheel, new_speed):
        """
        Set speed

        Read the speed scale, update the GUI and send the command to the SWM.
        """
        logger.info('Speed: %s, %s' % (smart_wheel, new_speed))
        self.speed_set_point = new_speed
        self.set_label(smart_wheel, self.GUI_SPEED_SET_POINT, str(self.speed_set_point))
        cmd = '$2,%d,%d' % (self.speed_set_point, self.steer_set_point)
        self.message(smart_wheel, '-> [%s]' % cmd)
        smart_wheel.command(cmd)

    def set_speed_fun(self, smart_wheel):
        """
        Wrapper for set_speed to eliminate the smart_wheel option.
        """
        def fun(new_speed):
            return self.set_speed(smart_wheel, int(float(new_speed)))
        return fun

    def handle_command(self, smart_wheel, event):
        """
        Handle command

        Read GUI element and send the command to SWM.
        Does nothing with given event (yet).
        """
        command = smart_wheel.get_elem(self.GUI_INPUT_FIELD).get()
        logger.debug("Handle: %s" % command)
        try:
            result = smart_wheel.command(command + '\r\n')
            self.message(smart_wheel, '-> [%s]' % result.strip())
        except NotConnectedException as ex:
            logger.exception("You're not connected yet.")
            self.message(smart_wheel, 'ERROR, you are not connected.')

    def event_fun(self, smart_wheel):
        """
        Return handle_command function with only the event as parameter.
        """
        def new_fun(event):
            return self.handle_command(smart_wheel, event)
        return new_fun

    def update_gui_elements(self, smart_wheel):
        """
        Use smart_wheel.state and smart_wheel.enabled to set the GUI status.
        """
        if smart_wheel.state == smart_wheel.STATE_CONNECTED:
            smart_wheel.get_elem(self.GUI_CONNECT_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_DISCONNECT_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_RESET_BUTTON)['state'] = tk.ACTIVE

            #smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.ACTIVE
            #smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.ACTIVE

            if smart_wheel.enabled:
                smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.DISABLED
                smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.ACTIVE
            else:
                smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.ACTIVE
                smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.DISABLED

            smart_wheel.get_elem(self.GUI_EDIT_BUTTON)['state'] = tk.ACTIVE
        elif smart_wheel.state == smart_wheel.STATE_NOT_CONNECTED:
            smart_wheel.get_elem(self.GUI_CONNECT_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_DISCONNECT_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_RESET_BUTTON)['state'] = tk.DISABLED

            smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_EDIT_BUTTON)['state'] = tk.DISABLED

    def button(self, smart_wheel, tab, action):
        """
        Handle button press

        Do the appropriate action for the current SmartWheel
        """
        logger.info("button: %s for SmartWheel[%s]" % (action, str(smart_wheel)))
        try:
            if action == 'reset':
                sent = smart_wheel.reset()
                self.message(smart_wheel, '-> [%s]' % sent.strip())
            elif action == 'connect':
                if not smart_wheel.connection.is_connected():
                    try:
                        smart_wheel.connect()
                        self.message(smart_wheel, 'connected')
                    except:
                        logging.exception('could not connect')
                        self.message(smart_wheel, 'ERROR connecting: %s' % smart_wheel.connection.last_error)
                else:
                    self.message(smart_wheel, 'Already connected. Disconnect first')
            elif action == 'disconnect':
                if smart_wheel.connection.is_connected():
                    smart_wheel.disconnect()
                self.message(smart_wheel, 'disconnected')
            elif action == 'config':
                # some config dialog, then save to smart_wheel
                logger.info("config")
                # the config_gui will call set_config
                config_gui(
                    tk.Toplevel(self.root), 
                    parent=self, smart_wheel=smart_wheel, 
                    connection_config=smart_wheel.connection.conf)
            elif action == 'wheel-gui':
                # some config dialog, then save to smart_wheel
                logger.info("wheel gui")
                # self.sub_window_open = True
                if smart_wheel.is_connected():
                    smart_wheel.wheel_gui = wheel_gui(
                        tk.Toplevel(self.root), parent=self, smart_wheel=smart_wheel)
                else:
                    self.message(smart_wheel, 'Connect me first before launching this screen')
            elif action == 'enable':
                # check the status, then enable or disable
                if not smart_wheel.enabled:
                    sent = smart_wheel.enable()
                    self.message(smart_wheel, '-> [%s]' % sent.strip())
                else:
                    self.message(smart_wheel, 'ignored, already enabled')
            elif action == 'disable':
                if smart_wheel.enabled:
                    sent = smart_wheel.disable()
                    self.message(smart_wheel, '-> [%s]' % sent.strip())
                else:
                    self.message(smart_wheel, 'ignored, already disabled')
            elif action == 'speed-0':
                self.set_speed(smart_wheel, 0)
                self.message(smart_wheel, 'speed-0')
            elif action == 'steer-0':
                self.set_steer(smart_wheel, 0)
                self.message(smart_wheel, 'steer-0')

        except NotConnectedException as err:
            self.message(smart_wheel, 'Oops, there was an error: {}'.format(err))

        # smart_wheel.update_state()
        # self.update_gui_elements(smart_wheel)

    def set_config(self, smart_wheel, config):
        """
        Set the SWM using the provided config.

        This function is called from the config screen after pressing save or ok.
        """
        logger.info("New smart wheel [%s] has new config [%s]" % (smart_wheel, config))
        smart_wheel.connection.conf = config
        self.gui_set_label_queue.append((smart_wheel, self.GUI_CONNECTION_NAME, config.name))
        self.gui_set_label_queue.append((smart_wheel, self.GUI_CONNECTION_INFO, str(config)))
        self.gui_set_tab_name_queue.append((smart_wheel.tab_id, config.name))

    def update_gui_from_wheel(self, smart_wheel):
        """
        Update specific buttons for a SWM. Called from update_me.        
        """
        cmds = smart_wheel.cmd_from_wheel
        if SWM.CMD_ACT_SPEED_DIRECTION in cmds:
            cmd = cmds[SWM.CMD_ACT_SPEED_DIRECTION]
            # $13, actual wheel position, actual wheel speed, actual steer position, actual steer<CR>
            smart_wheel.set_label(self.GUI_SPEED_ACTUAL, str(cmd[1]))
            smart_wheel.set_label(self.GUI_STEER_ACTUAL, str(cmd[3]))

        smart_wheel.set_label(self.GUI_FIRMWARE, smart_wheel.firmware)

        vin_cur, vin_min, vin_max = smart_wheel.get_adc_values('Vin')
        if vin_min is not None:
            smart_wheel.set_label(self.GUI_VIN, vin_min)
            if vin_min < 10500:
                smart_wheel.set_color(self.GUI_VIN, 'red')
            else:
                smart_wheel.set_color(self.GUI_VIN, 'black')

        if smart_wheel.enabled:
            smart_wheel.set_label(self.GUI_WHEEL_ENABLED, 'true')
            smart_wheel.set_color(self.GUI_WHEEL_ENABLED, 'darkgreen')
        else:
            smart_wheel.set_label(self.GUI_WHEEL_ENABLED, 'false')
            smart_wheel.set_color(self.GUI_WHEEL_ENABLED, 'grey')

        if smart_wheel.is_connected():
            smart_wheel.set_color(self.GUI_CONNECTION_STATUS, 'darkgreen')
        else:
            smart_wheel.set_color(self.GUI_CONNECTION_STATUS, 'grey')

        # textual status
        smart_wheel.set_label(
            self.GUI_CONNECTION_STATUS, smart_wheel.connection.status())  
                    
        # counters
        smart_wheel.set_label(
            self.GUI_COUNTERS, 
            'threads: r=%d, w=%d. counts: r=%d, w=%d' % (
                smart_wheel.read_counter, smart_wheel.write_counter, 
                smart_wheel.total_reads, smart_wheel.total_writes))
            
    def button_fun(self, smart_wheel, tab, action):
        """
        Button function wrapper.

        Return the same function, but without the parameters. 
        """
        def new_fun():
            return self.button(smart_wheel, tab, action)
        return new_fun

    def message(self, smart_wheel, msg):
        """
        The message function to be called, thread safe.

        Actually adds message to queue because this function can be called from 
        a thread
        """
        self.gui_message_queue.append((smart_wheel, msg))

    def _message(self, smart_wheel, msg):
        """
        The actual message function that must be called from the main thread
        """
        smart_wheel.get_elem(self.GUI_OUTPUT_FIELD).insert('end -1 chars', msg + '\n')
        smart_wheel.get_elem(self.GUI_OUTPUT_FIELD).yview('end -1 chars')  # scroll down


def read_settings():
    """
    Read settings from SETTINGS_FILENAME and return contents.

    with error messages and exiting when something is wrong
    """
    try:
        with open(SETTINGS_FILENAME, 'r') as settings_file:
            settings = json.load(settings_file)
    except ValueError:
        print(
            "Invalid settings file [%s], consider copying example_settings.json over it." % SETTINGS_FILENAME)
        sys.exit(1)

    for k in {'default_settings', 'logrotate_filesize', 'logrotate_numfiles', 'log_path'}:
        if k not in settings:
            print("Missing key [%s] in settings file [%s], look at example_settings.json" % (k, SETTINGS_FILENAME))
            sys.exit(1)
    return settings


def main():
    # read settings, must be valid json
    settings = read_settings()

    # set up logging
    setup_logging(
        settings['log_path'], 
        file_level=logging.DEBUG, 
        console_level=logging.INFO,
        logrotate_filesize=settings['logrotate_filesize'],
        logrotate_numfiles=settings['logrotate_numfiles'],
        # file_formatter='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # console_formatter='%(asctime)8s %(levelname)5s - %(message)s'
        )

    logger.info(70*"*")
    logger.info("*** SWM GUI ".ljust(70, '*'))
    logger.info(70*"*")
    logger.info("")

    logger.info("log_path: %s" % settings['log_path'])
    logger.info("logrotate_filesize: %s" % settings['logrotate_filesize'])
    logger.info("logrotate_numfiles: %s" % settings['logrotate_numfiles'])
    
    parser = argparse.ArgumentParser(description='Smart Wheel GUI.')
    parser.add_argument('config_filenames', metavar='config_filenames', type=str, nargs='*',
                       help='config filenames, run "python3 config.py" if you do not have any.')
    
    args = parser.parse_args()
    logger.info("command line arguments: %s" % str(args))

    root = tk.Tk()
    root.title("SmartWheel controller")

    smart_modules = []
    smart_wheels_loaded = False
    has_argument_files = False
    load_state_failed = False

    config_filenames = args.config_filenames
    if config_filenames:
        logger.info("Starting from config filenames [%s]..." % ', '.join(config_filenames))
        has_argument_files = True
        
    if os.path.exists(GUI_STATE_FILENAME) and not has_argument_files:
        logger.info("Starting from state file [%s]..." % GUI_STATE_FILENAME)
        try:
            smart_modules = smart_wheels_from_state_file(GUI_STATE_FILENAME)
            smart_wheels_loaded = True
        except:
            logger.exception("Load from [%s] failed." % GUI_STATE_FILENAME)
    
    if not smart_wheels_loaded:
        if not config_filenames:  # if they didn't come from cmdline
            config_filenames = ['default_propeller.json', 'default_mock.json', 'default_ethernet.json', ]
            logger.info("Starting with default settings [%s]..." % ', '.join(config_filenames))
        for filename in config_filenames:
            logger.info('Reading config file [%s]...' % filename)
            conn = connection.Connection.from_file(filename)
            new_sm = SWMGuiElements(connection=conn, populate_incoming=POPULATE_INCOMING)
            smart_modules.append(new_sm)
            # If anything is wrong, it should have crashed

    # log files
    for sm in smart_modules:
        filename = os.path.join(
            settings['log_path'], '%s.log' % sm.extra['wheel_slug'])
        logger.info("Look for logfile at [%s]" % filename)
        # os.remove(filename)
        # if os.path.exists(filename):
            # logger.info("Delete existing logfile at [%s]" % filename)
            # os.remove(filename)

    interface = Interface(root, smart_modules)

    root.protocol("WM_DELETE_WINDOW", interface.quit)  # close window
    root.mainloop()


if __name__ == '__main__':
    main()  

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
UPDATE_TIME_SLOW = 0.5

GUI_STATE_FILENAME = '_guistate.json'

LOG_PATH = './logs'


def smart_wheels_from_state_file(filename):
    smart_modules = []
    with open(GUI_STATE_FILENAME, 'r') as f:
        sm_config = json.load(f)
    for single_config in sm_config:
        conn = connection.Connection.from_dict(single_config['config'])
        new_sm = SWMGuiElements(connection=conn)
        smart_modules.append(new_sm)
    return smart_modules


def state_file_from_smart_wheels(smart_wheels):
    tabs = []
    for swm in smart_wheels:
        tabs.append({'config': swm.connection.conf.as_dict()})
    with open(GUI_STATE_FILENAME, 'w') as state_file:
        json.dump(tabs, state_file, indent=2)


class SWMGuiElements(SWM):
    """
    Smart Wheel Module with Interface elements (with corresponding values).
    """

    def __init__(self, *args, **kwargs):
        super(SWMGuiElements, self).__init__(*args, **kwargs)
        self.elements = {}  # organize elements by key
        self.state = self.STATE_NOT_CONNECTED  # status slug. user updatable; for use in GUI
        self.wheel_gui = None  # the GUI where you can call handle_cmd_from_wheel, once initialized

    def set_elem(self, elem_name, elem_value):
        self.elements[elem_name] = elem_value

    def get_elem(self, elem_name):
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
        
        label = ttk.Entry(
            frame, 
            textvariable=self.elements[elem_var_name],
            **elem_args
            )
        self.elements[elem_name] = label
        return label

    def set_label(self, elem_name, elem_value):
        """
        Set a new value for a label or button
        """
        elem_var_name = '%s_var' % elem_name
        # Only set the value if it was different: prevent all kinds of GUI updating
        if self.elements[elem_var_name].get() != elem_value:
            self.elements[elem_var_name].set(elem_value)

    def set_color(self, elem_name, color_value):
        """color_value is something like '#356' """
        self.elements[elem_name].configure(foreground=color_value)

    def get_label(self, elem_name):
        """
        Get value for a label
        """
        elem_var_name = '%s_var' % elem_name
        return self.elements[elem_var_name].get()


class Interface():
    #GUI_CONNECT_BTN = 'connect_button'
    #GUI_DISCONNECT_BTN = 'disconnect_button'

    GUI_CONNECTION_NAME = 'connection_name_label'
    GUI_CONNECTION_STATUS = 'connection_status_label'
    GUI_CONNECTION_INFO = 'connection_info_label'

    GUI_STEER_SET_POINT = 'steer_set_point'
    GUI_STEER_ACTUAL = 'steer_actual'
    GUI_STEER_SCALE = 'steer_scale'

    GUI_SPEED_SET_POINT = 'speed_set_point'
    GUI_SPEED_ACTUAL = 'speed_actual'
    GUI_SPEED_SCALE = 'speed_scale'

    GUI_CONNECT_BUTTON = 'connect_button'
    GUI_DISCONNECT_BUTTON = 'disconnect_button'
    GUI_RESET_BUTTON = 'reset_button'

    GUI_ENABLE_BUTTON = 'enable_button'
    GUI_DISABLE_BUTTON = 'disable_button'
    GUI_EDIT_BUTTON = 'edit_button'

    GUI_FIRMWARE = 'firmware'

    GUI_VIN = 'vin'
    GUI_COUNTERS = 'counters'

    PADDING = '10 2 10 4'

    def __init__(self, root, smart_wheels):
        """Interface for SmartWheels, 

        makes an interface for a list of SWMGuiElements objects.
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
        menu_file.add_command(label='Quit', command=self.quit)
        
        # tabs
        note = ttk.Notebook(mainframe)
        note.grid(row=0, column=0)

        self.smart_wheels = smart_wheels
        self.gui_elements = {}

        self.steer_set_point = 0
        self.speed_set_point = 0
        
        for i, smart_wheel in enumerate(smart_wheels):  # every smart_wheel must have a unique name
            self.gui_elements[smart_wheel.name] = {}
            new_tab = ttk.Frame(note)
            
            row = 0
            ttk.Label(new_tab, text=smart_wheel.name).grid(row=row, column=0, columnspan=3)

            # pw = ttk.PanedWindow(new_tab, orient=tk.VERTICAL)

            # Connection
            row += 1
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
                label_frame_connection, text='status', foreground=GREY).grid(
                row=label_frame_row, column=0, sticky=tk.E)
            label = smart_wheel.create_label(
                label_frame_connection, self.GUI_CONNECTION_STATUS, 
                '')  # fill initially with empty
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
            
            row += 1
            ttk.Label(new_tab, text="Speed").grid(row=row, column=0)
            #ttk.Label(new_tab, text="200").grid(row=row, column=1)
            label = smart_wheel.create_label(
                new_tab, self.GUI_SPEED_SET_POINT, 
                str(self.speed_set_point))
            label.grid(row=row, column=1)
            label = smart_wheel.create_label(
                new_tab, self.GUI_SPEED_ACTUAL, 
                '-')
            label.grid(row=row, column=2)

            row += 1
            ttk.Label(new_tab, text="Steer").grid(row=row, column=0)
            label = smart_wheel.create_label(
                new_tab, self.GUI_STEER_SET_POINT, 
                str(self.steer_set_point))
            label.grid(row=row, column=1)
            label = smart_wheel.create_label(
                new_tab, self.GUI_STEER_ACTUAL, 
                '-')
            label.grid(row=row, column=2)

            row += 1
            speed_scale = ttk.Scale(new_tab, 
                from_=200, to=-200, 
                orient=tk.VERTICAL,
                command=self.set_speed_fun(smart_wheel))
            speed_scale.grid(row=row, column=2)
            smart_wheel.set_elem(self.GUI_SPEED_SCALE, speed_scale)
            
            row += 1
            steer_scale = ttk.Scale(new_tab, 
                from_=-1800, to=1800,
                orient=tk.HORIZONTAL,
                command=self.set_steer_fun(smart_wheel))
            steer_scale.grid(row=row, column=0, columnspan=3)
            smart_wheel.set_elem(self.GUI_STEER_SCALE, steer_scale)
            
            # input command
            row += 1
            input_field = ttk.Entry(new_tab)
            input_field.grid(row=row, column=0, columnspan=4, sticky=tk.NSEW)
            self.gui_elements[smart_wheel.name]['input_field'] = input_field

            # <return> executes the command
            input_field.bind('<Return>', self.event_fun(smart_wheel, new_tab))

            # command result
            row += 1

            scrollbar = tk.Scrollbar(new_tab)
            scrollbar.grid(row=row, column=5, columnspan=4, rowspan=3, sticky=tk.E)

            output_field = tk.Text(new_tab, yscrollcommand=scrollbar.set)
            output_field.grid(
                row=row, column=0, columnspan=4, rowspan=3, sticky=tk.NSEW)
            self.gui_elements[smart_wheel.name]['output_field'] = output_field

            scrollbar.config(command=output_field.yview)

            # status bar
            # row += 1
            # status = smart_wheel.create_label(
            #     mainframe, 'status', 'status info', 
            #     label_args=dict(relief=tk.SUNKEN, anchor=tk.W))
            # status.grid(row=row, column=0)
            
            note.add(new_tab, text="%d %s" % (i, smart_wheel.name))

            # start a thread for listening the smart wheel
            update_thread = threading.Thread(target=self.update_thread_fun(smart_wheel))
            update_thread.start()

            # subscribe myself for back logging
            smart_wheel.subscribe(self.message)
            self.update_gui_elements(smart_wheel)

        # for child in mainframe.winfo_children(): 
        #     child.grid_configure(padx=5, pady=5)
        self.last_slow_update = time.time()
        self.gui_message_queue = []
        self.update_me()

    def update_me(self):
        # main thread for updating GUI stuff.
    
        check_time = time.time()
        if check_time - self.last_slow_update > UPDATE_TIME_SLOW:
            self.last_slow_update = check_time

            for smart_wheel in self.smart_wheels:
                if smart_wheel.wheel_gui is not None:
                    smart_wheel.wheel_gui.update_status_from_wheel()

                self.update_gui_from_wheel(smart_wheel)
              
        # messages
        try:
            target, msg = self.gui_message_queue.pop(0)
            self._message(target, msg)
        except:
            # empty queue
            pass

        self.mainframe.after(10, self.update_me)

    def new_wheel(self):
        """
        Add new wheel
        """
        logger.info('Add new wheel (not yet implemented)')

    def on_resize(self, event):
        logger.info('Resizing...')

    def quit(self):
        """
        Add new wheel
        """
        logger.info('Quit')
        self.i_wanna_live = False
        for swm in self.smart_wheels:
            swm.shut_down()
        self.root.quit()
        # store my config
        state_file_from_smart_wheels(self.smart_wheels)
        logger.info('GUI state saved.')

    def set_steer(self, smart_wheel, new_steer):
        logger.info('Steer: %s, %s' % (smart_wheel, new_steer))
        self.steer_set_point = new_steer
        smart_wheel.set_label(self.GUI_STEER_SET_POINT, str(self.steer_set_point))
        cmd = '$2,%d,%d' % (self.speed_set_point, self.steer_set_point)
        self.message(smart_wheel, '-> [%s]' % cmd)
        smart_wheel.command(cmd)

    def set_steer_fun(self, smart_wheel):
        def fun(new_steer):
            return self.set_steer(smart_wheel, int(float(new_steer)))
        return fun

    def set_speed(self, smart_wheel, new_speed):
        logger.info('Speed: %s, %s' % (smart_wheel, new_speed))
        self.speed_set_point = new_speed
        smart_wheel.set_label(self.GUI_SPEED_SET_POINT, str(self.speed_set_point))
        cmd = '$2,%d,%d' % (self.speed_set_point, self.steer_set_point)
        self.message(smart_wheel, '-> [%s]' % cmd)
        smart_wheel.command(cmd)

    def set_speed_fun(self, smart_wheel):
        def fun(new_speed):
            return self.set_speed(smart_wheel, int(float(new_speed)))
        return fun

    def handle_command(self, smart_wheel, tab, event):
        command = self.gui_elements[smart_wheel.name]['input_field'].get()
        logger.debug("Handle: %s" % command)
        try:
            result = smart_wheel.command(command + '\r\n')
            self.message(smart_wheel, '-> [%s]' % result.strip())
        except NotConnectedException as ex:
            logger.exception("You're not connected yet.")
            self.message(smart_wheel, 'ERROR, you are not connected.')

    def event_fun(self, smart_wheel, tab):
        """
        return a button function without parameters with these parameters included 
        """
        def new_fun(event):
            return self.handle_command(smart_wheel, tab, event)
        return new_fun

    def update_gui_elements(self, smart_wheel):
        """
        Use smart_wheel.status to set the GUI status.
        """
        if smart_wheel.state == smart_wheel.STATE_CONNECTED:
            smart_wheel.get_elem(self.GUI_CONNECT_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_DISCONNECT_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_RESET_BUTTON)['state'] = tk.ACTIVE

            smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_EDIT_BUTTON)['state'] = tk.ACTIVE
        elif smart_wheel.state == smart_wheel.STATE_NOT_CONNECTED:
            smart_wheel.get_elem(self.GUI_CONNECT_BUTTON)['state'] = tk.ACTIVE
            smart_wheel.get_elem(self.GUI_DISCONNECT_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_RESET_BUTTON)['state'] = tk.DISABLED

            smart_wheel.get_elem(self.GUI_ENABLE_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_DISABLE_BUTTON)['state'] = tk.DISABLED
            smart_wheel.get_elem(self.GUI_EDIT_BUTTON)['state'] = tk.DISABLED

    def button(self, smart_wheel, tab, action):
        """Do the appropriate action for the current SmartWheel"""
        logger.info("button: %s for SmartWheel[%s]" % (action, str(smart_wheel)))
        try:
            if action == 'reset':
                sent = smart_wheel.reset()
                self.message(smart_wheel, '-> [%s]' % sent.strip())
                # input_value = self.gui_elements[smart_wheel.name]['input_field'].get()
                # print("input field value = %s" % input_value)
                # self.gui_elements[smart_wheel.name]['output_field'].insert('end -1 chars', input_value + '\n')
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
                # self.gui_elements[smart_wheel.name]['connect_btn'].textvariable = tk.StringVar(self.root, self.TEXT_DISCONNECT)
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
            elif action == 'enable-disable':
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
                    self.message(smart_wheel, '-> [%s]' % sent.strip())

        except NotConnectedException as err:
            self.message(smart_wheel, 'Oops, there was an error: {}'.format(err))

        smart_wheel.update_state()
        self.update_gui_elements(smart_wheel)

    def set_config(self, smart_wheel, config):
        logger.info("New smart wheel [%s] has new config [%s]" % (smart_wheel, config))
        smart_wheel.connection.conf = config
        smart_wheel.set_label(self.GUI_CONNECTION_NAME, config.name)
        smart_wheel.set_label(self.GUI_CONNECTION_INFO, str(config))

    # def close_me(self, target):
    #     target.destroy()

    def update_gui_from_wheel(self, smart_wheel):
        """
        cmd is a message as received with smart_wheel.incoming.pop(0)
        
        which is typically a list of strings.

        smart_wheel object is probably a target where you want to set variables
        """
        cmds = smart_wheel.cmd_from_wheel
        if SWM.CMD_ACT_SPEED_DIRECTION in cmds:
            cmd = cmds[SWM.CMD_ACT_SPEED_DIRECTION]
            # $13, actual wheel position, actual wheel speed, actual steer position, actual steer<CR>
            smart_wheel.set_label(self.GUI_SPEED_ACTUAL, str(cmd[2]))
            smart_wheel.set_label(self.GUI_STEER_ACTUAL, str(cmd[4]))
        if SWM.CMD_GET_FIRMWARE in cmds:
            cmd = cmds[SWM.CMD_GET_FIRMWARE]
            smart_wheel.set_label(self.GUI_FIRMWARE, ' '.join(cmd[1:]))
        if SWM.CMD_GET_VOLTAGES in cmds:
            cmd = cmds[SWM.CMD_GET_VOLTAGES]
            c = cmd[1+6]  # TODO: make better
            smart_wheel.set_label(self.GUI_VIN, c)  # avg for all vars, then all min, all max 
            vin_min = int(c)
            if vin_min < 10500:
                smart_wheel.set_color(self.GUI_VIN, 'red')
            else:
                smart_wheel.set_color(self.GUI_VIN, 'black')

        # textual status
        smart_wheel.set_label(
            self.GUI_CONNECTION_STATUS, smart_wheel.connection.status())  
                    
        # counters
        smart_wheel.set_label(
            self.GUI_COUNTERS, 
            'threads: r=%d, w=%d. counts: r=%d, w=%d' % (
                smart_wheel.read_counter, smart_wheel.write_counter, 
                smart_wheel.total_reads, smart_wheel.total_writes))
            
    def update_thread_fun(self, smart_wheel):
        """Thread for listening a specific smart wheel module"""
        def update_thread():
            # last_slow_update = time.time()
            # last_very_slow_update = time.time()
            has_update = True
            while self.i_wanna_live:
                # prevent this thread to eat all messages and prevent this thread to send any commands
                #while self.sub_window_open:  
                #    time.sleep(1)

                while smart_wheel.incoming:
                    new_message = smart_wheel.incoming.pop(0)  # thread safe?
                    logger.debug('new message: %s' % new_message)
                    # too much info
                    # self.message(smart_wheel, '<- %s' % new_message)  # update main gui
                                     
                time.sleep(UPDATE_TIME)
        return update_thread

    def button_fun(self, smart_wheel, tab, action):
        """
        return a button function without parameters with these parameters included 
        """
        def new_fun():
            return self.button(smart_wheel, tab, action)
        return new_fun

    def message(self, smart_wheel, msg):
        """
        The message function to be called
        """

        self.gui_message_queue.append((smart_wheel, msg))

    def _message(self, smart_wheel, msg):
        """
        The actual message function that must be called from the main thread
        """
        self.gui_elements[smart_wheel.name]['output_field'].insert('end -1 chars', msg + '\n')
        self.gui_elements[smart_wheel.name]['output_field'].yview('end -1 chars')  # scroll down


def main():
    #logging.basicConfig(level=logging.DEBUG)  # no file, only console
    # pre logging: delete main.log, if exists
    filename = os.path.join(LOG_PATH, 'main.log')
    if os.path.exists(filename):
        print("Delete existing logfile at [%s]" % filename)
        os.remove(filename)

    # set up logging
    setup_logging(
        LOG_PATH, 
        file_level=logging.DEBUG, 
        console_level=logging.DEBUG,
        # file_formatter='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # console_formatter='%(asctime)8s %(levelname)5s - %(message)s'
        )

    parser = argparse.ArgumentParser(description='Smart Wheel GUI.')
    parser.add_argument('config_filenames', metavar='config_filenames', type=str, nargs='*',
                       help='config filenames, run "python3 config.py" if you do not have any.')
    
    args = parser.parse_args()
    logger.info("command line arguments: %s" % str(args))

    root = tk.Tk()
    root.title("SmartWheel")

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
            config_filenames = ['propeller.json', 'testconf1.json', 'ethernet_config.json', ]
            logger.info("Starting with default settings [%s]..." % ', '.join(config_filenames))
        for filename in config_filenames:
            conn = connection.Connection.from_file(filename)
            new_sm = SWMGuiElements(connection=conn)
            smart_modules.append(new_sm)
            # If anything is wrong, it should have crashed

    # delete log files
    for sm in smart_modules:
        filename = os.path.join(LOG_PATH, '%s.log' % sm.extra['wheel_slug'])
        if os.path.exists(filename):
            logger.info("Delete existing logfile at [%s]" % filename)
            os.remove(filename)

    interface = Interface(root, smart_modules)

    root.protocol("WM_DELETE_WINDOW", interface.quit)  # close window
    root.mainloop()


if __name__ == '__main__':
    main()  

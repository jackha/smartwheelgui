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
    import tkFileDialog as filedialog
except ImportError:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import filedialog
import json
import sys
import connection
import logging
import threading
import time
import random

# UPDATE_TIME = 0.01
# UPDATE_TIME_SLOW = 2

logger = logging.getLogger(__name__)


class WheelGUI(object):

    PADDING = '10 2 10 4'
    CONTROL_PARAMS = [
        'Ksetp wheel',
        'Ksetp steer',
        'L lin wheel',
        'L lin steer',
        'MAE offset',
        'Vin min',
        'Module address',
        'Result']
    STATUS_PARAMS = [
        'PF status',
        'cnt: PID, PLC, MAE',
        'time (us): PID, PLC, MAE',
        ]
    STATUS_BITS = [
        '3 EnableBit',
        '4 Esconrdy1',
        '5 Esconrdy2',
        '7 WheelMove',
        '8 SteerMove',
        '9 JoystickAc',
        '10 Joystickm',
        '15 AlarmBit',
        ]
    ERROR_BITS = [
        '0 MAELimPlus',
        '1 MAELimMin',
        '2 MAECntrErr',
        '3 VinAlarm',
        '4 V5Alarm',
        '5 V3V3',
        '9 Current1',
        '10 Current2',
        '11 CommandFa',
        '14 Watchdog',
        '15 AlarmBit',
    ]
    ADC_COLUMNS = ('param', 'act', 'min', 'max')

    def __init__(
        self, root, parent=None, smart_wheel=None):
        self.root = root
        self.parent = parent  # parent window, or None
        self.smart_wheel = smart_wheel  # either a SWM object, can't be None
        self.i_wanna_live = True
        # self.root.protocol("WM_DELETE_WINDOW", self.close())

        mainframe = ttk.Frame(self.root, padding="5 5 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        for x in range(3):
            mainframe.columnconfigure(x, weight=1)
        for y in range(100):
            mainframe.rowconfigure(y, weight=1)

        # Control Parameters
        row = 0
        control_parameters = ttk.Labelframe(mainframe, text='Control Parameters', padding=self.PADDING)
        control_parameters.grid(row=row, column=0, columnspan=3, sticky="nsew")
        control_parameters.columnconfigure(0, weight=5)
        control_parameters.columnconfigure(1, weight=1)
        control_parameters.columnconfigure(2, weight=1)

        cp_row = 0
        for control_param in self.CONTROL_PARAMS:
            label = self.smart_wheel.create_label(control_parameters, '%s-label' % control_param, control_param)
            label.grid(row=cp_row, column=0, sticky=tk.W)
            label = self.smart_wheel.create_label(control_parameters, '%s-read' % control_param, '0')
            label.grid(row=cp_row, column=1, sticky=tk.E)
            label = self.smart_wheel.create_entry(control_parameters, '%s-input' % control_param, '0')
            label.grid(row=cp_row, column=2, sticky=tk.E)
            cp_row += 1

        ttk.Button(control_parameters, text="Load from EEPROM", command=self.load_from_wheel).grid(row=cp_row, column=0, sticky=tk.E)
        ttk.Button(control_parameters, text="Save to EEPROM", command=self.store_to_wheel).grid(row=cp_row, column=1, sticky=tk.E)

        # Status
        row += 1
        lf = ttk.Labelframe(mainframe, text='Status', padding=self.PADDING)
        lf.grid(row=row, column=0, sticky="nsew")
        lf.columnconfigure(0, weight=5)
        lf.columnconfigure(1, weight=1)
        
        lf_row = 0
        for status in self.STATUS_PARAMS:
            label = self.smart_wheel.create_label(lf, '%s-label' % status, status)
            label.grid(row=lf_row, column=0, sticky=tk.W)
            label = self.smart_wheel.create_label(lf, '%s-read' % status, '0')
            label.grid(row=lf_row, column=1, sticky=tk.E)
            lf_row += 1

        # Status bits
        lf = ttk.Labelframe(mainframe, text='Status bits', padding=self.PADDING)
        lf.grid(row=row, column=1, sticky="nsew")
        lf.columnconfigure(0, weight=5)
        lf.columnconfigure(1, weight=1)
        
        lf_row = 0
        for status in self.STATUS_BITS:
            label = self.smart_wheel.create_label(lf, '%s-label' % status, status)
            label.grid(row=lf_row, column=0, sticky=tk.W)
            label = self.smart_wheel.create_label(lf, '%s-read' % status, '0')
            label.grid(row=lf_row, column=1, sticky=tk.E)
            lf_row += 1
        
        # Error bits
        lf = ttk.Labelframe(mainframe, text='Error bits', padding=self.PADDING)
        lf.grid(row=row, column=2, sticky="nsew")
        lf.columnconfigure(0, weight=5)
        lf.columnconfigure(1, weight=1)
        
        lf_row = 0
        for status in self.ERROR_BITS:
            label = self.smart_wheel.create_label(lf, '%s-label' % status, status)
            label.grid(row=lf_row, column=0, sticky=tk.W)
            label = self.smart_wheel.create_label(lf, '%s-read' % status, '0')
            label.grid(row=lf_row, column=1, sticky=tk.E)
            lf_row += 1
            
        # ADC listbox
        row += 1
        lf = ttk.Labelframe(mainframe, text='ADC', padding=self.PADDING)
        lf.grid(row=row, column=0, columnspan=3, sticky="nsew")
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        
        tree = ttk.Treeview(lf)
         
        tree["columns"] = ('act', 'min', 'max')
        tree.column("act", width=10)
        tree.column("min", width=10)
        tree.column("max", width=10)
        tree.heading("act", text="act")
        tree.heading("min", text="min")
        tree.heading("max", text="max")
         
        for i in range(8):
            tree.insert("", "end", text="ADC %d" % i, values=('0', '0', '0'))
        
        tree.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW)
         
    def load_from_wheel(self):
        pass

    def store_to_wheel(self):
        pass

    def handle_cmd_from_wheel(self, cmd):
        logger.info('cmd from wheel: %s' % str(' '.join(cmd)))
        if cmd[0] == '$13':
            pass
        elif cmd[0] == '$10':  # measurements
            pass
        elif cmd[0] == '$11':  # status, error words
            status = random.randint(0, 65535)  # int(cmd[1])
            error = random.randint(0, 65535)  # int(cmd[2])
            self.smart_wheel.set_label('3 EnableBit-read', 0b0000000000001000 & status > 0)
            self.smart_wheel.set_label('4 Esconrdy1-read', 0b0000000000010000 & status > 0)
            self.smart_wheel.set_label('5 Esconrdy2-read', 0b0000000000100000 & status > 0)
            self.smart_wheel.set_label('7 WheelMove-read', 0b0000000010000000 & status > 0)
            self.smart_wheel.set_label('8 SteerMove-read', 0b0000000100000000 & status > 0)
            self.smart_wheel.set_label('9 JoystickAc-read', 0b0000001000000000 & status > 0)
            self.smart_wheel.set_label('10 Joystickm-read', 0b0000010000000000 & status > 0)
            self.smart_wheel.set_label('15 AlarmBit-read', 0b1000000000000000 & status > 0)

            self.smart_wheel.set_label('0 MAELimPlus-read', 0b0000000000000001 & error > 0)
            self.smart_wheel.set_label('1 MAELimMin-read', 0b0000000000000010 & error > 0)
            self.smart_wheel.set_label('2 MAECntrErr-read', 0b0000000000000100 & error > 0)
            self.smart_wheel.set_label('3 VinAlarm-read', 0b0000000000001000 & error > 0)
            self.smart_wheel.set_label('4 V5Alarm-read', 0b0000000000010000 & error > 0)
            self.smart_wheel.set_label('5 V3V3-read', 0b0000000000100000 & error > 0)
            self.smart_wheel.set_label('9 Current1-read', 0b0000001000000000 & error > 0)
            self.smart_wheel.set_label('10 Current2-read', 0b0000010000000000 & error > 0)
            self.smart_wheel.set_label('11 CommandFa-read', 0b0000100000000000 & error > 0)
            self.smart_wheel.set_label('14 Watchdog-read', 0b0100000000000000 & error > 0)
            self.smart_wheel.set_label('15 AlarmBit-read', 0b1000000000000000 & error > 0)


def wheel_gui(root, parent=None, smart_wheel=None,):
    root.title("Wheel: %s" % str(smart_wheel))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    gui = WheelGUI(
        root, parent=parent,
        smart_wheel=smart_wheel) 
    return gui

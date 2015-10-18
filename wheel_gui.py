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
import copy

from swm import SWM


logger = logging.getLogger(__name__)


def just_try_it(orig_fun, *args, **kwargs):
    def fun(*args, **kwargs):
        try:
            orig_fun(*args, **kwargs)
        except:
            # probably it is just a closed window so some functions don't work anymore
            # change to logger.exception if you want to see the error
            # logger.warning('Something strange happened, but I ignored it')
            pass
    return fun


class WheelGUI(object):

    PADDING = '10 2 10 4'
    CONTROL_PARAMS = [
        # label, label name (augmented with '-label', '-read' and '-input')
        ('Kpid wheel', 'kpid-wheel'),
        ('Kpid steer', 'kpid-steer'),
        ('Ilim wheel', 'ilim-wheel'),
        ('Ilim steer', 'ilim-steer'),
        ('MAE offset', 'mae-offset'),
        ('Vin min', 'vin-min'),
        ('Module address', 'module-address'),
        ]
    # find the corresponding parameter idx for controller
    CONTROL_PARAM_IDX = {
        'kpid-wheel': '0',
        'kpid-steer': '1',
        'ilim-wheel': '2',
        'ilim-steer': '3',
        'mae-offset': '4',
        'vin-min': '5',
        'module-address': '6',
    }
    STATUS_PARAMS = [
        'PF status',
        'cnt: PID, PLC, MAE',
        'time (us): PID, PLC, MAE',
        'process',
        'counters',
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
    
    LBL_FIRMWARE = 'firmware'

    def __init__(
        self, root, parent=None, smart_wheel=None):
        self.root = root
        self.parent = parent  # parent window, or None
        self.smart_wheel = smart_wheel  # either a SWM object, can't be None
        self.i_wanna_live = True

        self.initial_control_params = False
        # self.root.protocol("WM_DELETE_WINDOW", self.close())

        mainframe = ttk.Frame(self.root, padding="5 5 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        for x in range(3):
            mainframe.columnconfigure(x, weight=1)
        for y in range(100):
            mainframe.rowconfigure(y, weight=1)

        # Control Parameters
        row = 0
        info = ttk.Labelframe(mainframe, text='Info', padding=self.PADDING)
        info.grid(row=row, column=0, columnspan=3, sticky="nsew")
        info.columnconfigure(0, weight=5)
        
        ttk.Label(info, text='firmware').grid(row=row, column=0, sticky=tk.W)
        label = self.smart_wheel.create_label(info, self.LBL_FIRMWARE, '-')
        label.grid(row=row, column=1, sticky=tk.E)

        row += 1
        control_parameters = ttk.Labelframe(mainframe, text='Control Parameters', padding=self.PADDING)
        control_parameters.grid(row=row, column=0, columnspan=3, sticky="nsew")
        control_parameters.columnconfigure(0, weight=5)
        control_parameters.columnconfigure(1, weight=1)
        control_parameters.columnconfigure(2, weight=1)

        cp_row = 0
        for control_label, control_param in self.CONTROL_PARAMS:
            label = self.smart_wheel.create_label(control_parameters, '%s-label' % control_param, control_label)
            label.grid(row=cp_row, column=0, sticky=tk.W)
            label = self.smart_wheel.create_label(control_parameters, '%s-read' % control_param, '0')
            label.grid(row=cp_row, column=1, sticky=tk.E)
            label = self.smart_wheel.create_entry(control_parameters, '%s-input' % control_param, '0', elem_args={'justify': tk.RIGHT})
            label.grid(row=cp_row, column=2, sticky=tk.E)
            label.bind('<Return>', self.store_pid_fun(self.CONTROL_PARAM_IDX[control_param], '%s-input' % control_param))
            cp_row += 1

        ttk.Button(control_parameters, text="Load from EEPROM", command=self.load_from_wheel).grid(row=cp_row, column=0, sticky=tk.W)
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
        self.adc_lf = lf
        lf.grid(row=row, column=0, columnspan=3, sticky="nsew")
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        
        self.update_adc_table()

        btn = ttk.Button(lf, text='Reset min/max', command=self.reset_min_max_adc)
        btn.grid(row=1, column=0)
         
    @just_try_it
    def update_adc_table(self):
        self.adc_tree = ttk.Treeview(self.adc_lf)
         
        self.adc_tree["columns"] = ('act', 'min', 'max')
        self.adc_tree.column("act", width=10)
        self.adc_tree.column("min", width=10)
        self.adc_tree.column("max", width=10)
        self.adc_tree.heading("act", text="act")
        self.adc_tree.heading("min", text="min")
        self.adc_tree.heading("max", text="max")
         
        if (SWM.CMD_GET_ADC_LABELS in self.smart_wheel.cmd_from_wheel and
           SWM.CMD_GET_VOLTAGES in self.smart_wheel.cmd_from_wheel):
            # CMD_GET_ADC_LABELS returns "'$60', '8', 'Vin', '3V3', 'NC', 'Curr1', 'Curr2', 'Nc2', 'Nc3', 'NTC'"
            num_labels = int(self.smart_wheel.cmd_from_wheel[SWM.CMD_GET_ADC_LABELS][1])
            for i in range(num_labels):
                label = self.smart_wheel.cmd_from_wheel[SWM.CMD_GET_ADC_LABELS][i+2]
                adc = self.smart_wheel.cmd_from_wheel[SWM.CMD_GET_VOLTAGES]
                self.adc_tree.insert("", "end", text=label, values=(adc[i+1], adc[i+num_labels+1], adc[i+num_labels*2+1]))
        else:
            # no data from wheel
            self.adc_tree.insert("", "end", text="ADC", values=('n/a', 'n/a', 'n/a'))
        
        self.adc_tree.grid(row=0, column=0, columnspan=3, sticky=tk.NSEW)

    def reset_min_max_adc(self):
        self.smart_wheel.command(self.smart_wheel.CMD_RESET_MIN_MAX_ADC)

    def load_from_wheel(self):
        self.smart_wheel.command(self.smart_wheel.CMD_LOAD_FROM_CONTROLLER)

    def store_to_wheel(self):
        self.smart_wheel.command(self.smart_wheel.CMD_STORE_IN_CONTROLLER)

    def store_pid(self, param_idx, param_value):
        self.smart_wheel.command('$51,%s,%s' % (str(param_idx), param_value))

    def store_pid_fun(self, param_idx, entry_name):
        def fun(event): 
            return self.store_pid(str(param_idx), self.smart_wheel.get_elem(entry_name).get())
        return fun

    def update_status_from_wheel(self):
        """
        update gui from status of wheel - do not call too often
        """
        # see if dict is sometimes changed during read
        wheel_values = copy.deepcopy(self.smart_wheel.cmd_from_wheel)

        for cmd_response in wheel_values.values():
            self.handle_cmd_from_wheel(cmd_response)
        self.update_adc_table()

    def set_control_params(self):
        if '$50' not in self.smart_wheel.cmd_from_wheel:
            return
        cmd = self.smart_wheel.cmd_from_wheel['$50']
        self.smart_wheel.set_label('kpid-wheel-input', cmd[1])
        self.smart_wheel.set_label('kpid-steer-input', cmd[2])
        self.smart_wheel.set_label('ilim-wheel-input', cmd[3])
        self.smart_wheel.set_label('ilim-steer-input', cmd[4])
        self.smart_wheel.set_label('mae-offset-input', cmd[5])
        self.smart_wheel.set_label('vin-min-input', cmd[6])
        self.smart_wheel.set_label('module-address-input', cmd[7])

    def handle_cmd_from_wheel(self, cmd):
        if cmd[0] == '$10':  # measurements, run $60 to find out number of measurements
            pass
        elif cmd[0] == '$11':  # status, error words
            status = int(cmd[1])
            error = int(cmd[2])
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
        elif cmd[0] == '$13':
            pass
        elif cmd[0] == '$29':
            # firmware
            self.smart_wheel.set_label(self.LBL_FIRMWARE, ' '.join(cmd[1:]))
        elif cmd[0] == '$50':
            self.smart_wheel.set_label('kpid-wheel-read', cmd[1])
            self.smart_wheel.set_label('kpid-steer-read', cmd[2])
            self.smart_wheel.set_label('ilim-wheel-read', cmd[3])
            self.smart_wheel.set_label('ilim-steer-read', cmd[4])
            self.smart_wheel.set_label('mae-offset-read', cmd[5])
            self.smart_wheel.set_label('vin-min-read', cmd[6])
            self.smart_wheel.set_label('module-address-read', cmd[7])
            if self.initial_control_params is False:
                self.set_control_params()
                self.initial_control_params = True
        elif cmd[0] == '$58':
            # process times  4 numbers
            self.smart_wheel.set_label('process-read', ' '.join(cmd[1:]))
        elif cmd[0] == '$59':
            # counters  3 numbers
            self.smart_wheel.set_label('counters-read', ' '.join(cmd[1:]))


def wheel_gui(root, parent=None, smart_wheel=None,):
    root.title("Wheel: %s" % str(smart_wheel))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    gui = WheelGUI(
        root, parent=parent,
        smart_wheel=smart_wheel) 
    return gui

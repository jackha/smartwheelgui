import json
import threading
import connection
import logging

from time import sleep
from serial import Serial


def connected_fun(func):
    """
    decorator that checks connection before doing something with the connection
    """
    def fun(self, *args, **kwargs):
        if not self.connection.is_connected():
            self.message("you're not connected. try connecting first.")
            raise connection.NotConnectedException("you're not connected. try connecting first.")
        else:
            return func(self, *args, **kwargs)
    return fun


class SWM(object):
    """
    Smart wheel module: SmartWheel (or other serial object) python binding

    The class uses threads for read and write separately, and a semaphore to 
    prevent events to happen simultaneous.
    """
    CMD_DISABLE = '$0'
    CMD_ENABLE = '$1'
    CMD_RESET = '$8'
    CMD_RESET_MIN_MAX_ADC = '$9'
    CMD_GET_VOLTAGES = '$10'
    CMD_ACT_SPEED_DIRECTION = '$13'
    CMD_GET_FIRMWARE = '$29'
    CMD_GET_COUNTERS = '$59'
    CMD_GET_ADC_LABELS = '$60'
    CMD_LOAD_FROM_CONTROLLER = '$97'
    CMD_STORE_IN_CONTROLLER = '$98'

    SEPARATOR = '|'    

    STATE_CONNECTED = 'connected'
    STATE_NOT_CONNECTED = 'not-connected'

    def __init__(self, connection):
        #port, baudrate, timeout=10, name='', serial_wrapper=Serial):
        """
        port + baudrate
        """
        #self.serial_port = port
        #self.baudrate = baudrate

        self.connection = connection

        self.counter = 0
        self.enabled = False
        self.name = self.connection.conf.name

        # self.connected = False

        # add actions to the write queue and the write thread will consume them
        self.write_queue = []  
        self.i_wanna_live = True

        self.semaphore = threading.Semaphore()

        # this connects the port
        self.serial = None
        #self.serial_wrapper = serial_wrapper
        
        self.timeout = self.connection.conf.timeout  
        # self.serial = serial_wrapper(self.serial_port, self.baudrate, timeout=timeout)  # '/dev/ttyS1', 19200, timeout=1

        self._read_thread = threading.Thread(target=self.read_thread)
        self._read_thread.start()
        self._write_thread = threading.Thread(target=self.write_thread)
        self._write_thread.start()

        self.incoming = []  # to be filled with read data

        # report subscription: who wants to know my (debug) info??
        self.report_to = []

        # last answers from wheel per command. key is command code, i.e. '$13'
        self.cmd_from_wheel = {}  

    @classmethod
    def from_config(
        cls, filename):

        conn = connection.Connection.from_file(filename)
        return cls(conn)

    def read_thread(self):
        while self.i_wanna_live:
            try:
                if self.connection.is_connected():
                    new_read = self.connection.connection.readline()  # let's hope this never crashes
                    if new_read:
                        data_decoded = new_read
                        logging.debug("Read: %s" % data_decoded)
                        data_items = data_decoded.split(self.SEPARATOR)
                        for item in data_items:
                            cleaned_item = item.strip()
                            if cleaned_item:
                                # split and filter out empty items
                                cleaned_item_split = [i for i in cleaned_item.split(',') if i != '']  
                                self.incoming.append(cleaned_item_split)
                                # store me
                                self.cmd_from_wheel[cleaned_item_split[0]] = cleaned_item_split
            except:
                if self.connection.connection is None:
                    continue
                err_msg = self.connection.connection.get_and_erase_last_error()
                if err_msg:
                    self.message('ERROR in read thread from connection: %s' % err_msg)
            sleep(0.01)  # 10 ms sleep

    def write_thread(self):
        while self.i_wanna_live:
            try:
                if self.connection.is_connected():
                    write_item = self.write_queue.pop(0)
                    logging.debug("going to write '%s'" % write_item)
                    self.connection.connection.write(write_item)
            except:
                if self.connection.connection is None:
                    continue
                err_msg = self.connection.connection.get_and_erase_last_error()
                if err_msg:
                    self.message('ERROR in write thread from connection: %s' % err_msg)
            sleep(0.01)  # 10 ms sleep

    def subscribe(self, callback_fun):
        """Subscribe instance for messages. will be called with (smart_wheel instance, message)"""
        self.report_to.append(callback_fun)

    def connect(self):
        self.message("connect")
        logging.info("going to connect to connection!!")
        logging.debug(str(self.connection))
        # self.serial = self.serial_wrapper(
        #     self.serial_port, self.baudrate, timeout=self.timeout)  # '/dev/ttyS1', 19200, timeout=1
        return self.connection.connect()  # will create connection.connection

    def disconnect(self):
        return self.connection.disconnect()

    def is_connected(self):
        return self.connection.is_connected()

    def status(self):
        # TODO: return status of smartwheel as dict
        return {'status': 'ok', 'counter': self.counter} 

    def do_something(self):
        self.counter += 1

    @connected_fun
    def reset(self):
        self.message("reset")
        self.write_queue.append(self.CMD_RESET)
        return self.CMD_RESET

    @connected_fun
    def enable(self):
        self.enabled = True
        self.write_queue.append(self.CMD_ENABLE)
        self.message("enable")
        return self.CMD_ENABLE

    @connected_fun
    def disable(self):
        self.enabled = False
        self.write_queue.append(self.CMD_DISABLE)
        self.message("disable")
        return self.CMD_DISABLE

    @connected_fun
    def command(self, cmd, once=False):
        """
        'once' if we need only 1 reply with this command
        """
        self.message("Command: %s" % cmd, logging_only=True)
        if once:
            if cmd not in self.cmd_from_wheel.keys():
                self.write_queue.append(cmd)
        else:
            self.write_queue.append(cmd)
        return cmd

    def __str__(self):
        return self.name

    def shut_down(self):
        self.message("shut down issued")
        self.i_wanna_live = False

    def message(self, msg, logging_only=False):
        logging.debug("[%s] %s" % (str(self), msg))
        if not logging_only:
            for callback_fun in self.report_to:
                callback_fun(self, "[%s] %s" % (str(self), msg))

    def update_state(self):
        if self.connection.is_connected():
            self.state = self.STATE_CONNECTED
        else:
            self.state = self.STATE_NOT_CONNECTED

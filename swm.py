"""
Smart Wheel Module: SmartWheel python binding

The class uses threads for read and write separately.
"""
import json
import threading
import connection
import logging
import time

from collections import defaultdict
from time import sleep
from serial import Serial

logger = logging.getLogger(__name__)


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


def slugify(s):
    """
    non foolproof, but easy slugify function
    """
    return s.lower().replace(' ', '-')


class SWM(object):
    """
    Smart Wheel Module: SmartWheel python binding

    The class uses threads for read and write separately.

    You can use from_config to instantiate from a config filename.

    POLL_COMMANDS are polled with interval update_period using the write thread.
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

    # (command, only first time)
    POLL_COMMANDS = [
        ('$60', True),  # get adc labels
        ('$29', True),  # get afirmware
        ('$9', True),   # reset min max values adc
        ('$50', True), # get PID parameters

        ('$10', False),  # get voltages
        ('$11', False),  # get status and errors
        ('$13', False),  # get actual speed and direction
        #('$15', False),
        ('$58', False),  # get process times
        ('$59', False),  # get counters
    ]

    SEPARATOR = '|'    

    STATE_CONNECTED = 'connected'
    STATE_NOT_CONNECTED = 'not-connected'

    def __init__(self, connection, update_period=.1, populate_incoming=False):
        """
        connection object
        update_period in seconds: poll info approximately at this rate
        """

        self.connection = connection
        self.update_period = update_period

        self.counter = 0
        self.enabled = False

        #self.name = self.connection.conf.name
        #self.slug = slugify(self.name)

        # for logging
        # self.extra = self._extra()
        logger.info(70*"*", extra=self.extra)
        logger.info("*** New instance of SWM   ".ljust(70, '*'), extra=self.extra)
        logger.info(70*"*", extra=self.extra)
        logger.info("Connection info: %s" % str(connection))
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

        # to be filled with read data
        # if you want to do something with the raw smart wheel responses yourself.
        # (if populate_incoming)
        self.incoming = []  

        # determines if self.incoming is being populated as messages come in.
        self.populate_incoming = populate_incoming  
        logger.info("pop incoming %s" % self.populate_incoming, extra=self.extra)

        # report subscription: who wants to know my (debug) info??
        self.report_to = []

        # last answers from wheel per command. key is command code, i.e. '$13'
        self.cmd_from_wheel = {}

        # number of times a command is received
        self.cmd_counters = defaultdict(int)
        self.total_reads = 0
        self.total_writes = 0

        # used to check alivenes of threads
        self.read_counter = 0
        self.write_counter = 0

    @classmethod
    def from_config(cls, filename):
        """
        Use a config filename to instantiate a SWM.
        """
        conn = connection.Connection.from_file(filename)
        return cls(conn)

    def read_thread(self):
        """
        The read thread.

        Read character by character to prevent losing messages and to prevent 
        any blocking.
        """
        while self.i_wanna_live:
            try:
                if self.connection.is_connected():
                    # read a character at a time, until a CR is detected
                    new_read = ''
                    read_try = 0
                    while not new_read and read_try < 100:
                        new_read = self.connection.connection.readline()
                        read_try += 1

                    if new_read:
                        # something like: $50,10,20,6000,6000,2000,10500,1|
                        # or: $58,0,0,6094426,0,|
                        logger.debug("Read: %s" % new_read, extra=self.extra)
                        data_items = new_read.split(self.SEPARATOR)
                        for item in data_items:
                            cleaned_item = item.strip()
                            if cleaned_item:
                                # split and filter out empty items
                                cleaned_item_split = [i for i in cleaned_item.split(',') if i != '']
                                if self.populate_incoming:
                                    self.incoming.append(cleaned_item_split)
                                # store me
                                self.cmd_from_wheel[cleaned_item_split[0]] = cleaned_item_split
                                self.cmd_counters[cleaned_item_split[0]] += 1
                                self.total_reads += 1
                                if cleaned_item_split[0] == '$1':
                                    self.enabled = True
                                elif cleaned_item_split[0] == '$0':
                                    self.enabled = False
            except:
                if self.connection.connection is None:
                    continue
                err_msg = self.connection.connection.get_and_erase_last_error()
                if err_msg:
                    self.message('ERROR in read thread from connection: %s' % err_msg)
            self.update_state()

            sleep(0.01)  # 10 ms sleep
            self.read_counter += 1

    def write_thread(self):
        """
        The write thread.

        Write the self.write_queue to a connection, with redundancy.
        """
        next_poll = time.time()
        while self.i_wanna_live:
            try:
                if self.connection.is_connected():
                    while self.write_queue:  # thread safe?
                        write_item = self.write_queue.pop(0)
                        # logger.debug("going to write '%s'" % write_item)
                        self.connection.connection.write(write_item)
                        self.total_writes += 1
            except:
                if self.connection.connection is None:
                    continue
                err_msg = self.connection.connection.get_and_erase_last_error()
                if err_msg:
                    self.message('ERROR in write thread from connection: %s' % err_msg)
            
            # update variables poll
            if self.connection.is_connected():
                curr_time = time.time()
                do_poll = False
                if (curr_time - next_poll) > 10 * self.update_period:
                    next_poll = curr_time - self.update_period  # artificially set a new next_poll
                while next_poll < curr_time:
                    if do_poll:
                        # missed some update step
                        logger.info("missed update step: %s" % next_poll, extra=self.extra)
                    next_poll += self.update_period
                    do_poll = True
                if do_poll:  # in case we missed some update step, just do update once.
                    logger.debug('update poll', extra=self.extra)
                    for poll_cmd, poll_once in self.POLL_COMMANDS:
                        self.command(poll_cmd, once=poll_once)

            sleep(0.01)  # 10 ms sleep
            self.write_counter += 1

    def subscribe(self, callback_fun):
        """
        Subscribe function for messages. will be called with (smart_wheel instance, message)
        """
        self.report_to.append(callback_fun)

    def connect(self):
        """
        Connect the connection object
        """
        self.message("connect")
        logger.info("going to connect to connection!!", extra=self.extra)
        logger.debug(str(self.connection), extra=self.extra)
        return self.connection.connect()  # will create connection.connection

    def disconnect(self):
        """
        Disconnect the connection object, clear memory.
        """
        self.cmd_from_wheel = {}  # reset all we've got from the wheel
        return self.connection.disconnect()

    def is_connected(self):
        """
        is_connected
        """
        return self.connection.is_connected()

    # def status(self):
    #     # TODO: return status of smartwheel as dict
    #     return {'status': 'ok', 'counter': self.counter} 

    # def do_something(self):
    #     self.counter += 1

    @connected_fun
    def reset(self):
        """
        Reset command
        """
        self.message("reset")
        self.write_queue.append(self.CMD_RESET)
        return self.CMD_RESET

    @connected_fun
    def enable(self):
        """
        Enable command
        """
        self.write_queue.append(self.CMD_ENABLE)
        self.message("enable")
        return self.CMD_ENABLE

    @connected_fun
    def disable(self):
        """
        Disable command
        """
        self.write_queue.append(self.CMD_DISABLE)
        self.message("disable")
        return self.CMD_DISABLE

    @connected_fun
    def command(self, cmd, once=False):
        """
        Send command to write_queue

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
        return '{wheel_name} [{wheel_slug}]'.format(**self.extra)

    def shut_down(self):
        """
        shut_down, let threads die
        """
        self.message("shut down issued")
        self.i_wanna_live = False

    def message(self, msg, logging_only=False):
        """
        Message using log and optionally the callback function provided using 
        subscribe.
        """
        logger.debug("[%s] %s" % (str(self), msg), extra=self.extra)
        if not logging_only:
            for callback_fun in self.report_to:
                callback_fun(self, "[%s] %s" % (str(self), msg))

    def update_state(self):
        """
        Update mu state, called from read thread. If we do it in realtime (lazy 
        method), we risk writing on a disconnected connection.
        """
        if self.connection.is_connected():
            self.state = self.STATE_CONNECTED
        else:
            self.state = self.STATE_NOT_CONNECTED

    @property
    def name(self):
        """
        transparently pass connection config name as the smart wheel name
        """
        return self.connection.conf.name

    @property
    def extra(self):
        """
        return dict which can be used in logger.info(msg, extra=...)

        compose dict when called: it always uses actual variable values
        """
        name = self.name
        slug = slugify(self.connection.conf.name)
        return dict(wheel_name=name, wheel_slug=slug)
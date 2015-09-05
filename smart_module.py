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


class SmartModule(object):
    """
    SmartModule: SmartWheel (or other serial object) python binding

    The class uses threads for read and write separately, and a semaphore to 
    prevent events to happen simultaneous.
    """
    CMD_RESET = '$8\r\n'
    CMD_ENABLE = '$1\r\n'
    CMD_DISABLE = '$0\r\n'

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

    @classmethod
    def from_config(
        cls, filename):

        conn = connection.Connection.from_file(filename)
        return cls(conn)

    def read_thread(self):
        while self.i_wanna_live:
            #self.semaphore.acquire()
            #try:
            if self.connection.is_connected():
                new_read = self.connection.connection.readline()  # let's hope this never crashes
                if new_read:
                    data_decoded = new_read.decode('utf-8')
                    logging.debug("Read: %s" % data_decoded)
                    self.incoming.append(data_decoded)
                else:
                    #print('.')
                    pass
            #except:
            #    self.message("OOPS, serial read failed")
            #self.semaphore.release()
            # self.do_something()
            # self.message(self.counter)
            sleep(0.01)  # 10 ms sleep

    def write_thread(self):
        while self.i_wanna_live:
            try:
                if self.connection.is_connected():
                    write_item = self.write_queue.pop(0)
                #self.semaphore.acquire()
                #try:
                    logging.debug("going to write '%s'" % write_item)
                    # let's hope this never crashes
                    self.connection.connection.write(bytes(write_item, 'UTF-8'))  
                #except:
                #    self.message("OOPS, serial write failed")
                #self.semaphore.release()
            except IndexError:
                pass  # no more items in the write queue
            sleep(0.01)  # 10 ms sleep

    def connect(self):
        self.message("connect")
        logging.info("going to connect to connection!!")
        logging.debug(str(self.connection))
        # self.serial = self.serial_wrapper(
        #     self.serial_port, self.baudrate, timeout=self.timeout)  # '/dev/ttyS1', 19200, timeout=1
        self.connection.connect()  # will create connection.connection

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
    def command(self, cmd):
        self.message("Command: %s" % cmd)
        self.write_queue.append(cmd)
        return cmd

    def __str__(self):
        return self.name

    def shut_down(self):
        self.message("shut down issued")
        self.i_wanna_live = False

    def message(self, msg):
        logging.debug("[%s] %s" % (str(self), msg))

#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import json
import serial
import socket
import time
import threading

from serial import Serial
from mock_serial import MockSerial
from socket import error as socket_error
from socket import errno as socket_errno

logger = logging.getLogger(__name__)

# possible baudrates
BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 250000)  


class NotConnectedException(Exception):
    pass


class SocketWrapper(socket.socket):
    """All the functions readline and write"""
    CR = '\r\n'

    def __init__(self, *args, **kwargs):
        super(SocketWrapper, self).__init__(*args, **kwargs)
        self.last_error = ''

    def get_and_erase_last_error(self):
        result = self.last_error
        self.last_error = ''
        return result

    def readline(self):
        try:
            result = self.recv(1024)
        except socket_error as serr:
            self.last_error = 'connection error (%s).' % socket_errno.errorcode[serr.errno]
            raise serr
        if result:
            return result.decode('UTF-8')
        else:
            return result

    def write(self, s):
        logging.debug('Writing [%s]...' % s)
        try:
            self.send(bytes(s + self.CR, 'UTF-8'))
        except socket_error as serr:
            self.last_error = 'connection error (%s).' % socket_errno.errorcode[serr.errno]
            raise serr

    def disconnect(self):
        self.shutdown(socket.SHUT_RDWR)
        self.close()


class SerialWrapper(Serial):
    """
    Wrapper includes coding and decoding to/from utf-8
    """
    CR = '\r\n'

    def __init__(self, *args, **kwargs):
        super(SerialWrapper, self).__init__(*args, **kwargs)
        #self.semaphore = threading.Semaphore()
        self.last_error = ''
        self.current_read = ''  # buffer

    def get_and_erase_last_error(self):
        result = self.last_error
        self.last_error = ''
        return result

    def readline(self):
        """
        Our readline reads a character at a time. This prevents problems as 
        described below.

        The readline command takes the amount of timeout time (1 second). And if 
        during that time we use write command, the readline is stopped.
        """
        #self.semaphore.acquire()
        result = ''
        #try:
        # if 1:
            #logger.info('jaaa')
            #time_start = time.time()
            #result = super(SerialWrapper, self).readline()  # takes 1 second

        # read a character at a time: very fast
        ch = super(SerialWrapper, self).read().decode('UTF-8')  
        if ch == '\r' or ch == '\n':
            result = self.current_read
            self.current_read = ''
        else:
            self.current_read += ch 

            #    logger.info('yea')
            # logger.info('read ch: %s' % ch)
            #logger.info("read time: %f" % (time.time() - time_start))
        # except serial.serialutil.SerialException as e:
        #     #self.semaphore.release()
        #     self.last_error = str(e)
        #     raise e
        #self.semaphore.release()
        # if result:
        #     return result.decode('UTF-8')
        # else:
        #     return result
        return result

    def write(self, s):
        #self.semaphore.acquire()
        try:
            super(SerialWrapper, self).write(bytes(s + self.CR, 'UTF-8'))
        except serial.serialutil.SerialException as e:
            self.last_error = str(e)
            #self.semaphore.release()
            raise e
        #self.semaphore.release()

    def disconnect(self):
        """Using a semaphore, because you do not want to disconnect, while reading"""
        #self.semaphore.acquire()
        self.close()
        #self.semaphore.release()


class ConnectionConfig(object):
    """
    Keep connection info, as well as saving / loading connection configs.
    """

    CONNECTION_TYPE_SERIAL = 'serial'
    CONNECTION_TYPE_MOCK = 'mock'
    CONNECTION_TYPE_ETHERNET = 'ethernet'

    CONNECTION_TYPES = [
        CONNECTION_TYPE_SERIAL, CONNECTION_TYPE_MOCK, CONNECTION_TYPE_ETHERNET]

    def __init__(self):
        self.comport = None
        self.baudrate = None  # int
        self.timeout = 0  # int
        self.name = None
        self.ip_address = None
        self.ethernet_port = None
        self.connection_type = self.CONNECTION_TYPE_SERIAL

    def as_dict(self):
        """representation of self as a dict for serialization purposes"""
        result = None
        name = self.name if self.name else 'SmartWheel [%s]' % self.connection_type
        if self.connection_type == self.CONNECTION_TYPE_SERIAL:
            result = {
                'comport': self.comport, 'baudrate': self.baudrate, 
                'timeout': self.timeout,
                'name': name,  
                'connection_type': self.connection_type}
        elif self.connection_type == self.CONNECTION_TYPE_ETHERNET:
            result = {
                'name': name,  
                'connection_type': self.connection_type,
                'ip_address': self.ip_address,
                'ethernet_port': self.ethernet_port}
        elif self.connection_type == self.CONNECTION_TYPE_MOCK:
            result = {
                'name': name,  
                'connection_type': self.connection_type}
        return result

    def save(self, filename):
        logging.info("Saving [%s]..." % filename)
        with open(filename, 'w') as config_file:
            json.dump(self.as_dict(), config_file, indent=2)

    @classmethod
    def from_dict(cls, d):
        result = cls()
        result.set_vars(d)
        return result

    @classmethod
    def from_json(cls, json_string):
        cfg = json.loads(json_string)
        result = cls()
        result.set_vars(cfg)
        return result

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            cfg = json.load(f)
        result = cls()
        result.set_vars(cfg)
        return result

    def set_vars(self, cfg):
        """
        cfg is a dict with all necessary fields;
        
        function is used by from_json and from_file
        """
        self.set_var('connection_type', cfg['connection_type'])
        self.set_var('name', cfg['name'])

        if self.connection_type == self.CONNECTION_TYPE_SERIAL:
            self.set_var('comport', cfg['comport'])
            self.set_var('baudrate', int(cfg['baudrate']))
            self.set_var('timeout', int(cfg['timeout']))
        elif self.connection_type == self.CONNECTION_TYPE_ETHERNET:
            self.set_var('ip_address', cfg['ip_address'])
            self.set_var('ethernet_port', int(cfg['ethernet_port']))
        elif self.connection_type == self.CONNECTION_TYPE_MOCK:
            pass

    def set_var(self, var_name, var_value):
        """Use set_var for setting class variables, it provides extra error 
        checking.
        """
        if var_name == 'comport':
            self.comport = var_value
        elif var_name == 'baudrate':
            self.baudrate = var_value
        elif var_name == 'timeout':
            self.timeout = var_value
        elif var_name == 'name':
            self.name = var_value
        elif var_name == 'connection_type':
            self.connection_type = var_value
        elif var_name == 'ip_address':
            self.ip_address = var_value
        elif var_name == 'ethernet_port':
            self.ethernet_port = var_value
        else:
            logger.error("Tried to set unknown variable: %s" % var_name)

    def __str__(self):
        if self.connection_type == self.CONNECTION_TYPE_SERIAL:
            return "ConnectionConfig [%s]: serial port=%s, baudrate=%s, timeout=%s" % (
                self.name, self.comport, self.baudrate, self.timeout)
        elif self.connection_type == self.CONNECTION_TYPE_MOCK:
            return "ConnectionConfig [%s]: mock timeout=%s" % (self.name, self.timeout)
        elif self.connection_type == self.CONNECTION_TYPE_ETHERNET:
            return "ConnectionConfig [%s]: ethernet ip=%s port=%s" % (
                self.name, self.ip_address, self.ethernet_port)


class Connection(object):
    """
    A generic connection, using ConnectionConfig to instantiate ourselves

    It contains a conf, connect using 'connect' and you 
    will get a connection
    """

    def __init__(self):
        self.conf = None
        # self.connection_class = None
        self.connection = None  # it will remain None until 'connect' is called
        self.last_error = ''
        
    @classmethod
    def from_file(cls, filename):
        result = cls()
        result.conf = ConnectionConfig.from_file(filename)
        return result  # voila, a Connection object that is ready to rock & roll

    @classmethod
    def from_dict(cls, d):
        result = cls()
        result.conf = ConnectionConfig.from_dict(d)
        return result  # voila, a Connection object that is ready to rock & roll

    def connect(self):
        """
        create connection instance
        """
        if self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_SERIAL:
            logging.debug("port=%s" % self.conf.comport)
            logging.debug("baud=%s" % self.conf.baudrate)
            logging.debug("timeout=%s" % self.conf.timeout)
            try:
                connection = SerialWrapper(
                    port=self.conf.comport, baudrate=self.conf.baudrate, 
                    timeout=self.conf.timeout) 
            except serial.SerialException as ex:
                logging.exception("Could not connect serial")
                self.last_error = str(ex)
                raise
            logging.debug('yay')
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_MOCK:
            connection = MockSerial(timeout=self.conf.timeout)
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_ETHERNET:
            try:
                connection = SocketWrapper(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect((self.conf.ip_address, self.conf.ethernet_port))
            except socket_error as serr:
                if serr.errno == socket_errno.ECONNREFUSED:
                    self.last_error = 'connection refused (%s).' % socket_errno.errorcode[serr.errno]
                else:
                    self.last_error = 'connection error (%s).' % socket_errno.errorcode[serr.errno]
                raise serr
        # If all goes well.
        self.last_error = ''
        self.connection = connection

    def disconnect(self):
        connection = self.connection
        self.connection = None  # so no subthreads are using this connection
        connection.disconnect()  # now disconnect

    def is_connected(self):
        if self.connection is not None:
            return True
        else:
            return False

    def status(self):
        """return status string"""
        msg = []
        if self.is_connected():
            msg.append('connected')
        else:
            msg.append('not connected')
        if self.last_error:
            msg.append(self.last_error)
        if self.connection and self.connection.last_error:
            msg.append(self.connection.last_error)
        return '. '.join(msg)

    def __str__(self):
        return "Connection: conf=%s" % str(self.conf)
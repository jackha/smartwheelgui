#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import json
import serial
import socket

from serial import Serial
from mock_serial import MockSerial

logger = logging.getLogger(__name__)

# possible baudrates
BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 250000)  


class NotConnectedException(Exception):
    pass


class SocketWrapper(socket.socket):
    """All the functions readline and write"""
    def readline(self):
        result = self.recv(1024)
        if result:
            return result.decode('UTF-8')
        else:
            return result

    def write(self, s):
        logging.debug('Writing [%s]...' % s)
        self.send(bytes(s, 'UTF-8'))


class SerialWrapper(Serial):
    """
    Wrapper includes coding and decoding to/from utf-8
    """
    def readline(self):
        result = super(SerialWrapper, self).readline()
        if result:
            return result.decode('UTF-8')
        else:
            return result

    def write(self, s):
        super(SerialWrapper, self).write(bytes(s, 'UTF-8'))



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

    def save(self, filename):
        logging.info("Saving [%s]..." % filename)
        with open(filename, 'w') as config_file:
            name = self.name if self.name else 'SmartWheel [%s]' % self.connection_type
            if self.connection_type == self.CONNECTION_TYPE_SERIAL:
                json.dump(
                    {'comport': self.comport, 'baudrate': self.baudrate, 
                     'timeout': self.timeout,
                     'name': name,  
                     'connection_type': self.connection_type}, 
                    config_file, indent=2)
            elif self.connection_type == self.CONNECTION_TYPE_ETHERNET:
                json.dump(
                    {'name': name,  
                     'connection_type': self.connection_type,
                     'ip_address': self.ip_address,
                     'ethernet_port': self.ethernet_port}, 
                    config_file, indent=2)
            elif self.connection_type == self.CONNECTION_TYPE_MOCK:
                json.dump(
                    {'name': name,  
                     'connection_type': self.connection_type}, 
                    config_file, indent=2)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            cfg = json.load(f)
        result = cls()
        result.set_var('connection_type', cfg['connection_type'])
        result.set_var('name', cfg['name'])

        if result.connection_type == cls.CONNECTION_TYPE_SERIAL:
            result.set_var('comport', cfg['comport'])
            result.set_var('baudrate', int(cfg['baudrate']))
            result.set_var('timeout', int(cfg['timeout']))
        elif result.connection_type == cls.CONNECTION_TYPE_ETHERNET:
            result.set_var('ip_address', cfg['ip_address'])
            result.set_var('ethernet_port', int(cfg['ethernet_port']))
        elif result.connection_type == cls.CONNECTION_TYPE_MOCK:
            pass
        return result

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

    @classmethod
    def from_file(cls, filename):
        result = cls()
        result.conf = ConnectionConfig.from_file(filename)
        # if result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_SERIAL:
        #     result.connection_class = Serial
        # elif result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_MOCK:
        #     result.connection_class = MockSerial
        # elif result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_ETHERNET:
        #     result.connection_class = socket.socket
        return result  # voila, a Connection object that is ready to rock & roll

    def connect(self):
        """
        create connecion instance
        """
        if self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_SERIAL:
            logging.debug("port=%s" % self.conf.comport)
            logging.debug("baud=%s" % self.conf.baudrate)
            logging.debug("timeout=%s" % self.conf.timeout)
            try:
                self.connection = SerialWrapper(
                    port=self.conf.comport, baudrate=self.conf.baudrate, 
                    timeout=self.conf.timeout) 
            except serial.SerialException as ex:
                logging.exception("Could not connect serial")
                raise
            logging.debug('yay')
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_MOCK:
            self.connection = MockSerial(timeout=self.conf.timeout)
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_ETHERNET:
            self.connection = SocketWrapper(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.conf.ip_address, self.conf.ethernet_port))

    def is_connected(self):
        if self.connection is not None:
            return True
        else:
            return False

    def __str__(self):
        return "Connection: conf=%s" % str(self.conf)
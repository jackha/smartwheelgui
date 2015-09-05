#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import json

from serial import Serial
from mock_serial import MockSerial

logger = logging.getLogger(__name__)

# possible baudrates
BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 250000)  


class NotConnectedException(Exception):
    pass


class ConnectionConfig(object):
    """
    Keep connection info, as well as saving / loading connection configs.
    """

    CONNECTION_TYPE_SERIAL = 'serial'
    CONNECTION_TYPE_MOCK = 'mock'
    CONNECTION_TYPE_NETWORK = 'network'

    CONNECTION_TYPES = [
        CONNECTION_TYPE_SERIAL, CONNECTION_TYPE_MOCK, CONNECTION_TYPE_NETWORK]

    def __init__(self):
        self.comport = None
        self.baudrate = None  # int
        self.timeout = 1  # int
        self.name = None
        self.connection_type = self.CONNECTION_TYPE_SERIAL

    def save(self, filename='testconf1.json'):
        with open(filename, 'w') as config_file:
            json.dump(
                {'comport': self.comport, 'baudrate': self.baudrate, 
                 'timeout': self.timeout,
                 'name': self.name if self.name else 'SmartWheel [%s]' % self.connection_type,  
                 'connection_type': self.connection_type}, 
                config_file, indent=2)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            cfg = json.load(f)
        result = cls()
        result.set_var('comport', cfg['comport'])
        result.set_var('baudrate', int(cfg['baudrate']))
        result.set_var('timeout', int(cfg['timeout']))
        result.set_var('connection_type', cfg['connection_type'])
        result.set_var('name', cfg['name'])
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
        else:
            logger.error("Tried to set unknown variable: %s" % var_name)


class Connection(object):
    """
    A generic connection, using ConnectionConfig to instantiate ourselves

    It contains a connection_class and conf, connect using 'connect' and you 
    will get a connection
    """
    def __init__(self):
        self.conf = None
        self.connection_class = None
        self.connection = None  # it will remain None until 'connect' is called

    @classmethod
    def from_file(cls, filename):
        result = cls()
        result.conf = ConnectionConfig.from_file(filename)
        if result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_SERIAL:
            result.connection_class = Serial
        elif result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_MOCK:
            result.connection_class = MockSerial
        elif result.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_NETWORK:
            logger.warning(
                "connection type 'network' not implemented yet. taking mock instead")
            result.connection_class = MockSerial
        return result  # voila, a Connection object that is ready to rock & roll

    def connect(self):
        """
        create connecion instance
        """
        if self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_SERIAL:
            self.connection = self.connection_class(
                self.conf.comport, self.conf.baudrate, timeout=self.conf.timeout) 
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_MOCK:
            self.connection = self.connection_class(timeout=self.conf.timeout)
        elif self.conf.connection_type == ConnectionConfig.CONNECTION_TYPE_NETWORK:
            self.connection = self.connection_class(timeout=self.conf.timeout)

    def is_connected(self):
        if self.connection is not None:
            return True
        else:
            return False


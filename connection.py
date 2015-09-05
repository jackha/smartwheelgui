#!/usr/bin/python
# -*- coding: utf-8 -*-


BAUDRATES = ('9600', '19200' , '38400', '57600','115200', '230400', '250000')  # possible baudrates

class ConnectionConfig(object):
    def __init__(self):
        self.port = None
        self.baud = None
        self.connection_type = 'serial'

    def save(self, filename='testconf1.json'):
        with open(filename, 'w') as config_file:
            json.dump(
                {'comport': self.port, 'baudrate': self.baud}, config_file, indent=2)


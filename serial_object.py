import json


class SerialObject(object):
    """
    SerialObject: SmartWheel (or other serial object) python binding
    """
    def __init__(self, filename=None, port=None, baudrate=None, name=''):
        """
        optionally initialize from filename - or -
        port + baudrate
        """
        self.config = {}
        if filename is not None:
            with open(filename, 'r') as f:
                self.config = json.load(f)
        else:
            if port is not None:
                self.config['port'] = port
            if baudrate is not None:
                self.config['baudrate'] = baudrate

        self.counter = 0
        self.enabled = False
        self.name = name

    def initialize(self):
        # TODO: initialize serial port with these settings
        pass

    def connect(self):
        print("connect")

    def status(self):
        # TODO: return status of smartwheel as dict
        return {'status': 'ok', 'counter': self.counter} 

    def do_something(self):
        self.counter += 1

    def reset(self):
        print("reset")

    def enable(self):
        self.enabled = True
        print("enable")

    def disable(self):
        self.enabled = False
        print("disable")

    def command(self, cmd):
        print("Command: %s" % cmd)

    def __str__(self):
        return self.name

class MockSerial(object):
    def __init__(self, serial_port, baudrate, timeout=1, **kwargs):
        # '/dev/ttyS1', 19200, timeout=1
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout

        self.name = '%s:%d timeout=%d' % (
            self.serial_port, self.baudrate, self.timeout)

    def read(self, num=1):
        self.message("read %d" % num)
        return "a"

    def readline(self):
        return "this is a dummy line"

    def write(self, s):
        self.message("write %s" % s)

    def close(self):
        pass

    def __str__(self):
        return "[mock com: %s]" % self.name

    def message(self, msg):
        return "[%s] %s" % (str(self), msg)
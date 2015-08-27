import time


class MockSerial(object):
    def __init__(self, serial_port, baudrate, timeout=1, **kwargs):
        # '/dev/ttyS1', 19200, timeout=1
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout

        self.name = '%s:%d timeout=%d' % (
            self.serial_port, self.baudrate, self.timeout)

        self.incoming = []
        self.outgoing = []

        self.setpoint_speed = 0
        self.setpoint_dir = 0

        self.actual_steer_speed = 0
        self.actual_steer_pos = 0

        self.actual_wheel_speed = 0
        self.actual_wheel_pos = 0

        self.use_watchdog = False
        self.debug_screen = False

        # dummy values in mV
        self.vin = 12000
        self.v3v3 = 3260
        self.v5v = 5020
        # mA
        self.cur1 = 30
        self.cur2 = 50
        # milli degree
        self.temp = 30354

    def read(self):
        start_time = time.time()
        while not self.outgoing and (
            (time.time() - start_time < self.timeout) or (self.timeout is None)):

            time.sleep(0.001)  # block until there is something to give back
        if self.outgoing:
            return self.outgoing.pop(0)
        else:
            # print("serial timeout")
            return ''  # timeout occurred

    def readline(self):
        return "this is a dummy line"

    def write(self, s):
        self.message("write %s" % s)
        self.incoming.append(s)
        self._process_incoming()

    def close(self):
        pass

    def __str__(self):
        return "[mock com: %s]" % self.name

    def message(self, msg):
        return "[%s] %s" % (str(self), msg)

    def _process_incoming(self):
        """Generate fake responses to commands
        """
        if self.incoming:
            command_line = self.incoming.pop(0)
            response = None
            command = command_line.split(',')
            if command[0] == '$0':
                response = ['$0']
            elif command[0] == '$1':
                response = ['$1']
            elif command[0] == '$2':
                self.setpoint_speed = max(min(int(command[1]), -200), 200)
                self.setpoint_dir = max(min(int(command[2]), -1800), 1800)
                print("$2: speed=%d, dir=%d" % self.setpoint_speed, self.setpoint_dir)
                response = ['$2']
            elif command[0] == '$8':
                response = ['$8', '1']
            elif command[0] == '$9':
                response = ['$9', '1']
            elif command[0] == '$10':
                response = [
                    '$10',
                    str(self.vin), str(self.vin), str(self.vin), 
                    str(self.v3v3), str(self.v3v3), str(self.v3v3),
                    str(self.v5v), str(self.v5v), str(self.v5v),
                    str(self.cur1), str(self.cur1), str(self.cur1),
                    str(self.cur2), str(self.cur2), str(self.cur2),
                    str(self.temp), str(self.temp), str(self.temp),
                    ]
            elif command[0] == '$11':
                response = ['$11', str(1), str(0)]
            elif command[0] == '$13':
                response = ['$13', 
                    str(self.actual_steer_pos),
                    self.actual_steer_speed,
                    self.actual_wheel_pos,
                    self.actual_wheel_speed,]
            elif command[0] == '$15':
                response = ['$15', str(int(command[1]) + 1)]
            elif command[0] == '$16':
                if int(command[1]) == 1:
                    print("watchdog enabled")
                    self.use_watchdog = True
                else:
                    print("watchdog disabled")
                    self.use_watchdog = False
            elif command[0] == '$29':
                response = ['$29', 'mock']
            elif command[0] == '$50':
                response = ['$50', '1', '2', '3', '4', '5']
            elif command[0] == '$51':
                response = ['$51', '1']
            elif command[0] == '$58':
                response = ['$58', '103', '5', '2', '3']
            elif command[0] == '$59':
                response = ['$59', '103', '5', '2']
            elif command[0] == '$60':
                response = ['$60', 'labela', 'labelb']
            elif command[0] == '$90':
                response = ['$90']
                print("enable debug screen")
                self.debug_screen = True
            elif command[0] == '$91':
                response = ['$91']
                print("disable debug screen")
                self.debug_screen = False
            elif command[0] == '$97':
                response = ['$97']
                print("load values from eeprom")
            elif command[0] == '$98':
                response = ['$98']
                print("save values to eeprom")

            if response is not None:
                self.outgoing.append(','.join(response))
            else:
                print("warning: no response generated from command [%s]" % command_line)
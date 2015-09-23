import time
import logging
import random
from time import sleep


class MockSerial(object):
    def __init__(self, timeout=1, **kwargs):
        self.timeout = timeout

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

        self.adc = {}
        self.adc_min = {}
        self.adc_max = {}

        self.adc_labels = ['vin', 'v3v3', 'v5v', 'cur1', 'cur2', 'temp']

        # dummy values in mV
        self.adc['vin'] = 12000
        self.adc['v3v3'] = 3260
        self.adc['v5v'] = 5020
        # mA
        self.adc['cur1'] = 30
        self.adc['cur2'] = 50
        # milli degree
        self.adc['temp'] = 30354

        self.reset_adc_min_max()

        # must be 7 numbers
        self.pid = [0, 0, 0, 0, 0, 0, 0]
        self.pid_eeprom = [0, 0, 0, 0, 0, 0, 0]
        for i in range(7):
            self.pid[i] = i
            self.pid_eeprom[i] = i
        
        self.last_error = ''

    def reset_adc_min_max(self):
        for k in self.adc_labels:
            self.adc_min[k] = self.adc[k]
            self.adc_max[k] = self.adc[k]

    def update_random_adc(self):
        for k in self.adc_labels:
            self.adc[k] += random.randint(-10, 10)
            if self.adc[k] < self.adc_min[k]:
                self.adc_min[k] = self.adc[k]
            if self.adc[k] > self.adc_max[k]:
                self.adc_max[k] = self.adc[k]

    def get_and_erase_last_error(self):
        result = self.last_error
        self.last_error = ''
        return result
        
    def read(self):
        start_time = time.time()
        while not self.outgoing and (
            (time.time() - start_time < self.timeout) or (self.timeout is None)):

            time.sleep(0.001)  # block until there is something to give back
        if self.outgoing:
            return self.outgoing.pop(0)
        else:
            # logging.debug("serial timeout")
            return ''  # timeout occurred

    def readline(self):
        # return "this is a dummy line"
        return self.read()

    def write(self, data):
        #data = s.decode('utf-8')
        self.message("write %s" % data)
        self.incoming.append(data)
        self._process_incoming()

    def close(self):
        pass

    def __str__(self):
        return "[mock com]"

    def message(self, msg):
        return "[%s] %s" % (str(self), msg)

    def _process_incoming(self):
        """Generate fake responses to commands
        """
        if self.incoming:
            command_line = self.incoming.pop(0)
            response = None
            command = [c.strip() for c in command_line.split(',')]

            if command[0] == '$0':
                response = ['$0']
            elif command[0] == '$1':
                response = ['$1']
            elif command[0] == '$2':
                self.setpoint_speed = max(min(int(command[1]), -200), 200)
                self.setpoint_dir = max(min(int(command[2]), -1800), 1800)
                logging.debug("$2: speed=%d, dir=%d" % self.setpoint_speed, self.setpoint_dir)
                response = ['$2']
            elif command[0] == '$8':
                # reset
                response = ['$8', '1']
            elif command[0] == '$9':
                response = ['$9', '1']
                self.reset_adc_min_max()
            elif command[0] == '$10':
                response = ['$10', ]
                response.extend([str(self.adc[k]) for k in self.adc_labels])
                response.extend([str(self.adc_min[k]) for k in self.adc_labels])
                response.extend([str(self.adc_max[k]) for k in self.adc_labels])
            elif command[0] == '$11':
                response = ['$11', str(random.randint(0,65535)), str(random.randint(0,65535))]
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
                    logging.debug("watchdog enabled")
                    self.use_watchdog = True
                else:
                    logging.debug("watchdog disabled")
                    self.use_watchdog = False
            elif command[0] == '$29':
                response = ['$29', 'mock']
            elif command[0] == '$50':
                response = ['$50', ]
                response.extend([str(p) for p in self.pid])
            elif command[0] == '$51':
                response = ['$51', '1']
                self.pid[int(command[1])] = int(command[2])
                logger.info("pid param %s is now %s" % (command[1], command[2]))
            elif command[0] == '$58':
                response = ['$58', '103', '5', '2', '3']
            elif command[0] == '$59':
                response = ['$59', '103', '5', '2']
            elif command[0] == '$60':
                response = ['$60', str(len(self.adc_labels)), ]
                response.extend(self.adc_labels)
            elif command[0] == '$90':
                response = ['$90']
                logging.debug("enable debug screen")
                self.debug_screen = True
            elif command[0] == '$91':
                response = ['$91']
                logging.debug("disable debug screen")
                self.debug_screen = False
            elif command[0] == '$97':
                response = ['$97']
                logging.debug("load values from eeprom")
                for i in range(7):
                    self.pid[i] = self.pid_eeprom[i]
            elif command[0] == '$98':
                response = ['$98']
                logging.debug("save values to eeprom")
                for i in range(7):
                    self.pid_eeprom[i] = self.pid[i]

            if response is not None:
                self.outgoing.append(','.join(response))
            else:
                logging.debug("warning: no response generated from command [%s]" % command_line)

        sleep(0.1)
        self.update_random_adc()
        
    def disconnect(self):
        logging.debug('Close mock')
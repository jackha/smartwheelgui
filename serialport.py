__author__ = 'henk'

import serial
import threading
#import sys
import comportconfig
import json
import os.path
import listports

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

try:
    import ttk
    py3 = 0
except ImportError:
    import tkinter.ttk as ttk
    py3 = 1

serialconfig = {"baudrate":"115200", "comport": "COM2"}
filename = 'serialconfig.txt'
cbaudrates = ('9600', '19200' , '38400', '57600','115200', '230400', '250000')  # possible baudrates

class tserial:
    global ser      #global to allow read and write functions access
    global connected

    # Init serial port
    def __init__(self):

        ''' open serial port with timeout '''
        global ser      # global to allow read and write functions access
        global connected, filename, serialconfig
      #  global root
      #  root = top

        print(' init serial')
        serialconfig = self.readconfig(filename)        # get config from file or defaults if no file found

        try:
            ser = serial.Serial()       # set only known parameters
            ser.bytesize = serial.EIGHTBITS
            ser.parity = serial.PARITY_NONE
            ser.serial = serial.STOPBITS_ONE
            ser.bytesize = serial.EIGHTBITS
            ser.timeout=0.1

            ser.baudrate = serialconfig['baudrate']
            ser.port = serialconfig['comport']
            ser.close()
        except:
           print(' Error opening serial port')
        connected = False

        # start serial->console thread reading incoming strings
        r = threading.Thread(target=self.reader)
        r.setDaemon(1)
        r.start()           #Start read thread

    def  readconfig(self, filename):      # Read config from file
        print(' Open config: ', filename)
        if os.path.isfile(filename):          # check if config file exists and load config
            print ('File found')
            f = open(filename, 'r')
            #print(json.load(f))
            llconfig = json.load(f)
            print('llconfig: ', llconfig)
            localserialconfig = llconfig
            f.close()
            print('Loaded : ', localserialconfig)
        else:
            localserialconfig =  {"baudrate":cbaudrates[0], "comport": listports.serial_ports()[0]}
            print('Not found, defaults set ', localserialconfig)
     #   localserialconfig = llocalserialconfig
        return localserialconfig

    def  saveconfig(self, filename, localserialconfig):      # save config to file
        f = open(filename,'w')
        json.dump(localserialconfig, f, indent=2)
        f.close()
        print('Stored config : ', localserialconfig)

    def config_comport(self):       # open Tk window to configure serial port parameters

#        root = Tk()
#        root.title('Test_Comport1')
#        root.geometry('600x450+497+117')

        print('TestComport1_support.config_comport')
       # vrex_help.create_Vrex_Help(root)
        comportconfig.vp_start_gui()
#            create_ComportConfig(root, serialconfig)
    #    comportconfig.localserialconfig = comportconfig.localserialconfig
    #    print('new config',comportconfig.localserialconfig)
        sys.stdout.flush()

    # Interpret separated string parts
    def parse_strings(self, strlist):
        if strlist[0].isdecimal():
            received_command = int(float(strlist[0]))
            print("command : {0:d}".format(received_command))

    def set_baudrate(self, baudrate):
        global ser
        ser.baudrate = baudrate

    def set_port(self, comport):
        global ser
        ser.port = comport

    # Check and parse incoming string into separated parts
    def separate_string(self, instr):
        # search for $.
       # global parselist
        dollarpos = instr.find("$")
        print (instr)
        print("$ found at: {: ", (dollarpos))
        if dollarpos > -1:
            instr = instr[dollarpos+1:] # strip left part of string including dollar sign
            parselist = instr.split(",")
            print(parselist)
            for item in range(len(parselist)):
                #print(parselist[item] + " ") # = parselist[w].strip
                parselist[item] = parselist[item].strip(" ")
            print(parselist)
            self.parse_strings(parselist)    # interpret data in string parts

        else:
            print("!!! $ sign missing")

    # thread function reading lines from comport
    def reader(self):
        global connected
        print('Reader created')
        # loop forever and copy serial->console
        while 1 and connected:
            data = ser.readline()
            if len(data) > 0:
                data_decoded = data.decode('utf-8')
                print('in:' + data_decoded)
                self.separate_string(data_decoded)       # parse incoming string into a separated list

    # read line from keyboard and send to serial port with CRLF
    def writer(self, serialstring):
        print('>ser', serialstring)
        outstr = serialstring + '\r\n'
        ser.write(outstr.encode('utf-8'))

    # initialize program and variables
    def init_vars(self):
        global received_command
        global connected
        connected = False

    def ConnectPort(self, status):
        global connected
        if status:
            ser.open()
        else:
            ser.close()
        connected = status


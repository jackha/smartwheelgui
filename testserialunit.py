__author__ = 'henk'

import serialport

def main():
    global root

    ser = serialport.tserial()
    ser.config_comport()
    ser.ConnectPort(True)
    print('Done')

if __name__ == '__main__':
    main()
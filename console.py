""" 
console.py

a console for smart wheel module 

usage: console.py [-h] [--port PORT] connection_config_filename

"""
import argparse
import signal
import threading
import sys

from swm import SWM
from time import sleep

i_wanna_live = True

if __name__ == '__main__':
    global i_wanna_live
    print('smart wheel console')
    parser = argparse.ArgumentParser()
    parser.add_argument("connection_config_filename")
    parser.add_argument("--port", help="override conf filenames ethernet port")

    args = parser.parse_args()
    
    config_filename = args.connection_config_filename

    module = SWM.from_config(config_filename)

    if args.port:
        module.connection.conf.ethernet_port = int(args.port)
        print('Ethernet port: %s' % module.connection.conf.ethernet_port)

    print('connecting...')
    module.connect()

    def worker():
        global i_wanna_live
        while i_wanna_live:
            while module.incoming:
                new_message = module.incoming.pop(0)
                print('<- [%s]' % new_message)
            sleep(0.01)
    
    t = threading.Thread(target=worker)
    t.start()

    def term_handler(signal, frame):
        global i_wanna_live
        print('shutting down...')
        module.shut_down()
        i_wanna_live = False
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)

    print("ready.")

    while 1:
        cmd = input()
        module.command(cmd)

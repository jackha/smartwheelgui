""" 
console.py

a console for smart wheel module 
"""
import argparse
import signal
import threading
import sys
import socket

from swm import SWM
from time import sleep

i_wanna_live = True

if __name__ == '__main__':
    global i_wanna_live
    print('smart wheel ethernet server')
    parser = argparse.ArgumentParser()
    parser.add_argument("connection_config_filename", help="local connection config")
    parser.add_argument("--host", help="default 127.0.0.1", default="127.0.0.1")
    parser.add_argument("--port", help="default 5000", default=5000)

    args = parser.parse_args()
    
    config_filename = args.connection_config_filename
    print('Config file: %s' % config_filename)
    print('Serving on [%s:%s]' % (args.host, args.port))

    module = SWM.from_config(config_filename)

    print('connecting to wheel module...')
    module.connect()

    def term_handler(signal, frame):
        global i_wanna_live
        print('shutting down...')
        module.shut_down()
        i_wanna_live = False
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)

    print("ready.")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((args.host, int(args.port)))
    i = 0
    while True:
        print('Listen')
        s.listen(1)
        i += 1
        conn, addr = s.accept()

        def worker():
            global i_wanna_live
            while i_wanna_live:
                while module.incoming:
                    new_message = module.incoming.pop(0)
                    print('sending [%s]' % new_message)
                    conn.send(bytes(new_message, 'UTF-8'))
                sleep(0.01)
        
        t = threading.Thread(target=worker)
        t.start()

        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            print("from remote [%s]" % data)
            if not data: break
            # conn.send(data)
            module.command(data.decode('UTF-8'))

            print(i, 'Data ', data)

        conn.close()

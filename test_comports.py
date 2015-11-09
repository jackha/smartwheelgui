"""
"""

from serial.tools.list_ports import comports
from config import comports_osx

if __name__ == '__main__':
    print('comports testprogram')
    print('looking for comports...')
    ports = comports()
    print('ports found:')

    if not ports:
        print('no comports found.')
        ports = comports_osx()
        if ports:
            print('ports found using custom version that behaves differently on osx')
        else:
            print('still no ports found')

    for p1, p2, p3 in ports:
        print('%s %s %s' % (p1, p2, p3))

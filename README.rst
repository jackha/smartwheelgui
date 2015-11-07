Overview
--------

This repository consist of a set of python tools written for the Opteq Smart 
Wheel Module (SWM in short).

- a GUI: The GUI has a set of basic operation commands as well as monitoring 
  functions.

- a python wrapper class SWM: this class can be used in your own program to
  control and monitor the SWM.

http://www.opteq.nl/


Prerequisities
--------------

You need python3 (tested with 3.4) with pyserial and tkinter. See below for 
installation instructions for each OS.


Ubuntu
======

Install python3 with python3-setuptools and tk.

    $ sudo apt-get install python3 python3-setuptools python3-tk

This will give you the commands python3 and easy_install3.

Install pip using Python 3's setuptools: run 

    $ sudo easy_install3 pip

this will give you the command pip3.2 (or pip-3.2 on raspbian).

Install your PyPI package pyserial: run 

    $ sudo pip3.2 install pyserial 


Raspbian jessie
===============

It seems that all the dependencies are already installed!

    $ sudo pip-3.2 install --upgrade pyserial

This will upgrade pyserial from 2.6 to 2.7.
The 'comports' function in version 2.6 is broken in our system and will give 
the error ``TypeError: can't use a string pattern on a bytes-like object``. 


OSX
===

Install python3 in a regular way. Starting from python3.4, pip is included
in the binaries, how convenient!

pyserial::

    $ pip3.4 install pyserial

you need a new ActiveTcl

https://www.python.org/download/mac/tcltk/


Testing
-------

Test the comports function using test_comports.

    $ python3 test_comports.py

If you get the error ``TypeError: can't use a string pattern on a bytes-like object``,
you may have to upgrade pyserial::

    $ sudo pip3.2 install --upgrade pyserial

output on mac::

    comports testprogram
    looking for comports...
    ports found:
    no comports found.
    ports found using custom version that behaves differently on osx
    /dev/tty.Bluetooth-Incoming-Port n/a n/a
    /dev/tty.Bluetooth-Modem n/a n/a
    /dev/tty.usbserial-DAYO2UPE n/a n/a

output on ubuntu::

    comports testprogram
    looking for comports...
    ports found:
    /dev/ttyS31 ttyS31 n/a
    ...
    /dev/ttyS2 ttyS2 n/a
    /dev/ttyS1 ttyS1 n/a
    /dev/ttyS0 ttyS0 n/a
    /dev/ttyUSB0 Future Technology Devices International, Ltd None  USB VID:PID=0403:6015 SNR=DAYO2UPE
    /dev/ttyACM0 ttyACM0 USB VID:PID=2341:0010 SNR=85235333135351A01151

    
Features
--------

Start the gui::

    $ python3 gui.py

You should see the main wheel control screen (using default settings). You can 
manage them using the Config button and the File menu.

The GUI program provides the basics of controlling and reading Smart Wheel 
Modules (SWM). The GUI is constantly updated with the latest state.

Manage SWMs:
- Add, set up and remove SWMs.
- Logging to each separate SWM in logs.
- When the program is closed, the GUI state is saved to _guistate.json
- If the _guistate.json is deleted, the next time the GUI is started with
  default settings.

Each separate SWM:
- Connection configuration (config.py)
- Connect / disconnect / reset
- Enable / disable / steer / speed the SWM
- Edit / inspect the SWM (wheel_gui.py)
- Low level commands to SWM.

Config
======

The default settings in settings.json looks like::

{
  "default_settings": ["default_propeller.json", "default_mock.json", "default_ethernet.json"],
  "logrotate_filesize": 1000000,
  "logrotate_numfiles": 10,
  "log_path": "./logs"
}

The settings are quite straight forward. Log files are created with the connection
name as filename. The log files are rotated according to the settings. 


Troubleshooting
===============

- If for any reason the gui configuration is messed up, you can quit the program,
  delete _guistate.json, and try again. This will start the program with defaults.

- If you cannot connect to the wheel module, try going to the config and see
  what comport you can select. Select one and try again.


Client-server
-------------

This feature is highly experimental.

You can start a server somewhere, for example on a raspberry pi::

    $ python3 server.py --host 192.168.1.36 --port 5000 wheel_config_pi.json

This will start the listening server.

In the GUI (on another computer), select ethernet connection, provide ip host 
address and port and press connect.



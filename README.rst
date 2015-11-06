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

python 3.4

pyserial::

    $ pip install pyserial

macosx
======

new ActiveTcl

https://www.python.org/download/mac/tcltk/


Ubuntu / raspbian
=================

Install package python3-setuptools: run 

    $ sudo apt-get install python3-setuptools

this will give you the command easy_install3.

Install pip using Python 3's setuptools: run 

    $ sudo easy_install3 pip

this will give you the command pip-3.2 like kev's solution.

Install your PyPI packages: run 

    $ sudo pip-3.2 install pyserial 

    
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


Ubuntu/linux list_ports Hack
----------------------------

source: https://github.com/AerospaceRobotics/RPLidar-SLAMbot/blob/master/README.md

Fixes list_ports in Python 3.  Do not apply this patch to pySerial if you are running Python 2.x.

Python3
=======

If you receive the error `TypeError: can't use a string pattern on a bytes-like object`, traced back to within pySerial, apply this patch (more info: [link](http://stackoverflow.com/questions/5184483/python-typeerror-on-regex)).

listports.patch
===============
Created with `diff -u list_ports_posix_old.py list_ports_posix_new.py > listports.patch`.

To use:

    cd /usr/lib/python3/dist-packages/serial
    sudo patch tools/list_ports_posix.py < /[path of patch file on your machine]/listports.patch

list_ports_posix_old.py
=======================
This is our backup of the `list_ports_posix.py` file.

list_ports_posix_new.py
=======================
This is what your `list_ports_posix.py` file should look like after applying the patch.

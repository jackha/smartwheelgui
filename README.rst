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

When the program is closed, the state is saved in _guistate.json. If 
_guistate.json is deleted, the next time the GUI is started with the default
settings.

Logfiles are created for every wheel module in the logs subfolder.


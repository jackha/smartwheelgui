Prerequisities
--------------

python 3.4

pyserial::

    $ pip install pyserial

macosx::

new ActiveTcl

https://www.python.org/download/mac/tcltk/

Ubuntu / raspbian
-----------------

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

Start the config screen::

    $ python3 config.py


In the gui, you can:

- Connect 

- Reset

- Type in commands manually

- Enable, disable

- Each wheel has a connection configuration as wel as a wheel configuration
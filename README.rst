Install OSX
-----------

Python 3

# download and install setuptools
curl -O https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
python3 ez_setup.py
# download and install pip
curl -O https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py
python3 get-pip.py

cd /usr/local/bin
ln -s ../../../Library/Frameworks/Python.framework/Versions/3.3/bin/pip pip

# use pip to install
pip install pyserial

# Don't want it?
pip uninstall pyserial


https://www.python.org/download/mac/tcltk/
#! /usr/bin/env python
#
# GUI module generated by PAGE version 4.4.4
# In conjunction with Tcl version 8.6
#    Aug 10, 2015 09:20:05 AM
import json

import comportconfig_support
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

import TestComport1_support
import comportconfig

serialconfig = {"baudrate":"115200", "comport": "COM2"}

def vp_start_gui(l_serialconfig):
    '''Starting point when module is the main routine.'''
    global val, w, root
    root = Tk()
 #   root.title('Test_Comport1')
#    TestComport1_support.ReadConfig()

    global serialconfig
    serialconfig = readconfig()

    root.title('SWC1 Comport1: ' + ',' + serialconfig['baudrate'] + ',' + serialconfig['comport'])
    root.geometry('600x450+497+117')
    w = frm_Comport1(root)
   # w.title('Test_Comport1 ')
    #updatetitle('Test_Comport1 ' + ',' + serialconfig['baudrate'] + ',' + serialconfig['comport'])
    TestComport1_support.init(root, w)
#    initvars()
#    ComportConfig.vp_start_gui()

    print('via: vp_start_gui' )
    root.mainloop()

w = None
def create_Test_Comport1(root, param=None):
    '''Starting point when module is imported by another program.'''
    global w, w_win, rt
    rt = root
    w = Toplevel (root)
    w.title('Test_Comport1 ')
#    w.title('Test_Comport1 ' + ',' + serialconfig['baudrate'] + ',' + serialconfig['comport'])
  #  w.updatetitle('Test_Comport1 ' + ',' + serialconfig['baudrate'] + ',' + serialconfig['comport'])
    w.geometry('600x450+497+117')
    w_win = frm_Comport1(w)
#    initvars()
    TestComport1_support.init(w, w_win, param)
    print('via: create_Test_Comport1' )
    return w_win

def destroy_Test_Comport1():
    global w
    w.destroy()
    w = None

def updatetitle(windowtitle):
    w.title = windowtitle

def readconfig():       #Read serial config from file
    f = open(comportconfig_support.filename, 'r')
    local_serialconfig = json.load(f)#[0]
    f.close()
  #  TestComport1.root.title('Test_Comport1 ' + ',' + TestComport1.serialconfig['baudrate'] + ',' + TestComport1.serialconfig['comport'])
    print('config: ', serialconfig)
    return local_serialconfig
   # return comportconfig_support.Readconfig

class frm_Comport1:

    def __init__(self, master=None):

        _bgcolor = 'wheat'  # X11 color: #f5deb3
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85' 
        _ana2color = '#d9d9d9' # X11 color: 'gray85' 
        font10 = "-family {Segoe UI} -size 9 -weight normal -slant "  \
            "roman -underline 0 -overstrike 0"
        font11 = "-family {DejaVu Sans Mono} -size 14 -weight normal "  \
            "-slant roman -underline 0 -overstrike 0"
        master.configure(background="#d0d0d0")
        master.configure(highlightbackground="#d9d9d9")
        master.configure(highlightcolor="black")

        self.btn_Connect = Button(master)
        self.btn_Connect.place(relx=0.77, rely=0.07, height=24, width=56)
        self.btn_Connect.configure(activebackground="#f4bcb2")
        self.btn_Connect.configure(activeforeground="#000000")
        self.btn_Connect.configure(background="#d0d0d0")
        self.btn_Connect.configure(command=TestComport1_support.connect_comport)
        self.btn_Connect.configure(disabledforeground="#a3a3a3")
        self.btn_Connect.configure(foreground="#000000")
        self.btn_Connect.configure(highlightbackground="wheat")
        self.btn_Connect.configure(highlightcolor="black")
        self.btn_Connect.configure(pady="0")
        self.btn_Connect.configure(text='''Connect''')

        self.btn_ = Button(master)
        self.btn_.place(relx=0.77, rely=0.13, height=24, width=57)
        self.btn_.configure(activebackground="#f4bcb2")
        self.btn_.configure(activeforeground="#000000")
        self.btn_.configure(background="#d0d0d0")
        self.btn_.configure(command=TestComport1_support.config_comport)
        self.btn_.configure(disabledforeground="#a3a3a3")
        self.btn_.configure(foreground="#000000")
        self.btn_.configure(highlightbackground="wheat")
        self.btn_.configure(highlightcolor="black")
        self.btn_.configure(pady="0")
        self.btn_.configure(text='''Config''')

        self.Entry1 = Entry(master)
        self.Entry1.place(relx=0.07, rely=0.07, relheight=0.06, relwidth=0.37)
        self.Entry1.configure(background="white")
        self.Entry1.configure(disabledforeground="#a3a3a3")
        self.Entry1.configure(font=font11)
        self.Entry1.configure(foreground="#000000")
        self.Entry1.configure(highlightbackground="#d9d9d9")
        self.Entry1.configure(highlightcolor="black")
        self.Entry1.configure(insertbackground="black")
        self.Entry1.configure(selectbackground="#c4c4c4")
        self.Entry1.configure(selectforeground="black")

        self.btn_Send = Button(master)
        self.btn_Send.place(relx=0.47, rely=0.07, height=24, width=37)
        self.btn_Send.configure(activebackground="#f4bcb2")
        self.btn_Send.configure(activeforeground="#000000")
        self.btn_Send.configure(background="#d0d0d0")
        self.btn_Send.configure(command=TestComport1_support.send)
        self.btn_Send.configure(disabledforeground="#a3a3a3")
        self.btn_Send.configure(foreground="#000000")
        self.btn_Send.configure(highlightbackground="wheat")
        self.btn_Send.configure(highlightcolor="black")
        self.btn_Send.configure(pady="0")
        self.btn_Send.configure(text='''Send''')

        self.Listbox1 = Listbox(master)
        self.Listbox1.place(relx=0.07, rely=0.18, relheight=0.68, relwidth=0.64)
        self.Listbox1.configure(background="white")
        self.Listbox1.configure(disabledforeground="#a3a3a3")
        self.Listbox1.configure(font=font11)
        self.Listbox1.configure(foreground="#000000")
        self.Listbox1.configure(highlightbackground="#d9d9d9")
        self.Listbox1.configure(highlightcolor="black")
        self.Listbox1.configure(selectbackground="#c4c4c4")
        self.Listbox1.configure(selectforeground="black")

        self.led_connect = Text(master)
        self.led_connect.place(relx=0.9, rely=0.07, relheight=0.05
                , relwidth=0.04)
        self.led_connect.configure(background="white")
        self.led_connect.configure(cursor="")
        self.led_connect.configure(font=font10)
        self.led_connect.configure(foreground="black")
        self.led_connect.configure(highlightbackground="wheat")
        self.led_connect.configure(highlightcolor="black")
        self.led_connect.configure(insertbackground="black")
        self.led_connect.configure(selectbackground="#c4c4c4")
        self.led_connect.configure(selectforeground="black")
        self.led_connect.configure(width=24)
        self.led_connect.configure(wrap=WORD)

    # def config_comport(self):
    #     print('TestComport1_support.config_comport')
    #    # vrex_help.create_Vrex_Help(root)
    #     comportconfig.create_ComportConfig(root)
    #     sys.stdout.flush()
    #
    # def connect_comport(self):
    #     #led_connect.configure(background="green")
    #     print('TestComport1_support.connect_comport')
    #     sys.stdout.flush()
    #
    # def send(send):
    #     print('TestComport1_support.send')
    #     sys.stdout.flush()
    #
    # def init(top, gui, arg=None):
    #     global w, top_level, root
    #     w = gui
    #     top_level = top
    #     root = top
    #     print('Init TestComport(support)')
    #
    # def destroy_window(send):
    #     # Function which closes the window.
    #     global top_level
    #     top_level.destroy()
    #     top_level = None


if __name__ == '__main__':
    vp_start_gui(serialconfig)




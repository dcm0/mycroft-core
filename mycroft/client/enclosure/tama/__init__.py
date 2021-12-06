# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import subprocess
import time
import sys
from alsaaudio import Mixer
from threading import Thread, Timer

import serial
import colorsys


import mycroft.dialog 
from mycroft.client.enclosure.base import Enclosure
from mycroft.api import has_been_paired
from mycroft.audio import wait_while_speaking
from mycroft.client.enclosure.tama.arduino import EnclosureArduino
from mycroft.client.enclosure.tama.eyes import EnclosureEyes
#from mycroft.client.enclosure.tama.mouth import EnclosureMouth
from mycroft.client.enclosure.tama.gaze import EnclosureGaze
from mycroft.enclosure.display_manager import \
    init_display_manager_bus_connection
from mycroft.configuration import Configuration, LocalConf, USER_CONFIG
from mycroft.messagebus.message import Message
from mycroft.util import play_wav, create_signal, connected, check_for_signal
from mycroft.util.audio_test import record
from mycroft.util.log import LOG
from queue import Queue
from mycroft.util.file_utils import get_temp_path

from mycroft.client.enclosure.tama.flaskapp.app import create_app

# The Tama writer

class EnclosureWriter(Thread):
    """
    Writes data to Serial port.
        # . Enqueues all commands received from Mycroft enclosures
           implementation
        # . Process them on the received order by writing on the Serial port

    E.g. Displaying a text on Mycroft's Mouth
        # . ``EnclosureMouth`` sends a text command
        # . ``EnclosureWriter`` captures and enqueue the command
        # . ``EnclosureWriter`` removes the next command from the queue
        # . ``EnclosureWriter`` writes the command to Serial port

    Note: A command has to end with a line break
    """

    def __init__(self, serial, bus, size=16):
        super(EnclosureWriter, self).__init__(target=self.flush)
        self.alive = True
        self.daemon = True
        self.serial = serial
        self.bus = bus
        self.commands = Queue(size)
        self.val = 0
        self.val0 = 0
        self.val1 = 1
        self.valx = 0
        self.valy = 0
        self.current_pos=[0,20]
        self.signs=[b'\x01', b'\x01']
        self.eye_alphas=[1.0,1.0]
        self.last_col = 'G'
        self.av = 'N'
        
        self.base_colours = {}
        self.base_colours['R'] = [255,0,0]
        self.base_colours['G'] = [0,255,0]
        self.base_colours['B'] = [0,0,255]
        self.base_colours['Y'] = [200,200,0]
        self.base_colours['P'] = [200,0,200]
        self.base_colours['C'] = [0,200,200]
        self.base_colours['W'] = [200,200,200]
        self.base_colours['N'] = [0,0,0]
        self.current_col = self.base_colours[self.last_col]
        
        
        self.start()

    def movement(self, x,y, point=False):
        if point: 
            self.current_pos[0]=x
            self.current_pos[1]=y
        else:
            self.current_pos[0]=self.current_pos[0]+x
            self.current_pos[1]=self.current_pos[1]+y

        if self.current_pos[0]<0:
            self.signs[0]=b'\x01'
        else:
            self.signs[0]=b'\xFF'

        if self.current_pos[1]>0:
            self.signs[1]=b'\x01'
        else:
            self.signs[1]=b'\xFF'
        LOG.info("Movement:" + str(self.current_pos[0]) +" "+ str(self.current_pos[1]) + " " + str(x) + " " +str(y))
        LOG.info("sign x/y:" + str(self.signs[0]) +" " + str(self.signs[1]))
    
    def hsv2rgb(h,s,v):
        return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

    def flush(self):
        while self.alive:
            try:
                cmd = self.commands.get() + '\n'
                #self.serial.write(cmd.encode())
                line = cmd
                print (line)
                sys.stdout.flush()
                if line=='GREEN\n':
                    #self.values = bytearray(['E','G', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('G'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='G'
                    self.current_col = self.base_colours[self.last_col]
                if line=='YELLOW\n':
                    #self.values = bytearray(['E','Y', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('Y'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='Y'
                    self.current_col = self.base_colours[self.last_col]
                if line=='RED\n':
                    #self.values = bytearray(['E','R', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('R'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='R'
                    self.current_col = self.base_colours[self.last_col]
                if line=='BLUE\n':
                    #self.values = bytearray(['E','B', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('B'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='B'
                    self.current_col = self.base_colours[self.last_col]
                if line=='CIAN\n':
                    #self.values = bytearray(['E','C', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('C'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='C'
                    self.current_col = self.base_colours[self.last_col]
                if line=='PINK\n':
                    #self.values = bytearray(['E','P', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('P'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='P'
                    self.current_col = self.base_colours[self.last_col]
                if line=='WHITE\n':
                    #self.values = bytearray(['E','W', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('W'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='W'
                    self.current_col = self.base_colours[self.last_col]
                if line=='NONE\n':
                    #self.values = bytearray(['E','N', 1, 0])
                    self.serial.write('E'.encode())
                    self.serial.write('N'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                    self.last_col='N'
                    self.current_col = self.base_colours[self.last_col]
                if line=='OPEN\n':
                    #self.values = bytearray(['T',1])
                    self.serial.write('T'.encode())
                    self.val=1
                    self.serial.write(self.val.to_bytes(1, 'little'))
                if line=='CLOSE\n':
                    #self.values = bytearray(['T',0])
                    self.serial.write('T'.encode())
                    self.val=0
                    self.serial.write(self.val.to_bytes(1, 'little'))
                if line=='HOME\n':
                    #self.values = bytearray(['M',1,0,1,0,0,0])
                    self.av = 'N'
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.current_pos[0]=0
                    self.current_pos[1]=20
                    self.signs[0]=b'\xFF'
                    self.signs[1]=b'\x01'
                    self.serial.write(self.val1.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val1.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                if line=='AVL\n':
                    #self.values = bytearray(['M',1,0,1,0,0,0])
                    if(self.av == 'N'):
                        self.serial.write('M'.encode())
                        self.val1=1
                        self.val0=0
                        self.movement(30,30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.av = 'L'
                    elif(self.av == 'R'):
                        #then should reverse the R and do L 
                        self.serial.write('M'.encode())
                        self.val1=1
                        self.val0=0
                        self.movement(30,-30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))  
                        self.val1=1
                        self.val0=0
                        self.movement(30,30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))  
                        self.av = 'L'
                        
                if line=='AVR\n':
                    #self.values = bytearray(['M',1,0,1,0,0,0])
                    LOG.info("AVR current av = "+self.av)
                    if(self.av == 'N'):
                        self.serial.write('M'.encode())
                        self.val1=1
                        self.val0=0
                        self.movement(-30,30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.av = 'R'
                    elif(self.av == 'L'):
                        #then should reverse the L and do R
                        self.serial.write('M'.encode())
                        self.val1=1
                        self.val0=0
                        self.movement(-30,-30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))  
                        self.val1=1
                        self.val0=0
                        self.movement(-30,30)
                        self.valx=abs(self.current_pos[0])
                        self.valy=abs(self.current_pos[1])
                        self.serial.write(self.signs[0])
                        self.serial.write(self.valx.to_bytes(1, 'little'))
                        self.serial.write(self.signs[1])
                        self.serial.write(self.valy.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))
                        self.serial.write(self.val0.to_bytes(1, 'little'))  
                        self.av = 'R'

                if line=='SHAKE\n':
                    #self.values = bytearray(['M',1,0,1,0,0,0])
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.movement(20,0)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    LOG.info("Shake:" +" "+ str(self.current_pos[0]) +" "+ str(self.current_pos[1]) +" "+ str(self.valx) +" "+ str(self.valy) +" "+ str(self.signs[0]) +" "+ str(self.signs[1]))
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.2)
                    self.serial.write('M'.encode())
                    self.movement(-40,0)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.2)
                    self.serial.write('M'.encode())
                    self.movement(40,0)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.2)
                    self.serial.write('M'.encode())
                    self.movement(-40,0)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.2)
                    self.serial.write('M'.encode())
                    self.movement(20,0)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                if line=='NOD\n':
                    #self.values = bytearray(['M',1,0,1,0,0,0])
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.movement(0,30)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.3)
                    self.serial.write('M'.encode())
                    self.valx=1
                    self.movement(0,-30)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.3)
                    self.serial.write('M'.encode())
                    self.valx=1
                    self.movement(0,30)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    time.sleep(0.3)
                    self.serial.write('M'.encode())
                    self.movement(0,-30)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                if line.find('HSV') != -1:
                    mylist = line.split(":")
                    self.current_col = self.hsv2rgb((float)(mylist[1]), (float)(mylist[2]), (float)(mylist[3]))
                    self.serial.write('C'.encode())
                    self.serial.write(((int)(self.current_col[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2])).to_bytes(1, 'little'))
                if line.find('COL') != -1:
                    mylist = line.split(":")
                    self.current_col[0]=(int)(mylist[1]) #r
                    self.current_col[1]=(int)(mylist[2]) #g
                    self.current_col[2]=(int)(mylist[3]) #b
                    self.serial.write('C'.encode())
                    self.serial.write(((int)(self.current_col[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2])).to_bytes(1, 'little'))
                if line.find('SQUINT') != -1:
                    mylist = line.split(":")
                    eye=(str)(mylist[1]) #EYE L/R
                    delta=(int)(mylist[2]) #Change in brighness
                    if eye=='L':
                       LOG.info("L has been selected")
                       self.eye_alphas[0]=delta/100
                    else:
                       LOG.info("R has been selected")
                       self.eye_alphas[1]=delta/100
                    self.serial.write('C'.encode())
                    self.serial.write(((int)(self.current_col[0]*self.eye_alphas[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1]*self.eye_alphas[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2]*self.eye_alphas[0])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[0]*self.eye_alphas[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[1]*self.eye_alphas[1])).to_bytes(1, 'little'))
                    self.serial.write(((int)(self.current_col[2]*self.eye_alphas[1])).to_bytes(1, 'little'))
                if line.find('MOVE') != -1:
                    self.av = 'N' #Should cancel any aversion I guess
                    mylist = line.split(":")
                    #self.valx=abs((int)(mylist[2])) #the abs seems to kill it...
                    #self.valy=abs((int)(mylist[3]))
                    #self.current_pos[0] = self.valx
                    #self.current_pos[1] = self.valy
                    #if mylist[1]=='1':
                    #    self.signs[0]=b'\x01'
                    #else:
                    #    self.signs[0]=b'\xFF'
                    #if mylist[3]=='1':
                    #    self.signs[1]=b'\x01'
                    #else:
                    #    self.signs[1]=b'\xFF'

                    #Do we still need the signs for this? I'm not sure any more 
                    LOG.info("Moving to " + mylist[2] + " " + mylist[4])
                    self.movement((int)(mylist[2]), (int)(mylist[4]), True)
                    self.valx=abs(self.current_pos[0])
                    self.valy=abs(self.current_pos[1])
                    self.serial.write('M'.encode())
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))

                    #LOG.info("Current position "+" "+ str(self.current_pos))
                    #self.serial.write('M'.encode())
                    #self.val1=1
                    #self.val0=0
                    #self.serial.write(self.signs[0])
                    #self.serial.write(self.valx.to_bytes(1, 'little'))
                    #self.serial.write(self.signs[1])
                    #self.serial.write(self.valy.to_bytes(1, 'little'))
                    #self.serial.write(self.val0.to_bytes(1, 'little'))
                    #self.serial.write(self.val0.to_bytes(1, 'little'))

                if  line=='\x1b[D\n':
                    self.current_pos[0]=self.current_pos[0]-1

                    if self.current_pos[0]<0:
                        self.signs[0]=b'\x01'
                    else:
                        self.signs[0]=b'\xFF'
                    if self.current_pos[1]>0:
                        self.signs[1]=b'\x01'
                    else:
                        self.signs[1]=b'\xFF'
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    LOG.info("Current position " +" "+ str(self.current_pos))
                if  line=='\x1b[C\n':
                    self.current_pos[0]=self.current_pos[0]+1


                    self.valx= abs(self.current_pos[0])
                    self.valy= abs(self.current_pos[1])

                    if self.current_pos[0]<0:
                        self.signs[0]=b'\x01'
                    else:
                        self.signs[0]=b'\xFF'
                    if self.current_pos[1]>0:
                        self.signs[1]=b'\x01'
                    else:
                        self.signs[1]=b'\xFF'
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    LOG.info("Current position "+" "+ str(self.current_pos) +" "+ str(self.valy))
                if  line=='\x1b[A\n':
                    self.current_pos[1]=self.current_pos[1]+1

                    self.valx= abs(self.current_pos[0])
                    self.valy= abs(self.current_pos[1])

                    if self.current_pos[0]<0:
                        self.signs[0]=b'\x01'
                    else:
                        self.signs[0]=b'\xFF'
                    if self.current_pos[1]>0:
                        self.signs[1]=b'\x01'
                    else:
                        self.signs[1]=b'\xFF'
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    LOG.info("Current position " +" "+ str(self.current_pos))

                if  line=='\x1b[B\n':
                    self.current_pos[1]=self.current_pos[1]-1

                    self.valx= abs(self.current_pos[0])
                    self.valy= abs(self.current_pos[1])

                    if self.current_pos[0]<0:
                        self.signs[0]=b'\x01'
                    else:
                        self.signs[0]=b'\xFF'
                    if self.current_pos[1]>0:
                        self.signs[1]=b'\x01'
                    else:
                        self.signs[1]=b'\xFF'
                    self.serial.write('M'.encode())
                    self.val1=1
                    self.val0=0
                    self.serial.write(self.signs[0])
                    self.serial.write(self.valx.to_bytes(1, 'little'))
                    self.serial.write(self.signs[1])
                    self.serial.write(self.valy.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    self.serial.write(self.val0.to_bytes(1, 'little'))
                    LOG.info("Current position  "+ str(self.current_pos))
                # Taking this from the tama_2019 tama.py file

                self.commands.task_done()
            except Exception as e:
                LOG.error("Writing error: {0}".format(e))
                print(
                    type(e).__name__,          # TypeError
                    __file__,                  # /tmp/example.py
                    e.__traceback__.tb_lineno  # 2
                )

    def write(self, command):
        self.commands.put(str(command))
        

    def stop(self):
        self.alive = False


class EnclosureTama(Enclosure):
    """
    Serves as a communication interface between Arduino and Mycroft Core.

    ``Enclosure`` initializes and aggregates all enclosures implementation.

    E.g. ``EnclosureEyes``, ``EnclosureMouth`` and ``EnclosureArduino``

    It also listens to the basic events in order to perform those core actions
    on the unit.

    E.g. Start and Stop talk animation
    """

    _last_internet_notification = 0

    def __init__(self):
        super().__init__()

        self.__init_serial()
        

        self.writer = EnclosureWriter(self.serial, self.bus)

        #create flask, flask manager and give it the bus and the writer
        #listen to the bus and write to thte bus 
        
        flask_app = create_app()
        flask_app.run(debug=True)

        # Seem to have to set the log level to DEBUG every time :-/
        
    
        # Prepare to receive message when the Arduino responds to the
        # following "system.version"
        self.bus.on("enclosure.started", self.on_arduino_responded)
        # self.arduino_responded = False
        # Send a message to the Arduino across the serial line asking
        # for a reply with version info.
        # self.writer.write("system.version")
        # Start a 5 second timer.  If the serial port hasn't received
        # any acknowledgement of the "system.version" within those
        # 5 seconds, assume there is nothing on the other end (e.g.
        # we aren't running a Mark 1 with an Arduino)
        #Timer(5, self.check_for_response).start()
        self.eyes = EnclosureEyes(self.bus, self.writer)
        #self.mouth = EnclosureMouth(self.bus, self.writer)
        self.system = EnclosureArduino(self.bus, self.writer)
        self.gaze = EnclosureGaze(self.bus, self.writer)
        self.__register_events()
        self.__reset()
        self.arduino_responded = True
        
        # Notifications from mycroft-core
        self.bus.on("enclosure.notify.no_internet", self.on_no_internet)
        # initiates the web sockets on display manager
        # NOTE: this is a temporary place to connect the display manager
        init_display_manager_bus_connection()

    def on_arduino_responded(self, event=None):
        self.eyes = EnclosureEyes(self.bus, self.writer)
        #self.mouth = EnclosureMouth(self.bus, self.writer)
        self.system = EnclosureArduino(self.bus, self.writer)
        self.__register_events()
        self.__reset()
        self.arduino_responded = True

        # verify internet connection and prompt user on bootup if needed
        if not connected():
            # We delay this for several seconds to ensure that the other
            # clients are up and connected to the messagebus in order to
            # receive the "speak".  This was sometimes happening too
            # quickly and the user wasn't notified what to do.
            Timer(5, self._do_net_check).start()

    def on_no_internet(self, event=None):
        if connected():
            # One last check to see if connection was established
            return

        if time.time() - Enclosure._last_internet_notification < 30:
            # don't bother the user with multiple notifications with 30 secs
            return

        Enclosure._last_internet_notification = time.time()

        # TODO: This should go into EnclosureMark1 subclass of Enclosure.
        if has_been_paired():
            # Handle the translation within that code.
            self.bus.emit(Message("speak", {
                'utterance': "This device is not connected to the Internet. "
                             "Either plug in a network cable or hold the "
                             "button on top for two seconds, then select "
                             "wifi from the menu"}))
        else:
            # enter wifi-setup mode automatically
            self.bus.emit(Message('system.wifi.setup', {'lang': self.lang}))

    def __init_serial(self):
        try:
            #For TAMA these should be '/dev/ttyS0',9600)#IK0312
            #added to the default config
            self.port = self.config.get("port")
            #self.port = '/dev/ttyS0'
            self.rate = self.config.get("rate")
            #self.rate = 9600
            self.timeout = self.config.get("timeout")
            self.serial = serial.serial_for_url(
                url=self.port, baudrate=self.rate, timeout=self.timeout)
            LOG.info("Connected to: %s rate: %s timeout: %s" %
                     (self.port, self.rate, self.timeout))
        except Exception:
            LOG.error("Impossible to connect to serial port: " +
                      str(self.port))
            raise

    def __register_events(self):
        #self.bus.on('enclosure.mouth.events.activate', self.__register_mouth_events)
        #self.bus.on('enclosure.mouth.events.deactivate', self.__remove_mouth_events)
        self.bus.on('enclosure.reset', self.__reset)
        #self.__register_mouth_events()

    '''
    #Commenting out the mouth stuff
     def __register_mouth_events(self, event=None):
        self.bus.on('recognizer_loop:record_begin', self.mouth.listen)
        self.bus.on('recognizer_loop:record_end', self.mouth.reset)
        self.bus.on('recognizer_loop:audio_output_start', self.mouth.talk)
        self.bus.on('recognizer_loop:audio_output_end', self.mouth.reset)

    def __remove_mouth_events(self, event=None):
        self.bus.remove('recognizer_loop:record_begin', self.mouth.listen)
        self.bus.remove('recognizer_loop:record_end', self.mouth.reset)
        self.bus.remove('recognizer_loop:audio_output_start',
                        self.mouth.talk)
        self.bus.remove('recognizer_loop:audio_output_end',
                        self.mouth.reset)
    '''

    def __reset(self, event=None):
        # Reset both the position and the eye colour to indicate the unit is
        # ready for input.
        self.eyes.reset()

    def speak(self, text):
        self.bus.emit(Message("speak", {'utterance': text}))

    def check_for_response(self):
        if not self.arduino_responded:
            # There is nothing on the other end of the serial port
            # close these serial-port readers and this process
            self.writer.stop()
            self.serial.close()
            self.bus.close()

    def _handle_pairing_complete(self, Message):
        """
            Handler for 'mycroft.paired', unmutes the mic after the pairing is
            complete.
        """
        self.bus.emit(Message("mycroft.mic.unmute"))


    def stop(self):
        self.eyes.close()
        self.gaze.shutdown()

    def _do_net_check(self):
        # TODO: This should live in the derived Enclosure, e.g. EnclosureMark1
        LOG.info("Checking internet connection")
        if not connected():  # and self.conn_monitor is None:
            if has_been_paired():
                # TODO: Enclosure/localization
                self.speak("This unit is not connected to the Internet. "
                           "Either plug in a network cable or check the "
                           "wifi settings. ")
            else:
                # Begin the unit startup process, this is the first time it
                # is being run with factory defaults.

                # TODO: This logic should be in EnclosureMark1
                # TODO: Enclosure/localization

                # Don't listen to mic during this out-of-box experience
                self.bus.emit(Message("mycroft.mic.mute"))
                # Setup handler to unmute mic at the end of on boarding
                # i.e. after pairing is complete
                self.bus.once('mycroft.paired', self._handle_pairing_complete)

                self.speak(mycroft.dialog.get('mycroft.intro'))
                wait_while_speaking()
                time.sleep(2)  # a pause sounds better than just jumping in

                # Kick off wifi-setup automatically
                data = {'allow_timeout': False, 'lang': self.lang}
                self.bus.emit(Message('system.wifi.setup', data))

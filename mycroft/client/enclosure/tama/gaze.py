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

from threading import Thread
import subprocess


class CameraManager:

    def __init__(bus, writer, threshold_time, wake_threshold, min_angle, max_angle):
        self.bus = bus
        self.writer = writer
        self.wake_threshold = wake_threshold
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.talking = False
        self.last = None
        self.volume_dropped = False
        self.count = 0
        self.iloop = 0
        self.threshold_time = threshold_time
        
    def lookEvent(event, other):
        command = event.data.get("data")
        #First update the threshold counts
        etime = time.time_ns()
        if (etime - self.last) <= self.threshold_time:
            self.count += 1
        else:
            self.count = 1
        self.last = etime
        
        #lets see if we have to start or claim an interaction
        if self.iloop == 0 && self.count > self.wake_threshold:
            self.talking = True
            self.bus.emit(Message('recognizer_loop:wakeword'))
        elif !other.talking && !self.talking && self.iloop < 5 && self.count > self.wake_threshold:
            #lets claim this interaction even if we didn't start it (wakeword)
            self.talking = True;
        
        #Should we move the eyes:
        #This should cover up to ouput
        if !other.talking && self.iloop < 5:
            self.bus.emit(Message('enclosure.eyes.look', command))
            
        #If we are in spoken output, just look anyway
        if self.iloop > 4:
            self.bus.emit(Message('enclosure.eyes.look', command))
            
    
    def cancelEvent(event, other):
        if self.talking:
            #If we are in the recognition phase then cancel
            if self.iloop < 5:
                self.bus.emit(Message('mycroft.stop'))
                self.talking = False
                self.count = 0
            else:
                #If we are giving output and the ownser isn't watching?
                #do we bother to check of other has gaze?
                self.bus.emit(Message('mycroft.volume.decrease','{"play_sound": False}'))
                self.volume_dropped = True
                
    def volumeReset():
        if self.volume_dropped:
            self.bus.emit(Message('mycroft.volume.increase','{"play_sound": False}'))
            self.volume_dropped = False

    def setLoop(loop):
        self.iloop = loop
        if self.iloop == 6:
            self.talking = False
            self.count = 0
            self.iloop = 0
            
    def setDOA(angle):
        if angle<self.max_angle && angle>self.min_angle:
            if other.talking && !self.talking:
                self.talking = True
                other.talking = False
        

class EnclosureGaze:
    """
    Starts and stops the Node service connected to the gaze cameras
    It would be nicer if this was using the Omron Python library
    but that doens't work in Python 3 ...
    
    """
    
    def runGazeNode():
        self.gazeServer = subprocess.run(["node", 'gaze.js'])
        self.bus.emit("enclosure.gaze.launched")

    def __init__(self, bus, writer):
        self.bus = bus
        self.writer = writer
        
        self.gazeServer = Thread(target=runGazeNode)
        self.gazeServer.start()
        
       

        #Interaction Loop
        # 0 = waiting for wakeword
        # 1 = wakeword detected
        # 2 = mic open
        # 3 = mic closed
        # 4 = recognised
        # 5 = playing output
        # 6 = playing output finshed
        self.iloop = 0
        self.volume_dropped = False
        
        #Config Variables - should put them in the config
        #time between detected gazes for them to be counted in mili-seconds
        self.threshold_time = 75
        #number of consecutive gazes to trigger a wakeword
        self.wake_threshold = 3
        
        #Camera Variables
        #Keeps trying to keep the logic in a class so my brain doesn't explode
        #with copy and paste code
        self.cameraR = CameraManager(bus, writer, threshold_time, wake_threshold, 10, 180)
        self.cameraL = CameraManager(bus, writer, threshold_time, wake_threshold, -10, -180)
        
        self.__init_events()

    def __init_events(self):
        self.bus.on('enclosure.eyes.right', self.right)
        self.bus.on('enclosure.eyes.right_cancel', self.right_cancel)
        self.bus.on('enclosure.eyes.left', self.left)
        self.bus.on('enclosure.eyes.left_cancel', self.left_cancel)
        self.bus.on('recognizer_loop:utterance', self.stateUpdate)
        self.bus.on('recognizer_loop:speech.recognition.unknown', self.stateUpdate)
        self.bus.on('recognizer_loop:record_begin', self.stateUpdate)
        self.bus.on('recognizer_loop:awoken', self.stateUpdate)
        self.bus.on('recognizer_loop:wakeword', self.stateUpdate)
        self.bus.on('recognizer_loop:record_end', self.stateUpdate)
        self.bus.on('recognizer_loop:no_internet', self.stateUpdate)
        self.bus.on('recognizer_loop:audio_output_start', self.stateUpdate)
        self.bus.on('recognizer_loop:audio_output_end', self.stateUpdate)
        self.bus.on('recognizer_loop:DOA', self.stateUpdate)
                        
                        
       
        
    def __del__(self):
        self.gazeServer.stop()


    def right(self, event=None):
        if event and event.data:
            self.cameraR.lookEvent(event, self.cameraL)
            
               
     def right_cancel(self, event=None):
        self.cameraR.cancelEvent(event, self.cameraL)
            
        
    def left(self, event=None):
        if event and event.data:
            self.cameraL.lookEvent(event, self.cameraR)
    
    def left_cancel(self, event=None):
        self.cameraL.cancelEvent(event, self.cameraR)
        

    def updateLoop(self, new_l):
        self.cameraR.setLoop(new_l)
        self.cameraL.setLoop(new_l)
        self.iloop = new_l
            
    def updateDOA(self, event):
        self.cameraR.setDOA(event.data.get('angle'))
        self.cameraR.setDOA(event.data.get('angle'))
        

    def resetVolume(self):
        self.cameraL.resetVolume()
        self.cameraR.resetVolume()
            

        #Interaction Loop
        # 0 = waiting for wakeword
        # 1 = wakeword detected
        # 2 = mic open
        # 3 = mic closed
        # 4 = recognised
        # 5 = playing output
        # 6 = playing output finshed
    def stateUpdate(self, event=None):
        if event:
            match event.Message.msg_type:
                case 'recognizer_loop:wakeword':
                    resetVolume(self)
                    updateLoop(self, 1)
                    
                case 'recognizer_loop:record_begin':
                    updateLoop(self, 2)
                
                case 'recognizer_loop:record_end':
                    updateLoop(self, 3)
                
                case 'recognizer_loop:utterance':
                    updateLoop(self, 4)
                    
                case 'recognizer_loop:speech.recognition.unknown':
                    #recognition failed - what do?
                    #send the shake command here, or catch this in eyes?
                    updateLoop(self, 4)
                
                case 'recognizer_loop:audio_output_start':
                    updateLoop(self, 5)
                    
                case 'recognizer_loop:audio_output_end':
                    updateLoop(self, 6)
                    #cameras update to 0 on this, keep local consistant even if it isn't used
                    self.iloop = 0
                    
                    
                case 'recognizer_loop:awoken':
                    #This actually should be opening head as opposed to sleep closing it
                
                case 'recognizer_loop:DOA':
                    updateDOA(self, event)

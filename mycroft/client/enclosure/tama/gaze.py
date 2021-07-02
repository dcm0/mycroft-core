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

from mycroft.messagebus.message import Message
from threading import Thread
import time
import subprocess
import mycroft.client.enclosure.tama.hvc.p2def as p2def
from mycroft.client.enclosure.tama.hvc.utils import *
from mycroft.client.enclosure.tama.hvc.serial_connector import SerialConnector
from mycroft.client.enclosure.tama.hvc.hvc_p2_api import HVCP2Api
from mycroft.client.enclosure.tama.hvc.hvc_tracking_result import HVCTrackingResult
from mycroft.client.enclosure.tama.hvc.grayscale_image import GrayscaleImage
from mycroft.util.log import LOG
from mycroft.util import play_wav, create_signal, connected, check_for_signal

class CameraManager(Thread):

    def __init__(self, threadID, bus, writer, threshold_time, wake_threshold, min_angle, max_angle, portinfo, baudrate):
        Thread.__init__(self)
        self.threadID = threadID
        self.bus = bus
        self.writer = writer
        self.wake_threshold = wake_threshold
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.talking = False
        self.last = time.time_ns()
        self.volume_dropped = False
        self.count = 0
        self.iloop = 0
        self.cancelCounter = 0
        self.cancelThreshold = 8
        self.threshold_time = threshold_time
        self.portinfo = portinfo
        self.baudrate = baudrate
        self.other = None
        self.detecting = False
        self.image = GrayscaleImage()

        self.connector = SerialConnector()
        self.hvc_p2_api = HVCP2Api(self.connector, exec_func, p2def.USE_STB_ON)
        LOG.info("Creating connections for camera "+str(self.threadID))
        # The 1st connection. (It should be 9600 baud.)
        self.hvc_p2_api.connect(self.portinfo, p2def.DEFAULT_BAUD, 10)
        try:
            check_connection(self.hvc_p2_api)
        except:
            LOG.info("Connection check failed "+str(self.threadID))

        self.hvc_p2_api.set_uart_baudrate(self.baudrate) # Changing to the specified baudrate
        self.hvc_p2_api.disconnect()
        LOG.info("Disconnecting setup event "+str(self.threadID))
        # The 2nd connection in specified baudrate
        self.hvc_p2_api.connect(self.portinfo, self.baudrate, 30)
        LOG.info("Main connection event "+str(self.threadID))
        try:
            check_connection(self.hvc_p2_api)
        except:
            LOG.info("Connection check failed "+str(self.threadID))


        try:
            # Sets HVC-P2 parameters
            set_hvc_p2_parameters(self.hvc_p2_api)
            LOG.info("Parameters sent "+str(self.threadID))
            # Sets STB library parameters
            set_stb_parameters(self.hvc_p2_api)
            LOG.info("Stb Sent "+str(self.threadID))
            self.hvc_tracking_result = HVCTrackingResult()
        except Exception as e:
            LOG.error("Unexpected error: {0}".format(e))


    def run(self):
        #start = time.time()
        LOG.info("Thread started "+str(self.threadID))
       
        #elapsed_time = str(float(time.time() - start) * 1000)[0:6]
        self.detecting = True
        while(self.detecting):
            (res_code, stb_status) = self.hvc_p2_api.execute(p2def.OUT_IMG_TYPE_NONE, self.hvc_tracking_result, self.image)
            time.sleep(0.2)
            if len(self.hvc_tracking_result.faces) > 0:
                #LOG.info("Face Detected "+str(self.threadID))
                try:
                    for i in range(len(self.hvc_tracking_result.faces)):
                        face = self.hvc_tracking_result.faces[i]
                        if face.gaze is not None: 
                            yaw = face.gaze.gazeLR
                            pitch = face.gaze.gazeUD
                            LOG.info("Face  p/y "+str(pitch)+" "+str(yaw)+" c:"+str(self.threadID))
                            if (pitch<10 and pitch>-2 and yaw<5 and yaw>-5):
                                #LOG.info("Look  "+str(face))
                                x = face.pos_x
                                y = face.pos_y
                                #LOG.info("Calc directions  "+str(x) + " " + str(y)+ " " + str(self.threadID))
                                (x_sign,x_m,y_sign,y_m)=getdeg(x,y)
                                x_m = x_m - 15 #15 = camera offset angle
                                x_m=abs(x_m)
                                y_m=abs(y_m)
                                LOG.info("x - y calculated "+str(x) + " " + str(y)+ " to " +str(x_m)+"/"+str(y_m)+" "+str(self.threadID))
                                etime = time.time_ns()
                                if (etime - self.last) <= self.threshold_time*100000000: #convert from mili to nanos 100000000
                                    self.count += 1 
                                else:
                                    LOG.info("Too Slow!  "+str(etime - self.last)+" / " + str(self.threshold_time*100000000)+ " "+str(self.threadID))    
                                    self.count = 1
                                self.last = etime
                                LOG.info("count  "+str(self.count)+" "+str(self.threadID))
                                #lets see if we have to start or claim an interaction
                                if self.iloop == 0 and self.count > self.wake_threshold:
                                    LOG.info("Starting interaction from gaze "+str(self.threadID))
                                    self.talking = True
                                    self.bus.emit(Message('mycroft.mic.listen'))
                                elif ((self.other.talking == False or self.other.cancelCounter > self.cancelThreshold/2) 
                                    and (self.talking == False) and (self.iloop < 5) and (self.count > self.wake_threshold)):
                                    #lets claim this interaction even if we didn't start it (wakeword)
                                    LOG.info("Claiming interaction from other/wakeword "+str(self.threadID))
                                    self.talking = True
                                elif self.count > 6:
                                    LOG.info('Not talking because C='+str(self.count)+" i="+str(self.iloop)+" t="+str(self.talking)+" o="+str(self.other.talking)+ " ct="+str(self.cancelThreshold) + " OT="+ str(self.other.cancelCounter)) 
                                    

                                #Should we move the eyes:

                                update_pos='MOVE:'+str(x_sign)+":"+str(x_m)+":"+str(y_sign)+":"+str(y_m)+":\n"
                                data = '{"data":'+update_pos+'}'

                                #This should cover up to ouput
                                if (self.other.talking ==False) and (self.iloop < 5):
                                    LOG.info("Sending look at "+str(self.iloop) + " "+str(self.threadID))
                                    self.bus.emit(Message('enclosure.eyes.look', data))

                                #If we are in spoken output, just look anyway
                                if self.iloop > 4:
                                    LOG.info("Sending look at "+str(self.iloop) + " "+str(self.threadID))
                                    self.bus.emit(Message('enclosure.eyes.look', data))

                                self.cancelCounter = 0
                            else:
                                self.cancelCounter += 1
                except Exception as e:
                    LOG.error("Exeption ERROR "+ str(e))
                    LOG.info("Exeption "+ str(e))
            else:
                self.cancelCounter +=1

            #Have to cancel even if we don't see a face!
            if(self.cancelCounter == self.cancelThreshold):
                LOG.info("Cancel threshold reached, talking: "+str(self.talking))
                if self.talking:
                    #If we are in the recognition phase then cancel
                    if self.iloop < 5:
                        LOG.info("Stopping" + " "+str(self.threadID))
                        create_signal('buttonPress') #This seems like an out of date way to do it...
                        self.bus.emit(Message('mycroft.stop'))
                        self.talking = False
                        self.count = 0
                    else:
                        #If we are giving output and the ownser isn't watching?
                        #do we bother to check of other has gaze?
                        LOG.info("Decrease Volume" + " "+str(self.threadID))
                        self.bus.emit(Message('mycroft.volume.decrease','{"play_sound": False}'))
                        self.volume_dropped = True

        #Out of the main loop so cleanup
        LOG.info("Cleanup Omron" + " "+str(self.threadID))
        self.hvc_p2_api.set_uart_baudrate(p2def.DEFAULT_BAUD)
        self.hvc_p2_api.disconnect()


    def volumeReset(self):
        if self.volume_dropped:
            LOG.info("Increasing Volume" + " "+str(self.threadID))
            self.bus.emit(Message('mycroft.volume.increase','{"play_sound": False}'))
            self.volume_dropped = False

    def setLoop(self, loop):
        LOG.info("Interaction loop updated to " + str(loop) + " "+str(self.threadID))
        self.iloop = loop
        if self.iloop == 6:
            self.talking = False
            self.count = 0
            self.iloop = 0

    def setDOA(self, angle):
        if angle<self.max_angle and angle>self.min_angle:
            if (self.other.talking == True) and (self.talking == False):
                self.talking = True
                self.other.talking = False


class EnclosureGaze:
    """
    
    """

    def __init__(self, bus, writer):
        self.bus = bus
        self.writer = writer

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
        #threadID, bus, writer, threshold_time, wake_threshold, min_angle, max_angle, portinfo, baudrate
        self.cameraR = CameraManager(1, self.bus, self.writer, self.threshold_time, self.wake_threshold, 10, 180, '/dev/ttyACM0', 921600)
        LOG.info("Created R")
        self.cameraL = CameraManager(2, self.bus, self.writer, self.threshold_time, self.wake_threshold, -10, -180, '/dev/ttyACM1', 921600)
        LOG.info("Created L")
        self.cameraR.other = self.cameraL
        self.cameraL.other = self.cameraR

        self.cameraR.start()
        #self.cameraL.start()
        LOG.info("Cameras Started")

        self.__init_events()

    def __init_events(self):
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
        self.bus.on('enclosure.gaze.shutdown', self.stateUpdate)



    def __del__(self):
        self.shutdown()

    def updateLoop(self, new_l):
        self.cameraR.setLoop(new_l)
        self.cameraL.setLoop(new_l)
        self.iloop = new_l

    def updateDOA(self, event):
        self.cameraR.setDOA(event.data.get('angle'))
        self.cameraR.setDOA(event.data.get('angle'))


    def resetVolume(self):
        self.cameraL.volumeReset()
        self.cameraR.volumeReset()

    def shutdown(self):
        self.cameraL.detecting = False
        self.cameraR.detecting = False
        self.cameraL.join()
        self.cameraR.join()
        LOG.info("Camera Threads ended")

        #Interaction Loop
        # 0 = waiting for wakeword
        # 1 = wakeword detected
        # 2 = mic open
        # 3 = mic closed
        # 4 = recognised
        # 5 = playing output
        # 6 = playing output finshed
    def stateUpdate(self, event=None):
        LOG.info("Status update "+event.msg_type)
        if event:
            if event.msg_type == 'recognizer_loop:wakeword':
                self.resetVolume()
                self.updateLoop(1)

            if event.msg_type == 'recognizer_loop:record_begin':
                self.updateLoop(2)

            if event.msg_type == 'recognizer_loop:record_end':
                if(self.iloop == 2):
                    self.updateLoop(3)
                #Don't move to 3 if the recording has failed and went back to 0

            if event.msg_type == 'recognizer_loop:utterance':
                self.updateLoop(4)

            if event.msg_type == 'recognizer_loop:speech.recognition.unknown':
                #recognition failed - back to 0
                self.updateLoop(0)

            if event.msg_type == 'recognizer_loop:audio_output_start':
                self.updateLoop(5)

            if event.msg_type == 'recognizer_loop:audio_output_end':
                self.updateLoop(6)
                #cameras update to 0 on this, keep local consistant even if it isn't used
                self.iloop = 0

            if event.msg_type == 'recognizer_loop:awoken':
                #This actually should be opening head as opposed to sleep closing it
                pass

            if event.msg_type == 'recognizer_loop:DOA':
                self.updateDOA(event)

            if event.msg_type == 'enclosure.gaze.shutdown':
                self.shutdown()

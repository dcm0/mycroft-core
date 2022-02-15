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

from mycroft.util.log import LOG
from mycroft.util import play_audio_file
from mycroft.messagebus.message import Message
from pathlib import Path

class EnclosureEyes:
    """
    Listens to enclosure commands for Tama's Eyes
    
    Performs the associated command on Arduino by writing on the Serial port.
    """

    def __init__(self, bus, writer):
        self.bus = bus
        self.writer = writer
        self.isOpen = False
        self.automove = True
        self.ignoreGazeWake = True
        self.voiceWake = True
        

        self._num_pixels = 1 * 2
        self._current_rgb = [(255, 255, 255) for i in range(self._num_pixels)]
        self.__init_events()

    def __init_events(self):
        self.bus.on('enclosure.eyes.on', self.on)
        self.bus.on('enclosure.eyes.off', self.off)
        self.bus.on('enclosure.eyes.blink', self.blink)
        self.bus.on('enclosure.eyes.narrow', self.narrow)
        self.bus.on('enclosure.eyes.look', self.look)
        self.bus.on('enclosure.eyes.toggleAutolook', self.toggleAutoLook)
        self.bus.on('enclosure.eyes.toggleGazeWake', self.toggleGazeWake)
        self.bus.on('enclosure.eyes.toggleVoiceWake', self.toggleVoiceWake)        
        self.bus.on('enclosure.eyes.color', self.color)
        self.bus.on('enclosure.eyes.level', self.brightness)
        self.bus.on('enclosure.eyes.volume', self.volume)
        self.bus.on('enclosure.eyes.spin', self.spin)
        self.bus.on('enclosure.eyes.timedspin', self.timed_spin)
        self.bus.on('enclosure.eyes.reset', self.reset)
        self.bus.on('enclosure.eyes.yellow', self.yellow)
        self.bus.on('enclosure.eyes.green', self.green)
        self.bus.on('enclosure.eyes.pink', self.pink)
        self.bus.on('enclosure.eyes.blue', self.blue)
        self.bus.on('enclosure.eyes.setpixel', self.set_pixel)
        self.bus.on('enclosure.eyes.fill', self.fill)
        self.bus.on('enclosure.eyes.shutdown', self.close)
        self.bus.on('recognizer_loop:speech.recognition.unknown', self.shake)
        self.bus.on('recognizer_loop:record_begin', self.listen)
        self.bus.on('recognizer_loop:record_end', self.think)
        self.bus.on('recognizer_loop:audio_output_start', self.talk)
        self.bus.on('recognizer_loop:audio_output_end', self.talkOver)
        self.bus.on('enclosure.head.move', self.move)
        self.bus.on('enclosure.sounds.bing', self.playSound)
        self.bus.on('enclosure.trial.start', self.trialStart)
        self.bus.on('enclosure.trial.end', self.trialEnd)
        self.bus.on('enclosure.trial.log', self.trialLog)

        self.bus.on('enclosure.eyes.rgb.get', self.handle_get_color)


    def playSound(self, message):
        audiopath = str(Path().absolute()) +'/mycroft/client/enclosure/tama/error.mp3'
        LOG.info("BING Error sound "+ audiopath)
        play_audio_file(audiopath)


    def handle_get_color(self, message):
        """Get the eye RGB color for all pixels
        Returns:
           (list) list of (r,g,b) tuples for each eye pixel
        """
        self.bus.emit(message.reply("enclosure.eyes.rgb",
                                    {"pixels": self._current_rgb}))

    def on(self, event=None):
        self.writer.write("OPEN")
        self.isOpen = True

    def off(self, event=None):
        self.writer.write("CLOSE")
        self.isOpen = False

    def blink(self, event=None):
        side = "b"
        if event and event.data:
            side = event.data.get("side", side)
        self.writer.write("eyes.blink=" + side)

    def narrow(self, event=None):
        self.writer.write("eyes.narrow")

    def look(self, event=None):
        if event and event.data:
            #side = event.data.get("data", "")
            LOG.info("Trying to look at "+str(event.data))
            if(self.automove):
                self.writer.write(event.data)
                
    def toggleAutoLook(self, event=None):
        self.automove = not self.automove
        if(self.automove):
            data = {"data":'true'}
        else:
            data = {"data":'false'}
            
        self.bus.emit(Message('enclosure.eyes.lookstatus', data))
        LOG.info("Toggling the autohead " + str(data))

    def toggleGazeWake(self, event=None):
        self.ignoreGazeWake = not self.ignoreGazeWake
        if(self.ignoreGazeWake):
            data = {"data":'true'}
        else:
            data = {"data":'false'}
            
        self.bus.emit(Message('enclosure.eyes.gazeWake', data))
        LOG.info("Toggling the gazeWake " + str(data))        

    def toggleVoiceWake(self, event=None):
        self.voiceWake = not self.voiceWake
        if(self.voiceWake):
            data = {"data":'true'}
            self.bus.emit(Message('recognizer_loop:wake_up'))
        else:
            data = {"data":'false'}
            self.bus.emit(Message('recognizer_loop:sleep'))
            
        self.bus.emit(Message('enclosure.eyes.voiceWake', data))
        LOG.info("Toggling the voiceWake " + str(data))          
        
        

    def talk(self, event=None):
        self.writer.write("PINK")

    def talkOver(self, event=None):
        self.writer.write("GREEN")

    #CHANGED from blu and the AVR is commented 
    def think(self, event=None):
        #self.writer.write("BLUE")
        if(self.automove):
            self.writer.write("AVR")
        else:
            self.writer.write("YELLOW")

    def listen(self, event=None):
        self.writer.write("YELLOW")


    def color(self, event=None):
        r, g, b = 255, 255, 255
        if event and event.data:
            r = int(event.data.get("r", r))
            g = int(event.data.get("g", g))
            b = int(event.data.get("b", b))
        color = (r * 65536) + (g * 256) + b
        self._current_rgb = [(r, g, b) for i in range(self._num_pixels)]
        LOG.info("Changing color " + str(event.data))
        self.writer.write("COL:" + str(r) + ":" + str(g) + ":" + str(b))

    def yellow(self, event=None):
        #self._current_rgb = [(r, g, b) for i in range(self._num_pixels)]
        #should update these calles to use the real colour set function
        self.writer.write("YELLOW")

    def green(self, event=None):
        self.writer.write("GREEN")

    def pink(self, event=None):
        self.writer.write("PINK")

    def blue(self, event=None):
        self.writer.write("BLUE")


    def close(self, event=None):   
        #self._current_rgb = [(r, g, b) for i in range(self._num_pixels)]
        #should update these calles to use the real colour set function
        self.writer.write("HOME")
        self.writer.write("NONE")
        self.writer.write("CLOSE")        

    def set_pixel(self, event=None):
        idx = 0
        r, g, b = 255, 255, 255
        if event and event.data:
            idx = int(event.data.get("idx", idx))
            r = int(event.data.get("r", r))
            g = int(event.data.get("g", g))
            b = int(event.data.get("b", b))
        self._current_rgb[idx] = (r, g, b)
        color = (r * 65536) + (g * 256) + b
        self.writer.write("eyes.set=" + str(idx) + "," + str(color))

    def fill(self, event=None):
        amount = 0
        if event and event.data:
            percent = int(event.data.get("percentage", 0))
            amount = int(round(23.0 * percent / 100.0))
        self.writer.write("eyes.fill=" + str(amount))

    def brightness(self, event=None):
        level = 30
        if event and event.data:
            level = event.data.get("level", level)
        self.writer.write("eyes.level=" + str(level))

    def shake(self):
        self.writer.write("PINK")
        self.writer.write("SHAKE")
        if(self.automove):
            self.writer.write("HOME")
        self.writer.write("GREEN")


    def volume(self, event=None):
        volume = 4
        if event and event.data:
            volume = event.data.get("volume", volume)
        self.writer.write("eyes.volume=" + str(volume))

    def reset(self, event=None):
        if self.isOpen == True:
            self.writer.write("CLOSE")
            self.isOpen = False
            
        if self.isOpen == False:
            self.writer.write("OPEN")
            self.isOpen = True

        if(self.automove):
            self.writer.write("HOME")
        self.writer.write("GREEN")

    def spin(self, event=None):
        self.writer.write("eyes.spin")

    def timed_spin(self, event=None):
        length = 5000
        if event and event.data:
            length = event.data.get("length", length)
        self.writer.write("eyes.spin=" + str(length))

    def move(self, event):
        #this ethod should move the head and send the data on the bus after the msg is sent from webscoket
        #LOG.info(str(event.data['pos']))
        x_sign = 0 
        x_m = event.data['pos']
        y_sign = 0
        y_m = 0
        update_pos='MOVE:'+str(x_sign)+":"+str(x_m)+":"+str(y_sign)+":"+str(y_m)+":\n"
        self.writer.write(update_pos)

    def trialStart():
        LOG.info('Trial started')

    def trialEnd():
        LOG.info('Trial ended')

    def trialLog(self, event=None):
        LOG.info(event.data)
    


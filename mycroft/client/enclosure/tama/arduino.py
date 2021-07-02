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


class EnclosureArduino:
    """
    Listens to enclosure commands for Mycroft's Arduino.

    Performs the associated command on Arduino by writing on the Serial port.
    """

    def __init__(self, bus, writer):
        self.bus = bus
        self.writer = writer
        self.__init_events()

    def __init_events(self):
        self.bus.on('enclosure.system.reset', self.reset)
        self.bus.on('enclosure.system.mute', self.mute)
        self.bus.on('enclosure.system.unmute', self.unmute)
        
    def reset(self, event=None):
        self.writer.write("HOME")

    def mute(self, event=None):
        self.writer.write("HOME")
        self.writer.write("CLOSE")

    def unmute(self, event=None):
        self.writer.write("OPEN")
        self.writer.write("HOME")


from machine import I2C, Pin
from is31fl3731 import IS31FL3731_I2C

import framebuf, machine, utime

machine.freq(160000000)

class Connector(object):
    def __init__(self, layout=(116, 119, 117, 118)):
        i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
        available = i2c.scan()
        devices   = list(filter(lambda x:x in available, layout))

        self.disp = IS31FL3731_I2C(i2c, devices, framebuf.GS8)
        self.page = 0

        self.pin  = Pin(2, Pin.OUT, value=1)

        self.disp.rect(1, 1, len(self.disp) *16 -2, self.disp.RCNT -2, 0x01)
        self.disp.send()

    def __call__(self, payload):
        if len(payload) == len(self.disp.buffer):
            self.page ^= 1
            self.disp.send(self.page, payload)
            self.disp(self.page)
        elif len(payload) <= len(self.disp.INIT):
            self.disp.func(payload)

    def action(self, parameter):
        self.pin(not self.pin.value())
        utime.sleep_ms(20)
        self.pin(not self.pin.value())


import endos
endos.Listener(Connector()).run()


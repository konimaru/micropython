# MicroPython IS31FL3731 matrix LED driver, I2C interface

import framebuf, micropython

class IS31FL3731(framebuf.FrameBuffer):
    PCNT = micropython.const(8)

    CCNT = micropython.const(16)
    RCNT = micropython.const(9)

    FUNC = b'\xFD\x0B'
    DOWN = b'\x0A\x00'
    INIT = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00'

    BASE = {framebuf.GS8:       (0, 0xFF, 0x00, range(0x24, 0xB4, 16)),
            framebuf.MONO_HMSB: (3, 0x00, 0x20, range(0x00, 0x12,  2))}

    def __init__(self, i2c, devices, format, brightness=0):
        self.i2c     = i2c
        self.devices = devices

        scale, led, pwm, self.layout = IS31FL3731.BASE[format]

        self.width   = IS31FL3731.CCNT *len(devices)
        self.step    = IS31FL3731.CCNT >> scale
        self.bcnt    = self.width      >> scale

        self.buffer  = bytearray(self.bcnt *IS31FL3731.RCNT)
        super().__init__(self.buffer, self.width, IS31FL3731.RCNT, format)

        pwm = brightness or pwm                             # override

        for dev in devices:
            i2c.writeto(dev, IS31FL3731.FUNC)
            i2c.writeto(dev, IS31FL3731.DOWN)               # shutdown mode

            for page in range(IS31FL3731.PCNT):
                i2c.writeto(dev, b'\xFD'+bytes((page,)))
                i2c.writeto(dev, b'\x00'+bytes((led,))*18)  # LED control
                i2c.writeto(dev, b'\x12'+b'\x00'*18)        # blink control
                i2c.writeto(dev, b'\x24'+bytes((pwm,))*144) # PWM

            i2c.writeto(dev, IS31FL3731.FUNC)
            i2c.writeto(dev, IS31FL3731.INIT)               # normal operation

    # ---

    def send(self, page=0, external=None):
        """send internal/external buffer to specified page"""
        surface = external or self.buffer

        for device, column in zip(self.devices, range(0, self.bcnt, self.step)):
            self.i2c.writeto(device, b'\xFD'+bytes((page,)))

            for idx in self.layout:
                self.i2c.writeto(device, bytes((idx,))+surface[column:column+self.step])
                column += self.bcnt

    def show(self, page=0):
        """display specified page"""
        self.func(bytes((0x01, page)))

    def func(self, data=None):
        """update or initialise function register/s"""
        data = data or IS31FL3731.INIT

        for dev in self.devices:
            self.i2c.writeto(dev, IS31FL3731.FUNC)
            self.i2c.writeto(dev, data)

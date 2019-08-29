# MicroPython IS31FL3731 matrix LED driver, I2C interface

import framebuf, micropython

class IS31FL3731(framebuf.FrameBuffer):
    PCNT  = micropython.const(8)

    CCNT  = micropython.const(16)
    RCNT  = micropython.const(9)

    FUNC  = b'\xFD' b'\x0B'
    DOWN  = b'\x0A' b'\x00'
    INIT  = b'\x00' b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00'

    BASE  = {framebuf.GS8:       (0, 0xFF, 0x00, range(0x24, 0xB4, 16)),
             framebuf.MONO_HMSB: (3, 0x00, 0x20, range(0x00, 0x12,  2))}

    PWM32 = b'\x00\x01\x02\x04\x06\x0A\x0D\x12' \
            b'\x16\x1C\x21\x27\x2E\x35\x3D\x45' \
            b'\x4E\x56\x60\x6A\x74\x7E\x8A\x95' \
            b'\xA1\xAD\xBA\xC7\xD4\xE2\xF0\xFF'

    PWM64 = b'\x00\x01\x02\x03\x04\x05\x06\x07' \
            b'\x08\x0A\x0C\x0E\x10\x12\x14\x16' \
            b'\x18\x1A\x1D\x20\x23\x26\x29\x2C' \
            b'\x2F\x32\x35\x39\x3D\x41\x45\x49' \
            b'\x4D\x51\x55\x59\x5E\x63\x68\x6D' \
            b'\x72\x77\x7C\x81\x86\x8C\x92\x98' \
            b'\x9E\xA4\xAA\xB0\xB6\xBC\xC3\xCA' \
            b'\xD1\xD8\xDF\xE6\xED\xF4\xFB\xFF'

    def __init__(self, i2c, devices, format, brightness=0):
        self.i2c     = i2c
        self.devices = devices

        scale, led, pwm, self.layout = IS31FL3731.BASE[format]

        self.width   = IS31FL3731.CCNT *len(devices)
        self.step    = IS31FL3731.CCNT >> scale
        self.bcnt    = self.width      >> scale

        self.buffer  = bytearray(self.bcnt *IS31FL3731.RCNT)
        super().__init__(self.buffer, self.width, IS31FL3731.RCNT, format)

        page = bytearray(1)                     # page select
        eins = bytes((led,))*18                 # LED control
        zwei = bytes(18)                        # blink control
        drei = bytes((brightness or pwm,))*144  # PWM

        for dev in devices:
            i2c.writeto(dev, IS31FL3731.FUNC)
            i2c.writeto(dev, IS31FL3731.DOWN)   # shutdown mode

        for dev in devices:
            for page[0] in range(IS31FL3731.PCNT):
                i2c.writeto_mem(dev, 0xFD, page)
                i2c.writeto_mem(dev, 0x00, eins)
                i2c.writeto_mem(dev, 0x12, zwei)
                i2c.writeto_mem(dev, 0x24, drei)

        self.func(IS31FL3731.INIT)              # normal operation

    def __call__(self, page=None):
        if page is not None:                    # set page/s
            return self.func(bytes((0x01, page)))

        status = list()
        for dev in self.devices:                # query page/s
            self.i2c.writeto(dev, IS31FL3731.FUNC)
            status.append(self.i2c.readfrom_mem(dev, 0x07, 1)[0])

        return status

    def __len__(self):
        return len(self.devices)

    # ---

    def send(self, page=0, external=None):
        """send internal/external buffer to specified page"""
        mv = memoryview(external or self.buffer)
        b  = self.bcnt
        s  = self.step

        for device, column in zip(self.devices, range(0, b, s)):
            self.i2c.writeto_mem(device, 0xFD, bytes((page,)))

            for idx in self.layout:
                self.i2c.writeto_mem(device, idx, mv[column:column+s])
                column += b

    def func(self, data):
        """update function register/s"""
        for dev in self.devices:
            self.i2c.writeto(dev, IS31FL3731.FUNC)
            self.i2c.writeto(dev, data)

IS31FL3731_I2C = IS31FL3731

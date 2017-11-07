from serial import Serial
from .wiznet import SerialFromEthernet

from .serial_interface import SerialInstrument

import socket

class LakeShore331(SerialInstrument):
    parity = 'O'
    bytesize = 7
    linebreak = '\r\n'

    async def temp(self, ch='A'):
        string = await self.serial.ask("KRDG? " + ch)
        return float(string)

    async def temp_chA(self):
        return await self.temp("A")

    async def temp_chB(self):
        return await self.temp("B")
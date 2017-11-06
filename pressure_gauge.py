from serial import Serial
from .wiznet import SerialFromEthernet
from .serial_interface import SerialInstrument
import socket

class PressureGauge(SerialInstrument):
    parity = 'O'
    bytesize = 7
    linebreak = '\r'
    CONNECT_DELAY = 0.5

    async def pressure(self):
        res = await self.serial.ask("?GA1")
        return float(res)

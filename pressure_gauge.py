from serial import Serial
from .wiznet import SerialFromEthernet
from pyrpl.async_utils import sleep_async, ensure_future, wait

from .serial_interface import SerialInstrument
import socket

class PressureGauge(SerialInstrument):
    parity = 'O'
    bytesize = 7
    linebreak = '\r'
    CONNECT_DELAY = 0.5

    async def pressure_async(self):
        res = await self.serial.ask("?GA1")
        return float(res)
    
    def pressure(self):
        res = wait(ensure_future(self.pressure_async()))
        return res
        

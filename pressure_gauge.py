from serial import Serial
from wiznet import SerialFromEthernet
import numpy as np


class PressureGauge(object):
    def __init__(self, port="COM1"):
        if port.find("COM")>=0: # IP adress
            self.serial = Serial(port)
            self.serial.parity = 'O'
            self.serial.bytesize = 7
        else:
            self.serial = SerialFromEthernet(port)

    def pressure(self):
        try:
            return float(self.serial.ask("?GA1\r"))
        except ValueError:
            return 0.
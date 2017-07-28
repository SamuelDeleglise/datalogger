from serial import Serial
from wiznet import SerialFromEthernet
import socket

class LakeShore331(object):
    def __init__(self, port="COM1"):
        if port.find("COM")>=0:
            self.serial = Serial(port)
            self.serial.parity = 'O'
            self.serial.bytesize = 7
        else:
            self.serial = SerialFromEthernet(port)

    def write(self, val):
        self.serial.write(val + '\r\n')

    def readline(self):
        st = b''
        ch = b''
        while (ch != b'\r'):
            try:
                ch = self.serial.socket.recv(1)
                st += ch
            except socket.error :
                return st
        return st

    def ask(self, val):
        self.write(val)
        return self.readline()

    def temp(self, ch='A'):
        try:
            return float(self.ask("KRDG? " + ch).decode('utf-8'))
        except ValueError:
            pass
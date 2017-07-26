from serial import Serial
from wiznet import SerialFromEthernet

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
        st = ''
        ch = ''
        while (ch != '\r'):
            ch = self.serial.read()
            st += ch
        return st[:-1]

    def ask(self, val):
        self.write(val)
        return self.readline()

    def temp(self, ch='A'):
        return float(self.ask("KRDG? " + ch))

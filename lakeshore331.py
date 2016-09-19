from serial import Serial

class LakeShore331(object):
    def __init__(self, port="COM1"):
        self.serial = Serial(port)
        self.serial.setParity('O')
        self.serial.setByteSize(7)

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
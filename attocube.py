from .serial_interface import SerialInstrument
import serial

class Attocube(SerialInstrument):
    linebreak = '\r\n'
    timeout = 2
    parity = serial.PARITY_NONE
    stopbits = serial.STOPBITS_ONE
    bytesize = 8
    baudrate = 38400

    def __init__(self, *args, **kwds):
        super(Attocube, self).__init__(*args, **kwds)
        for index in (1,2,3):
            self.serial.ask_sync("setm %i stp\r\n"%index)

    def steps(self, ax, numsteps):
        string = "stepd" if numsteps<0 else "stepu"
        self.serial.ask_sync("%s %i %i\r\n"%(string, ax, numsteps))

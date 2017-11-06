from serial import Serial
from io import StringIO
import numpy as np
from .wiznet import SerialFromEthernet

def curve_2_340(filename):
    with open(filename, 'r') as f:
        with open(filename[:-5] + '340', 'w') as new:
            name = f.readline()
            type = f.readline()
            units = f.readline()
            logohm = f.readline()

            new.writelines(["Sensor Model:   " + name,
                            "Serial Number:   " + type,
                            "Data Format: 4      (Log Ohms vs. Kelvin)" + '\n',
                            "SetPoint Limit: +300" + '\n',
                            "Temperature coefficient: 1 (Negative)" + '\n'])
            line = f.readline()
            string = ''
            index = 1
            while(line!=''):
                string+=str(index) + '\t' + '\t'.join(line.split()) + '\n'
                line = f.readline()
                index+=1
            new.write("Number of Breakpoints: " + str(index - 1) + '\n')

            new.write("\nNo.   Units      Temperature (K) \n\n")
            new.write(string)
            new.write('\n')




class CryoConChannel(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name

    @property
    def v_bias(self):
        return self.parent.ask("INPUT " + str(self.name) + ":VBIAS?")

    @v_bias.setter
    def v_bias(self, val):
        if isinstance(val, basestring):
            string = val
        else:
            string = str(val) + "mV"
        self.parent.write("INPUT " + self.name + ":VBIAS " + string)
        return val

    @property
    def temp(self):
        try:
            val = self.parent.ask(("INPUT %s:TEMPER?"%self.name).encode())
            return float(val)
        except ValueError:
            return 0.


class CryoCon(object):
    def __init__(self, port='COM1'):
        if port.find("COM")>=0:
            self.serial = Serial(port)
        else:
            self.serial = SerialFromEthernet(port)
        self.timeout = 1
        self.ch_a = CryoConChannel(self, "A")
        self.ch_b = CryoConChannel(self, "B")

    def write(self, val):
        self.serial.write(val + b'\n\r')

    def ask(self, string):
        self.write(string)
        return self.serial.readline()

    def read(self):
        return self.serial.readline()[:-1]

    def ask_curve(self, index):
        self.write("CALCUR? %i"%index)
        val = "foo"
        name = self.read()
        type = self.read()
        coeff = float(self.read())
        units = self.read()
        string = ''
        while (val.find(";") < 0):
            val = self.serial.readline()
            string+=val
        arr = np.loadtxt(StringIO.StringIO(string[:-2]))
        return name, type, coeff, units, arr

    def curve_from_file(self, filename):
        curve = []
        with open(filename, 'r') as f:
            name = f.readline().split(":")[1].split()[0]
            ser_num = f.readline().split(":")[1].split()[0]
            df = f.readline().split(":")[1].split()[0]
            setpoint = f.readline().split(":")[1].split()[0]
            coeff = float(f.readline().split(":")[1].split()[0])
            n_points = int(f.readline().split(":")[1].split()[0])
            line = f.readline()
            line = f.readline()
            line = f.readline()
            while(line!=''):
                line = f.readline()
                vals = map(float, line.split()[1:])
                if len(vals)!=2:
                    continue
                curve.append(vals)
            return name, ser_num, coeff, df, np.array(curve)

    def set_curve(self, index, name, type, coeff, units, curve):
        self.write("CALCUR %i"%index)
        self.write(name)
        self.write(type)
        self.write(str(coeff))
        self.write(units)
        for vals in curve:
            self.write(str(vals[0]) + " " + str(vals[1]))
        self.write(";")

    def set_curve_from_file(self, index, filename):
        name, ser_num, coeff, df, curve = self.curve_from_file(filename)
        self.set_curve(index, name, 'ACR', coeff, 'LogOhm', curve)

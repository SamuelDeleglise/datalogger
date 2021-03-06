from serial import Serial
from .wiznet import  SerialFromEthernet
import numpy as np
import time
import matplotlib.pylab as plt
from .serial_interface import SerialInstrument
import serial


class HeliumDepth_old(object):
    def __init__(self, port='COM1'):
        if port.find("COM")>=0:
            self.serial = Serial(port)
        else:
            self.serial = SerialFromEthernet(port)
        # self.timeout = 1
        # self.parity = 'N'
        # self.bytesize = 8

    def write(self, val):
        self.serial.write(val + '\n\r')

    def ask(self, string):
        self.write(string)
        return self.serial.readline()

    def close(self):
        self.serial.close()

    def ask_level(self):
        res = self.ask("G")
        i = res.find('mm') - 4
        try:
            return int(res[i:i + 4])
        except ValueError:
            return 0

    def ask_curve(csv_filename, picture_filename):
        pass

    def start_gathering(self, delay, csv_filename):
        t_ini = time.clock()
        levels = []
        times = []
        time_ticks = []
        with open(csv_filename, 'w') as new:
            new.writelines(["log started :,", str(
                int(time.strftime("%H", time.gmtime())) + 1) + time.strftime(
                ":%M:%S on, %Y_%m_%d", time.gmtime()), "\n"])
            new.writelines(["Delay (in s) :,", "Level (in mm)", "\n"])
        while (1):
            try:
                t = time.clock()
                delta_t = t - t_ini
                if (delta_t % delay == 0):
                    delta_t = int(delta_t)

                    level = self.ask_level()
                    print("delay =" + str(delta_t) + " s, level : " + str(
                        level) + " mm")
                    levels.append(level)
                    times.append(delta_t)
                    time_ticks.append(str(int(time.strftime("%H",
                                                            time.gmtime())) + 1) + time.strftime(
                        ":%M:%S", time.gmtime()))
                    '''plt.close("all")
                    plt.plot(times, levels)
                    ax = plt.gca()
                    ax.set_xticklabels(time_ticks)
                    plt.savefig(picture_filename)'''
                    with open(csv_filename, 'a') as new:
                        new.writelines([str(delta_t), ",", str(level), "\n"])

            except (KeyboardInterrupt, SystemExit):
                break

class HeliumDepth(SerialInstrument):
    linebreak = '\r\n'
    timeout = 2
    parity = serial.PARITY_NONE
    stopbits = serial.STOPBITS_ONE
    bytesize = 8
    baudrate = 9600
    CONNECT_DELAY = 0.1

    async def ask_level(self):
        string = await self.serial.ask("G")
        i = string.find('mm') - 4
        return int(string[i:i + 4])

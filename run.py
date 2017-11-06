from datalogger.model import DataLogger
from datalogger.cryocon import CryoCon
from datalogger.helium_depth import HeliumDepth
from datalogger.lakeshore331 import LakeShore331
from datalogger.optic_reader import OpticReader
from datalogger.pressure_gauge import PressureGauge
from datalogger.redpitaya_channel import RedpitayaChannel
from datalogger.wiznet import SerialFromEthernet

from pyrpl import Pyrpl
from qtpy import QtWidgets

#s = SerialFromEthernet('10.214.1.78')


APP = QtWidgets.QApplication(["datalogger"])
CRC = CryoCon()
opt = OpticReader()
LKS = LakeShore331('10.214.1.85')
PRESSURE = PressureGauge('10.214.1.86')

DLG = DataLogger()

DLG.add_channel('Pressure', PRESSURE.pressure)

DLG.add_channel('3He RuO2', lambda : CRC.ch_a.temp)
DLG.add_channel('1Kpot RuO2', lambda : CRC.ch_b.temp)
DLG.add_channel('3He AB', lambda : LKS.temp("A"))
DLG.add_channel('Sorb AB', lambda : LKS.temp("B"))


HD = HeliumDepth('10.214.1.78')

DLG.add_channel('He level', HD.ask_level)

DLG.add_channel('derivative recovery He', opt.derivative)

#DLG.add_channel('pressure interferometer', PRESSURE.pressure)

DLG.gui()
APP.exec_()

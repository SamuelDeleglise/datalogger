from model import DataLogger
from cryocon import CryoCon
from helium_depth import HeliumDepth
from lakeshore331 import LakeShore331
from optic_reader import OpticReader
from qtpy import QtWidgets
from wiznet import SerialFromEthernet
#s = SerialFromEthernet('10.214.1.78')

CRC = CryoCon()
opt = OpticReader()
LKS = LakeShore331('10.214.1.85')

DLG = DataLogger()

#DLG.add_channel('Pressure', lambda : float(s.ask('?GA1\r')))

DLG.add_channel('3He RuO2', lambda : CRC.ch_a.temp)
DLG.add_channel('1Kpot RuO2', lambda : CRC.ch_b.temp)
DLG.add_channel('3He AB', lambda : LKS.temp("A"))
DLG.add_channel('Sorb AB', lambda : LKS.temp("B"))

HD = HeliumDepth('10.214.1.78')

DLG.add_channel('He level', HD.ask_level)

DLG.add_channel('derivative recovery He', opt.derivative)
APP = QtWidgets.QApplication(["datalogger"])
DLG.gui()
APP.exec_()

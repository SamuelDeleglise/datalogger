from model import DataLogger
from cryocon import CryoCon

CRC = CryoCon()

DLG = DataLogger()

DLG.add_channel('3He RuO2', lambda : CRC.ch_a.temp)
DLG.add_channel('1Kpot RuO2', lambda : CRC.ch_b.temp)


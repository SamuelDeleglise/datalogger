from model import DataLogger
from cryocon import CryoCon
from lakeshore331 import LakeShore331



CRC = CryoCon('10.214.1.78')
LKS = LakeShore331()

DLG = DataLogger()

DLG.add_channel('3He RuO2', lambda : CRC.ch_a.temp)
DLG.add_channel('1Kpot RuO2', lambda : CRC.ch_b.temp)
DLG.add_channel('3He AB', lambda : LKS.temp("A"))
DLG.add_channel('Sorb AB', lambda : LKS.temp("B"))

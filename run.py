import sys
from qtpy import QtWidgets
import os.path as osp
dir_path = osp.split(osp.dirname(osp.realpath(__file__)))[0]
sys.path.append(dir_path) # In case datalogger not
# accessible in normal PYTHONPATH


if __name__=='__main__':
    directory = sys.argv[1]


    APP = QtWidgets.QApplication(sys.argv)

    from datalogger import DataLogger

    DLG = DataLogger(directory)

    APP.exec_()

import sys
from qtpy import QtWidgets
import os.path as osp
dir_path = osp.split(osp.dirname(osp.realpath(__file__)))[0]
sys.path.append(dir_path) # In case datalogger not
# accessible in normal PYTHONPATH


if __name__=='__main__':
    if len(sys.argv)>=2:
        directory = sys.argv[1]
    else:
        directory = None
    APP = QtWidgets.QApplication(sys.argv)

    from datalogger import DataPlotter

    DLG = DataPlotter(directory)

    APP.exec_()

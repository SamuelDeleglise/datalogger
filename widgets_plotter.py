from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np

class PlotterItem(MyTreeItem):
    COLORS = ['red', 'green', 'blue', 'cyan', 'magenta']
    N_CHANNELS = 0

    def plot_point(self, val, moment):
        self.values.append(val)
        self.times.append(moment)

        for index, moment in enumerate(self.times):
            if moment<self.dlg.earliest_point:
                self.values.pop(index)
                self.times.pop(index)
            else:
                break
        self.curve.setData(self.times, self.values)

    def plot_points(self, vals, times):
        self.values = [val for val in vals]
        self.times = [time for time in times]

        self.curve.setData(self.times, self.values)


class PlotterTree(MyTreeWidget):
    pass


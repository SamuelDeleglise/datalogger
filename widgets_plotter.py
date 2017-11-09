from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np
from  . import widgets_base as wb

class PlotterItem(wb.MyTreeItem):
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

class PlotterTree(wb.MyTreeWidget):
    def __init__(self):
        super(wb.MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Channel", "Visible"])

        self.itemChanged.connect(self.update)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.visible = channel.widget.checkState(1) == 2

class DataPlotterWidget(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        self.dlg = datalogger
        self.graph = pg.GraphicsWindow(title="DataLogger")
        self.plot_item = self.graph.addPlot(title="DataLogger", axisItems={
            'bottom': wb.TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)

        self._dock_tree = wb.MyDockTreeWidget(datalogger)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)

        self.show()
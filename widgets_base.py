from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np


class MyTreeItem(QtWidgets.QTreeWidgetItem):
    N_CHANNELS = 0
    EDITABLE = False
    def __init__(self, parent, channel):
        super(MyTreeItem, self).__init__(parent)
        #self.times = []
        #self.values = []
        self.channel = channel

        MyTreeItem.N_CHANNELS += 1
        self.dlg = parent.dlg
        self.setText(0, channel.name)
        for index, val in enumerate(channel.args):
            if isinstance(val, bool):
                self.setCheckState(index + 1, val * 2)
            else:
                self.setText(index + 1, str(val))
        if self.EDITABLE:
            self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        self.initialize(self.channel)

class MyTreeWidget(QtWidgets.QTreeWidget):
    item_class = None

    def create_channel(self, channel):
        self.blockSignals(True)
        widget = self.item_class(self, channel)  # QtWidgets.QTreeWidgetItem(
        # self)
        channel.widget = widget
        self.addTopLevelItem(widget)
        self.blockSignals(False)
        return widget

    def remove_channel(self, channel):
        self.blockSignals(True)
        self.takeTopLevelItem(self.indexOfTopLevelItem(channel.widget))
        self.blockSignals(False)


class TimeAxisItem(pg.AxisItem):

    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        return [QtCore.QDateTime(1970, 1, 1, 1, 0).addSecs(value).toString(
            'hh:mm:ss')
                for
                value in
                values]

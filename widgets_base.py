from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np


class MyTreeItem(QtWidgets.QTreeWidgetItem):
    N_CHANNELS = 0
    def __init__(self, parent, channel):
        super(MyTreeItem, self).__init__(parent)
        self.times = []
        self.values = []
        self.channel = channel

        MyTreeItem.N_CHANNELS += 1
        self.dlg = parent.dlg
        self.setText(0, channel.name)
        for index, val in enumerate(channel.args):
            if isinstance(val, bool):
                self.setCheckState(index + 1, val * 2)
            else:
                self.setText(index + 1, str(val))

        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        self.initialize(self.channel)

class MyTreeWidget(QtWidgets.QTreeWidget):
    item_class = None

    def create_channel(self, channel):
        self.blockSignals(True)
        widget = self.item_class(self, channel)  # QtWidgets.QTreeWidgetItem(
        # self)
        self.addTopLevelItem(widget)
        self.blockSignals(False)
        return widget


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        return [QtCore.QDateTime(1970, 1, 1, 1, 0).addSecs(value).toString(
            'hh:mm:ss')
                for
                value in
                values]


from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np


class LoggerItem(MyTreeItem):
    def show_error_state(self):
        color = 'red' if self.channel.error_state else 'green'
        self.setBackground(4, QtGui.QColor(color))


class LoggerTree(MyTreeWidget):
    def __init__(self, datalogger):
        super(MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Channel", "Visible", "Active",
                              "Delay", "Callback"])
        self.setColumnCount(5)
        self.dlg = datalogger
        self.itemChanged.connect(self.update)
        self.setSortingEnabled(True)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.name = str(channel.widget.text(0))
            channel.visible = channel.widget.checkState(1) == 2
            channel.active = channel.widget.checkState(2) == 2
            channel.delay = float(channel.widget.text(3))
            channel.callback = str(channel.widget.text(4))
            channel.widget.show_error_state()

    def contextMenuEvent(self, evt):
        menu = QtWidgets.QMenu()
        action_add = QtWidgets.QAction(menu)
        action_add.setText('add channel')
        action_add.triggered.connect(self.dlg.new_channel)
        menu.addAction(action_add)

        action_rerun = QtWidgets.QAction(menu)
        action_rerun.setText('run start_script again')
        action_rerun.triggered.connect(self.dlg.run_start_script)
        menu.addAction(action_rerun)
        menu.exec(evt.globalPos())

    """
    def add_channels(self):
        return
        colors = ['red', 'green', 'blue', 'cyan', 'magenta']
        for index, ch in enumerate(
                self.dataloggergui.datalogger.channels.keys()):
            color = colors[index % len(colors)]
            self.add_channel(ch, color)
    """
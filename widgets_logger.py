from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np
from . import widgets_base as wb


class DataLoggerWidget(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        super(DataLoggerWidget, self).__init__()
        self.setWindowTitle('DataLogger')
        self.current_channel_index = -1
        self.dlg = datalogger

        self.tree = LoggerTree(self.dlg)
        self.setCentralWidget(self.tree)

        self.menubar = DataLoggerMenu(datalogger)
        self.setMenuBar(self.menubar)

        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

    def remove_channel(self, channel):
        self.tree.remove_channel(channel)


class LoggerItem(wb.MyTreeItem):
    EDITABLE = True
    def initialize(self, channel):
        self.show_error_state()

    def show_error_state(self):
        color = 'red' if self.channel.error_state else 'green'
        self.setBackground(4, QtGui.QColor(color))


class LoggerTree(wb.MyTreeWidget):
    item_class = LoggerItem
    def __init__(self, datalogger):
        super(wb.MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Channel", "Active",
                              "Delay", "Callback"])
        self.setColumnCount(4)
        self.dlg = datalogger
        self.itemChanged.connect(self.update)
        self.setSortingEnabled(True)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.name = str(channel.widget.text(0))
            channel.active = channel.widget.checkState(1) == 2
            channel.delay = float(channel.widget.text(2))
            channel.callback = str(channel.widget.text(3))
            channel.widget.show_error_state()

    def contextMenuEvent(self, evt):
        menu = QtWidgets.QMenu()
        action_add = QtWidgets.QAction(menu)
        action_add.setText('add channel')
        action_add.triggered.connect(self.dlg.new_channel)
        menu.addAction(action_add)

        item = self.itemAt(evt.pos())
        if item is not None:
            action_remove = QtWidgets.QAction(menu)
            channel = item.channel
            action_remove.setText('remove ' + channel.name)
            def remove_item():
                self.dlg.remove_channel(item.channel)
            action_remove.triggered.connect(remove_item)
            menu.addAction(action_remove)


        action_rerun = QtWidgets.QAction(menu)
        action_rerun.setText('run start_script again')
        action_rerun.triggered.connect(self.dlg.run_start_script)

        menu.addAction(action_rerun)
        menu.exec(evt.globalPos())


class DataLoggerMenu(QtWidgets.QMenuBar):
    def __init__(self, datalogger):
        super(DataLoggerMenu, self).__init__()
        self.menufile = QtWidgets.QMenu("File")
        self.addMenu(self.menufile)

        self.action_load = QtWidgets.QAction("Load...", self)
        self.action_new = QtWidgets.QAction("New file...", self)
        self.dlg = datalogger
        self.action_load.triggered.connect(self.load)
        self.action_new.triggered.connect(self.new_file)
        self.menufile.addAction(self.action_new)
        self.menufile.addAction(self.action_load)

    def new_file(self):
        accept, filename = self.dialog.getSaveFileName()
        if accept:
            self.logfile = filename

    def load(self):
        self.datalogger.load()

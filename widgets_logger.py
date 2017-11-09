from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np
import .widgets_base as wb

class DataLoggerWidget(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        super(DataLoggerWidget, self).__init__()
        self.current_channel_index = -1
        """
        self.dlg = datalogger
        self.graph = pg.GraphicsWindow(title="DataLogger")
        self.plot_item = self.graph.addPlot(title="DataLogger", axisItems={
            'bottom': TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)
        """

        self._dock_tree = wb.MyDockTreeWidget(datalogger)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)
        self.menubar = DataloggerMenu(datalogger)
        self.setMenuBar(self.menubar)
        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

class LoggerItem(wb.MyTreeItem):
    def show_error_state(self):
        color = 'red' if self.channel.error_state else 'green'
        self.setBackground(4, QtGui.QColor(color))

class LoggerTree(wb.MyTreeWidget):
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
            #channel.visible = channel.widget.checkState(1) == 2
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

class DataloggerMenu(QtWidgets.QMenuBar):
    def __init__(self, datalogger):
        super(DataloggerMenu, self).__init__()
        self.menufile = QtWidgets.QMenu("File")
        self.addMenu(self.menufile)

        self.action_load = QtWidgets.QAction("Load...", self)
        self.action_new = QtWidgets.QAction("New file...", self)
        self.dlg = datalogger
        self.action_load.triggered.connect(self.load)
        self.action_new.triggered.connect(self.new_file)
        self.menufile.addAction(self.action_new)
        self.menufile.addAction(self.action_load)
        '''
        #modif Edouard
        self.action_load_1_more_day = QtWidgets.QAction("Load 1 more day of data...", self)
        self.action_load_1_more_day.triggered.connect(self.load_1_more_day)
        self.menufile.addAction(self.action_load_1_more_day)
        '''

    def new_file(self):
        accept, filename = self.dialog.getSaveFileName()
        if accept:
            self.logfile = filename

    def load(self):
        self.datalogger.load()
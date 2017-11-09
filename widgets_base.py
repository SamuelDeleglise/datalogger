from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np


class MyTreeItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, channel):
        super(MyTreeWidgetItem, self).__init__(parent)
        self.times = []
        self.values = []
        self.channel = channel
        color = self.COLORS[self.N_CHANNELS % len(self.COLORS)]
        MyTreeWidgetItem.N_CHANNELS += 1
        self.dlg = parent.dlg
        self.setText(0, channel.name)
        for index, val in enumerate(channel.args):
            if isinstance(val, bool):
                self.setCheckState(index + 1, val * 2)
            else:
                self.setText(index + 1, str(val))
        self.show_error_state()
        self.setBackground(0, QtGui.QColor(color))
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.curve = self.dlg.widget.plot_item.plot(pen=color[0])
        self.curve.setVisible(channel.visible)

class BaseItem(object):
    pass


class MyTreeWidget(QtWidgets.QTreeWidget):
    item_class = None

    def create_channel(self, channel):
        self.blockSignals(True)
        widget = self.item_class(self, channel)  # QtWidgets.QTreeWidgetItem(
        # self)
        self.addTopLevelItem(widget)
        self.blockSignals(False)
        return widget

class BaseTree(MyTreeWidget):
    pass


class MyControlWidget(QtWidgets.QWidget):
    def __init__(self, datalogger):
        super(MyControlWidget, self).__init__()
        self.dlg = datalogger
        self.lay_v = QtWidgets.QVBoxLayout()
        self.setLayout(self.lay_v)
        self.lay_h = QtWidgets.QHBoxLayout()
        self.lay_v.addLayout(self.lay_h)

        self.label = QtWidgets.QLabel("# of days to display")
        self.lay_h.addWidget(self.label)
        self.spinbox = QtWidgets.QSpinBox()
        self.lay_h.addWidget(self.spinbox)
        self.lay_h.addStretch()

        self.tree = MyTreeWidget(datalogger)
        self.lay_v.addWidget(self.tree)
        self.spinbox.setValue(self.dlg.days_to_show)

        self.spinbox.valueChanged.connect(self.update_days_to_show)

    def update_days_to_show(self):
        days = self.spinbox.value()
        self.dlg.days_to_show = days

class MyDockTreeWidget(QtWidgets.QDockWidget):
    def __init__(self, datalogger):
        super(MyDockTreeWidget, self).__init__()

        self.mycontrolwidget = MyControlWidget(datalogger)
        self.tree = self.mycontrolwidget.tree
        self.setWidget(self.mycontrolwidget)


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


class DataLoggerWidget(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        super(DataLoggerWidget, self).__init__()
        self.current_channel_index = -1
        self.dlg = datalogger
        self.graph = pg.GraphicsWindow(title="temperatures")
        self.plot_item = self.graph.addPlot(title="temperatures", axisItems={
            'bottom': TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)

        self._dock_tree = MyDockTreeWidget(datalogger)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)
        self.menubar = DataloggerMenu(datalogger)
        self.setMenuBar(self.menubar)
        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

class DataPlotterWidget(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        pass
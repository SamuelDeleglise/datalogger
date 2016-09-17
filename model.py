from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import json
import time
import os.path as osp
import os


class Channel(object):
    """A floating point is returned every period seconds"""

    def __init__(self, name, callback=None, period=10):
        self.timer = QtCore.QTimer()
        self.period = period
        self.name = name
        self.callback = callback
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.measure)
        self.logfile = osp.join(os.environ["HOMEDRIVE"], os.environ[
            "HOMEPATH"], "datalogger.json")
        self.times = []
        self.values = []

    @property
    def active(self):
        return self.timer.isActive()

    @active.setter
    def active(self, val):
        if val:
            self.start()
        else:
            self.stop()
        return val

    def start(self):
        self.timer.start()

    @property
    def period(self):
        return self.timer.interval()/1000

    @period.setter
    def period(self, val):
        self.timer.setInterval(val*1000)
        return val

    def measure(self):
        """Performs the actual measurement. Should return a float"""
        from sys import stdout
        stdout.flush()
        val = self.callback()
        time_ = time.time()
        with open(self.logfile, 'a') as f:
            json.dump([self.name, val, time_], f)
            f.write('\n')
            f.close()
        self.times.append(time_)
        self.values.append(val)
        self.plot(val, time_)

    def plot(self, val, time):
        pass

    def stop(self):
        self.timer.stop()

class DataLogger(object):
    def __init__(self):
        self.channels = {}

    def add_channel(self, name, callback):
        self.channels[name] = Channel(name, callback)

    def gui(self):
        self.widget = DataLoggerGui(self)


class MyTreeWidget(QtGui.QTreeWidget):
    def __init__(self, dataloggergui):
        super(MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Active", "channel", "period"])
        self.setColumnCount(3)
        self.dataloggergui = dataloggergui
        self.add_channels()
        self.itemChanged.connect(self.update)

        def plot(self, val, time):
            self.curve.setData(self.times, self.values)
        Channel.plot = plot


    def update(self):
        for channel in self.dataloggergui.datalogger.channels.values():
            channel.name = str(channel.treeitem.text(1))
            channel.period = int(channel.treeitem.text(2))
            active = channel.treeitem.checkState(0)==2
            if active!=channel.active:
                channel.active = active

    def add_channels(self):
        for ch in self.dataloggergui.datalogger.channels.keys():
            chan = self.dataloggergui.datalogger.channels[ch]
            item = QtGui.QTreeWidgetItem(["", ch, str(chan.period)])
            chan.treeitem = item
            chan.curve = self.dataloggergui.plot_item.plot(pen="r")
            self.addTopLevelItem(item)
            item.setCheckState(0, chan.active)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

class MyDockTreeWidget(QtGui.QDockWidget):
    def __init__(self, datalogger):
        super(MyDockTreeWidget, self).__init__()
        self.tree = MyTreeWidget(datalogger)
        self.setWidget(self.tree)

class TimeAxisItem(pg.AxisItem):
    """
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)
    """

    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        return [QtCore.QDateTime(1970,1,1,1,0).addSecs(value).toString(
            'hh:mm:ss')
                for
                value in
                values]

class DataLoggerGui(QtGui.QMainWindow):
    def __init__(self, datalogger):
        super(DataLoggerGui, self).__init__()
        self.datalogger = datalogger
        self.graph = pg.GraphicsWindow(title="temperatures")
        self.plot_item = self.graph.addPlot(title="temperatures", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)
        self._dock_tree = MyDockTreeWidget(self)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)
        self.show()
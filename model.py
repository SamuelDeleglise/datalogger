from qtpy import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import json
import time
import os.path as osp
import os

class Channel(object):
    """A floating point is returned every period seconds"""

    def __init__(self, name, callback=None, period=10, parent=None):
        if parent is None:
            parent = DLG
        self.parent = parent
        self.timer = QtCore.QTimer()
        self.period = period
        self.name = name
        self.callback = callback
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.measure)
        self.path = osp.join(os.environ["HOMEDRIVE"], os.environ[
            "HOMEPATH"], '.datalogger')
        if not osp.exists(self.path):
            os.mkdir(self.path)
        self.configfile = osp.join(self.path, "config.json")
        if not osp.exists(self.configfile):
            with open(self.configfile, 'w') as f:
                json.dump(self.default_config(), f)
        with open(self.configfile, 'r') as f:
            self.config = json.loads(f.read())
        self.times = []
        self.values = []
        if osp.exists(self.logfile):
            self.load_data()

    '''@property
    def config(self):
        return self.parent.config'''

    @property
    def logfile(self):
        return self.config["logfile"]

    def default_config(self):
        return dict(logfile=osp.join(self.path, "logfile.json"))

    def load_data(self):
        with open(self.logfile, 'r') as f:
            for line in f:
                name, val, time = json.loads(line)
                if name==self.name:
                    self.values.append(val)
                    self.times.append(time)


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
        self.plot()

    def plot(self):
        self.curve.setData(self.times, self.values)

    def stop(self):
        self.timer.stop()

class DataLogger(object):
    def __init__(self):
        self.channels = {}

    def add_channel(self, name, callback):
        self.channels[name] = Channel(name, callback)

    def gui(self):
        self.widget = DataLoggerGui(self)


class MyTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, dataloggergui):
        super(MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Active", "channel", "period"])
        self.setColumnCount(3)
        self.dataloggergui = dataloggergui
        self.add_channels()
        self.itemChanged.connect(self.update)

    def update(self):
        for channel in self.dataloggergui.datalogger.channels.values():
            channel.name = str(channel.treeitem.text(1))
            channel.period = float(channel.treeitem.text(2))
            active = channel.treeitem.checkState(0)==2
            if active!=channel.active:
                channel.active = active

    def add_channels(self):
        colors = ['red', 'green', 'blue', 'cyan', 'magenta']
        for index, ch in enumerate(
                self.dataloggergui.datalogger.channels.keys()):
            color = colors[index%len(colors)]
            chan = self.dataloggergui.datalogger.channels[ch]
            item = QtWidgets.QTreeWidgetItem(["", ch, str(chan.period)])
            chan.treeitem = item
            chan.curve = self.dataloggergui.plot_item.plot(pen=color[0])
            chan.plot()
            self.addTopLevelItem(item)
            item.setCheckState(0, chan.active)
            item.setBackground(1, QtGui.QColor(color))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

class MyDockTreeWidget(QtWidgets.QDockWidget):
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

class DataloggerMenu(QtWidgets.QMenuBar):
    def __init__(self):
        super(DataloggerMenu, self).__init__()
        self.menufile = QtWidgets.QMenu("File")
        self.addMenu(self.menufile)

        self.action_load = QtWidgets.QAction("Load...", self)
        self.action_new = QtWidgets.QAction("New file...", self)
        self.action_load.triggered.connect(self.load)
        self.action_new.triggered.connect(self.new_file)
        self.menufile.addAction(self.action_new)
        self.menufile.addAction(self.action_load)
        self.dialog = QtWidgets.QFileDialog()

    def load(self):
        accept, filename = self.dialog.getOpenFileName()


    def new_file(self):
        accept, filename = self.dialog.getSaveFileName()
        if accept:
            self.logfile = filename

class DataLoggerGui(QtWidgets.QMainWindow):
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
        self.menubar = DataloggerMenu()
        self.setMenuBar(self.menubar)
        self.show()

DLG = DataLogger()

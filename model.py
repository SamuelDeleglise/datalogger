from qtpy import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import json
import time
import os.path as osp
import os, struct
import numpy as np


class ReadOnlyChannel(object):
    def __init__(self, name, parent=None):
        if parent is None:
            parent = DLG
        self.parent = parent
        self.name = name

        self.times = []
        self.values = []

    def add_point(self, val, time):
        self.times.append(time)
        self.values.append(val)

    def plot(self):
        self.curve.setData(self.times, self.values)

class Channel(ReadOnlyChannel):
    """A floating point is returned every period seconds"""

    def __init__(self, name, callback=None, period=10, parent=None):
        super(Channel, self).__init__(name, parent)
        if parent is not None:
            self.config_path=self.parent.config_path
        self.timer = QtCore.QTimer()
        self.callback = callback
        self.period = period
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.measure)


    @property
    def filename(self):
        return osp.join(self.parent.directory,self.name+'.dat')

    @property
    def logfile(self):
        return self.config["logfile"]

    def load_data(self):
        with open(self.filename, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=float)
        times = data[::2]
        values = data[1::2]
        for i in range(len(times)):
            self.add_point(values[i], times[i])

    @property
    def active(self):
        return self.timer.isActive()

    @active.setter
    def active(self, val):
        if val:
            self.start()
        else:
            self.stop()
        self.update_json(active=val)
        return val

    def start(self):
        self.timer.start()

    @property
    def period(self):
        return self.timer.interval()/1000

    @period.setter
    def period(self, val):
        self.timer.setInterval(val*1000)
        self.update_json(period=val)
        return val

    def measure(self):
        """Performs the actual measurement. Should return a float"""
        from sys import stdout
        stdout.flush()
        val = self.callback()
        time_ = time.time()
        with open(self.filename, 'ab') as f:
            f.write(struct.pack('d', time_))
            f.write(struct.pack('d', val))
        self.times.append(time_)
        self.values.append(val)
        self.plot()

    def plot(self):
        self.curve.setData(self.times, self.values)

    def stop(self):
        self.timer.stop()

    def setup(self, **kwargs):
        for item in kwargs.keys():
            setattr(self, item, kwargs[item])
        self.update_json(**kwargs)

    def update_json(self, **kwargs):
        with open(self.config_path, 'r') as f:
            dic = json.load(f)
        for item in kwargs.keys():
            dic[item]=kwargs[item]
        with open(self.config_path, 'w') as f:
            json.dump(dic, f)

class DataLogger(object):
    def __init__(self):
        self.channels = {}
        self.loaded_channels = {}
        self.widget = None
        self._directory = None
        self.dialog = QtWidgets.QFileDialog
        self.config_dir = osp.join(os.environ["HOMEDRIVE"], os.environ["HOMEPATH"], '.datalogger')
        if not osp.exists(self.config_dir):
            os.mkdir(self.config_dir)
        self.config_path = osp.join(self.config_dir,'config.json')
        if not osp.exists(self.config_path):
            with open(self.config_path, 'w') as f:
                json.dump("", f)
        with open(self.config_path, 'r') as f:
            dic = json.loads(f.read())
        if dic!="":
            self._previous_directory = dic['directory']
        else:
            self._previous_directory = ""
        self.select_directory()

    @property
    def directory(self):
        if self._directory is None:
            with open(self.config_path, 'r') as f:
                self._directory = json.loads(f.read())['directory']
        return self._directory

    @directory.setter
    def directory(self, val):
        self._directory = val
        with open(self.config_path, 'w') as f:
            json.dump(dict(directory=val), f)

    def select_directory(self):
        directory = self.dialog.getExistingDirectory(
            directory=self._previous_directory)
        self.directory = directory

    def add_channel(self, name, callback):
        self.channels[name] = Channel(name, callback, parent=self)
        with open(self.config_path, 'r') as f:
            dic = json.load(f)
            if name in dic:
                self.channels[name].setup(dict(name, dic[name]))



    def add_read_only_channel(self, name):
        self.loaded_channels[name] = ReadOnlyChannel(name, parent=self)

    def load(self):
        filename, accept = self.dialog.getOpenFileName()
        if filename is not None:
            if '.json' in filename:
                with open(filename, 'r') as f:
                    for line in f:
                        name, val, time = json.loads(line)
                        if not name in self.loaded_channels:
                            self.add_read_only_channel(name)
                        self.loaded_channels[name].add_point(val=val, time=time)
                for ch in self.loaded_channels.values():
                    if self.widget is not None:
                        self.widget.add_read_only_channel(ch, filename)
            elif '.dat' in filename:
                with open(filename, 'rb') as f:
                    data = np.frombuffer(f.read(), dtype=float)
                times = data[::2]
                values = data[1::2]
                name=""
                for s in filename.split('/')[-2::]:
                    name=name+'/'+s
                name = name.split('.')[0]
                if not name in self.loaded_channels:
                    self.add_read_only_channel(name)
                    for i in range(len(times)):
                        self.loaded_channels[name].add_point(val=values[i],
                                                         time=times[i])
                    self.widget.add_read_only_channel(name)

    def gui(self):
        self.widget = DataLoggerGui(self)


class MyTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, dataloggergui):
        super(MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Active", "channel", "period"])
        self.setColumnCount(3)
        self.dataloggergui = dataloggergui
        self.datalogger = self.dataloggergui.datalogger
        self.config_path = self.datalogger.config_path
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
            self.add_channel(ch, color)

    '''
    def add_read_only_channels(self):
        colors = ['white', 'yellow', 'pink', 'purple', 'brown']
        for index, ch in enumerate(
                self.dataloggergui.datalogger.loaded_channels.keys()):
            color = colors[index%len(colors)]
            print (index)
            #print("ch = "+str(ch))
            self.add_read_only_channel(ch, color)
    '''

    def add_read_only_channel(self, ch):
        colors = ['white', 'yellow', 'pink', 'purple', 'brown', 'orange']
        index = len(self.dataloggergui.datalogger.loaded_channels)
        color = colors[index%len(colors)]
        if color=='pink':
            color = QtGui.QColor(236,124,240)
        elif color=='brown':
            color = QtGui.QColor(182,90,90)
        else:
            color = QtGui.QColor(color)
        chan = self.dataloggergui.datalogger.loaded_channels[ch]
        item = QtWidgets.QTreeWidgetItem(["", ch, "0"])
        chan.treeitem = item
        chan.curve = self.dataloggergui.plot_item.plot(pen=color)
        chan.plot()
        self.addTopLevelItem(item)
        #item.setCheckState(0, chan.active)
        item.setBackground(1, color)
        #item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def add_channel(self, ch, color):
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

    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)


    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        return [QtCore.QDateTime(1970,1,1,1,0).addSecs(value).toString(
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
        self.datalogger = datalogger
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


class DataLoggerGui(QtWidgets.QMainWindow):
    def __init__(self, datalogger):
        super(DataLoggerGui, self).__init__()
        self.datalogger = datalogger
        self.graph = pg.GraphicsWindow(title="temperatures")
        self.plot_item = self.graph.addPlot(title="temperatures", axisItems={
            'bottom': TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)
        self._dock_tree = MyDockTreeWidget(self)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)
        self.menubar = DataloggerMenu(datalogger)
        self.setMenuBar(self.menubar)
        self.show()

    def add_read_only_channel(self, channel):
        self._dock_tree.tree.add_channel(channel)

    def add_read_only_channel(self, channel):
        self._dock_tree.tree.add_read_only_channel(channel)



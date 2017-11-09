import os
import os.path as osp
import json
import numpy as np
from shutil import copyfile
import asyncio
from asyncio import ensure_future
import time
import inspect
from asyncio import Future, ensure_future, CancelledError, \
    set_event_loop, TimeoutError
import quamash
import asyncio
import sys
import struct

#modif Edouard
import datetime

from qtpy.QtWidgets import QApplication

from .widgets_plotter import DataPlotterWidget
from .channel_base import ChannelBase, BaseModule

from quamash import QEventLoop, QThreadExecutor
#app = QApplication.instance()
app = QApplication(sys.argv)

set_event_loop(quamash.QEventLoop())

class ChannelPlotter(ChannelBase):

    def initialize(self):
        self._visible = True

    def plot_points(self, vals, times):
        '''
        Erases the current curve and replots all the requested data
        '''

        self.widget.plot_points(vals, times)

    def set_curve_visible(self, val):
        # ignores the visibility toggle until the widget attr has been successfully loaded
        if hasattr(self, 'widget'):
            self.widget.curve.setVisible(val)

    @property
    def name(self):
        return self._name

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, val):
        self._visible = val
        self.set_curve_visible(val)
        self.save_config()

    @property
    def args(self):
        return self.visible

    @args.setter
    def args(self, val):
        self.visible = val

    def load_data(self):
        """Load data from file"""
        with open(self.filename, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=float)
        times = data[::2]
        values = data[1::2]

        values = values[times > self.parent.earliest_point]
        times = times[times > self.parent.earliest_point]

        self.plot_points(values, times)

class DataPlotter(BaseModule):
    widget_type = DataPlotterWidget

    def initialize(self):
        self.config_file = configfilename
        self.show_real_time = False
        self.channel_name_source = self.load_a_channel
        self._days_to_show = 1

    def prepare_path(self, path):
        assert osp.exists(path)
        self.config_file = path

    @property
    def days_to_show(self):
        return self._days_to_show

    @days_to_show.setter
    def days_to_show(self, val):
        self._days_to_show = val
        self.save_config()
        for ch in self.channels.values():
            ch.load_data()

    @property
    def latest_point(self):
        latest_point = self.earliest_point + 24*3600*self.days_to_show#datetime.timedelta(days=self.parent.days_to_load)
        #earliest_point = time.mktime(loadstart_date.timetuple())
        return latest_point

    def save_config(self):
        config = self.get_config_from_file()
        # config["days_to_show"] = self.days_to_show
        self.write_config_to_file(config)

    def load_config(self):
        config = self.get_config_from_file()
        if "days_to_show" in config:
            self.days_to_show = config["days_to_show"]

# from qtpy import QtWidgets, QtCore
# w.addPath("Z:\ManipMembranes\Data Edouard\Datalogger Values\pressure_gauge.chan")
# w = QtCore.QFileSystemWatcher("Z:\ManipMembranes\Data Edouard\Datalogger Values\pressure_gauge.chan")
# w.fileChanged.connect(lambda:print("coucou"))
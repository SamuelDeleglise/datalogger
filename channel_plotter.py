import os
import os.path as osp
import json
import numpy as np
from shutil import copyfile
import asyncio
from asyncio import ensure_future
import time, datetime
import inspect
from asyncio import Future, ensure_future, CancelledError, \
    set_event_loop, TimeoutError
import quamash
import asyncio
import sys
import struct
import bisect
from qtpy import QtCore

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

    def initialize_attributes(self, name):
        self._visible = False
        self._name = name
        self.all_dates = []# an ordered list of all existing dates in the data
        self.load_data()

        config = self.parent.get_config_from_file()
        if self.name in config["channels"]:
            self.load_config()
        else:
            self.save_config()

        self.change_detector = QtCore.QFileSystemWatcher()
        self.change_detector.addPath(self.filename)
        self.change_detector.fileChanged.connect(self.load_and_plot_data)

    def set_curve_visible(self, val):
        # ignores the visibility toggle until the widget attr has been successfully loaded

        if hasattr(self, 'widget'):
            #self.widget.plot_points(self.values, self.times)
            self.widget.curve.setVisible(self.visible)

    @property
    def directory(self):
        return self.parent.directory

    @property
    def filename(self):
        return osp.join(self.directory, self.name + '.chan')

    @property
    def name(self):
        return self._name

    @name.setter #initialises the filename for the corresponding channel if one has been sucessfully loaded
    def name(self, val):
        #os.rename(self.filename, osp.join(self.parent.directory, val + '.chan'))

        config = self.parent.get_config_from_file()
        config['channels'][val] = config['channels'][self._name]
        self.parent.write_config_to_file(config)

        self._name = val

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
        self.times = data[::2]
        self.values = data[1::2]
        self.update_days_with_data()

    def find_intermediate_dates(self, date_start, date_end, index_start, index_end):
        if date_start==date_end:
            pass
        index = bisect.bisect(self.all_dates, date_start)
        bisect.insort(self.all_dates, date_start)
        bisect.insort(self.all_dates, date_end)



    def update_days_with_data(self):
        """
        Maintains a list of days where data have been acquired
        """
        # for now, use a naive method

        """
        current_date = fromtimestamp(self.times[0])
        self.all_dates = []
        def find_intermediate_dates(date_start, date_end):
            all_dates.insert
        """


        current_date = None
        for time in self.times[::10000]:
            new_date = datetime.datetime.fromtimestamp(time)
            if new_date!=current_date:
                current_date = new_date
                if not current_date in self.parent.days_with_data:
                    self.parent.days_with_data.append(current_date)

    def load_and_plot_data(self):
        """Load data from file"""
        self.load_data()
        self.plot_data()

    def plot_data(self):
        if self.widget is not None:
            self.widget.plot_points(self.values, self.times)


class DataPlotter(BaseModule):
    widget_type = DataPlotterWidget

    def initialize(self):
        self._days_to_show = 1
        self._selected_date = datetime.datetime.now()
        self._show_real_time = True
        self.days_with_data = []

    def prepare_path(self, path):
        if osp.isdir(path): # use the default config_file path/dataplotter.conf
            self.config_file = osp.join(path, 'dataplotter.conf')
        else:
            self.config_file = path

    @property
    def days_to_show(self):
        return self._days_to_show

    @days_to_show.setter
    def days_to_show(self, val):
        self._days_to_show = val
        self.save_config()
        self.update_plot()

    @property
    def show_real_time(self):
        return self._show_real_time

    @show_real_time.setter
    def show_real_time(self, val):
        self._show_real_time = val

    @property
    def selected_date(self):
        return self._selected_date

    @selected_date.setter
    def selected_date(self, val):
        self._selected_date = val
        self.save_config()
        self.update_plot()

    @property
    def latest_point(self):
        if self.show_real_time:
            return time.time()
        else:
            selected_timestamp = time.mktime(self.selected_date.timetuple())
            return selected_timestamp

    @property
    def earliest_point(self):
        return self.latest_point - 24*3600*self.days_to_show

    def save_config(self):
        config = self.get_config_from_file()
        config['days_to_show'] = self.days_to_show
        config["show_real_time"] = self.show_real_time
        #config["selected_date"] = self.selected_date
        self.write_config_to_file(config)

    def load_config(self):
        config = self.get_config_from_file()
        if not 'channels' in config:
            config['channels'] = dict() #makes sure the dictionnary is initialised
            self.write_config_to_file(config)
        if "days_to_show" in config:
            self.days_to_show = config["days_to_show"]
        if "show_real_time" in config:
            self.show_real_time = config["show_real_time"]
        '''
        if "selected_date" in config:
            self.selected_date = config["selected_date"]
        '''

    def load_channels(self):
        for val in os.listdir(osp.dirname(self.config_file)):
            if val.endswith('.chan'):
                name = val.rstrip('.chan')
                #prevents reloading all the channels if a new channel is added while running
                #if self.channels[name] not in self.channels:
                self.channels[name] = ChannelPlotter(self, name)

    @property
    def directory(self):
        return osp.dirname(self.config_file)

    def update_plot(self):
        for channel in self.channels.values():
            channel.plot_data()

# from qtpy import QtWidgets, QtCore
# w.addPath("Z:\ManipMembranes\Data Edouard\Datalogger Values\pressure_gauge.chan")
# w = QtCore.QFileSystemWatcher("Z:\ManipMembranes\Data Edouard\Datalogger Values\pressure_gauge.chan")
# w.fileChanged.connect(lambda:print("coucou"))
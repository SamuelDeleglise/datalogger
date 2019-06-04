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
import heapq
import datetime
from datetime import date
from qtpy.QtWidgets import QApplication
from qtpy import QtGui, QtWidgets

from .widgets_plotter import DataPlotterWidget
from .base import ChannelBase, BaseModule

from quamash import QEventLoop, QThreadExecutor
#app = QApplication.instance()
app = QApplication(sys.argv)

set_event_loop(quamash.QEventLoop())

class FileNotFoundError(ValueError): pass


import os

def read_tail(filename, n_floats=64):
    """a generator that returns the last floats of a file in reverse order"""
    with open(filename, 'rb') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        tail_size = n_floats*8 # size of float64
        while remaining_size > 0:
            offset = min(file_size, offset + tail_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, tail_size))
            remaining_size -= tail_size
            yield np.frombuffer(buffer, dtype=float)

def get_last_temperature(temperature_filename = r'Z:\ManipMembranes\Data Cryo\He3 RuO2.chan'):
    a = read_tail(temperature_filename)
    for line in a:
        return float(line[1])

class ChannelPlotter(ChannelBase):
    INDEX = 0
    COLORS = ['#1f77b4',
              '#ff7f0e',
              '#2ca02c',
              '#d62728',
              '#9467bd',
              '#8c564b',
              '#e377c2',
              '#7f7f7f',
              '#bcbd22',
              '#17becf']
    #[QtGui.QColor(name).name() for name in QtGui.QColor.colorNames()]
    def initialize_attributes(self, name):

        self._visible = False
        self._color = self.COLORS[ChannelPlotter.INDEX%len(ChannelPlotter.COLORS)]
        ChannelPlotter.INDEX+=1
        #self._name = name
        self.all_dates = []# an ordered list of all existing dates in the data

        self.change_detector = QtCore.QFileSystemWatcher()
        self.change_detector.addPath(self.filename)
        self.change_detector.fileChanged.connect(
            self.load_last_points_and_plot)


    def set_curve_visible(self, val):
        # ignores the visibility toggle until the widget attr has been successfully loaded
        if self.widget is not None:
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
    def color(self):
        return self._color

    @color.setter
    def color(self, val):
        self._color = val
        if self.widget is not None:
            self.widget.set_color(val)
        self.save_config()

    @property
    def args(self):
        return self.visible, self.color

    @args.setter
    def args(self, val):
        self.visible, self.color = val

    def load_data(self):
        """Load data from file"""
        if osp.exists(self.filename):
            with open(self.filename, 'rb') as f:
                data = np.frombuffer(f.read(), dtype=float)
            self.times = data[::2]
            self.values = data[1::2]
        else:
            raise FileNotFoundError("No file named " + str(self.filename))

    def find_intermediate_dates(self, index_start, index_end):

        if index_end - index_start<=1:
            return
        date_start = date.fromtimestamp(self.times[index_start])
        date_end = date.fromtimestamp(self.times[index_end])
        index_intermediate = (index_start + index_end)//2
        date_intermediate = date.fromtimestamp(self.times[index_intermediate])
        if date_intermediate!=date_start and date_intermediate!=date_end:
            bisect.insort(self.all_dates, date_intermediate)
        if date_intermediate - date_start > datetime.timedelta(1):
            self.find_intermediate_dates(index_start, index_intermediate)
        if date_end - date_intermediate > datetime.timedelta(1):
            self.find_intermediate_dates(index_intermediate, index_end)


    def find_all_dates(self):

        if len(self.times)==0:
            self.all_dates = []
            return self.all_dates
        date_start = date.fromtimestamp(self.times[0])
        self.all_dates = [date_start]
        date_end = date.fromtimestamp(self.times[-1])
        if date_end!=date_start:
            self.all_dates.append(date_end)
        self.find_intermediate_dates(0, len(self.times)-1)

        return self.all_dates

    def load_last_points(self):

        all_times = []
        all_vals = []
        for ind, table in enumerate(read_tail(self.filename)):
            times = table[::2]
            vals = table[1::2]
            all_times = np.concatenate((times, all_times))
            all_vals = np.concatenate((vals, all_vals))
            if times[0]<self.times[-1]: # already past the previous point
                mask = all_times>self.times[-1]
                self.times = np.concatenate((self.times, all_times[mask]))
                self.values = np.concatenate((self.values, all_vals[mask]))
                return


    def load_last_points_and_plot(self):
        """Load data from file"""

        self.load_last_points()
        self.plot_data()

        if not date.fromtimestamp(self.times[-1]) in self.parent.all_dates:
            if self.widget is not None:
                self.parent.widget.set_green_days()


    def plot_data(self):
        if self.widget is not None:
            self.widget.plot_points(self.values, self.times)


class DataPlotter(BaseModule):
    widget_type = DataPlotterWidget

    def initialize(self):

        self._days_to_show = 1
        self._hours_to_show = 0
        self._minutes_to_show = 0
        self._selected_date = datetime.date.today()
        self._show_real_time = True
        self.days_with_data = []

        self.change_detector = QtCore.QFileSystemWatcher([self.directory])
        self.change_detector.directoryChanged.connect(self.update_channel_list)


    def update_channel_list(self):
        keep = []
        for val in os.listdir(osp.dirname(self.config_file)):
            if val.endswith('.chan'):
                name = val[:-5]
                keep.append(name)
                if not name in self.channels.keys():
                    chan = ChannelPlotter(self, name)
                    self.channels[name] = chan
                    chan.widget = chan.create_widget()
        to_remove = []
        for key in self.channels.keys():
            if not key in keep:
                to_remove.append(key)
        for key in to_remove:
            if self.widget is not None:
                self.widget.remove_channel(self.channels[key])
                del self.channels[key]


    def prepare_path(self, path):
        if osp.isdir(path): # use the default config_file path/dataplotter.conf
            self.config_file = osp.join(path, 'dataplotter.conf')
        else:
            self.config_file = path

    def find_all_dates(self):
        self.all_dates = set(heapq.merge(*[channel.find_all_dates() for channel in self.channels.values()]))
        return self.all_dates

    @property
    def seconds_to_show(self):
        return self.days_to_show*3600*24 + self.hours_to_show*3600 + self.minutes_to_show*60

    @property
    def days_to_show(self):
        return self._days_to_show

    @days_to_show.setter
    def days_to_show(self, val):
        self._days_to_show = val
        self.save_config()
        self.update_plot()

    @property
    def hours_to_show(self):
        return self._hours_to_show

    @hours_to_show.setter
    def hours_to_show(self, val):
        self._hours_to_show = val
        self.save_config()
        self.update_plot()

    @property
    def minutes_to_show(self):
        return self._minutes_to_show

    @minutes_to_show.setter
    def minutes_to_show(self, val):
        self._minutes_to_show = val
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
            selected_timestamp = time.mktime(self.selected_date.timetuple()) + 24*3600
            return selected_timestamp

    @property
    def earliest_point(self):
        return self.latest_point - self.seconds_to_show

    def save_config(self):
        config = self.get_config_from_file()
        config['days_to_show'] = self.days_to_show
        config['hours_to_show'] = self.hours_to_show
        config['minutes_to_show'] = self.minutes_to_show
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
        if "hours_to_show" in config:
            self.hours_to_show = config["hours_to_show"]
        if "minutes_to_show" in config:
            self.minutes_to_show = config["minutes_to_show"]
        if "show_real_time" in config:
            self.show_real_time = config["show_real_time"]
        '''
        if "selected_date" in config:
            self.selected_date = config["selected_date"]
        '''

    def load_channels(self):
        print("start")
        from sys import stdout
        stdout.flush()
        
        for val in os.listdir(self.directory):
            if val.endswith('.chan'):
                name = val[:-5]
                #prevents reloading all the channels if a new channel is added while running
                #if self.channels[name] not in self.channels:
                try:
                    self.channels[name] = ChannelPlotter(self, name)
                except FileNotFoundError:
                    pass
        print("stop")
        from sys import stdout
        stdout.flush()
    @property
    def directory(self):
        return osp.dirname(self.config_file)

    def update_plot(self):
        for channel in self.channels.values():
            channel.plot_data()
        if self.widget is not None:
            self.widget.plot_item.setXRange(self.earliest_point, self.latest_point)

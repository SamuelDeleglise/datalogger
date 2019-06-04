import os
import os.path as osp
import json
import numpy as np
from shutil import copyfile
import asyncio
from asyncio import ensure_future
import time
import inspect
#from asyncio import Future, ensure_future, CancelledError, \
 #   set_event_loop, TimeoutError
from pyrpl.async_utils import ensure_future, sleep_async
import quamash
import asyncio
import sys
import struct
import datetime

from qtpy import QtWidgets
from qtpy.QtWidgets import QApplication
from .base import ChannelBase, BaseModule

from .widgets_logger import DataLoggerWidget

from quamash import QEventLoop, QThreadExecutor
#app = QApplication.instance()
app = QApplication(sys.argv)

#set_event_loop(quamash.QEventLoop())

class ChannelLogger(ChannelBase):
    def initialize_attributes(self, name):
        self.error_state = True  # no callback defined at the beginnning
        self.callback_func = None
        self._active = False
        self._delay = 5
        self._callback = "random_coroutine"

    def load_data(self):
        if osp.exists(self.filename): # load existing data (widget needs to exist to plot)
            with open(self.filename, 'r') as f:
                pass
        else: # create a data file
            with open(self.filename, 'w') as f:
                pass

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val): #The config file has to be heavily
        # twicked
        if val==self._name: # nothing changed
            return
        # 0. make sure no other channel has the same name
        if val in self.parent.channels.keys():
            raise ValueError('A channel named %s already exists'%val)
        # 1. change data file name
        os.rename(self.filename, osp.join(self.parent.directory,
                                          val + '.chan'))
        # 2. Change the name in the config file
        config = self.parent.get_config_from_file()
        config['channels'][val] = config['channels'][self._name]
        del config['channels'][self._name]
        self.parent.write_config_to_file(config)
        # 3. Modify the channels dictionnary
        self.parent.channels[val] = self.parent.channels[self._name]
        del self.parent.channels[self._name]
        # 4. Actually perform the rename
        self._name = val

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, val):
        self._callback = val
        self.save_config()
        try:
            func = eval(self.callback,
                        self.parent.script_globals,
                        self.parent.script_locals)
        except BaseException as e:
            self.error_state = True
        else:
            self.error_state = False
            self.callback_func = func

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        if val and not self._active: # Measurement has to be launched again
            ensure_future(self.measure())
        self._active = val
        self.save_config()

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, val):
        self._delay = val
        self.save_config()

    @property
    def args(self):
        return self.active, self.delay, self.callback

    @args.setter
    def args(self, val):
        # set active last to trigger measurement
        active, self.delay, self.callback = val
        self.active = active

    @property
    def filename(self):
        return osp.join(self.parent.directory, self.name + '.chan')

    async def measure(self):
        while(self.active):
            try:
                if inspect.iscoroutinefunction(self.callback_func):
                    val = await self.callback_func()
                else:
                    val = self.callback_func()
            except BaseException as e:
                print(self.name, ':', e)
            else:
                moment = time.time()
                self.save_point(val, moment)
            await sleep_async(self.delay)

    def save_point(self, val, moment):
        """
        Appends a single point at the end of the curve, eventually, removes points that are too old from the curve,
        and saves the val and moment in the channel file.
        """
        with open(self.filename, 'ab') as f:
            f.write(struct.pack('d', moment))
            f.write(struct.pack('d', val))
        #self.parent.latest_point = moment
        #self.widget.plot_point(val, moment)

class DataLogger(BaseModule):
    widget_type = DataLoggerWidget

    def initialize(self):
        self.script_globals = dict()
        self.script_locals = dict()
        self.run_start_script()

    def prepare_path(self, path):
        self.directory = path
        if not osp.exists(self.directory):
            os.mkdir(self.directory)

        if not osp.exists(self.script_file):
            copyfile(osp.join(osp.dirname(__file__),
                               'start_script_template.py'),
                      self.script_file)

    def save_config(self):
        config = self.get_config_from_file()
        self.write_config_to_file(config)

    def load_config(self):
        pass

    def run_start_script(self):
        self.script_locals = dict()
        self.script_globals = dict()
        with open(self.script_file, 'r') as f:
            exec(f.read(), self.script_globals, self.script_locals)

    def new_channel(self):
        name = self.get_unique_ch_name()
        self.channels[name] = ChannelLogger(self, name)
        if self.widget is not None:
            self.widget.create_channel(self.channels[name])
        return self.channels[name]

    def remove_channel(self, channel):
        name = channel.name
        if not name in self.channels:
            return
        file_size = osp.getsize(channel.filename)
        if file_size>0:
            reply = QtWidgets.QMessageBox.question(None, 'Confirmation',
            'Are you sure you want to delete the file %s, containing %i data points ?'%(channel.filename, file_size//16)) == QtWidgets.QMessageBox.Yes
        else:
            reply = True
        if reply:
            os.remove(channel.filename)
            if self.widget is not None:
                self.widget.remove_channel(channel)
            self.channels[name].active = False
            del self.channels[name]
            config = self.get_config_from_file()
            del config['channels'][name]
            self.write_config_to_file(config)

    def get_unique_ch_name(self):
        name = 'new_channel'
        index = 0
        while (name in self.channels.keys()):
            index += 1
            name = 'new_channel' + str(index)
        return name

    def load_channels(self):
        config = self.get_config_from_file()
        if 'channels' in config:
            for name in config['channels'].keys():
                self.channels[name] = ChannelLogger(self, name)
        else:
            config['channels'] = dict()
            self.write_config_to_file(config)

    @property
    def config_file(self):
        return osp.join(self.directory, 'datalogger.conf')

    @property
    def script_file(self):
        return osp.join(self.directory, 'start_script.py')

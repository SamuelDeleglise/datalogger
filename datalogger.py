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

from qtpy.QtWidgets import QApplication

from .widgets import DataLoggerWidget

from quamash import QEventLoop, QThreadExecutor
#app = QApplication.instance()
app = QApplication(sys.argv)

set_event_loop(quamash.QEventLoop())

class Channel(object):
    def __init__(self, parent, name):
        self._name = name
        self.parent = parent
        self.error_state = True # no callback defined at the beginnning
        #self.times = []
        #self.values = []

        self._callback = "random_coroutine"
        self._visible = True
        self._active = False
        self._delay = 5

        self.callback_func = None

        if osp.exists(self.filename): # load existing data
            self.load_data()
        else: # create a data file
            with open(self.filename, 'w') as f:
                pass
        config = self.parent.get_config_from_file()
        if self.name in config["channels"]:
            self.load_config()
        else:
            self.save_config()
        self.widget = self.create_widget()

    def create_widget(self):
        return self.parent.widget.create_channel(self)

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
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, val):
        self._visible = val
        self.save_config()

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

    def save_config(self):
        config = self.parent.get_config_from_file()
        config['channels'][self.name] = self.args
        self.parent.write_config_to_file(config)

    def load_config(self):
        config = self.parent.get_config_from_file()
        self.args = config['channels'][self.name]

    @property
    def args(self):
        return self.visible, self.active, self.delay, self.callback

    @args.setter
    def args(self, val):
        # set active last to trigger measurment
        self.visible, active, self.delay, self.callback = val
        self.active = active


    def load_data(self):
        """Load data from file"""
        with open(self.filename, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=float)
        self.times = data[::2]
        self.values = data[1::2]

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
            moment = time.time()
            self.plot_point(val, moment)
            await asyncio.sleep(self.delay)

    def plot_point(self, val, moment):
        self.widget.plot_point(val, moment)

class DataLogger(object):
    def __init__(self, directory=None):
        """
        If directory is None, uses the default home directory (+.datalogger)
        """

        self.channels = dict()
        if directory is None:
            directory = osp.join(os.environ["HOMEDRIVE"], os.environ[
                "HOMEPATH"], '.datalogger')
        self.directory = directory
        if not osp.exists(self.directory):
            os.mkdir(self.directory)

        if not osp.exists(self.script_file):
            copyfile(osp.join(osp.dirname(__file__),
                               'start_script_template.py'),
                      self.script_file)

        self.script_globals = dict()
        self.script_locals = dict()
        self.run_start_script()

        self.widget = DataLoggerWidget(self)
        self.load_channels()

    def run_start_script(self):
        self.script_locals = dict()
        self.script_globals = dict()
        with open(self.script_file, 'r') as f:
            exec(f.read(), self.script_globals, self.script_locals)


    def load_channels(self):
        config = self.get_config_from_file()
        if 'channels' in config:
            for name in config['channels'].keys():
                self.channels[name] = Channel(self, name)
        else:
            config['channels'] = dict()
            self.write_config_to_file(config)

    def new_channel(self):
        name = self.get_unique_ch_name()
        self.channels[name] = Channel(self, name)

    def get_unique_ch_name(self):
        name = 'new_channel'
        index = 0
        while(name in self.channels.keys()):
            index+=1
            name = 'new_channel' + str(index)
        return name

    @property
    def config_file(self):
        return osp.join(self.directory, 'datalogger.conf')

    @property
    def script_file(self):
        return osp.join(self.directory, 'start_script.py')

    def get_config_from_file(self):
        if not osp.exists(self.config_file):
            return dict()
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def write_config_to_file(self, config_dict):
        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f)

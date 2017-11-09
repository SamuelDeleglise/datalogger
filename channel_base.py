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
from qtpy.QtWidgets import QApplication
import datetime
from qtpy import QtCore

from .widgets_logger import DataLoggerWidget

from quamash import QEventLoop, QThreadExecutor
#app = QApplication.instance()
APP = QApplication(sys.argv)


LOOP = quamash.QEventLoop()
set_event_loop(LOOP)


def sleep_with_loop(interval):
    f = ensure_future(asyncio.sleep(interval))
    while not f.done():
        APP.processEvents()


class ChannelBase(object):

    def __init__(self, parent, name):
        self._name = name
        self.parent = parent
        self.initialize_attributes()
        self.widget = self.create_widget()
        self.initialize()

    def intialize_attributes(self):
        pass

    def create_widget(self):
        return self.parent.widget.create_channel(self)

    def load_config(self):
        config = self.parent.get_config_from_file()
        self.args = config['channels'][self.name]

    def save_config(self):
        config = self.parent.get_config_from_file()
        config['channels'][self.name] = self.args
        self.parent.write_config_to_file(config)


class BaseModule(object):
    """
    Base module for Datalogger and DataPlotter
    """

    def __init__(self, path=None):
        """
        If directory is None, uses the default home directory (+.datalogger)
        """

        self.channels = dict()
        self.prepare_path(path)
        self.initialize()
        self.load_config()
        self.widget = self.widget_type(self)
        self.load_channels()



    def get_config_from_file(self):
        if not osp.exists(self.config_file):
            return dict()
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def write_config_to_file(self, config_dict):
        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f)

    def load_a_channel(self):
        '''
        Should give a choice of exising channels and load the selected one 
        '''

        pass
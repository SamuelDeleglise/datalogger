import os.path as osp
import os
import shutil
import time
import numpy as np
from ..channel_base import sleep_with_loop

from .. import DataLogger

class TestBase(object):
    def setUp(self):
        self.dir = osp.join(osp.dirname(__file__), "test_data")
        if not osp.exists(self.dir):
            os.mkdir(self.dir)
        self.dlg = DataLogger(self.dir)
        print("Setting up (Base)")

    def tearDown(self):
        shutil.rmtree(self.dir)
        print("Tearing down (base)")


class TestDataLogger(TestBase):

    def test_create_datalogger(self):
        #self.dlg = DataLogger() # This should be open in a special "sandbox" directory
        pass

    def test_new_channel(self):
        #self.dlg = DataLogger()
        self.dlg.new_channel()

    def test_configs(self):
        #self.dlg = DataLogger()
        self.dlg.load_config()
        self.dlg.save_config()


class TestChannels(TestBase):

    def setUp(self):
        super(TestChannels, self).setUp()
        self.chan = self.dlg.new_channel()
        print("Setting Up")

    def test_channel_callback(self):
        self.chan.callback = 'zzz'
        assert self.chan.error_state

        self.chan.callback = 'random_func'
        assert not self.chan.error_state

    def test_acquisition(self):
        self.chan.delay = 0.
        self.chan.active = True
        sleep_with_loop(1.)
        with open(self.chan.filename, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=float)
        times = data[::2]
        values = data[1::2]

        assert(len(times)==len(values) and len(times)>0)
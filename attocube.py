import serial
from serial import Serial
import socket
import sys
from asyncio import Future, ensure_future, CancelledError, \
    set_event_loop, TimeoutError
import quamash
import asyncio
import warnings
import time
import numpy as np

# from .wiznet import SerialFromEthernet
from .async_utils import wait
from .serial_interface import SerialInstrument


class FalseAttocubeReplyError(Exception):
    pass


class Attocube(object):
    # made from scratch without using serial-interface due to its unique format (multiple lined responses)
    LINEBREAK = '\r\n'
    PROMPT = '> '  # some instruments also reply with a prompt after the linebreak, such as >
    TIMEOUT = 2
    PARITY = serial.PARITY_NONE
    STROPBITS = serial.STOPBITS_ONE
    BYTESIZE = 8
    BAUDRATE = 38400

    XONXOFF = False
    RTSCTS = False
    DSRDTR = False

    #ERROR = FalseAttocubeReplyError

    def __init__(self, ip, want_full_startup=True, ip_or_port='COM1', *args, **kwds):
        self.ip = ip
        self.parameters = {"linebreak": self.LINEBREAK, "prompt": self.PROMPT}
        self.axes = ['x', 'z', 'y']  # must be arranged in the same order as the axes on the attocube driver
        # self.direction_flip = [-1, 1, -1]  # added manually to make directions correspond with the desired image

        self.a = MultilineWiznet(self.ip, self.parameters)

        if want_full_startup:
            for index in range(len(self.axes)):
                self.a.ask_sync("setm %i stp\r\n" % (index+1))

    def check_capacity(self, ax):
        """
        Returns the capacity measured on the desired axis, in nF. Returns NaN if the reply from the attocube isn't
        as indicated in the documentation
        :param ax:
        :return: capacity
        """
        ax_no = self.axes.index(ax) + 1
        self.a.ask_sync('setm {} cap'.format(ax_no))
        capacity = self.a.ask_sync('getc {}'.format(ax_no))
        self.a.ask_sync('setm {} stp'.format(ax_no))
        start = capacity.find('=')
        end = capacity.find(' nF')
        try:
            capacity = int(capacity[start+2:end])
        except ValueError as e:
            capacity = np.nan
            print(e)
        return capacity

    def check_mode(self, ax):
        """
        Checks the mode in which all axes currently are.
        :return: a 3-letter string corresponding to the mode of the axis for each axis
        """
        ax_no = self.axes.index(ax) + 1
        res = self.a.ask_sync('getm {}'.format(ax_no))
        start = res.find('= ')
        end = res.find('\r\nOK')
        mode = res[start+2:end]
        return mode

    def ensure_step_mode(self, *axes):
        """
        Checks the mode of all given axes; If they aren't "stp", switches it to that. Otherwise it does nothing.
        It returns the state the axes were in originally.
        :param axes:
        :return: previous_mode
        """
        previous_modes = []
        for ax in axes:
            current_mode = self.check_mode(ax)
            if current_mode != 'stp':
                ax_no = self.axes.index(ax) + 1
                res = self.a.ask_sync('setm {} stp'.format(ax_no))
            previous_modes.append(current_mode)
        return previous_modes

    def check_connections(self):
        """
        Does the check in order of the attribute self.axes. Returns 1 if it is connected, 0 otherwise
        :return:
        """
        connected_check = [0, 0, 0]
        for i in range(len(self.axes)):
            if self.check_capacity(self.axes[i]):
                connected_check[i] = 1
        return connected_check

    def steps(self, ax, numsteps, time_per_step=1/400):
        ''' Advances by numsteps along the given axis ax.
        The axes are indicated on the attocube generator '''
        # note: exists command for faster, not implemented

        if ax not in self.axes:
            warnings.warn("Direction asked for doesn't exists")
            pass
        else:
            dir = self.axes.index(ax) + 1
            string = "stepd" if numsteps < 0 else "stepu"
            try:
                self.a.ask_sync("%s %i %i"%(string, dir, abs(numsteps)))
            except FalseAttocubeReplyError as e:
                print(e)
            time.sleep(int(round(abs(numsteps)*time_per_step)))


class MultilineWiznet(object):
    """
    a serial interface includes a function "ask"
    """
    CONNECT_DELAY = 0.1
    # SEND_DELAY = 0.1
    # CLOSE_DELAY = 0.1
    PORT = 5000
    N_RETRIES = 50

    def __init__(self, ip, parameters):
        self.ip = ip
        self.parameters = parameters

    async def write(self, val):
        for retry in range(self.N_RETRIES):
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.setblocking(0)  # connect, send, and receive should return
            # or fail immediately
            try:
                conn.connect((self.ip, self.PORT))
            except BlockingIOError as e:  # always fails to connect instantly
                pass
            await asyncio.sleep(self.CONNECT_DELAY) # (even with a succesful
            # blocking connect, a delay seems to be needed by the wiznet
            string = (val + self.parameters['linebreak']).encode('utf-8')
            try:
                conn.send(string)
                return
            except OSError as e: # send failed because connection is not
                # available
                continue # continue with the retry loop
            finally: # In any case, the connection should be closed
                try:
                    conn.shutdown(socket.SHUT_WR) # closes quickly
                except OSError as e:  # socket already disconnected
                    pass
                finally:
                    await asyncio.sleep(self.CLOSE_DELAY)
                    conn.close()
        raise ValueError("Failed to connect after %i retries"%self.N_RETRIES)

    async def ask(self, val):
        for retry in range(self.N_RETRIES):
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.setblocking(0)  # connect, send, and receive should return
            # or fail immediately
            try:
                conn.connect((self.ip, self.PORT))
            except BlockingIOError as e:  # always fails to connect instantly
                pass
            await asyncio.sleep(self.CONNECT_DELAY)  # (even with a succesful
            # blocking connect, a delay seems to be needed by the wiznet
            try:
                conn.recv(1024)  # Make sure the buffer is empty
            except OSError as e:
                pass
            await asyncio.sleep(self.CONNECT_DELAY)
            string = (val + self.parameters['linebreak']).encode('utf-8')
            try:
                conn.send(string)
                await asyncio.sleep(self.CONNECT_DELAY)
                result = conn.recv(1024)
                result = result.decode()
                try:
                    assert result.endswith(self.parameters['linebreak']
                                           + self.parameters['prompt'])  # to make sure all data have been received
                    return result.rstrip(self.parameters['linebreak'] + self.parameters['prompt'])
                except AssertionError:
                    raise FalseAttocubeReplyError(repr('last line from Attocube: {}'.format(result)))
            except OSError as e:  # send failed because connection is not
                # available
                continue  # continue with the retry loop
            finally:  # In any case, the connection should be closed
                try:
                    conn.shutdown(socket.SHUT_WR)  # closes quickly
                except OSError as e:  # socket already disconnected
                    pass
                finally:
                    await asyncio.sleep(self.CONNECT_DELAY)
                    conn.close()
        raise ValueError("Failed to connect after %i retries"%self.N_RETRIES)

    def ask_sync(self, val):
        return wait(self.ask(val))

    def write_sync(self, val):
        return wait(self.write(val))

import serial
from serial import Serial
import socket
import sys
from asyncio import Future, ensure_future, CancelledError, \
    set_event_loop, TimeoutError
import quamash
import asyncio
import warnings

# from .wiznet import SerialFromEthernet
from .async_utils import wait
from .serial_interface import SerialInstrument


class Attocube(object):
# made from scratch without using serial-interface due to its unique format (multiple lined responses)
    linebreak = '\r\n'
    prompt = '> '  # some instruments also reply with a prompt after the linebreak, such as >
    timeout = 2
    parity = serial.PARITY_NONE
    stopbits = serial.STOPBITS_ONE
    bytesize = 8
    baudrate = 38400

    xonxoff = False
    rtscts = False
    dsrdtr = False

    def __init__(self, ip, ip_or_port='COM1', *args, **kwds):
        self.ip = ip
        self.parameters = {"linebreak": "\r\n", "prompt": '> '}

        self.a = MultilineWiznet(self.ip, self.parameters)

        for index in (1, 2, 3):
            self.a.ask_sync("setm %i stp\r\n"%index)

    def steps(self, ax, numsteps):
        ''' Advances by numsteps along the given axis ax.
        The axes are indicated on the attocube generator '''
        # note: exists command for faster, not implemented
        directions = ['x', 'y', 'z']

        if ax not in directions:
            warnings.warn("Direction asked for doesn't exists")
            pass
        else:
            if ax == 'x':
                dir = 1
            if ax == 'y':
                dir = 3
            if ax == 'z':
                dir = 2
            string = "stepd" if numsteps < 0 else "stepu"
            self.a.ask_sync("%s %i %i"%(string, dir, abs(numsteps)))


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
            conn.setblocking(0) # connect, send, and receive should return
            # or fail immediately
            try:
                conn.connect((self.ip, self.PORT))
            except BlockingIOError as e: # always fails to connect instantly
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
            conn.setblocking(0) # connect, send, and receive should return
            # or fail immediately
            try:
                conn.connect((self.ip, self.PORT))
            except BlockingIOError as e: # always fails to connect instantly
                pass
            await asyncio.sleep(self.CONNECT_DELAY) # (even with a succesful
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
                assert result.endswith(self.parameters['linebreak']
                                       + self.parameters['prompt']) # to make sure all data have been received
                return result.rstrip(self.parameters['linebreak'] + self.parameters['prompt'])
            except OSError as e: # send failed because connection is not
                # available
                continue # continue with the retry loop
            finally: # In any case, the connection should be closed
                try:
                    conn.shutdown(socket.SHUT_WR) # closes quickly
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


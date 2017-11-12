from serial import Serial
import socket
import sys
from asyncio import Future, ensure_future, CancelledError, \
    set_event_loop, TimeoutError
import quamash
import asyncio

from serial import SerialException


def serial_interface_factory(ip_or_port, **kwds):
    """
    Returns either a Wiznet or a Serial object, depending on ip_or_port.
    kwds are the extra parameters for the Serial object (unfortunately, have
    to be set manually in the wiznet for an ethernet connection).
    """
    if ip_or_port.find("COM") >= 0:  # serial port
        return SerialConnection(ip_or_port, **kwds)
    else:
        return Wiznet(ip_or_port)


class SerialInterface(object):
    """
    Asynchronous serial interface.
    Exposes an asynchronous coroutine "ask".
    """
    N_RETRIES = 1
    linebreak = '\n'

    async def ask(self, val):
        raise NotImplementedError("To implement in a derived class")


class SerialConnection(SerialInterface):
    """
    a serial object includes a function "ask".
    The linebreak attribute has to be set properly for ask to work.
    The serial port is closed outside calls of function 'ask'
    """

    baudrate = 9600
    bytesize = 8
    parity = 'O'
    stopbits = 1
    timeout = None
    xonxoff = False
    rtscts = False
    dsrdtr = False

    def __init__(self, port):
        self.port = port

    @property
    def conn_kwds(self):
        return dict(port=self.port, baudrate=self.baudrate,
                    bytesize=self.bytesize, parity=self.parity,
                    stopbits=self.stopbits, timeout=self.timeout,
                    xonxoff=self.xonxoff, rtscts=self.rtscts,
                    dsrdtr=self.dsrdtr)

    async def write(self, val):
        for retry in range(self.N_RETRIES):
            try:
                with Serial(**self.conn_kwds) as ser:
                    ser.write((val + self.linebreak).encode())
                    return
            except SerialException as e:
                continue
        raise ValueError("Failed to connect after %i retries" % self.N_RETRIES)

    async def ask(self, val):
        for retry in range(self.N_RETRIES):
            try:
                with Serial(**self.conn_kwds) as ser:
                    ser.write((val + self.linebreak).encode())
                    return ser.readline().decode().rstrip(self.linebreak)
            except SerialException as e:
                continue
        raise ValueError("Failed to connect after %i retries" % self.N_RETRIES)


class Wiznet(SerialInterface):
    """
    a serial interface includes a function "ask"
    """
    CONNECT_DELAY = 0.1
    #SEND_DELAY = 0.1
    #CLOSE_DELAY = 0.1
    PORT = 5000

    def __init__(self, ip):
        self.ip = ip

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
            string = (val + self.linebreak).encode('utf-8')
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
            string = (val + self.linebreak).encode('utf-8')
            try:
                conn.send(string)
                await asyncio.sleep(self.CONNECT_DELAY)
                result = conn.recv(1024)
                result = result.decode()
                assert result.endswith(self.linebreak) # to make sure all data have been received
                return result.rstrip(self.linebreak)
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


class SerialInstrument(object):
    """
    Is created with SerialInstrument(ip_or_port, **kwds):
    an instance member "serial" with the right interface depending on
    ip_or_port (COM1--> SerialInterface, '10.214.1.85'--> Wiznet) is
    created. The remaining kwds are used for the SerialInterface constructor.
    """
    CONNECT_DELAY = 0.1
    N_RETRIES = 10
    baudrate = 9600
    bytesize = 8
    parity = 'O'
    stopbits = 1
    timeout = None
    xonxoff = False
    rtscts = False
    dsrdtr = False
    linebreak = '\n'

    def __init__(self, ip_or_port='COM1', **kwds):
        self.serial = serial_interface_factory(ip_or_port, **kwds)
        self.serial.linebreak = self.linebreak
        self.serial.CONNECT_DELAY = self.CONNECT_DELAY
        self.serial.N_RETRIES = self.N_RETRIES
        self.serial.parity = self.parity
        self.serial.stopbits = self.stopbits
        self.serial.baudrate = self.baudrate
        self.serial.bytesize = self.bytesize
        self.serial.dsrdtr = self.dsrdtr
        self.serial.rtscts = self.rtscts
        self.serial.timeout = self.timeout
        self.serial.xonxoff = self.xonxoff

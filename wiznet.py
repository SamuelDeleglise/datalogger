import socket

class SerialFromEthernet(object):
    TCP_PORT = 5000
    BUFFER_SIZE = 1024

    def __init__(self, ip):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, self.TCP_PORT))
        self.socket.setblocking(False)
        #self.socket.settimeout(1)

    def write(self, val):
        self.socket.send(val)

    def read(self):
        st = ''
        while(True):
            try:
                st+=self.socket.recv(self.BUFFER_SIZE)
            except socket.error:
                return st

    def readline(self):
        st = ''
        char = ''
        while (char!='\n'):
            try:
                char = self.socket.recv(self.BUFFER_SIZE)
                st += char
            except socket.error:
                return st
        return st
import socket

class SerialFromEthernet(object):
    TCP_PORT = 5000
    BUFFER_SIZE = 1024

    def __init__(self, ip, baudrate=9600, ):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.1)
        try:
            self.socket.connect((ip, self.TCP_PORT))
        except socket.error:
            print("could not connect to ip:" + str(ip))
        else:
            self.socket.setblocking(False)

        #self.socket.settimeout(1)

    def write(self, val):
        self.socket.send(val.encode('utf-8'))

    def read(self):
        st = ''
        while(True):
            try:
                st+=self.socket.recv(self.BUFFER_SIZE).decode('utf-8')
            except socket.error:
                return st

    def readline(self):
        st = ''
        char = ''
        while (char!='\n'):
            try:
                char = self.socket.recv(1)
                st += char.decode("utf-8")
            except socket.error:
                return st
        return st

    def ask(self,val, timeout=-1):
        self.write(val)

        return self.readline()

